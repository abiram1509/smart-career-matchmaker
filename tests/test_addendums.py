from auth_fixture import sign_in
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import adaptive_quiz as quiz,main,addon_api
from backend.assessment_config import ASSESSMENT_TRACKS
from backend.domain import SKILLS,rank_jobs,build_job_matrix
from backend.loader import HybridJobLoader
from backend.category_mapping import CATEGORY_CODE_TO_FIELD_TRACK,CATEGORY_TO_SKILLS_TEMPLATE
from backend.learning_resources import resources

def answer_phase(state,value=8):
 return [{'question_id':q['id'],'value':'' if q['type']=='project_note' else value if q['type']=='self_rating' else 0} for q in state['pending']]
def through_context(track='backend',heavy=False):
 s=quiz.initial(ASSESSMENT_TRACKS[track]['field'],track)
 s=quiz.advance(s,answer_phase(s))
 s=quiz.advance(s,[{'question_id':q['id'],'value':2 if i==0 else 0} for i,q in enumerate(s['pending'])])
 a=answer_phase(s)
 for x in a:
  if x['question_id']=='context-ai':x['value']=2 if heavy else 0
 return quiz.advance(s,a)

class AdaptiveTests(unittest.TestCase):
 def test_all_thirty_tracks_and_universal_ratings(self):
  for track,c in ASSESSMENT_TRACKS.items():
   state=quiz.initial(c['field'],track);self.assertEqual(len(state['pending']),15)
   state=quiz.advance(state,answer_phase(state));self.assertEqual(len(state['pending']),5)
   state=quiz.advance(state,answer_phase(state));self.assertEqual(state['phase'],'complete')
   v,e=quiz.score(state);self.assertEqual(set(v),set(SKILLS));self.assertEqual(sum(x['assessed'] for x in e.values()),15)
   self.assertFalse(any(x['verified'] for x in e.values()))
 def test_context_changes_project_question_and_preserves_pure_check(self):
  # Exercise the generic context variants on an unchanged starter bank.
  # Authored Frontend intentionally has its own source-preserved context IDs.
  standard=through_context('cloud-devops');deep=through_context('cloud-devops',heavy=True)
  self.assertNotEqual([q['id'] for q in standard['pending']],[q['id'] for q in deep['pending']])
  self.assertTrue(any(q['verification_kind']=='skill' for q in deep['pending']))
  self.assertTrue(all(q['skill']=='Docker' for q in deep['pending']))
 def test_wrong_answer_caps_claim_without_zeroing_unrelated_skills(self):
  s=through_context();answers=[{'question_id':q['id'],'value':q['correct_option']} for q in s['pending']];answers[0]['value']=(answers[0]['value']+1)%4
  v,e=quiz.score(quiz.advance(s,answers));self.assertEqual(v['Python'],4);self.assertFalse(e['Python']['verified']);self.assertEqual(v['SQL'],8);self.assertEqual(v['Circuit Design'],0);self.assertFalse(e['Circuit Design']['assessed'])
 def test_correct_answers_only_confirm_quiz_evidence(self):
  s=through_context();v,e=quiz.score(quiz.advance(s,[{'question_id':q['id'],'value':q['correct_option']} for q in s['pending']]))
  self.assertEqual(v['Python'],8);self.assertTrue(e['Python']['verified']);self.assertFalse(e['Python']['example_checks'])
 def test_even_cap_and_unflagged_exclusion(self):
  s=through_context();s['flags']=['Python','SQL','Git'];s['bank']=[]
  for skill in ['Python','SQL','Git','React']:
   for i in range(12):s['bank'].append({'id':skill+str(i),'tier':3,'track':'backend','skill':skill,'requires_tier2_flag':skill,'verification_kind':'project' if i%2 else 'skill','difficulty':'standard'})
  selected=quiz.select_verification(s);self.assertEqual(len(selected),15)
  self.assertEqual({skill:sum(q['skill']==skill for q in selected) for skill in s['flags']},{'Python':5,'SQL':5,'Git':5})
 def test_invalid_field_and_forged_values_rejected(self):
  with self.assertRaises(ValueError):quiz.initial('design','backend')
  s=quiz.initial('tech','backend');a=answer_phase(s);a[0]['value']=True
  with self.assertRaises(ValueError):quiz.advance(s,a)
 def test_all_35_templates_use_shared_taxonomy(self):
  self.assertEqual(len(CATEGORY_CODE_TO_FIELD_TRACK),35);self.assertEqual(set(CATEGORY_CODE_TO_FIELD_TRACK),set(CATEGORY_TO_SKILLS_TEMPLATE))
  for values in CATEGORY_TO_SKILLS_TEMPLATE.values():self.assertTrue(set(values)<=set(SKILLS))
 def test_untested_skills_have_no_practice_time(self):
  rows=rank_jobs({'Python':0},[{'id':'j','skills':{'Python':6}}],evidence={'Python':{'assessed':False}})
  self.assertFalse(rows[0]['gaps'][0]['assessed']);self.assertEqual(rows[0]['suggestions'],[])

class AddendumAPITests(unittest.TestCase):
 def fixture(self,directory):
  loader=HybridJobLoader(Path(directory)/'missing.csv',Path(directory)/'missing.json','')
  loader.jobs=[{'id':'one','title':'Python role','company':'Example','skills':{'Python':10},'field':'technology','source_kind':'kaggle','description':'Python','location':'Remote','type':'Full-time','url':'https://example.test/job'}];loader.matrix=build_job_matrix(loader.jobs)
  return loader
 def test_session_keys_hidden_completion_and_replay_protection(self):
  with tempfile.TemporaryDirectory() as d,patch.object(main,'DB',Path(d)/'test.db'),patch.object(main,'HybridJobLoader',lambda:self.fixture(d)):
   with TestClient(main.app) as client:
    sign_in(client,'test')
    result=client.post('/api/assessment/start',json={'student_id':'test','field':'tech','track':'backend'}).json()
    first=result.copy()
    while result['phase']!='complete':
     self.assertTrue(all('correct_option' not in q for q in result['questions']))
     answers=[{'question_id':q['id'],'value':8 if q['type']=='self_rating' else 0} for q in result['questions']]
     response=client.post('/api/assessment/'+result['session_id']+'/advance',json={'student_id':'test','version':result['version'],'answers':answers});self.assertEqual(response.status_code,200,response.text);result=response.json()
    profile=client.get('/api/student/test/profile').json();self.assertEqual(profile['track'],'backend');self.assertEqual(profile['field'],'tech');self.assertEqual(sum(e['assessed'] for e in profile['evidence'].values()),15)
    self.assertEqual(client.post('/api/assessment/'+first['session_id']+'/advance',json={'student_id':'test','version':0,'answers':[]}).status_code,409)
    self.assertEqual(client.post('/api/assessment/'+first['session_id']+'/advance',json={'student_id':'other','version':2,'answers':[]}).status_code,404)
    match=client.post('/api/match',json={'skill_vector':{'Python':10},'profile_id':'test'}).json()[0]
    self.assertEqual(match['gaps'][0]['actual'],8)
    # The compatibility endpoint must never carry applied evidence into a legacy score.
    old_questions=client.get('/api/quiz/questions').json()['questions']
    body={'student_id':'test','answers':[{'question_id':q['id'],'value':5 if q['kind']=='rating' else 0} for q in old_questions]}
    self.assertEqual(client.post('/api/quiz/submit',json=body).status_code,200)
    self.assertEqual(client.get('/api/student/test/profile').json()['evidence'],{})

 def test_alert_new_job_threshold_crossing_and_no_duplicates(self):
  with tempfile.TemporaryDirectory() as d:
   loader=self.fixture(d)
   with patch.object(main,'DB',Path(d)/'test.db'),patch.object(main,'HybridJobLoader',lambda:loader):
    with TestClient(main.app) as client:
     sign_in(client,'test')
     with main.connection() as db:db.execute('INSERT INTO profiles(id,vector,updated) VALUES (?,?,?)',('test',json.dumps({'SQL':10}),main.now()))
     self.assertEqual(client.post('/api/alerts/subscribe',json={'student_id':'test','job_id':'one','min_match_threshold':75}).status_code,200)
     with main.connection() as db:db.execute('UPDATE profiles SET vector=? WHERE id=?',(json.dumps({'Python':10}),'test'))
     self.assertEqual(addon_api.check_alerts(loader),1);self.assertEqual(addon_api.check_alerts(loader),0)
     loader.jobs.append({**loader.jobs[0],'id':'two'});loader.matrix=build_job_matrix(loader.jobs)
     self.assertEqual(addon_api.check_alerts(loader),1);self.assertEqual(addon_api.check_alerts(loader),0)
     self.assertEqual(len(client.get('/api/student/test/alerts').json()['alerts']),2)
     client.delete('/api/student/test/alerts/subscription');self.assertEqual(addon_api.check_alerts(loader),0)
 def test_resource_links_only_and_missing_entries(self):
  with patch('backend.learning_resources.Path.read_text',return_value=json.dumps({'Python':[{'type':'doc','title':'Docs','url':'https://example.test/docs'},{'type':'doc','title':'Unsafe','url':'javascript:alert(1)'}]})):
   self.assertEqual(len(resources()['Python']),1);self.assertEqual(resources().get('SQL',[]),[])
