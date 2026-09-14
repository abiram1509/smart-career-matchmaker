from auth_fixture import sign_in
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from backend.domain import rank_jobs, QUESTIONS, ANSWERS, score_answers, SKILLS
from backend.loader import HybridJobLoader, fallback_jobs, normalize
from backend import main

class MatchingTests(unittest.TestCase):
    def test_direction_and_explanation_are_distinct(self):
        job = {'id':'a','skills':{'Python':8,'SQL':8}}
        result = rank_jobs({'Python':4,'SQL':4},[job])[0]
        self.assertEqual(result['match_score'],100)
        self.assertEqual([g['delta'] for g in result['gaps']],[4,4])
        self.assertEqual(rank_jobs({'Python':0},[job])[0]['match_score'],0)

    def test_unassessed_skill_is_marked(self):
        result = rank_jobs({'Python':7},[{'id':'a','skills':{'Python':6,'AWS':5}}])[0]
        self.assertFalse(result['gaps'][0]['assessed'])
        self.assertEqual(result['matched_skills'][0]['skill'],'Python')

    def test_assessment_and_missing_questions(self):
        answers = [main.Answer(question_id=q['id'],value=10 if q['kind']=='rating' else 4 if q['kind']=='projects' else ANSWERS[q['id']]) for q in QUESTIONS]
        self.assertTrue(all(v==10 for v in score_answers(answers).values()))
        with self.assertRaises(ValueError): score_answers(answers[:-1])
        self.assertEqual(len(SKILLS),len(set(SKILLS)))

class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def loader(self,api=''): return HybridJobLoader(self.root/'jobs.csv',self.root/'cache.json',api)
    def test_absent_or_corrupt_data_falls_back(self):
        self.assertEqual(self.loader().layer,'fallback')
        (self.root/'cache.json').write_text('{broken')
        self.assertEqual(len(self.loader().jobs),12)
    def test_csv_available_when_api_disabled(self):
        row = fallback_jobs()[0]
        with (self.root/'jobs.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['id','title','company','skills']);w.writeheader();w.writerow({k:json.dumps(row[k]) if k=='skills' else row[k] for k in w.fieldnames})
        with patch('backend.loader.httpx.get') as get:
            self.assertEqual(self.loader('').layer,'kaggle');get.assert_not_called()
    def test_api_cache_and_rate_limit(self):
        response=httpx.Response(200,json=fallback_jobs(),request=httpx.Request('GET','https://example.test'))
        with patch('backend.loader.httpx.get',return_value=response): self.assertEqual(self.loader('https://example.test').layer,'api')
        blocked=httpx.Response(429,request=httpx.Request('GET','https://example.test'))
        with patch('backend.loader.httpx.get',return_value=blocked) as get, patch('backend.loader.time.sleep'):
            self.assertEqual(self.loader('https://example.test').layer,'cache');self.assertEqual(get.call_count,3)
    def test_malformed_rows_do_not_break_loader(self):
        self.assertEqual(normalize([None,'bad',{'skills':{'Python':'bad'}}],'CSV'),[])

class APITests(unittest.TestCase):
    def test_assess_match_persist_and_track(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(main,'DB',Path(directory)/'test.sqlite3'), patch.object(main,'HybridJobLoader',lambda:HybridJobLoader(Path(directory)/'none.csv',Path(directory)/'none.json','')):
            with TestClient(main.app) as client:
                sign_in(client,'test')
                self.assertEqual(client.get('/api/health').json()['data_layer'],'fallback')
                questions=client.get('/api/quiz/questions').json()['questions']
                self.assertEqual(len(questions),25)
                self.assertNotIn('answer',questions[-1])
                body={'student_id':'test','answers':[{'question_id':q['id'],'value':5 if q['kind']=='rating' else 1} for q in questions]}
                response=client.post('/api/quiz/submit',json=body);self.assertEqual(response.status_code,200)
                vector=response.json()['skill_vector']
                matches=client.post('/api/match',json={'skill_vector':vector,'student_id':'test'}).json()
                self.assertEqual(len(matches),10)
                self.assertTrue(all(matches[i]['match_score']>=matches[i+1]['match_score'] for i in range(9)))
                payload={'student_id':'test','job_id':matches[0]['job']['id']}
                for _ in range(2): self.assertEqual(client.post('/api/applications',json=payload).status_code,200)
                self.assertEqual(len(client.get('/api/student/test/applications').json()),1)
                self.assertEqual(len(client.get('/api/student/test/profile').json()['match_history']),1)
                self.assertEqual(client.get('/api/analytics').status_code,403)
                self.assertEqual(client.post('/api/match',json={'skill_vector':{'Unknown':3}}).status_code,422)
                self.assertEqual(client.post('/api/match',json={'skill_vector':{'Python':11}}).status_code,422)
                self.assertEqual(client.post('/api/quiz/submit',json={'student_id':'test','answers':[]}).status_code,422)
                self.assertEqual(client.get('/api/student/missing/profile').status_code,404)

if __name__=='__main__': unittest.main()
