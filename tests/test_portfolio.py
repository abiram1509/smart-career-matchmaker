import base64,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from auth_fixture import sign_in
from backend import main,portfolio
from backend.loader import HybridJobLoader

class PortfolioTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  fixture=HybridJobLoader(self.root/'none.csv',self.root/'none.json','')
  for target,value in [('DB',self.root/'test.db'),('HybridJobLoader',lambda:fixture)]:
   p=patch.object(main,target,value);p.start();self.addCleanup(p.stop)
  p=patch.object(portfolio,'STORAGE',self.root/'private');p.start();self.addCleanup(p.stop)
  self.client=TestClient(main.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)
 def payload(self,**extra):
  return {'title':'Course certificate','filename':'certificate.pdf','content_base64':base64.b64encode(b'%PDF-1.4\nTest document').decode(),**extra}
 def upload(self):
  response=self.client.post('/api/portfolio/upload',json=self.payload())
  self.assertEqual(response.status_code,201,response.text);return response.json()
 def test_upload_download_private_and_owner_review(self):
  self.assertEqual(self.client.get('/api/portfolio').status_code,401)
  sign_in(self.client,'portfolio-one');doc=self.upload()
  self.assertEqual(doc['status'],'self-reported');self.assertNotIn('file_reference',doc)
  download=self.client.get(doc['download_url']);self.assertEqual(download.content,b'%PDF-1.4\nTest document')
  self.assertIn('attachment',download.headers['content-disposition'])
  self.assertEqual(download.headers['content-type'],'application/octet-stream')
  self.assertEqual(self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'}).status_code,403)
  sign_in(self.client,'portfolio-two');self.assertEqual(self.client.get('/api/portfolio').json(),[])
  self.assertEqual(self.client.get(doc['download_url']).status_code,404)
  for role in ['faculty','institution','industry']:
   sign_in(self.client,'portfolio-'+role,role)
   self.assertEqual(self.client.get('/api/portfolio').status_code,403)
   self.assertEqual(self.client.get(doc['download_url']).status_code,403)
  sign_in(self.client,'portfolio-owner','owner')
  self.assertEqual(len(self.client.get('/api/portfolio').json()),1)
  result=self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'})
  self.assertEqual(result.status_code,200,result.text);self.assertTrue(result.json()['verified_at'])
  with main.connection() as db:self.assertEqual(db.execute('SELECT verified_by FROM portfolio_documents').fetchone()[0],'portfolio-owner')
  sign_in(self.client,'portfolio-one');self.assertEqual(self.client.get('/api/portfolio').json()[0]['status'],'verified')

 def test_validation_upload_limit_and_request_protection(self):
  sign_in(self.client,'portfolio-invalid')
  for body in [self.payload(filename='../certificate.pdf'),self.payload(filename='run.exe'),self.payload(title=' '),self.payload(content_base64='%%%'),self.payload(content_base64=base64.b64encode(b'not a PDF').decode())]:
   self.assertEqual(self.client.post('/api/portfolio/upload',json=body).status_code,422)
  with patch.object(portfolio,'MAX_BODY',50):
   self.assertEqual(self.client.post('/api/portfolio/upload',json=self.payload()).status_code,413)
  self.assertEqual(self.client.post('/api/portfolio/upload',json=self.payload(),headers={'X-Bridge-Request':''}).status_code,403)
  self.assertEqual(self.client.get('/api/portfolio').json(),[])
  self.assertFalse(portfolio.STORAGE.exists())

 def test_portfolio_never_changes_assessment_or_jobs(self):
  sign_in(self.client,'portfolio-isolated')
  with main.connection() as db:
   db.execute('INSERT INTO profiles(id,vector,updated,track) VALUES (?,?,?,?)',('portfolio-isolated',json.dumps({'Python':8}),'test','backend'))
   tables=['profiles','assessment_sessions','questions','jobs','history','applications']
   before={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  doc=self.upload();sign_in(self.client,'portfolio-admin','owner')
  self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'})
  with main.connection() as db:
   after={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  self.assertEqual(before,after)
  self.assertEqual(self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'self-reported'}).json()['verified_at'],None)

 def test_missing_file_and_student_limit(self):
  sign_in(self.client,'portfolio-limit');doc=self.upload()
  with main.connection() as db:
   row=db.execute('SELECT * FROM portfolio_documents').fetchone()
   for i in range(29):
    db.execute('INSERT INTO portfolio_documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',('extra'+str(i),row['student_id'],'missing'+str(i),'Extra','self-reported',row['uploaded_at'],'extra.pdf',1,'test',None,None))
  self.assertEqual(self.client.post('/api/portfolio/upload',json=self.payload()).status_code,409)
  (portfolio.STORAGE/row['file_reference']).unlink()
  self.assertEqual(self.client.get(doc['download_url']).status_code,404)
