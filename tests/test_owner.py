import json,time,unittest,tempfile,io
from pathlib import Path
from contextlib import ExitStack,redirect_stdout
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import main
from backend.loader import HybridJobLoader
from auth_fixture import sign_in

class OwnerTests(unittest.TestCase):
 def setUp(self):
  self.stack=ExitStack();self.addCleanup(self.stack.close);d=self.stack.enter_context(tempfile.TemporaryDirectory())
  loader=HybridJobLoader(Path(d)/'none.csv',Path(d)/'none.json','');loader.api_url='https://provider.test?key=NEVER-EXPOSE'
  self.stack.enter_context(patch.object(main,'DB',Path(d)/'test.db'));self.stack.enter_context(patch.object(main,'HybridJobLoader',lambda:loader))
  self.client=self.stack.enter_context(TestClient(main.app));self.client.headers['X-Bridge-Request']='1'
 def test_owner_only_and_no_public_privilege(self):
  self.assertEqual(self.client.get('/api/owner/overview').status_code,401)
  for role in ['student','faculty','industry','institution']:
   self.client.cookies.clear();sign_in(self.client,'role-'+role,role)
   self.assertEqual(self.client.get('/api/owner/overview').status_code,403)
  self.assertEqual(self.client.post('/api/auth/register',json={'email':'hacker@example.test','password':'password-12345','name':'Test','role':'owner'}).status_code,422)
  self.client.cookies.clear();sign_in(self.client,'owner','owner')
  self.assertEqual(self.client.get('/api/owner/overview').status_code,200)
  self.assertEqual(self.client.get('/api/student/role-student/profile').status_code,404)
 def test_metrics_and_no_private_payloads(self):
  sign_in(self.client,'student','student');self.client.cookies.clear();sign_in(self.client,'owner','owner')
  with main.connection() as db:
   db.execute('INSERT INTO profiles(id,vector,updated) VALUES (?,?,?)',('student','{"Python":8}',main.now()))
   db.execute('INSERT INTO profiles(id,vector,updated) VALUES (?,?,?)',('anonymous','{}',main.now()))
   db.execute('INSERT INTO assessment_sessions VALUES (?,?,?,?,?)',('test-session','student',json.dumps({'phase':'complete','answers':{'private-answer':'NEVER-EXPOSE'}}),1,main.now()))
   db.execute('INSERT INTO collaboration_requests (id,owner,title,kind,skills,description,location,mode,duration,status,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)',('r','owner','PRIVATE-TITLE','Training','Python','PRIVATE-DESCRIPTION','Remote','Remote','One day','Open',int(time.time())))
   db.execute('INSERT INTO collaboration_interests VALUES (?,?,?,?,?,?)',('i','r','student','PRIVATE-MESSAGE','Accepted',int(time.time())))
  r=self.client.get('/api/owner/overview');self.assertEqual(r.status_code,200);data=r.json()
  self.assertEqual(data['totals']['account_profiles'],1);self.assertEqual(data['totals']['legacy_profiles'],1);self.assertEqual(data['totals']['completed_assessments'],1)
  self.assertEqual(data['requests']['Open'],1);self.assertEqual(data['interests']['Accepted'],1);self.assertEqual(len(data['activity']),7)
  self.assertEqual(data['questions']['total'],1209);self.assertTrue(data['data_sources']['api_configured'])
  for private in ['NEVER-EXPOSE','PRIVATE-TITLE','PRIVATE-DESCRIPTION','PRIVATE-MESSAGE','password_hash','token_hash','@example.test']:self.assertNotIn(private,r.text)
 def test_owner_command_does_not_promote_existing_account(self):
  from backend import create_owner
  args=['create_owner','--email','owner@example.test','--name','Owner Person']
  with patch('sys.argv',args),patch('getpass.getpass',return_value='strong-password-123'),redirect_stdout(io.StringIO()):create_owner.run()
  with main.connection() as db:self.assertEqual(db.execute('SELECT role FROM accounts WHERE email=?',('owner@example.test',)).fetchone()[0],'owner')
  with patch('sys.argv',args),patch('getpass.getpass',return_value='different-password-123'),self.assertRaises(SystemExit):create_owner.run()
