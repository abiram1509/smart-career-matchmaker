import unittest,tempfile,os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import main,privacy
from backend.loader import HybridJobLoader
from auth_fixture import sign_in

class PrivacyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);root=Path(self.temp.name)
  loader=HybridJobLoader(root/'none.csv',root/'none.json','')
  for name,value in [('DB',root/'test.db'),('HybridJobLoader',lambda:loader)]:
   p=patch.object(main,name,value);p.start();self.addCleanup(p.stop)
  self.client=TestClient(main.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)
 def test_public_notices_no_login_cookie_and_security_headers(self):
  for path in privacy.PAGES:
   r=self.client.get('/'+path);self.assertEqual(r.status_code,200)
   self.assertIn('<h1>',r.text);self.assertNotIn('set-cookie',r.headers)
   self.assertEqual(r.headers['referrer-policy'],'no-referrer')
   self.assertIn("frame-ancestors 'none'",r.headers['content-security-policy'])
  self.assertIn('MIT',self.client.get('/third-party-notices').text)
 def test_operator_content_escaped_and_missing_details_honest(self):
  with patch.dict(os.environ,{'SITE_OPERATOR_NAME':'<script>alert(1)</script>'}):
   r=self.client.get('/privacy');self.assertNotIn('<script>',r.text);self.assertIn('&lt;script&gt;',r.text)
  self.assertIn('No refund guarantee',self.client.get('/terms').text)
 def test_registration_requires_explicit_both_choices_and_records_version(self):
  self.client.headers['X-Bridge-Request']='1'
  body={'name':'Test member','email':'privacy@example.test','password':'testing-password-123'}
  for extra in ({},{'privacy_consent':True},{'privacy_consent':'yes','terms_accepted':True}):
   self.assertEqual(self.client.post('/api/auth/register',json={**body,**extra}).status_code,422)
  r=self.client.post('/api/auth/register',json={**body,'privacy_consent':True,'terms_accepted':True});self.assertEqual(r.status_code,201)
  with main.connection() as db:
   record=db.execute('SELECT * FROM privacy_acknowledgements').fetchone();self.assertEqual(record['account_id'],r.json()['user']['id']);self.assertEqual(record['version'],privacy.VERSION)
 def test_request_isolation_owner_access_and_no_automatic_deletion(self):
  self.assertEqual(self.client.get('/api/privacy/requests').status_code,401)
  sign_in(self.client,'alice');r=self.client.post('/api/privacy/requests',json={'kind':'deletion','message':'Please remove my account.'});self.assertEqual(r.status_code,201)
  self.assertIn('No data has been deleted',r.json()['message']);self.assertEqual(len(self.client.get('/api/privacy/requests').json()),1)
  with main.connection() as db:self.assertIsNotNone(db.execute("SELECT id FROM accounts WHERE id='alice'").fetchone())
  sign_in(self.client,'bob');self.assertEqual(self.client.get('/api/privacy/requests').json(),[])
  sign_in(self.client,'owner','owner');self.assertEqual(self.client.get('/api/privacy/requests').json()[0]['account_id'],'alice')
 def test_request_protection_validation_and_pending_limit(self):
  sign_in(self.client,'alice')
  for body in ({'kind':'invalid'},{'kind':'access','account_id':'other'},{'kind':'access','message':'x'*2001}):self.assertEqual(self.client.post('/api/privacy/requests',json=body).status_code,422)
  self.assertEqual(self.client.post('/api/privacy/requests',json={'kind':'access'},headers={'Origin':'https://evil.test'}).status_code,403)
  for _ in range(10):self.assertEqual(self.client.post('/api/privacy/requests',json={'kind':'access'}).status_code,201)
  self.assertEqual(self.client.post('/api/privacy/requests',json={'kind':'access'}).status_code,429)
 def test_faculty_publication_is_explicit_and_reversible(self):
  sign_in(self.client,'faculty','faculty');body={'headline':'Test faculty','expertise':'Python','bio':'Practical teaching expertise.'}
  self.assertEqual(self.client.put('/api/connector/faculty/me',json=body).status_code,200)
  sign_in(self.client,'student');self.assertEqual(self.client.get('/api/connector/faculty').json(),[])
  sign_in(self.client,'faculty','faculty');self.client.put('/api/connector/faculty/me',json={**body,'published':True})
  sign_in(self.client,'student');self.assertEqual(len(self.client.get('/api/connector/faculty').json()),1)
  sign_in(self.client,'faculty','faculty');self.client.put('/api/connector/faculty/me',json={**body,'published':False})
  sign_in(self.client,'student');self.assertEqual(self.client.get('/api/connector/faculty').json(),[])
