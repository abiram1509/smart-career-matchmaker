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
