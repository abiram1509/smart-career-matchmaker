import base64
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import main, portfolio, institutions
from backend.loader import HybridJobLoader
from auth_fixture import sign_in

class InstitutionIsolationTests(unittest.TestCase):
 def setUp(self):
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
  loader=HybridJobLoader(self.root/'none.csv',self.root/'none.json','')
  self.stack.enter_context(patch.object(main,'DB',self.root/'test.db'))
  self.stack.enter_context(patch.object(main,'HybridJobLoader',lambda:loader))
  self.stack.enter_context(patch.object(portfolio,'STORAGE',self.root/'documents'))
  self.client=self.stack.enter_context(TestClient(main.app))
  sign_in(self.client,'owner','owner')
  self.a=self.client.post('/api/owner/institutions',json={'name':'A'}).json()['id']
  self.b=self.client.post('/api/owner/institutions',json={'name':'B'}).json()['id']
  for identity,role in [('sa','student'),('sb','student'),('fa','faculty'),('fb','faculty'),('ia','institution'),('ib','institution'),('unassigned','faculty')]:
   sign_in(self.client,identity,role)
  sign_in(self.client,'owner','owner')
  for identity in ['sa','fa','ia','sb','fb','ib']:
   response=self.client.put('/api/owner/institutions/members/'+identity,json={'institution_id':self.a if identity.endswith('a') else self.b})
   self.assertEqual(response.status_code,200,response.text)
  with main.connection() as db:
   for identity,skill in [('sa','Python'),('sb','SQL'),('legacy','Secret')]:
    db.execute('INSERT INTO profiles(id,vector,evidence) VALUES (?,?,?)',(identity,json.dumps({skill:2}),'{}'))
    db.execute('INSERT INTO applications VALUES (?,?,?,?)',(identity,'job-'+identity,'Saved','now'))

 def upload(self,identity):
  sign_in(self.client,identity)
  response=self.client.post('/api/portfolio/upload',json={'title':identity+' document','filename':'test.txt','content_base64':base64.b64encode(b'demo').decode()})
  self.assertEqual(response.status_code,201,response.text)
  return response.json()

 def test_analytics_scoped_even_with_forged_query(self):
  sign_in(self.client,'ia','institution')
  for url in ['/api/analytics','/api/analytics/','/api/analytics?institution_id='+self.b]:
   response=self.client.get(url);self.assertEqual(response.status_code,200,response.text)
   self.assertEqual(response.json()['students'],1)
   self.assertEqual(response.json()['applications'],1)
   self.assertEqual(response.json()['gaps'],[['Python',1]])
  self.assertEqual(self.client.get('/api/analytics?student_id=sb').status_code,404)
  self.assertEqual(self.client.get('/api/student/sb').status_code,404)
  self.assertEqual(self.client.get('/api/owner/overview').status_code,403)
  sign_in(self.client,'ib','institution')
  self.assertEqual(self.client.get('/api/analytics').json()['gaps'],[['SQL',1]])

 def test_faculty_cannot_list_download_or_verify_other_institution(self):
  da=self.upload('sa');db=self.upload('sb')
  sign_in(self.client,'fa','faculty')
  self.assertEqual([d['id'] for d in self.client.get('/api/portfolio').json()],[da['id']])
  self.assertEqual(self.client.get('/api/portfolio?institution_id='+self.b).json()[0]['id'],da['id'])
  self.assertEqual(self.client.get(db['download_url']).status_code,404)
  self.assertEqual(self.client.patch('/api/portfolio/'+db['id']+'/status',json={'status':'verified'}).status_code,404)
  self.assertEqual(self.client.get(da['download_url']).content,b'demo')
  self.assertEqual(self.client.patch('/api/portfolio/'+da['id']+'/status',json={'status':'verified'}).status_code,200)

 def test_owner_unrestricted_and_students_private(self):
  da=self.upload('sa');db=self.upload('sb')
  self.assertEqual(self.client.get(da['download_url']).status_code,404)
  sign_in(self.client,'owner','owner')
  self.assertEqual(len(self.client.get('/api/portfolio').json()),2)
  for doc in [da,db]:
   self.assertEqual(self.client.get(doc['download_url']).status_code,200)
   self.assertEqual(self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'}).status_code,200)

 def test_unassigned_and_removal_fail_closed_with_existing_session(self):
  doc=self.upload('sa');sign_in(self.client,'unassigned','faculty')
  self.assertEqual(self.client.get('/api/portfolio').status_code,403)
  sign_in(self.client,'fa','faculty')
  self.assertEqual(self.client.get(doc['download_url']).status_code,200)
  with main.connection() as db:institutions.assign(db,'fa',None,'owner')
  self.assertEqual(self.client.get(doc['download_url']).status_code,403)
  self.assertEqual(self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'}).status_code,403)
  sign_in(self.client,'ia','institution')
  with main.connection() as db:institutions.assign(db,'ia',None,'owner')
  self.assertEqual(self.client.get('/api/analytics').status_code,403)

 def test_student_transfer_revokes_old_faculty_access(self):
  doc=self.upload('sa');sign_in(self.client,'fa','faculty')
  with main.connection() as db:institutions.assign(db,'sa',self.b,'owner')
  self.assertEqual(self.client.get('/api/portfolio').json(),[])
  self.assertEqual(self.client.get(doc['download_url']).status_code,404)
  sign_in(self.client,'fb','faculty')
  self.assertEqual(self.client.get(doc['download_url']).status_code,200)

 def test_membership_owner_only_and_signup_cannot_self_assign(self):
  sign_in(self.client,'fa','faculty')
  self.assertEqual(self.client.get('/api/owner/institutions').status_code,403)
  self.assertEqual(self.client.put('/api/owner/institutions/members/fa',json={'institution_id':self.b}).status_code,403)
  response=self.client.post('/api/auth/register',json={'email':'new@example.test','name':'New Student','password':'test-password-123','organization':'A','institution_id':self.a,'role':'student','privacy_consent':True,'terms_accepted':True})
  self.assertEqual(response.status_code,201,response.text)
  self.assertIsNone(self.client.get('/api/auth/me').json()['user']['institution_id'])

 def test_migration_repeatable_and_foreign_keys_enforced(self):
  with main.connection() as db:
   before=[tuple(r) for r in db.execute('SELECT * FROM accounts ORDER BY id')]
   institutions.migrate(db);institutions.migrate(db)
   self.assertEqual(before,[tuple(r) for r in db.execute('SELECT * FROM accounts ORDER BY id')])
   self.assertEqual(db.execute('PRAGMA foreign_keys').fetchone()[0],1)
   self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
   with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE accounts SET institution_id='missing' WHERE id='sa'")

 def test_membership_and_review_leave_protected_tables_unchanged(self):
  tables=['profiles','questions','jobs','assessment_sessions','history','applications']
  with main.connection() as db:before={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  doc=self.upload('sa');sign_in(self.client,'fa','faculty')
  self.assertEqual(self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'}).status_code,200)
  with main.connection() as db:
   institutions.assign(db,'sa',self.b,'owner')
   self.assertEqual(before,{t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables})

 def test_legacy_migration_preserves_accounts_without_auto_linking(self):
  db=sqlite3.connect(':memory:');self.addCleanup(db.close);db.row_factory=sqlite3.Row
  db.execute('PRAGMA foreign_keys=ON')
  db.execute('CREATE TABLE accounts (id TEXT PRIMARY KEY,email TEXT,name TEXT,organization TEXT,role TEXT,password_hash TEXT,created_at INTEGER)')
  rows=[('one','one@example.test','One','Same name','student','hash-one',1),('two','two@example.test','Two','Same name','institution','hash-two',2)]
  db.executemany('INSERT INTO accounts VALUES (?,?,?,?,?,?,?)',rows)
  institutions.migrate(db)
  self.assertEqual(rows,[tuple(r)[:7] for r in db.execute('SELECT * FROM accounts ORDER BY id')])
  self.assertTrue(all(r[0] is None for r in db.execute('SELECT institution_id FROM accounts')))
  self.assertEqual(db.execute('SELECT COUNT(*) FROM institutions').fetchone()[0],0)
  self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])

 def test_unassigned_students_never_become_visible_to_unassigned_faculty(self):
  sign_in(self.client,'no-school-student')
  doc=self.client.post('/api/portfolio/upload',json={'title':'Unassigned document','filename':'test.txt','content_base64':base64.b64encode(b'demo').decode()}).json()
  sign_in(self.client,'unassigned','faculty')
  self.assertEqual(self.client.get('/api/portfolio').status_code,403)
  self.assertEqual(self.client.get(doc['download_url']).status_code,403)
  self.assertEqual(self.client.patch('/api/portfolio/'+doc['id']+'/status',json={'status':'verified'}).status_code,403)
