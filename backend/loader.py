"""Live API + Kaggle; cached API + Kaggle on failure; demo only if all empty."""
import csv
import json
import logging
import os
import time
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit,parse_qsl,urlencode
import httpx
from .domain import SKILLS, build_job_matrix
from .settings import load_environment
from .experience import describe_experience

log = logging.getLogger('career.data')
DATA = Path(__file__).resolve().parent / 'data'

def fallback_jobs():
    roles = [
        ('Junior Python Developer', 'Northstar Labs', 'Bengaluru', 'Full-time', {'Python':7,'SQL':6,'REST APIs':5,'Git':5}, '₹5–8 LPA'),
        ('Frontend Engineering Intern', 'Studio Orbit', 'Remote', 'Internship', {'React':6,'JavaScript':6,'HTML':5,'CSS':5,'Git':3}, '₹20k–30k / month'),
        ('Data Analyst Intern', 'Meridian Analytics', 'Hyderabad', 'Internship', {'Python':5,'SQL':7,'Excel':5,'Communication':5}, '₹18k–25k / month'),
        ('Cloud Engineering Apprentice', 'Nimbus Works', 'Pune', 'Apprenticeship', {'AWS':5,'Docker':4,'Linux':5,'Python':4}, '₹25k / month'),
        ('Full Stack Developer', 'Canvas Digital', 'Remote', 'Full-time', {'React':7,'Node.js':6,'SQL':5,'REST APIs':6,'Git':5}, '₹6–10 LPA'),
        ('QA Engineering Intern', 'Quality Arc', 'Chennai', 'Internship', {'Testing':6,'Python':4,'Problem Solving':5,'Communication':4}, '₹15k–22k / month'),
        ('Backend Engineering Intern', 'Harbor Systems', 'Bengaluru', 'Internship', {'Python':5,'SQL':4,'REST APIs':4,'Data Structures':5}, '₹25k–35k / month'),
        ('UI Developer', 'Pixel Collective', 'Mumbai', 'Full-time', {'HTML':7,'CSS':7,'JavaScript':5,'Accessibility':4,'Teamwork':5}, '₹4–7 LPA'),
        ('ML Research Intern', 'Signal AI', 'Remote', 'Internship', {'Python':7,'Machine Learning':6,'Statistics':5,'Pandas':5}, '₹30k / month'),
        ('DevOps Trainee', 'Launchpad Tech', 'Hyderabad', 'Apprenticeship', {'Docker':5,'AWS':4,'Git':6,'CI/CD':4}, '₹22k / month'),
        ('Industry API Project', 'Openbridge', 'Remote', 'Project', {'REST APIs':5,'Python':5,'Documentation':4,'Teamwork':5}, 'Project certificate'),
        ('Graduate Software Engineer', 'Evergreen Technologies', 'Pune', 'Full-time', {'JavaScript':5,'Data Structures':6,'Problem Solving':6,'Communication':5}, '₹5–9 LPA'),
    ]
    return [{'id': f'demo-{i+1}', 'title': title, 'company': company, 'location': location, 'type': kind, 'skills': skills, 'salary': salary, 'description': f'Build practical experience as a {title.lower()}. Collaborate with a mentor, contribute to real-world-style tasks, and grow your engineering skills.', 'source': 'Demo', 'url': '', 'demo': True} for i,(title,company,location,kind,skills,salary) in enumerate(roles)]

def normalize(rows, source):
    jobs, seen = [], set()
    for row in rows:
        if not isinstance(row, dict): continue
        try:
            skills = row.get('skills', {})
            if isinstance(skills, str): skills = json.loads(skills)
            if not isinstance(skills, dict): continue
            if not skills and source=='API':
                from .prepare_data import extract_skills
                skills={s:5 for s in extract_skills(str(row.get('title',''))+' '+str(row.get('description','')))}
                row={**row,'requirement_basis':'Skill mentions only; 5/10 is an application learning baseline, not an employer-stated proficiency requirement.'}
            cleaned = {}
            for skill, value in skills.items():
                number = float(value)
                if skill in SKILLS and 0 < number <= 10: cleaned[skill] = number
            if not cleaned: continue
            identity = str(row.get('id', '')).strip()
            title, company = str(row.get('title', '')).strip(), str(row.get('company', '')).strip()
            if not identity or not title or not company or identity in seen: continue
            seen.add(identity)
            url = str(row.get('url', ''))
            jobs.append({'id': identity, 'title': title, 'company': company, 'skills': cleaned, 'location': str(row.get('location') or 'Not specified'), 'type': str(row.get('type') or 'Full-time'), 'salary': str(row.get('salary') or 'Not disclosed'), 'description': str(row.get('description') or ''), 'url': url if url.startswith(('https://','http://')) else '', 'source': source, 'demo': False})
            job=jobs[-1]
            job.update(describe_experience(row))
            if source=='API' and not row.get('field'):
                from .prepare_data import career_field
                job['field']=career_field(title)
            for key in ['field','requirement_basis','eligibility_note','extraction_version','fetched_at','skill_source','company_id','onet_soc_code']:
                if row.get(key): job[key]=str(row[key])
            job['source']=str(row.get('source') or source)
            job['historical']=row.get('historical') in (True,'true','True')
            for key in ['salary_data','benefits','industries','search_fields','category_codes','category_fields','category_tracks']:
                value=row.get(key)
                try: job[key]=json.loads(value) if isinstance(value,str) else value
                except (ValueError,TypeError): job[key]=None
        except (ValueError, TypeError):
            continue
    return jobs

class HybridJobLoader:
    def __init__(self, csv_path=None, cache_path=None, api_url=None):
        load_environment()
        self.csv_path = Path(csv_path or os.getenv('JOBS_CSV', str(DATA/'jobs.csv')))
        self.cache_path = Path(cache_path or DATA/'jobs-cache.json')
        self.api_url = api_url if api_url is not None else os.getenv('JOBS_API_URL', '')
        self.search_mode=os.getenv('JOBS_API_SEARCH_MODE','single') if api_url is None else 'single'
        self.active_search_field=None
        self.query_status={}
        self.events, self.layer = [], 'fallback'
        self.source_counts = {}
        self.cache_write_failures = 0
        self.jobs = self.load()
        from .onet_alignment import OccupationAlignment
        alignment = OccupationAlignment()
        self.jobs = [alignment.enrich(job) for job in self.jobs]
        self.alignment_status = alignment.counts
        self.matrix = build_job_matrix(self.jobs)

    def event(self, message):
        self.events.append(message)
        log.info(message)

    def write_cache(self, jobs):
        """Atomically replace a snapshot; failed writes preserve the previous copy."""
        tmp = None
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.cache_path.parent,
                                             prefix=self.cache_path.stem+'-', suffix='.tmp', delete=False) as stream:
                tmp = Path(stream.name)
                json.dump(jobs, stream, ensure_ascii=False, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            tmp.replace(self.cache_path)
            return True
        except (OSError, ValueError, TypeError):
            self.cache_write_failures += 1
            self.event('Cache write failed; existing snapshot preserved and fetched jobs remain available')
            return False
        finally:
            if tmp is not None:
                try: tmp.unlink(missing_ok=True)
                except OSError: pass

    def cache_status(self):
        """Count stored backups separately from records currently served from cache."""
        from datetime import datetime, timezone
        records, usable, invalid, latest = [], 0, 0, None
        paths = [self.cache_path, *self.cache_path.parent.glob(self.cache_path.stem+'-*'+self.cache_path.suffix)]
        for path in paths:
            if not path.exists(): continue
            try:
                rows = json.loads(path.read_text(encoding='utf-8'))
                jobs = normalize(rows, 'Cache') if isinstance(rows, list) else []
                if not jobs:
                    invalid += 1
                    continue
                records = self.merge(records, jobs)
                usable += 1
                modified = path.stat().st_mtime
                latest = max(latest, modified) if latest is not None else modified
            except (OSError, ValueError, TypeError): invalid += 1
        return {'stored_jobs':len(records), 'usable_files':usable, 'invalid_files':invalid,
                'last_saved_at':datetime.fromtimestamp(latest, timezone.utc).isoformat() if latest is not None else None,
                'served_jobs':self.source_counts.get('cache',0), 'write_failures':self.cache_write_failures}

    def done(self, jobs, layer):
        self.layer = layer
        self.source_counts={kind:sum(j.get('source_kind')==kind for j in jobs) for kind in ['live','cache','kaggle','demo']}
        self.event(f'Loaded {len(jobs)} jobs from {layer}')
        return jobs

    def read_csv(self):
        try:
            with self.csv_path.open(encoding='utf-8-sig', newline='') as f: jobs = normalize(csv.DictReader(f), 'CSV')
            if jobs:
                self.event(f'Loaded {len(jobs)} Kaggle records to combine with API data')
                return [{**j,'source_kind':'kaggle'} for j in jobs]
            self.event('CSV contained no valid jobs')
        except (OSError, UnicodeError, csv.Error) as e: self.event(f'CSV unavailable ({type(e).__name__})')
        return []

    def read_single_api(self):
        if self.api_url:
            headers={}
            key=os.getenv('JOBS_API_KEY','')
            is_jsearch=urlsplit(self.api_url).hostname=='jsearch.p.rapidapi.com'
            if is_jsearch:
                headers['X-RapidAPI-Host']='jsearch.p.rapidapi.com'
                if key:headers['X-RapidAPI-Key']=key
            elif key:
                prefix=os.getenv('JOBS_API_KEY_PREFIX','Bearer')
                headers[os.getenv('JOBS_API_KEY_HEADER','Authorization')]=(prefix+' ' if prefix!='NONE' else '')+key
            for attempt in range(3):
                try:
                    response = httpx.get(self.api_url, headers=headers, timeout=60 if is_jsearch else 4, follow_redirects=False)
                    response.raise_for_status()
                    payload = response.json()
                    if is_jsearch:
                        from .jsearch import adapt_jobs
                        rows=adapt_jobs(payload)
                    else:rows = payload.get('jobs', []) if isinstance(payload, dict) else payload
                    jobs = normalize(rows, 'API') if isinstance(rows, list) else []
                    if is_jsearch and self.active_search_field:
                        # Fetch additional provider pages only when usable unique jobs fall below ten.
                        cursor=payload.get('data',{}).get('cursor') if isinstance(payload.get('data'),dict) else None
                        visited=set()
                        while len(jobs)<10 and cursor and cursor not in visited and len(visited)<2:
                            visited.add(cursor)
                            parts=urlsplit(self.api_url)
                            params=[(k,v) for k,v in parse_qsl(parts.query) if k!='cursor']
                            page_url=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(params+[('cursor',cursor)]),''))
                            try:
                                extra=httpx.get(page_url,headers=headers,timeout=60,follow_redirects=False)
                                extra.raise_for_status();page=extra.json()
                                jobs=self.merge(jobs,normalize(adapt_jobs(page),'API'))
                                cursor=page.get('data',{}).get('cursor') if isinstance(page.get('data'),dict) else None
                            except (httpx.HTTPError,ValueError,TypeError):
                                self.event('Additional page unavailable; retaining successful results')
                                break
                        jobs=jobs[:10]
                    if not jobs: raise ValueError('API contained no valid jobs')
                    from datetime import datetime, timezone
                    fetched=datetime.now(timezone.utc).isoformat()
                    jobs=[{**j,'source':'Live API','source_kind':'live','historical':False,'fetched_at':fetched} for j in jobs]
                    if self.active_search_field:
                        jobs=[{**j,'search_fields':[self.active_search_field]} for j in jobs]
                    saved = self.write_cache(jobs)
                    self.event(f'Live API returned {len(jobs)} usable jobs; '+('cache saved' if saved else 'cache could not be updated'))
                    return jobs
                except (httpx.HTTPError, ValueError, TypeError) as error:
                    code=error.response.status_code if isinstance(error,httpx.HTTPStatusError) else None
                    self.event(f'API attempt {attempt+1}/3 failed'+(f' (HTTP {code})' if code else f' ({type(error).__name__})'))
                    if code in {400,401,403,404}:
                        self.event('Check the API URL, key, subscription and request parameters; using other data sources')
                        break
                    if attempt < 2: time.sleep(0.5 * 2**attempt)
        else: self.event('Live API disabled')
        return []

    def read_api(self):
        if self.search_mode!='fields' or urlsplit(self.api_url).hostname!='jsearch.p.rapidapi.com':
            return self.read_single_api()
        queries=json.loads((Path(__file__).parent/'field_queries.json').read_text(encoding='utf-8'))
        base_url,base_cache=self.api_url,self.cache_path
        combined_backup=self.read_cache() if base_cache.exists() else []
        collected=[]
        try:
            for field,query in queries.items():
                parts=urlsplit(base_url)
                params=[(k,v) for k,v in parse_qsl(parts.query) if k not in {'query','cursor','page','num_pages'}]
                self.api_url=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(params+[('query',query)]),''))
                self.cache_path=base_cache.with_name(base_cache.stem+'-'+field+base_cache.suffix)
                self.active_search_field=field
                self.event(f'Fetching JSearch career field: {field}')
                records=self.read_single_api()
                state='live'
                if not records:
                    records=self.read_cache()
                    if not records:
                        records=[dict(j) for j in combined_backup if field in (j.get('search_fields') or [j.get('field')])]
                    state='cache' if records else 'unavailable'
                for j in records:j['search_fields']=list(dict.fromkeys([*(j.get('search_fields') or []),field]))
                collected=self.merge(collected,records)
                self.query_status[field]={'source':state,'returned_jobs':len(records)}
                self.event(f'{field}: {len(records)} usable {state} records')
        finally:
            self.api_url,self.cache_path=base_url,base_cache
            self.active_search_field=None
        if collected:
            self.write_cache(collected)
        return collected

    def read_cache(self):
        try:
            rows = json.loads(self.cache_path.read_text(encoding='utf-8'))
            jobs = normalize(rows, 'Cache') if isinstance(rows, list) else []
            if jobs:
                self.event(f'Recovered {len(jobs)} cached API jobs; freshness not verified')
                return [{**j,'source':'Cached API','source_kind':'cache','historical':False} for j in jobs]
        except (OSError, ValueError, TypeError): self.event('No usable cache')
        return []

    @staticmethod
    def merge(preferred, secondary):
        """API/cache wins collisions on stable ID or canonical source URL."""
        merged=[]; ids=set(); urls=set(); identities={}; url_jobs={}
        for job in sorted([*preferred,*secondary],key=lambda j: {'live':0,'cache':1,'kaggle':2}.get(j.get('source_kind'),3)):
            url=job.get('url','')
            if url:
                try:
                    parts=urlsplit(url)
                    query=urlencode(sorted((k,v) for k,v in parse_qsl(parts.query) if not k.lower().startswith('utm_') and k.lower() not in {'source','trk'}))
                    url=urlunsplit((parts.scheme.lower(),parts.netloc.lower(),parts.path.rstrip('/'),query,''))
                except ValueError: pass
            if job['id'] in ids:
                existing=identities[job['id']]
                existing['search_fields']=list(dict.fromkeys([*(existing.get('search_fields') or []),*(job.get('search_fields') or [])]))
                continue
            if url and url in urls:
                existing=url_jobs[url]
                existing['search_fields']=list(dict.fromkeys([*(existing.get('search_fields') or []),*(job.get('search_fields') or [])]))
                continue
            ids.add(job['id'])
            if url: urls.add(url); url_jobs[url]=job
            merged.append(job)
            identities[job['id']]=job
        return merged

    def load(self):
        live=self.read_api()
        cached=[] if live else self.read_cache()
        kaggle=self.read_csv()
        preferred=live or cached
        merged=self.merge(preferred,kaggle)
        if merged:
            kinds={j.get('source_kind') for j in merged}
            layer='+'.join(label for kind,label in [('live','api'),('cache','cache'),('kaggle','kaggle')] if kind in kinds)
            return self.done(merged,layer)
        return self.done([{**j,'source_kind':'demo'} for j in fallback_jobs()], 'fallback')
