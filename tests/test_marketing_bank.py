import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from auth_fixture import sign_in
from backend import adaptive_quiz as quiz, main
from backend.import_marketing_bank import parse, validate
from backend.loader import HybridJobLoader

class MarketingImportTests(unittest.TestCase):
 def test_exact_parse_and_source_ids_options_flags(self):
  rows=parse();self.assertEqual(len(rows),85)
  self.assertEqual([q['id'] for q in rows if q['tier']==3],[f'Q{i}' for i in range(1,61)])
  by_id={q['id']:q for q in rows}
  self.assertEqual(by_id['Q26']['prompt_text'],'An advertiser spends ₹20,000 and receives 400 clicks. What is the average cost per click?')
  self.assertEqual(by_id['Q26']['options'],['₹50','₹5','₹80','₹200'])
  self.assertEqual(by_id['Q26']['skill'],'Paid Search')
  self.assertEqual(by_id['Q26']['requires_tier2_flag'],'SEO / SEM')
  self.assertEqual(by_id['marketing_t1_q03']['skill'],'Search Engine Optimization')
  self.assertTrue(all(q['correct_option']==0 for q in rows if q['tier']==3))
  self.assertEqual(validate(rows)['unknown_labels'],[])

 def test_loaded_bank_and_controls_match_source(self):
  rows=parse();stored=[q for q in quiz.bank() if q['track']=='marketing']
  self.assertEqual(stored,rows)
  self.assertEqual([q['options'] for q in rows if q.get('phase')=='counts'],[['0','1','2–3','4–5','6+']]*5)
  self.assertEqual(len([q for q in quiz.bank() if q['track']=='business-marketing']),23)

 def test_actual_api_serves_parsed_tiers_and_keeps_cap(self):
  with tempfile.TemporaryDirectory() as temp:
   fixture=HybridJobLoader(Path(temp)/'none.csv',Path(temp)/'none.json','')
   with patch.object(main,'DB',Path(temp)/'test.sqlite3'),patch.object(main,'HybridJobLoader',lambda:fixture):
    with TestClient(main.app) as client:
     student=sign_in(client,'marketing-import')
     # sign_in's account ID is the explicitly supplied fixture identity.
     response=client.post('/api/assessment/start',json={'student_id':'marketing-import','field':'marketing-sales','track':'marketing'})
     self.assertEqual(response.status_code,200,response.text)
     current=response.json();sizes=[]
     while current['phase']!='complete':
      sizes.append((current['phase'],len(current['questions'])))
      answers=[]
      for q in current['questions']:
       self.assertNotIn('correct_option',q)
       value=8 if q['type']=='self_rating' else '' if q['type']=='project_note' else 2 if q['type']=='project_count' else 0
       answers.append({'question_id':q['id'],'value':value})
      response=client.post(f"/api/assessment/{current['session_id']}/advance",json={'student_id':'marketing-import','version':current['version'],'answers':answers})
      self.assertEqual(response.status_code,200,response.text);current=response.json()
     self.assertEqual(sizes,[('confidence',15),('counts',5),('context',5),('verification',15)])
     self.assertEqual(current['skill_vector']['Digital Marketing'],8)
     with main.connection() as db:
      self.assertEqual(db.execute("SELECT count(*) FROM questions WHERE track='marketing'").fetchone()[0],85)
      self.assertEqual(db.execute("SELECT count(*) FROM questions WHERE track='marketing' AND tier=3").fetchone()[0],60)

