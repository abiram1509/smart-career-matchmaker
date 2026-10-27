import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from auth_fixture import sign_in
from backend import adaptive_quiz as quiz, main
from backend.import_frontend_bank import parse, validate, namespaced_id
from backend.loader import HybridJobLoader

class FrontendImportTests(unittest.TestCase):
 def test_source_code_answers_flags_and_loaded_bank(self):
  rows=parse();self.assertEqual(len(rows),85)
  self.assertEqual({q['id'] for q in rows if q['tier']==3},{f'FE-Q{i}' for i in range(1,61)})
  self.assertEqual(rows,[q for q in quiz.bank() if q['track']=='frontend'])
  by_id={q['id']:q for q in rows}
  self.assertEqual(by_id['FE-Q11']['prompt_text'],'What does this code print?\n```js\nconst nums = [1, 2, 3];\nconst result = nums.map(x => x * 2);\nconsole.log(result);\n```')
  self.assertEqual(by_id['FE-Q11']['options'],['`[1, 2, 3]`','`[2, 4, 6]`','`[1, 4, 9]`','`6`'])
  self.assertEqual(by_id['FE-Q11']['correct_option'],1)
  self.assertEqual(by_id['FE-Q4']['correct_option'],1)
  self.assertEqual(by_id['FE-Q10']['skill'],'Accessibility')
  self.assertEqual(by_id['FE-Q10']['requires_tier2_flag'],'HTML/CSS')
  self.assertEqual(by_id['FE-Q59']['verification_kind'],'project')
  self.assertIn('*Example trigger:',by_id['FE-Q59']['prompt_text'])
  self.assertEqual(namespaced_id('future-track','Q1'),'FUTURE-TRACK-Q1')
  self.assertEqual(validate(rows)['checks_without_baselines'],['Project-Informed API Integration','Project-Informed React'])

 def test_api_tiers_cap_sqlite_and_database_driven_catalog(self):
  with tempfile.TemporaryDirectory() as temp:
   fixture=HybridJobLoader(Path(temp)/'none.csv',Path(temp)/'none.json','')
   with patch.object(main,'DB',Path(temp)/'test.sqlite3'),patch.object(main,'HybridJobLoader',lambda:fixture):
    with TestClient(main.app) as client:
     sign_in(client,'frontend-import')
     tracks=client.get('/api/assessment/catalog').json()['tracks']
     self.assertEqual(sum(t['bank_summary']['kind']=='authored' for t in tracks.values()),8)
     self.assertEqual(tracks['frontend']['bank_summary']['total'],85)
     self.assertEqual(tracks['business-marketing']['bank_summary']['kind'],'starter')
     current=client.post('/api/assessment/start',json={'student_id':'frontend-import','field':'tech','track':'frontend'}).json();sizes=[]
     while current['phase']!='complete':
      self.assertIn('Full authored bank: 85',current['notice'])
      sizes.append((current['phase'],len(current['questions'])))
      answers=[]
      for q in current['questions']:
       self.assertNotIn('correct_option',q)
       value=8 if q['type']=='self_rating' else '' if q['type']=='project_note' else 2 if q['type']=='project_count' else 0
       answers.append({'question_id':q['id'],'value':value})
      response=client.post(f"/api/assessment/{current['session_id']}/advance",json={'student_id':'frontend-import','version':current['version'],'answers':answers})
      self.assertEqual(response.status_code,200,response.text);current=response.json()
     self.assertEqual(sizes,[('confidence',10),('counts',5),('context',5),('verification',20)])
     with main.connection() as db:
      self.assertEqual(db.execute("SELECT count(*) FROM questions WHERE track='frontend'").fetchone()[0],85)
      self.assertEqual(db.execute("SELECT count(*) FROM questions WHERE track='frontend' AND tier=3").fetchone()[0],60)
      db.execute("DELETE FROM questions WHERE track='frontend' AND tier=3")
     changed=client.get('/api/assessment/catalog').json()['tracks']['frontend']['bank_summary']
     self.assertEqual(changed['total'],25);self.assertEqual(changed['kind'],'partial')
