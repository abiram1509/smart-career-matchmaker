from auth_fixture import sign_in
import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit
import httpx
from backend.loader import HybridJobLoader
from backend.experience import describe_experience

class FieldExperienceTests(unittest.TestCase):
    def test_experience_evidence(self):
        self.assertEqual(describe_experience({'job_required_experience':{'required_experience_in_months':24}})['experience_level'],'2 years required')
        self.assertEqual(describe_experience({'full_time_remote':'Full-time · Associate'})['experience_level'],'Associate')
        self.assertEqual(describe_experience({'description':'We require 3+ years of relevant experience.'})['experience_level'],'3+ years mentioned')
        self.assertEqual(describe_experience({'experience_level':'Not stated in source'})['experience_basis'],'Not available')
        self.assertEqual(describe_experience({'description':'Freshers are welcome.'})['experience_level'],'No experience required')
    def test_nine_queries_and_partial_cache(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'JOBS_API_URL':'https://jsearch.p.rapidapi.com/search-v2?country=in','JOBS_API_SEARCH_MODE':'fields'}):
            queries=[]
            def fetch(url,**kwargs):
                query=parse_qs(urlsplit(url).query)['query'][0];queries.append(query)
                return httpx.Response(200,request=httpx.Request('GET',url),json={'status':'OK','data':{'jobs':[{'job_id':query,'job_title':'Accountant','employer_name':'Example','job_description':'Accounting and Excel experience.'}]}})
            cache=Path(temp)/'cache.json'
            with patch('backend.loader.httpx.get',side_effect=fetch):
                first=HybridJobLoader(Path(temp)/'absent.csv',cache)
            self.assertEqual(len(queries),9);self.assertEqual(len(set(queries)),9);self.assertEqual(len(first.jobs),9)
            self.assertEqual(len(list(Path(temp).glob('cache-*.json'))),9)
            def partial(url,**kwargs):
                if 'teacher' in url:return httpx.Response(403,request=httpx.Request('GET',url))
                return fetch(url,**kwargs)
            with patch('backend.loader.httpx.get',side_effect=partial):
                second=HybridJobLoader(Path(temp)/'absent.csv',cache)
            self.assertEqual(second.query_status['education']['source'],'cache')
            self.assertEqual(second.source_counts['live'],8);self.assertEqual(second.source_counts['cache'],1)
            self.assertEqual(second.source_counts['demo'],0)
    def test_live_wins_cached_duplicate_and_preserves_fields(self):
        records=HybridJobLoader.merge([{'id':'1','source_kind':'cache','search_fields':['education']}],[{'id':'1','source_kind':'live','search_fields':['technology']}])
        self.assertEqual(len(records),1);self.assertEqual(records[0]['source_kind'],'live')
        self.assertEqual(set(records[0]['search_fields']),{'education','technology'})


    def test_source_filter_applies_before_limit(self):
        from fastapi.testclient import TestClient
        from backend import main
        with tempfile.TemporaryDirectory() as temp:
            loader=HybridJobLoader(Path(temp)/'missing.csv',Path(temp)/'cache.json','')
            loader.jobs[0]['source_kind']='live'
            with patch.object(main,'DB',Path(temp)/'test.sqlite3'),patch.object(main,'HybridJobLoader',lambda:loader):
                with TestClient(main.app) as client:
                    sign_in(client,'test')
                    response=client.post('/api/match',json={'skill_vector':{'Python':5},'source_filter':'live','limit':10})
                    self.assertEqual(response.status_code,200)
                    self.assertEqual(len(response.json()),1)
                    self.assertEqual(response.json()[0]['job']['source_kind'],'live')
                    self.assertEqual(client.post('/api/match',json={'skill_vector':{'Python':5},'source_filter':'bad'}).status_code,422)

    def test_pagination_fills_to_ten_without_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            loader=HybridJobLoader(Path(temp)/'absent.csv',Path(temp)/'cache.json','')
            loader.api_url='https://jsearch.p.rapidapi.com/search-v2?query=healthcare'
            loader.active_search_field='healthcare'
            def job(i):return {'job_id':str(i),'job_title':'Healthcare Assistant','employer_name':'Example','job_description':'Patient care and communication.'}
            first={'status':'OK','data':{'jobs':[job(i) for i in range(8)],'cursor':'next'}}
            second={'status':'OK','data':{'jobs':[job(i) for i in range(6,16)],'cursor':None}}
            responses=[httpx.Response(200,json=p,request=httpx.Request('GET',loader.api_url)) for p in [first,second]]
            with patch('backend.loader.httpx.get',side_effect=responses) as fetch:
                jobs=loader.read_single_api()
            self.assertEqual(len(jobs),10);self.assertEqual(len({j['id'] for j in jobs}),10)
            self.assertIn('cursor=next',fetch.call_args.args[0])
