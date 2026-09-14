import sqlite3,tempfile,unittest
from pathlib import Path
from typing import get_args
from unittest.mock import patch
from fastapi.testclient import TestClient
from auth_fixture import sign_in
from backend import main,connector
from backend.loader import HybridJobLoader

class BridgeCategoryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);r=Path(self.temp.name)
  fixture=HybridJobLoader(r/'none.csv',r/'none.json','')
  for name,value in [('DB',r/'test.db'),('HybridJobLoader',lambda:fixture)]:
   p=patch.object(main,name,value);p.start();self.addCleanup(p.stop)
  self.client=TestClient(main.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)
  sign_in(self.client,'category-industry','industry')
 def body(self,**extra):return {'title':'Industry collaboration','skills':'Python','description':'A practical collaboration opportunity.',**extra}
 def test_legacy_migration_preserves_rows_and_is_idempotent(self):
  db=sqlite3.connect(':memory:');self.addCleanup(db.close)
  db.execute('CREATE TABLE collaboration_requests (id TEXT PRIMARY KEY,owner TEXT,title TEXT,kind TEXT,skills TEXT,description TEXT,location TEXT,mode TEXT,duration TEXT,status TEXT,created INTEGER)')
  row=('old','industry','Original','Workshop','Python','Description','Local','Remote','1 day','Closed',123)
  db.execute('INSERT INTO collaboration_requests VALUES (?,?,?,?,?,?,?,?,?,?,?)',row)
  connector.migrate(db);connector.migrate(db)
  loaded=db.execute('SELECT * FROM collaboration_requests').fetchone()
  self.assertEqual(loaded[:-1],row);self.assertEqual(loaded[-1],'Collaboration')

 def test_seven_categories_filter_search_and_invalid_values(self):
  categories=get_args(connector.RequestCategory)[:-1];self.assertEqual(len(categories),7)
  for category in categories:
   self.assertEqual(self.client.post('/api/connector/requests',json=self.body(request_type=category)).status_code,201)
  for role in ['industry','faculty']:
   sign_in(self.client,'category-'+role,role)
   for category in categories:
    rows=self.client.get('/api/connector/requests',params={'request_type':category}).json()
    self.assertEqual(len(rows),1);self.assertEqual(rows[0]['request_type'],category)
  self.assertEqual(len(self.client.get('/api/connector/requests',params={'search':'Consultancy'}).json()),1)
  self.assertEqual(self.client.get('/api/connector/requests',params={'request_type':'Invented'}).status_code,422)
  sign_in(self.client,'category-industry','industry')
  self.assertEqual(self.client.post('/api/connector/requests',json=self.body(request_type='Invented')).status_code,422)

 def test_legacy_payload_default_and_update_preserves_category(self):
  response=self.client.post('/api/connector/requests',json=self.body());self.assertEqual(response.status_code,201)
  identity=response.json()['id']
  self.assertEqual(self.client.get('/api/connector/requests').json()[0]['request_type'],'Collaboration')
  self.assertEqual(self.client.put('/api/connector/requests/'+identity,json=self.body(request_type='Consultancy')).status_code,200)
  self.assertEqual(self.client.put('/api/connector/requests/'+identity,json=self.body(title='Updated title')).status_code,200)
  self.assertEqual(self.client.get('/api/connector/requests').json()[0]['request_type'],'Consultancy')

 def test_categorized_interest_decline_and_close_workflow(self):
  identity=self.client.post('/api/connector/requests',json=self.body(request_type='Collaborative Research')).json()['id']
  sign_in(self.client,'category-faculty','faculty')
  self.client.put('/api/connector/faculty/me',json={'headline':'Research educator','expertise':'Python','bio':'Experienced faculty researcher.','published':True})
  response=self.client.post('/api/connector/requests/'+identity+'/interest',json={'message':'I would like to collaborate.'})
  self.assertEqual(response.status_code,201)
  interest=self.client.get('/api/connector/interests').json()[0]
  self.assertEqual(interest['request_type'],'Collaborative Research')
  sign_in(self.client,'category-industry','industry')
  self.assertEqual(self.client.patch('/api/connector/interests/'+interest['id'],json={'status':'Declined'}).status_code,200)
  self.assertEqual(self.client.put('/api/connector/requests/'+identity,json=self.body(status='Closed')).status_code,200)
  self.assertEqual(self.client.get('/api/connector/requests',params={'request_type':'Collaborative Research'}).json()[0]['status'],'Closed')
  sign_in(self.client,'category-faculty','faculty')
  self.assertEqual(self.client.get('/api/connector/requests').json(),[])
  self.assertEqual(self.client.get('/api/connector/interests').json()[0]['status'],'Declined')
