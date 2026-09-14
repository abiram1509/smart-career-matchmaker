import unittest,tempfile,hashlib,time
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import main,accounts
from backend.loader import HybridJobLoader
from auth_fixture import sign_in

class AccountsConnectorTests(unittest.TestCase):
 def setUp(self):
  self.stack=ExitStack();self.addCleanup(self.stack.close);d=self.stack.enter_context(tempfile.TemporaryDirectory())
  loader=HybridJobLoader(Path(d)/'none.csv',Path(d)/'none.json','')
  self.stack.enter_context(patch.object(main,'DB',Path(d)/'test.db'));self.stack.enter_context(patch.object(main,'HybridJobLoader',lambda:loader))
  self.client=self.stack.enter_context(TestClient(main.app));self.client.headers['X-Bridge-Request']='1'
 def register(self,role='student',email='member@example.test'):
  r=self.client.post('/api/auth/register',json={'name':'Test Member','email':email,'organization':'Test Organization','password':'a-good-password-123','role':role})
  self.assertEqual(r.status_code,201,r.text);return r.json()['user']
 def test_auth_hash_cookie_logout_and_expiry(self):
  self.assertEqual(self.client.get('/api/quiz/questions').status_code,401)
  user=self.register();token=self.client.cookies.get(accounts.COOKIE)
  self.assertEqual(self.client.get('/api/auth/me').json()['user']['id'],user['id'])
  with main.connection() as db:
   row=db.execute('SELECT * FROM accounts').fetchone();self.assertNotIn('a-good-password',row['password_hash']);self.assertTrue(accounts.password_valid('a-good-password-123',row['password_hash']))
   self.assertNotEqual(db.execute('SELECT token_hash FROM login_sessions').fetchone()[0],token)
  self.assertEqual(self.client.post('/api/auth/logout',json={}).status_code,200)
  self.client.cookies.set(accounts.COOKIE,token);self.assertEqual(self.client.get('/api/auth/me').status_code,401);self.client.cookies.clear()
  self.assertEqual(self.client.post('/api/auth/login',json={'email':user['email'],'password':'wrong'}).status_code,401)
  r=self.client.post('/api/auth/login',json={'email':user['email'].upper(),'password':'a-good-password-123'});self.assertEqual(r.status_code,200)
  cookie=r.headers['set-cookie'].lower();self.assertIn('httponly',cookie);self.assertIn('samesite=strict',cookie)
  with main.connection() as db:db.execute('UPDATE login_sessions SET expires_at=0')
  self.assertEqual(self.client.get('/api/auth/me').status_code,401)
 def test_csrf_validation_and_privileged_role(self):
  self.client.headers.pop('X-Bridge-Request')
  self.assertEqual(self.client.post('/api/auth/login',json={'email':'member@example.test','password':'password'}).status_code,403)
  self.client.headers['X-Bridge-Request']='1'
  self.assertEqual(self.client.post('/api/auth/login',json={'email':'member@example.test','password':'password'},headers={'Origin':'https://evil.example'}).status_code,403)
  for role,password in [('institution','a-long-password'),('student','short')]:
   self.assertEqual(self.client.post('/api/auth/register',json={'name':'Member','email':'member@example.test','password':password,'role':role}).status_code,422)
 def test_identity_isolation_and_analytics_roles(self):
  user=self.register()
  for path in ['/api/student/another/profile','/api/student/another/applications','/api/student/another/alerts']:
   self.assertEqual(self.client.get(path).status_code,404)
  for path,body in [('/api/quiz/submit',{'student_id':'another','answers':[]}),('/api/assessment/start',{'student_id':'another','field':'tech','track':'backend'}),('/api/match',{'skill_vector':{'Python':8},'profile_id':'another'}),('/api/applications',{'student_id':'another','job_id':'demo-1'})]:
   self.assertEqual(self.client.post(path,json=body).status_code,404)
  self.assertEqual(self.client.get('/api/analytics').status_code,403)
  self.client.cookies.clear();sign_in(self.client,'institution-fixture','institution')
  self.assertEqual(self.client.get('/api/analytics').status_code,200)
  self.assertEqual(self.client.post('/api/assessment/start',json={'student_id':'institution-fixture','field':'tech','track':'backend'}).status_code,403)
 def test_login_attempts_are_bounded(self):
  for _ in range(10):self.assertEqual(self.client.post('/api/auth/login',json={'email':'absent@example.test','password':'wrong'}).status_code,401)
  self.assertEqual(self.client.post('/api/auth/login',json={'email':'absent@example.test','password':'wrong'}).status_code,429)
 def test_connector_full_lifecycle_and_ownership(self):
  industry=self.register('industry','industry@example.test');industry_cookie=self.client.cookies.get(accounts.COOKIE)
  body={'title':'Practical Python mentoring','kind':'Mentorship','skills':'Python, REST APIs','description':'Help our team design and test a practical API.','mode':'Remote','duration':'Two sessions','status':'Open'}
  r=self.client.post('/api/connector/requests',json=body);self.assertEqual(r.status_code,201,r.text);request_id=r.json()['id']
  self.assertEqual(self.client.put('/api/connector/faculty/me',json={'headline':'Teacher','expertise':'Python','bio':'Experienced teacher of Python.'}).status_code,403)
  self.client.cookies.clear();faculty=self.register('faculty','faculty@example.test');faculty_cookie=self.client.cookies.get(accounts.COOKIE)
  self.assertEqual(self.client.post('/api/connector/requests/'+request_id+'/interest',json={'message':'I can offer practical workshops.'}).status_code,400)
  profile={'headline':'Applied computing educator','expertise':'Python, REST APIs','bio':'Teaching software engineering with practical industry projects.','published':True}
  self.assertEqual(self.client.put('/api/connector/faculty/me',json=profile).status_code,200)
  listed=self.client.get('/api/connector/faculty').json();self.assertEqual(len(listed),1);self.assertNotIn('email',listed[0]);self.assertNotIn('password_hash',listed[0])
  self.assertEqual(self.client.post('/api/connector/requests/'+request_id+'/interest',json={'message':'I can offer practical workshops.'}).status_code,201)
  self.assertEqual(self.client.post('/api/connector/requests/'+request_id+'/interest',json={'message':'I can offer practical workshops.'}).status_code,409)
  interest_id=self.client.get('/api/connector/interests').json()[0]['id']
  self.assertEqual(self.client.put('/api/connector/requests/'+request_id,json=body).status_code,403)
  self.client.cookies.clear();self.register('industry','other-industry@example.test')
  self.assertEqual(self.client.get('/api/connector/interests').json(),[])
  self.assertEqual(self.client.put('/api/connector/requests/'+request_id,json=body).status_code,404)
  self.assertEqual(self.client.patch('/api/connector/interests/'+interest_id,json={'status':'Accepted'}).status_code,409)
  self.client.cookies.clear();self.client.cookies.set(accounts.COOKIE,industry_cookie)
  self.assertEqual(self.client.patch('/api/connector/interests/'+interest_id,json={'status':'Accepted'}).status_code,200)
  self.assertEqual(self.client.patch('/api/connector/interests/'+interest_id,json={'status':'Declined'}).status_code,409)
  self.assertEqual(self.client.put('/api/connector/requests/'+request_id,json={**body,'status':'Closed'}).status_code,200)
  self.client.cookies.clear();self.client.cookies.set(accounts.COOKIE,faculty_cookie)
  self.assertEqual(self.client.get('/api/connector/interests').json()[0]['status'],'Accepted')
  self.assertEqual(self.client.get('/api/connector/requests').json(),[])
  self.assertEqual(self.client.put('/api/connector/faculty/me',json={**profile,'published':False}).status_code,200)
  self.client.cookies.clear();self.client.cookies.set(accounts.COOKIE,industry_cookie)
  self.assertEqual(self.client.get('/api/connector/faculty').json(),[])
