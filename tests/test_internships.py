import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from auth_fixture import sign_in
from backend import main
from backend.loader import HybridJobLoader

class InternshipTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
  fixture=HybridJobLoader(root/'none.csv',root/'none.json','')
  for key,value in [('DB',root/'test.db'),('HybridJobLoader',lambda:fixture)]:
   p=patch.object(main,key,value);p.start();self.addCleanup(p.stop)
  self.client=TestClient(main.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)
  sign_in(self.client,'faculty-one','faculty');sign_in(self.client,'faculty-two','faculty')
  sign_in(self.client,'student-one')
 def create(self):
  response=self.client.post('/api/internships',json={'title':'Summer internship at X','mentor_id':'faculty-one'})
  self.assertEqual(response.status_code,201,response.text)
  return response.json()['id']

 def test_creation_feedback_timeline_and_completion(self):
  mentors=self.client.get('/api/internships/mentors').json()
  self.assertEqual({m['id'] for m in mentors},{'faculty-one','faculty-two'})
  self.assertNotIn('email',mentors[0])
  identity=self.create()
  record=self.client.get('/api/internships').json()[0]
  self.assertEqual(record['student_id'],'student-one');self.assertEqual(record['status'],'ongoing');self.assertEqual(record['feedback'],[])
  sign_in(self.client,'faculty-one','faculty')
  self.assertEqual(self.client.get('/api/internships').json()[0]['id'],identity)
  for text in ['First feedback','Second feedback\nWith detail']:
   response=self.client.post('/api/internships/'+identity+'/feedback',json={'feedback_text':text})
   self.assertEqual(response.status_code,201,response.text);self.assertEqual(response.json()['author'],'faculty-one')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'}).status_code,200)
  sign_in(self.client,'student-one')
  record=self.client.get('/api/internships').json()[0]
  self.assertEqual(record['status'],'completed')
  self.assertEqual([f['feedback_text'] for f in record['feedback']],['Second feedback\nWith detail','First feedback'])

 def test_other_students_and_unassigned_mentors_cannot_access_or_write(self):
  identity=self.create()
  sign_in(self.client,'student-two')
  self.assertEqual(self.client.get('/api/internships').json(),[])
  self.assertEqual(self.client.post('/api/internships/'+identity+'/feedback',json={'feedback_text':'Forged'}).status_code,403)
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'}).status_code,403)
  sign_in(self.client,'faculty-two','faculty')
  self.assertEqual(self.client.get('/api/internships').json(),[])
  self.assertEqual(self.client.post('/api/internships/'+identity+'/feedback',json={'feedback_text':'Forged'}).status_code,404)
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'}).status_code,404)
  with main.connection() as db:self.assertEqual(db.execute('SELECT count(*) FROM internship_feedback').fetchone()[0],0)

 def test_role_checks_validation_and_forged_fields(self):
  for body in [{'title':' ','mentor_id':'faculty-one'},{'title':'Title','mentor_id':'missing'},{'title':'Title','mentor_id':'student-one'},{'title':'Title','mentor_id':'faculty-one','student_id':'student-two'}]:
   self.assertIn(self.client.post('/api/internships',json=body).status_code,[404,422])
  identity=self.create()
  sign_in(self.client,'faculty-one','faculty')
  for body in [{'feedback_text':' '},{'feedback_text':'x'*3001},{'feedback_text':'Text','author':'faculty-two'}]:
   self.assertEqual(self.client.post('/api/internships/'+identity+'/feedback',json=body).status_code,422)
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'approved'}).status_code,422)
  for role in ['industry','institution','owner']:
   sign_in(self.client,'role-'+role,role)
   self.assertEqual(self.client.get('/api/internships').status_code,403)
   self.assertEqual(self.client.get('/api/internships/mentors').status_code,403)
   self.assertEqual(self.client.post('/api/internships',json={'title':'Title','mentor_id':'faculty-one'}).status_code,403)

 def test_existing_auth_and_request_protection(self):
  self.client.cookies.clear()
  self.assertEqual(self.client.get('/api/internships').status_code,401)
  sign_in(self.client,'student-one')
  self.assertEqual(self.client.post('/api/internships',json={'title':'Title','mentor_id':'faculty-one'},headers={'X-Bridge-Request':''}).status_code,403)

 def test_no_assessment_matching_portfolio_or_notification_mutations(self):
  tables=['profiles','assessment_sessions','questions','jobs','history','applications','portfolio_documents','job_alert_subscriptions','match_alerts']
  with main.connection() as db:
   before={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  identity=self.create();sign_in(self.client,'faculty-one','faculty')
  self.client.post('/api/internships/'+identity+'/feedback',json={'feedback_text':'Useful review'})
  self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'})
  with main.connection() as db:
   after={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  self.assertEqual(before,after)

 def upload(self,identity,filename='report.txt',content=b'Internship report'):
  import base64
  return self.client.post('/api/internships/'+identity+'/documents',json={'title':'Internship report','filename':filename,'content_base64':base64.b64encode(content).decode()})

 def test_evidence_submission_download_and_private_metadata(self):
  identity=self.create();response=self.upload(identity)
  self.assertEqual(response.status_code,201,response.text);document=response.json()
  self.assertNotIn('content',document)
  listed=self.client.get('/api/internships').json()[0]['documents']
  self.assertEqual(len(listed),1);self.assertNotIn('content',listed[0])
  for account,role in [('student-one','student'),('faculty-one','faculty')]:
   sign_in(self.client,account,role)
   response=self.client.get(document['download_url'])
   self.assertEqual(response.status_code,200);self.assertEqual(response.content,b'Internship report')
   self.assertEqual(response.headers['cache-control'],'no-store')
   self.assertIn('attachment',response.headers['content-disposition'])

 def test_evidence_cannot_be_read_or_written_by_other_accounts(self):
  identity=self.create();document=self.upload(identity).json()
  for account,role in [('student-two','student'),('faculty-two','faculty'),('industry','industry'),('owner','owner'),('institution','institution')]:
   sign_in(self.client,account,role)
   self.assertIn(self.client.get(document['download_url']).status_code,[403,404])
   self.assertIn(self.upload(identity).status_code,[403,404])
  sign_in(self.client,'faculty-one','faculty')
  self.assertEqual(self.upload(identity).status_code,403)
  sign_in(self.client,'student-one')
  other=self.create()
  self.assertEqual(self.client.get(document['download_url'].replace(identity,other)).status_code,404)

 def test_rejection_reason_permissions_preservation_and_reopening(self):
  identity=self.create();document=self.upload(identity).json()
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'rejected','reason':'Stopped'}).status_code,403)
  sign_in(self.client,'faculty-two','faculty')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'rejected','reason':'Stopped'}).status_code,404)
  sign_in(self.client,'faculty-one','faculty')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'rejected','reason':'  '}).status_code,422)
  response=self.client.patch('/api/internships/'+identity+'/status',json={'status':'rejected','reason':'Student discontinued the placement.'})
  self.assertEqual(response.status_code,200,response.text)
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'}).status_code,409)
  sign_in(self.client,'student-one')
  record=self.client.get('/api/internships').json()[0]
  self.assertEqual(record['status'],'rejected');self.assertEqual(record['rejection_reason'],'Student discontinued the placement.')
  self.assertEqual(record['rejected_by'],'faculty-one');self.assertTrue(record['rejected_at'])
  self.assertEqual(len(record['documents']),1);self.assertIn('Internship rejected',record['feedback'][0]['feedback_text'])
  self.assertEqual(self.upload(identity).status_code,409)
  self.assertEqual(self.client.get(document['download_url']).status_code,200)
  sign_in(self.client,'faculty-one','faculty')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/status',json={'status':'ongoing'}).status_code,200)
  record=self.client.get('/api/internships').json()[0]
  self.assertEqual(record['status'],'ongoing');self.assertIsNone(record['rejected_at']);self.assertEqual(len(record['feedback']),2)
  sign_in(self.client,'student-one');self.assertEqual(self.upload(identity).status_code,201)

 def test_invalid_files_and_upload_limits(self):
  from backend import internship_documents
  identity=self.create()
  for name,content in [('bad.exe',b'test'),('../report.txt',b'test'),('bad.pdf',b'not pdf'),('bad.txt',b'\x00'),('bad.txt',b'\xff')]:
   self.assertEqual(self.upload(identity,name,content).status_code,422)
  self.assertEqual(self.upload(identity,content=b'').status_code,422)
  with patch.object(internship_documents,'MAX_FILE',4):self.assertEqual(self.upload(identity).status_code,413)
  self.assertEqual(self.upload(identity).status_code,201)
  with patch.object(internship_documents,'MAX_DOCUMENTS',1):self.assertEqual(self.upload(identity).status_code,409)
  with patch.object(internship_documents,'MAX_BODY',30):self.assertEqual(self.upload(identity).status_code,413)
  sign_in(self.client,'faculty-one','faculty')
  self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'})
  sign_in(self.client,'student-one');self.assertEqual(self.upload(identity).status_code,409)

 def test_additive_migration_preserves_legacy_records_and_repeats(self):
  import sqlite3
  from backend.internships import migrate
  db=sqlite3.connect(':memory:')
  self.addCleanup(db.close)
  db.execute("CREATE TABLE internships (id TEXT PRIMARY KEY,student_id TEXT NOT NULL,title TEXT NOT NULL,mentor_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'ongoing' CHECK(status IN ('ongoing','completed')),created_at TEXT NOT NULL)")
  db.execute("INSERT INTO internships VALUES ('old','s','Existing title','f','completed','date')")
  migrate(db);migrate(db)
  self.assertEqual(db.execute('SELECT id,student_id,title,mentor_id,status,created_at FROM internships').fetchone(),('old','s','Existing title','f','completed','date'))
  self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])

 def test_evidence_and_rejection_do_not_change_protected_tables(self):
  tables=['profiles','assessment_sessions','questions','jobs','history','applications','portfolio_documents','job_alert_subscriptions','match_alerts']
  with main.connection() as db:before={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  identity=self.create();self.upload(identity);sign_in(self.client,'faculty-one','faculty')
  self.client.patch('/api/internships/'+identity+'/status',json={'status':'rejected','reason':'Placement discontinued.'})
  with main.connection() as db:after={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  self.assertEqual(before,after)

 def test_acceptance_is_persistent_scoped_and_separate_from_completion(self):
  identity=self.create()
  self.assertEqual(self.client.get('/api/internships').json()[0]['review_status'],'pending')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/accept',json={}).status_code,403)
  sign_in(self.client,'faculty-two','faculty')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/accept',json={}).status_code,404)
  sign_in(self.client,'faculty-one','faculty')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/accept',json={}).status_code,200)
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/accept',json={}).status_code,200)
  record=self.client.get('/api/internships').json()[0]
  self.assertEqual(record['review_status'],'accepted');self.assertEqual(record['status'],'ongoing')
  self.assertEqual(len(record['feedback']),1)
  self.client.patch('/api/internships/'+identity+'/status',json={'status':'rejected','reason':'Insufficient evidence'})
  self.assertEqual(self.client.get('/api/internships').json()[0]['review_status'],'rejected')
  self.assertEqual(self.client.patch('/api/internships/'+identity+'/accept',json={}).status_code,409)
  self.client.patch('/api/internships/'+identity+'/status',json={'status':'ongoing'})
  self.assertEqual(self.client.get('/api/internships').json()[0]['review_status'],'pending')
  self.client.patch('/api/internships/'+identity+'/status',json={'status':'completed'})
  self.assertEqual(self.client.get('/api/internships').json()[0]['review_status'],'accepted')
