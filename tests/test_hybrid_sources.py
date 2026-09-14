import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from backend.loader import HybridJobLoader,normalize
from backend.settings import load_environment

class HybridSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.csv=self.root/'jobs.csv';self.cache=self.root/'cache.json'
        self.kaggle={'id':'k1','title':'Accountant','company':'Historical Company','skills':{'Accounting':5},'historical':True}
        self.live={'id':'l1','title':'Accountant','company':'Live Company','skills':{'Accounting':7}}
    def tearDown(self):self.temp.cleanup()
    def write_csv(self):
        with self.csv.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=self.kaggle);w.writeheader();w.writerow({k:json.dumps(v) if isinstance(v,dict) else v for k,v in self.kaggle.items()})
    def response(self,code=200,rows=None):return httpx.Response(code,json=rows if rows is not None else [self.live],request=httpx.Request('GET','https://example.test/jobs'))
    def load(self,url='https://example.test/jobs'):return HybridJobLoader(self.csv,self.cache,url)
    def test_live_combines_with_kaggle_and_caches_only_api(self):
        self.write_csv()
        with patch('backend.loader.httpx.get',return_value=self.response()) as fetch:
            data=self.load();fetch.assert_called_once()
        self.assertEqual(data.layer,'api+kaggle')
        self.assertEqual([j['id'] for j in data.jobs],['l1','k1'])
        self.assertEqual(data.source_counts,{'live':1,'cache':0,'kaggle':1,'demo':0})
        self.assertEqual([j['id'] for j in json.loads(self.cache.read_text())],['l1'])
    def test_failed_api_combines_cache_and_kaggle(self):
        self.write_csv();self.cache.write_text(json.dumps([self.live]))
        with patch('backend.loader.httpx.get',return_value=self.response(429)),patch('backend.loader.time.sleep'):
            data=self.load()
        self.assertEqual(data.layer,'cache+kaggle');self.assertEqual(len(data.jobs),2)
        self.assertTrue(all(not j['demo'] for j in data.jobs))
    def test_kaggle_survives_api_failure_and_corrupt_cache(self):
        self.write_csv();self.cache.write_text('broken')
        with patch('backend.loader.httpx.get',side_effect=httpx.ConnectError('offline')),patch('backend.loader.time.sleep'):
            data=self.load()
        self.assertEqual(data.layer,'kaggle');self.assertEqual(len(data.jobs),1)
        self.assertEqual(data.source_counts['demo'],0)
    def test_demo_only_when_all_sources_fail(self):
        with patch('backend.loader.httpx.get',return_value=self.response(200,[])),patch('backend.loader.time.sleep'):
            data=self.load()
        self.assertEqual(data.layer,'fallback');self.assertTrue(all(j['demo'] for j in data.jobs))
    def test_live_duplicate_wins_and_url_query_is_ignored(self):
        live={**self.live,'id':'k1'}
        self.assertEqual(HybridJobLoader.merge([live],[self.kaggle]),[live])
        live={**self.live,'url':'https://example.test/job/123?source=api'}
        historical={**self.kaggle,'url':'https://example.test/job/123/?source=csv'}
        self.assertEqual(HybridJobLoader.merge([live],[historical]),[live])
        live={**self.live,'url':'https://example.test/job?id=1'}
        historical={**self.kaggle,'url':'https://example.test/job?id=2'}
        self.assertEqual(len(HybridJobLoader.merge([live],[historical])),2)
    def test_api_description_can_supply_skills_and_field(self):
        rows=normalize([{'id':'a','title':'Accountant','company':'A','description':'Accounting and reconciliation with Excel.'}],'API')
        self.assertEqual(rows[0]['field'],'finance');self.assertIn('Accounting',rows[0]['skills'])
        self.assertIn('baseline',rows[0]['requirement_basis'])
    def test_environment_file_keeps_existing_environment(self):
        config=self.root/'.env';config.write_text('JOBS_API_URL=https://from-file.test\nJOBS_API_KEY="secret value"\n')
        with patch.dict(os.environ,{'JOBS_API_URL':'https://environment.test'},clear=True):
            load_environment(config)
            self.assertEqual(os.environ['JOBS_API_URL'],'https://environment.test')
            self.assertEqual(os.environ['JOBS_API_KEY'],'secret value')
    def test_api_key_is_header_only(self):
        with patch.dict(os.environ,{'JOBS_API_KEY':'test-key','JOBS_API_KEY_HEADER':'X-API-Key','JOBS_API_KEY_PREFIX':'NONE'}),patch('backend.loader.httpx.get',return_value=self.response()) as fetch:
            data=self.load()
        self.assertEqual(fetch.call_args.kwargs['headers'],{'X-API-Key':'test-key'})
        self.assertNotIn('test-key',' '.join(data.events))
