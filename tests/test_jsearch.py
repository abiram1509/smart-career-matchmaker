import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from backend.jsearch import adapt_jobs
from backend.loader import HybridJobLoader

class JSearchTests(unittest.TestCase):
    def example(self):return {'status':'OK','data':[{'job_id':'123','job_title':'Accountant','employer_name':'Example','job_description':'Accounting, reconciliation and Excel.','job_employment_type':'FULLTIME','job_city':'Chennai','job_country':'IN','job_min_salary':30000,'job_max_salary':50000,'job_salary_currency':'INR','job_salary_period':'MONTH','job_apply_link':'https://example.test/jobs/123','job_benefits':['paid_time_off']}]}
    def test_provider_mapping_and_salary_units(self):
        job=adapt_jobs(self.example())[0]
        self.assertEqual(job['id'],'jsearch-123');self.assertEqual(job['company'],'Example')
        self.assertEqual(job['type'],'Full-time');self.assertEqual(job['salary'],'INR 30,000–50,000 / month')
        self.assertEqual(job['benefits'][0]['type'],'paid time off')
    def test_missing_currency_is_not_inferred_from_country(self):
        payload=self.example();del payload['data'][0]['job_salary_currency']
        self.assertIsNone(adapt_jobs(payload)[0]['salary_data'])
    def test_v2_nested_job_array(self):
        payload={'status':'OK','data':{'jobs':self.example()['data'],'cursor':'next-page'}}
        self.assertEqual(adapt_jobs(payload)[0]['id'],'jsearch-123')
    def test_jsearch_headers_extraction_and_cache(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'JOBS_API_KEY':'test-secret'}):
            response=httpx.Response(200,json=self.example(),request=httpx.Request('GET','https://jsearch.p.rapidapi.com/search'))
            with patch('backend.loader.httpx.get',return_value=response) as fetch:
                loader=HybridJobLoader(Path(temp)/'missing.csv',Path(temp)/'cache.json','https://jsearch.p.rapidapi.com/search?query=accountant')
            self.assertEqual(fetch.call_args.kwargs['headers'],{'X-RapidAPI-Host':'jsearch.p.rapidapi.com','X-RapidAPI-Key':'test-secret'})
            self.assertEqual(loader.jobs[0]['field'],'finance');self.assertIn('Accounting',loader.jobs[0]['skills'])
            self.assertTrue((Path(temp)/'cache.json').exists());self.assertNotIn('test-secret',' '.join(loader.events))
    def test_subscription_error_does_not_repeat_request(self):
        with tempfile.TemporaryDirectory() as temp:
            response=httpx.Response(403,request=httpx.Request('GET','https://jsearch.p.rapidapi.com/search'))
            with patch('backend.loader.httpx.get',return_value=response) as fetch:
                loader=HybridJobLoader(Path(temp)/'missing.csv',Path(temp)/'cache.json','https://jsearch.p.rapidapi.com/search')
            fetch.assert_called_once();self.assertEqual(loader.layer,'fallback')
            self.assertTrue(any('HTTP 403' in e for e in loader.events))
