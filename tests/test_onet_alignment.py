import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from backend.onet_alignment import OccupationAlignment,DATA
from backend.onet_policy import candidates, assignments, HELD
from backend.prepare_onet import derive_vector, derive_profile
from backend.domain import build_job_matrix,rank_jobs,SKILLS

class OnetTests(unittest.TestCase):
 def test_marketing_rated_tasks_cover_four_exact_baselines(self):
  engine=self.aligner()
  expected={'11-2021.00':{'Marketing Strategy','Market Research'},
            '13-1161.00':{'Market Research','Customer Research','Marketing Analytics'}}
  covered=set()
  for code,skills in expected.items():
   profile=engine.corpus['occupations'][code]
   self.assertTrue(skills<=set(profile['vector']))
   self.assertEqual({s:profile['track_vectors']['marketing'][s] for s in skills},{s:5.0 for s in skills})
   for skill in skills:
    self.assertTrue(all(e['kind']=='Task Statements' and e['importance']>1 and not e['suppressed'] for e in profile['evidence'][skill]))
   original=self.job(onet_soc_code=code);original['skills']={}
   enriched=engine.enrich(original)
   self.assertGreater(rank_jobs({s:8 for s in skills},[enriched])[0]['match_score'],0)
   for key in ['id','title','company','url','salary','source_kind']:self.assertEqual(enriched[key],original[key])
   covered.update(skills)
  self.assertEqual(len(covered),4)

 def test_marketing_unsupported_proxies_and_suppressed_tasks_stay_unmapped(self):
  profile={'track':'marketing','skills':[{'name':'Sales and Marketing','importance':5}],
           'software':[{'name':'Google Ads'},{'name':'Google Analytics'},{'name':'Facebook'},{'name':'Microsoft Outlook'},{'name':'WordPress'}],
           'tasks':[{'id':'951','importance':5,'suppressed':True},{'id':'963','importance':1}]}
  self.assertEqual(derive_vector(profile)[0],{})
 def test_marketing_approved_proxies_cover_ten_baselines_and_exclude_five(self):
  from backend.adaptive_quiz import bank
  from backend.onet_policy import MARKETING_UNMAPPED
  engine=self.aligner();covered=set()
  for code,size in [('11-2021.00',7),('13-1161.00',8)]:
   profile=engine.corpus['occupations'][code];vector=profile['track_vectors']['marketing']
   self.assertEqual(len(vector),size);self.assertTrue(all(value==5 for value in vector.values()))
   self.assertTrue(set(vector).isdisjoint(MARKETING_UNMAPPED))
   for skill in ['Digital Marketing','Search Engine Marketing','Social Media Marketing','Email Marketing']:
    self.assertTrue(all(e.get('mapping_basis')=='user-approved occupation-specific proxy' for e in profile['evidence'][skill]))
   covered.update(vector)
  baselines={q['skill'] for q in bank() if q['track']=='marketing' and q['tier']==1}
  self.assertEqual(len(covered & baselines),10)
  self.assertEqual(baselines-covered,set(MARKETING_UNMAPPED))

 def test_marketing_proxies_are_scoped_and_rejections_do_not_leak(self):
  p={'code':'11-2021.00','track':'marketing','skills':[],
     'software':[{'name':'Google Ads'},{'name':'WordPress'},{'name':'Microsoft Outlook'},{'name':'Google Analytics'}],
     'tasks':[{'id':'20709','importance':5,'suppressed':True},{'id':'961','importance':1}]}
  vector,evidence=derive_vector(p)
  self.assertEqual(vector,{'Digital Marketing':5,'Search Engine Marketing':5})
  self.assertEqual(derive_vector({**p,'code':'13-1071.00'})[0],{})
  self.assertEqual(derive_vector({**p,'track':'business-marketing'})[0],{})
  p['software']=[{'name':'WordPress'},{'name':'Drupal'},{'name':'Microsoft Outlook'},{'name':'Google Analytics'}]
  self.assertEqual(derive_vector(p)[0],{})
 def test_final_software_sharing_and_marketing_release(self):
  engine=self.aligner()
  expected={'15-1251.00':['backend','frontend'],'15-1252.00':['backend','frontend'],
            '15-1254.00':['backend','frontend'],'15-1243.00':['backend','data-ml'],
            '11-2021.00':['marketing'],'13-1161.00':['marketing']}
  for code,tracks in expected.items():
   self.assertEqual(assignments()[code],tracks)
   self.assertNotIn(code,HELD)
   profile=engine.corpus['occupations'][code]
   self.assertEqual(profile['tracks'],tracks)
   self.assertEqual(set(profile['track_vectors']),set(tracks))
   self.assertEqual(profile['vector'],{s:v for vector in profile['track_vectors'].values() for s,v in vector.items()})
   self.assertIsNone(profile['track'] if len(tracks)>1 else None)
   if len(tracks)>1:
    original=self.job(onet_soc_code=code);enriched=engine.enrich(original)
    self.assertEqual(enriched['onet_alignment']['tracks'],tracks)
    self.assertEqual(enriched['id'],original['id']);self.assertEqual(enriched['url'],original['url'])
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
 def aligner(self,corpus=None):
  return OccupationAlignment(corpus,self.root/'cache.json',api_key='')
 def job(self,title='Human Resources Specialist',**kw):
  return dict(id='real-1',title=title,company='Real employer',skills={'SQL':7},url='https://example.test/apply/1',source_kind='kaggle',salary='original salary',**kw)
 def test_source_preserved_and_exact_hr_labels_added(self):
  engine=self.aligner();job=self.job(onet_soc_code='13-1071.00');result=engine.enrich(job)
  self.assertIn('Talent Acquisition',result['skills']);self.assertIn('HR Information Systems',result['skills'])
  self.assertEqual(result['skills']['SQL'],7)
  for key in ['id','title','company','url','salary','source_kind']:self.assertEqual(result[key],job[key])
  self.assertEqual(job['skills'],{'SQL':7});self.assertEqual(result['onet_alignment']['track'],'hr')
  self.assertGreater(rank_jobs({'Talent Acquisition':8},[result])[0]['match_score'],0)
  self.assertEqual(build_job_matrix([result]).shape,(1,len(SKILLS)))
 def test_shared_occupation_requires_approval(self):
  engine=self.aligner()
  for code,pools in candidates().items():
   if len(pools)>1 and code not in assignments():
    job=self.job(onet_soc_code=code);self.assertIs(engine.enrich(job),job)
  self.assertNotIn('hr',candidates()['11-2022.00'])
 def test_ambiguous_and_unrelated_titles_not_fuzzy_matched(self):
  engine=self.aligner()
  for title in ['Completely Unknown Role','Senior Human Resources Specialist / Sales Manager']:
   job=self.job(title);self.assertIs(engine.enrich(job),job)
  key=next(iter(engine.corpus['ambiguous_aliases']))
  job=self.job(key);self.assertIs(engine.enrich(job),job)
 def test_missing_corrupt_and_demo_leave_original_input(self):
  path=self.root/'broken.json'
  for content in ['{broken','{"occupations": []}','{}']:
   path.write_text(content,encoding='utf-8');engine=self.aligner(path)
   job=self.job();self.assertIs(engine.enrich(job),job)
  job=self.job(demo=True,onet_soc_code='13-1071.00');self.assertIs(self.aligner().enrich(job),job)
 def test_local_is_primary_and_no_api_call(self):
  engine=self.aligner();engine.api_key='test-only'
  with patch('backend.onet_alignment.httpx.get',side_effect=AssertionError('network not needed')):
   self.assertEqual(engine.enrich(self.job(onet_soc_code='13-1071.00'))['onet_alignment']['source'],'local')
 def test_api_failure_uses_cache_and_preserves_original_when_all_fail(self):
  engine=self.aligner(self.root/'missing.json');engine.api_key='test-only'
  real=json.loads((DATA/'onet-corpus.json').read_text(encoding='utf-8'))['occupations']['13-1071.00']
  engine.cache['13-1071.00']=real
  with patch('backend.onet_alignment.httpx.get',side_effect=httpx.ConnectError('offline')):
   self.assertEqual(engine.enrich(self.job(onet_soc_code='13-1071.00'))['onet_alignment']['source'],'cache')
  engine=self.aligner(self.root/'missing.json');job=self.job(onet_soc_code='13-1071.00')
  self.assertIs(engine.enrich(job),job)
 def test_api_response_cached_without_changing_ratings(self):
  engine=self.aligner(self.root/'missing.json');engine.api_key='test-only'
  payloads=[{'element':[{'id':'2.B.1.e','name':'Negotiation','importance':72}],'total':1},
            {'element':[],'total':0},{'task':[{'id':'18862','title':'Interview job applicants','importance':81}],'total':1},
            {'category':[],'total':0}]
  responses=[httpx.Response(200,json=p,request=httpx.Request('GET','https://api-v2.onetcenter.org/')) for p in payloads]
  with patch('backend.onet_alignment.httpx.get',side_effect=responses) as fetch:
   result=engine.enrich(self.job(onet_soc_code='13-1071.00'))
  self.assertEqual(result['onet_alignment']['source'],'api');self.assertEqual(result['skills']['Interviewing'],5)
  saved=json.loads(engine.cache_path.read_text(encoding='utf-8'))
  self.assertEqual(saved['13-1071.00']['tasks'][0]['importance'],81)
  self.assertNotIn('test-only',engine.cache_path.read_text(encoding='utf-8'))
  self.assertEqual(fetch.call_args.kwargs['headers'],{'X-API-Key':'test-only'})
 def test_suppressed_missing_and_not_important_tasks_do_not_map(self):
  profile={'track':'hr','skills':[],'software':[],'tasks':[{'id':'18862','importance':5,'suppressed':True},{'id':'18870','importance':1},{'id':'18865'}]}
  self.assertEqual(derive_vector(profile)[0],{})
 def test_all_derived_vectors_follow_approved_assignments(self):
  engine=self.aligner();seen=set()
  for code,profile in engine.corpus['occupations'].items():
   self.assertEqual(assignments()[code],profile['tracks']);self.assertNotIn(code,seen);seen.add(code)
   self.assertTrue(set(profile['vector'])<=set(SKILLS))
   self.assertEqual(profile['vector'],derive_profile(profile,assignments()[code])['vector'])
 def test_approved_single_tracks_exclude_duplicate_candidates(self):
  engine=self.aligner()
  for code,track in [('11-2022.00','sales-track'),('41-3091.00','sales-track'),('15-1255.00','frontend'),('11-3131.00','hr'),('13-1151.00','hr')]:
   self.assertEqual(engine.assignments[code],[track])
   result=engine.enrich(self.job(onet_soc_code=code))
   self.assertEqual(result['onet_alignment']['tracks'],[track])
   if code in ['11-3131.00','13-1151.00']:
    self.assertIn('Training Needs Analysis',result['skills'])
    self.assertIn('Training Evaluation',result['skills'])
 def test_held_and_conditional_assignments_cannot_enter_through_cache(self):
  engine=self.aligner();engine.api_key='test-only'
  with patch('backend.onet_alignment.httpx.get',side_effect=AssertionError('held occupation must not query API')):
   for code in HELD:
    self.assertNotIn(code,engine.corpus['occupations'])
    engine.cache[code]={'code':code,'track':'marketing'}
    job=self.job(onet_soc_code=code);self.assertIs(engine.enrich(job),job)
 def test_shared_healthcare_keeps_distinct_track_vectors_and_single_listing(self):
  engine=self.aligner();job=self.job(onet_soc_code='29-2072.00')
  result=engine.enrich(job);meta=result['onet_alignment']
  self.assertEqual(meta['tracks'],['health-admin','health-it']);self.assertIsNone(meta['track'])
  self.assertIn('Medical Records',meta['track_vectors']['health-admin'])
  self.assertNotIn('Medical Records',meta['track_vectors']['health-it'])
  self.assertIn('Medical Records',result['skills'])
  self.assertEqual(result['id'],job['id']);self.assertEqual(result['url'],job['url'])
  self.assertEqual(len(rank_jobs({'Medical Records':8},[result])),1)
