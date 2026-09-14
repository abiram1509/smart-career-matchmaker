import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from auth_fixture import sign_in
from backend import main,recruitment
from backend.domain import rank_jobs
from backend.loader import HybridJobLoader

class RecruitmentTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);r=Path(self.temp.name)
  fixture=HybridJobLoader(r/'none.csv',r/'none.json','')
  for name,value in [('DB',r/'test.db'),('HybridJobLoader',lambda:fixture)]:
   p=patch.object(main,name,value);p.start();self.addCleanup(p.stop)
  self.client=TestClient(main.app);self.client.__enter__();self.addCleanup(self.client.__exit__,None,None,None)
  sign_in(self.client,'recruiter','industry')
  response=self.client.post('/api/recruitment/roles',json={'title':'Python developer','description':'Build practical APIs using Python and SQL.','required_skills':{'Python':8,'SQL':8},'eligibility':'Able to participate in a supervised project.'})
  self.assertEqual(response.status_code,201,response.text);self.role=response.json()['id']
 def student(self,identity='candidate',vector=None):
  sign_in(self.client,identity)
  if vector is not None:
   evidence={s:{'assessed':True,'verified':False,'basis':'Self-reported; not verified'} for s in vector}
   with main.connection() as db:db.execute('INSERT INTO profiles(id,vector,updated,track,evidence) VALUES (?,?,?,?,?)',(identity,json.dumps(vector),'snapshot-date','backend',json.dumps(evidence)))
 def apply(self):
  r=self.client.post('/api/recruitment/roles/'+self.role+'/apply',json={'consent':True,'eligibility_response':'meets'})
  self.assertEqual(r.status_code,201,r.text);return r.json()['id']
 def applicants(self):
  sign_in(self.client,'recruiter','industry')
  r=self.client.get('/api/recruitment/roles/'+self.role+'/applicants');self.assertEqual(r.status_code,200,r.text);return r.json()
 def test_explicit_consent_assessment_required_and_duplicate_protection(self):
  self.student()
  url='/api/recruitment/roles/'+self.role+'/apply'
  self.assertEqual(self.client.post(url,json={'consent':False,'eligibility_response':'meets'}).status_code,422)
  self.assertEqual(self.client.post(url,json={'consent':True,'eligibility_response':'meets'}).status_code,400)
  with main.connection() as db:db.execute('INSERT INTO profiles(id,vector,updated,track) VALUES (?,?,?,?)',('candidate','{"Python":8}','test','backend'))
  self.apply()
  self.assertEqual(self.client.post(url,json={'consent':True,'eligibility_response':'meets'}).status_code,409)
  self.assertEqual(self.client.post(url,json={'consent':True,'eligibility_response':'meets','student_id':'another'}).status_code,404)

 def test_ranking_parity_snapshots_and_human_shortlisting(self):
  self.student('higher',{'Python':8,'SQL':8});high=self.apply()
  self.student('lower',{'Python':0,'SQL':8});low=self.apply()
  with main.connection() as db:db.execute("UPDATE profiles SET vector='{}' WHERE id='higher'")
  result=self.applicants();rows=result['applicants']
  self.assertEqual([r['id'] for r in rows],[high,low])
  self.assertEqual(rows[0]['match_score'],rank_jobs({'Python':8,'SQL':8},[{'id':self.role,'skills':{'Python':8,'SQL':8}}])[0]['match_score'])
  self.assertEqual(rows[0]['assessment_updated'],'snapshot-date');self.assertNotIn('vector',rows[0]);self.assertNotIn('email',rows[0])
  self.assertTrue(all(r['decision']=='pending' for r in rows))
  self.assertEqual(self.client.patch('/api/recruitment/applications/'+high+'/review',json={'decision':'shortlisted','reviewed':True,'review_seconds':90,'evaluation_label':'qualified'}).status_code,200)
  self.assertEqual(len(self.applicants()['applicants']),2)
  sign_in(self.client,'higher');mine=self.client.get('/api/recruitment/roles').json()[0]['application'];self.assertEqual(mine['decision'],'shortlisted')

 def test_recruiter_ownership_student_isolation_and_withdrawal(self):
  self.student('candidate',{'Python':8});identity=self.apply()
  sign_in(self.client,'recruiter','industry')
  self.client.patch('/api/recruitment/roles/'+self.role,json={'status':'open','baseline_seconds':600})
  sign_in(self.client,'other-recruiter','industry')
  self.assertEqual(self.client.get('/api/recruitment/roles').json(),[])
  self.assertEqual(self.client.get('/api/recruitment/roles/'+self.role+'/applicants').status_code,404)
  self.assertEqual(self.client.patch('/api/recruitment/applications/'+identity+'/review',json={'decision':'shortlisted','reviewed':True}).status_code,404)
  sign_in(self.client,'other-student')
  self.assertIsNone(self.client.get('/api/recruitment/roles').json()[0]['application'])
  self.assertEqual(self.client.delete('/api/recruitment/applications/'+identity).status_code,404)
  self.assertEqual(self.client.get('/api/recruitment/roles/'+self.role+'/applicants').status_code,403)
  sign_in(self.client,'candidate');self.assertEqual(self.client.delete('/api/recruitment/applications/'+identity).status_code,200)
  self.assertEqual(self.applicants()['applicants'],[])
  self.assertIsNone(self.client.get('/api/recruitment/roles').json()[0]['baseline_seconds'])
  with main.connection() as db:self.assertEqual(db.execute('SELECT vector,evidence FROM recruitment_applications').fetchone()[:],('{}','{}'))

 def test_role_closure_bad_inputs_and_auth(self):
  self.assertEqual(self.client.post('/api/recruitment/roles',json={'title':'Title','description':'A real description','required_skills':{'Unknown':8}}).status_code,422)
  self.assertEqual(self.client.patch('/api/recruitment/roles/'+self.role,json={'status':'closed','baseline_seconds':600}).status_code,200)
  self.student('candidate',{'Python':8})
  self.assertEqual(self.client.get('/api/recruitment/roles').json(),[])
  self.assertEqual(self.client.post('/api/recruitment/roles/'+self.role+'/apply',json={'consent':True,'eligibility_response':'meets'}).status_code,409)
  self.client.cookies.clear();self.assertEqual(self.client.get('/api/recruitment/roles').status_code,401)

 def test_evaluation_computes_actual_counts_and_withholds_incomplete_claims(self):
  rows=[{'reviewed':i<6,'decision':'shortlisted' if i<2 else 'pending','review_seconds':100 if i<6 else 0,'evaluation_label':'qualified' if i<2 else 'not_qualified'} for i in range(10)]
  role={'status':'closed','baseline_seconds':1200}
  m=recruitment.metrics(role,rows)
  self.assertEqual(m['review_reduction_percent'],40);self.assertEqual(m['time_reduction_percent'],50)
  self.assertEqual(m['qualified_retention_percent'],100);self.assertEqual(m['qualified_missed'],0)
  rows[-1]['evaluation_label']='unlabelled';m=recruitment.metrics(role,rows)
  self.assertIsNone(m['qualified_retention_percent']);self.assertIsNone(m['qualified_missed'])
  self.assertIsNone(recruitment.metrics({'status':'open','baseline_seconds':None},rows)['review_reduction_percent'])
  self.assertIsNone(recruitment.metrics(role,[])['review_reduction_percent'])
  rows[1]['decision']='not_shortlisted';rows[-1]['evaluation_label']='not_qualified'
  self.assertEqual(recruitment.metrics(role,rows)['qualified_missed'],1)

 def test_no_mutations_to_existing_assessment_or_workflows(self):
  self.student('candidate',{'Python':8})
  tables=['profiles','assessment_sessions','questions','jobs','history','applications','portfolio_documents','internships','internship_feedback','collaboration_requests','collaboration_interests','job_alert_subscriptions','match_alerts']
  with main.connection() as db:before={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  identity=self.apply();self.applicants()
  self.client.patch('/api/recruitment/applications/'+identity+'/review',json={'decision':'shortlisted','reviewed':True,'review_seconds':20})
  with main.connection() as db:after={t:[tuple(r) for r in db.execute('SELECT * FROM '+t)] for t in tables}
  self.assertEqual(before,after)
