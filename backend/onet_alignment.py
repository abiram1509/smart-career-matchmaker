"""Optional occupation enrichment before matrix construction; no scoring changes."""
import json
import os
import tempfile
from pathlib import Path
import httpx
from .assessment_config import ASSESSMENT_TRACKS
from .onet_policy import candidates, assignments, title_key
from .prepare_onet import derive_profile

DATA=Path(__file__).resolve().parent/'data'

def read_json(path):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError,TypeError): return {}

class OccupationAlignment:
    def __init__(self, corpus_path=None, cache_path=None, api_key=None):
        self.corpus=read_json(Path(corpus_path or DATA/'onet-corpus.json'))
        if not isinstance(self.corpus.get('occupations',{}),dict) or not isinstance(self.corpus.get('ambiguous_aliases',{}),dict):
            self.corpus={}
        self.cache_path=Path(cache_path or DATA/'onet-cache.json')
        self.cache=read_json(self.cache_path)
        self.api_key=os.getenv('ONET_API_KEY','') if api_key is None else api_key
        self.pools=candidates()
        self.assignments=assignments()
        self.aliases={}
        self.memo={}
        self.api_failed=False
        self.counts={'local':0,'api':0,'cache':0,'unchanged':0,'ambiguous':0}
        for code,item in self.corpus.get('occupations',{}).items():
            if code not in self.assignments or not isinstance(item,dict): continue
            aliases=item.get('aliases',[])
            if not isinstance(aliases,list): continue
            for alias in aliases:
                if isinstance(alias,str): self.aliases.setdefault(title_key(alias),set()).add(code)

    def valid(self, code, item):
        if not isinstance(item,dict) or code not in self.assignments: return None
        if item.get('code')!=code or item.get('tracks',[item.get('track')])!=self.assignments[code]: return None
        try:
            return derive_profile(item,self.assignments[code])
        except (KeyError,TypeError,ValueError,AttributeError): return None

    def fetch(self,code):
        if not self.api_key or self.api_failed: return None
        track=self.assignments[code][0]
        result={'code':code,'title':code,'track':track,'field':ASSESSMENT_TRACKS[track]['field'],
                'tracks':self.assignments[code],
                'skills':[],'software':[],'tasks':[]}
        try:
            for endpoint,key in [('skills','element'),('knowledge','element'),('tasks','task'),('technology_skills','category')]:
                response=httpx.get(f'https://api-v2.onetcenter.org/online/occupations/{code}/details/{endpoint}',
                    params={'start':1,'end':2000},headers={'X-API-Key':self.api_key},timeout=5,follow_redirects=False)
                response.raise_for_status()
                payload=response.json()
                items=payload[key]
                if not isinstance(items,list) or payload.get('total',len(items))>len(items):
                    raise ValueError('Incomplete O*NET response')
                if endpoint=='technology_skills':
                    for category in items:
                        for example in [*category.get('example',[]),*category.get('example_more',[])]:
                            result['software'].append({'kind':'O*NET API software','id':str(category['code']),
                                'name':example['title'],'category':category['title']})
                else:
                    for row in items:
                        importance=row.get('importance')
                        if isinstance(importance,bool) or not isinstance(importance,(int,float)) or not 0<=importance<=100: continue
                        result['tasks' if endpoint=='tasks' else 'skills'].append({'kind':'O*NET API '+endpoint,
                            'id':str(row['id']),'name':row['title' if endpoint=='tasks' else 'name'],
                            'importance':importance,'importance_min':0,'importance_scale':'standardized 0–100'})
            return self.valid(code,result)
        except (httpx.HTTPError,ValueError,KeyError,TypeError,AttributeError):
            self.api_failed=True
            return None

    def save_cache(self):
        tmp=None
        try:
            self.cache_path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.cache_path.parent,suffix='.tmp',delete=False) as stream:
                tmp=Path(stream.name);json.dump(self.cache,stream,ensure_ascii=False,allow_nan=False)
            tmp.replace(self.cache_path)
        except (OSError,ValueError,TypeError): pass
        finally:
            if tmp:
                try: tmp.unlink(missing_ok=True)
                except OSError: pass

    def profile(self,code):
        if not isinstance(code,str) or code not in self.assignments: return None,'unchanged'
        if code in self.memo: return self.memo[code]
        local=self.valid(code,self.corpus.get('occupations',{}).get(code))
        if local is not None: answer=(local,'local')
        else:
            remote=self.fetch(code)
            if remote is not None:
                self.cache[code]=remote;self.save_cache();answer=(remote,'api')
            else: answer=(self.valid(code,self.cache.get(code)),'cache')
        self.memo[code]=answer
        return answer

    def enrich(self,job):
        if job.get('demo'): self.counts['unchanged']+=1;return job
        code=job.get('onet_soc_code')
        if code is not None and not isinstance(code,str): self.counts['unchanged']+=1;return job
        key=title_key(job.get('title',''))
        if not code:
            if key in self.corpus.get('ambiguous_aliases',{}):
                self.counts['ambiguous']+=1;return job
            codes=self.aliases.get(key,set())
            if len(codes)!=1: self.counts['unchanged']+=1;return job
            code=next(iter(codes))
        if code not in self.assignments:
            self.counts['ambiguous']+=1;return job
        occupation,source=self.profile(code)
        if not occupation or not occupation['vector']: self.counts['unchanged']+=1;return job
        # Preserve employer/source values. Add compatible dimensions only.
        skills={**occupation['vector'],**job['skills']}
        added=sorted(set(skills)-set(job['skills']))
        self.counts[source]+=1
        return {**job,'skills':skills,'onet_alignment':{'code':code,'occupation':occupation['title'],
            'field':occupation['field'],'track':occupation['track'],'tracks':occupation['tracks'],
            'track_vectors':occupation['track_vectors'],'source':source,'added_skills':added,
            'evidence':{s:occupation['evidence'][s] for s in added},
            'note':'O*NET occupation-derived skill presence; added dimensions use the app learning baseline of 5/10, not employer requirements or a conversion of O*NET importance.'}}
