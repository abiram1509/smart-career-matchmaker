from auth_fixture import sign_in
import unittest
from backend import adaptive_quiz as quiz

class BackendBankTests(unittest.TestCase):
 def state(self,flags,context=''):
  s=quiz.initial('tech','backend')
  def submit(values):
   return quiz.advance(s,[{'question_id':q['id'],'value':values(q)} for q in s['pending']])
  submit(lambda q:8)
  submit(lambda q:2 if q['skill'] in flags else 0)
  if s['phase']=='context':submit(lambda q:context if q['type']=='project_note' else 8 if q['type']=='self_rating' else 0)
  return s
 def test_exact_import_and_hidden_keys(self):
  rows=[q for q in quiz.bank() if q['track']=='backend']
  self.assertEqual(len(rows),85)
  checks=[q for q in rows if q['tier']==3]
  self.assertEqual({q['id'] for q in checks},{f'backend-user-q{i:02d}' for i in range(1,61)})
  self.assertFalse(any(q.get('example') for q in checks))
  self.assertTrue(all('correct_option' not in quiz.public(q) for q in checks))
 def test_cluster_gate_and_separate_scoring(self):
  s=self.state(['Deployment'])
  self.assertEqual(len(s['pending']),10)
  self.assertEqual({q['skill'] for q in s['pending']},{'Git','Deployment'})
  answers=[{'question_id':q['id'],'value':(q['correct_option']+1)%4 if q['skill']=='Git' else q['correct_option']} for q in s['pending']]
  vector,evidence=quiz.score(quiz.advance(s,answers))
  self.assertEqual(vector['Git'],4);self.assertEqual(vector['Deployment'],8)
  self.assertTrue(evidence['Deployment']['verified'])
 def test_full_path_context_and_missing_baseline(self):
  s=self.state(['Python','SQL','REST APIs','Authentication','Deployment'],'An e-commerce authentication API')
  self.assertEqual(len(s['pending']),20)
  self.assertIn('backend-user-q15',[q['id'] for q in s['pending']])
  self.assertEqual(len({q['requires_tier2_flag'] for q in s['pending']}),5)
  vector,evidence=quiz.score(quiz.advance(s,[{'question_id':q['id'],'value':q['correct_option']} for q in s['pending']]))
  for skill in ['Backend Testing','Adaptive / Project Context']:
   self.assertEqual(vector[skill],0);self.assertFalse(evidence[skill]['assessed']);self.assertFalse(evidence[skill]['verified'])
   self.assertGreater(evidence[skill]['checks'],0)
  self.assertEqual(vector['Java / Node.js'],8);self.assertEqual(vector['Java'],0);self.assertEqual(vector['Node.js'],0)
 def test_context_prioritizes_project_check(self):
  flags=['Python','SQL','REST APIs','Authentication','Deployment']
  generic=self.state(flags);relevant=self.state(flags,'JWT login authentication')
  self.assertNotIn('backend-user-q15',[q['id'] for q in generic['pending']])
  self.assertIn('backend-user-q15',[q['id'] for q in relevant['pending']])
 def test_only_eligible_questions_for_every_flag(self):
  for flag in ['Python','SQL','REST APIs','Authentication','Deployment']:
   s=self.state([flag]);self.assertLessEqual(len(s['pending']),20)
   self.assertTrue(all(q['requires_tier2_flag']==flag for q in s['pending']))

class BackendPersistenceTests(unittest.TestCase):
 def test_full_assessment_persists_context_and_unrated_evidence(self):
  import tempfile
  from pathlib import Path
  from unittest.mock import patch
  from fastapi.testclient import TestClient
  from backend import main
  from backend.loader import HybridJobLoader
  from backend.domain import build_job_matrix
  with tempfile.TemporaryDirectory() as d:
   loader=HybridJobLoader(Path(d)/'absent.csv',Path(d)/'absent.json','')
   with patch.object(main,'DB',Path(d)/'profile.db'),patch.object(main,'HybridJobLoader',lambda:loader):
    with TestClient(main.app) as client:
     sign_in(client,'backend-import-test')
     response=client.post('/api/assessment/start',json={'student_id':'backend-import-test','field':'tech','track':'backend'})
     self.assertEqual(response.status_code,200);result=response.json();count=0
     keys={q['id']:q.get('correct_option') for q in quiz.bank()}
     while result['phase']!='complete':
      questions=result['questions'];count+=len(questions)
      answers=[{'question_id':q['id'],'value':8 if q['type']=='self_rating' else 'Authentication API project' if q['type']=='project_note' else keys[q['id']] if q['tier']==3 else 2 if q['type']=='project_count' else 0} for q in questions]
      response=client.post('/api/assessment/'+result['session_id']+'/advance',json={'student_id':'backend-import-test','version':result['version'],'answers':answers})
      self.assertEqual(response.status_code,200,response.text);result=response.json()
     self.assertEqual(count,40)
     profile=client.get('/api/student/backend-import-test/profile').json()
     self.assertEqual(profile['project_notes']['backend-user-context-1'],'Authentication API project')
     self.assertGreater(profile['evidence']['Backend Testing']['checks'],0)
     self.assertFalse(profile['evidence']['Backend Testing']['assessed'])
