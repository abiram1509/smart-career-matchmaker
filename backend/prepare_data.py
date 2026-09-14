"""Reproducible, offline preparation; no model weights or proficiency labels fabricated."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from .domain import SKILLS
from .career_fields import ALIASES, TRACKS
from .experience import describe_experience
from .category_mapping import CATEGORY_CODE_TO_FIELD_TRACK,CATEGORY_TO_SKILLS_TEMPLATE

# A combined literal-phrase expression scans each description once.
_ALIAS_LOOKUP=defaultdict(set)
for skill in SKILLS:
    for alias in ALIASES.get(skill,[skill]):_ALIAS_LOOKUP[alias.casefold()].add(skill)
_SCAN=re.compile(r'(?<![\w])(?:'+'|'.join(re.escape(a) for a in sorted(_ALIAS_LOOKUP,key=len,reverse=True))+r')(?![\w])',re.I)
def skill_counts(text):
    found=Counter()
    for match in _SCAN.finditer(text):
        for skill in _ALIAS_LOOKUP[match.group().casefold()]:found[skill]+=1
    return found
FIELD_PATTERNS=[
 ('healthcare',r'nurs|physician|therapist|medical|health|patient|clinical|pharmac|dentist|caregiver|dietitian'),
 ('education',r'teacher|teaching|educat|tutor|instructor|professor|lecturer|curriculum'),
 ('legal',r'legal|attorney|paralegal|counsel|compliance'),
 ('people',r'recruit|human resource|talent acquisition|payroll|administrative|office assistant|office associate|receptionist'),
 ('finance',r'accountant|accounting|audit|financial|finance|bookkeep|tax\b|controller|investment|banker'),
 ('creative',r'market|creative|graphic|content|copywriter|video|editor|designer|social media|public relations'),
 ('sales',r'sales|customer|account manager|business development|insurance agent|retail|cashier'),
 ('technology',r'software|developer|data |\bIT\b|cyber|devops|cloud|programmer|full.?stack|front.?end|back.?end|machine learning|database|systems engineer'),
 ('operations',r'engineer|manufactur|warehouse|logistics|supply chain|inventory|technician|maintenance|construction|driver|production|operator|project manager'),
]

def extract_skills(text): return sorted(skill_counts(text))
def career_field(title):
    for field,pattern in FIELD_PATTERNS:
        if re.search(pattern,title,re.I): return field
    return 'other'

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f: yield from csv.DictReader(f)
def clean(value): return re.sub(r'\s+',' ',str(value or '')).strip()
def numeric(value):
    try:
        n=float(value)
        return n if 0<n<1e9 else None
    except (ValueError,TypeError): return None
def company_key(value): return re.sub(r'\.0$','',clean(value))

def salary(row):
    currency=clean(row.get('currency'))
    period=clean(row.get('pay_period')).upper()
    lo,mid,hi=[numeric(row.get(k)) for k in ['min_salary','med_salary','max_salary']]
    if lo and hi and lo>hi: return 'Not disclosed',None
    if not currency or period not in {'HOURLY','MONTHLY','YEARLY'} or not any([lo,mid,hi]): return 'Not disclosed',None
    amount=f'{lo:,.0f}–{hi:,.0f}' if lo and hi else f'{mid or lo or hi:,.0f}'
    return f"{currency} {amount} / {dict(HOURLY='hour',MONTHLY='month',YEARLY='year')[period]}", {'currency':currency,'period':period,'min':lo,'median':mid,'max':hi,'basis':'Reported in historical source; not a prediction'}

def prepare(source, output):
    output.mkdir(parents=True,exist_ok=True)
    industries=defaultdict(list); benefits=defaultdict(list); categories=defaultdict(list)
    companies={company_key(r['company_id']):r for r in rows(source/'companies.csv')} if (source/'companies.csv').exists() else {}
    if (source/'job_skills.csv').exists():
        for r in rows(source/'job_skills.csv'):categories[company_key(r['job_id'])].append(r['skill_abr'])
    for r in rows(source/'company_industries.csv'):
        industries[company_key(r['company_id'])].append(r['industry'])
    for r in rows(source/'benefits.csv'):
        benefits[r['job_id']].append({'type':r['type'],'inferred':r['inferred']=='1'})
    jobs=[]; identities=set(); fingerprints=set(); counts=Counter(); field_counts=Counter(); salary_counts=Counter()
    sources=['job_postings.csv','linkdin_Job_data.csv']
    for filename in sources:
        for r in rows(source/filename):
            counts[f'{filename}:input']+=1
            title=clean(r.get('title') or r.get('job'))
            description=clean(r.get('description') or r.get('job_details'))
            raw_id=clean(r.get('job_id') or r.get('job_ID'))
            identity='linkedin-'+raw_id
            joined_company=companies.get(company_key(r.get('company_id')),{})
            company=clean(joined_company.get('name') or joined_company.get('company_name') or r.get('company_name')) or ('Company ID '+company_key(r.get('company_id')) if r.get('company_id') else 'Company not provided')
            location=clean(r.get('location')) or 'Not specified'
            fingerprint=hashlib.sha256((title.lower()+'|'+description.lower()).encode()).hexdigest()
            if not raw_id or not title or len(description)<80:
                counts['invalid_or_short']+=1;continue
            if identity in identities or fingerprint in fingerprints:
                counts['duplicates']+=1;continue
            codes=list(dict.fromkeys(categories.get(company_key(raw_id),[])))
            frequency_in_description=skill_counts(description)
            extracted=sorted(frequency_in_description)
            skills={skill:(7 if frequency_in_description[skill]>=3 else 6) for skill in extracted}
            skill_source='description_parsed'
            if len(extracted)<2:
                template={skill:level for code in codes for skill,level in CATEGORY_TO_SKILLS_TEMPLATE.get(code,{}).items()}
                if not template:
                    counts['fewer_than_two_skills']+=1;continue
                skills=template;skill_source='category_template'
            counts[skill_source]+=1
            identities.add(identity);fingerprints.add(fingerprint)
            category_fields=list(dict.fromkeys(CATEGORY_CODE_TO_FIELD_TRACK[c][0] for c in codes if c in CATEGORY_CODE_TO_FIELD_TRACK))
            category_tracks=list(dict.fromkeys(t for c in codes if c in CATEGORY_CODE_TO_FIELD_TRACK for t in CATEGORY_CODE_TO_FIELD_TRACK[c][1]))
            field=category_fields[0] if category_fields else career_field(title);field_counts[field]+=1
            salary_text,salary_data=salary(r)
            if salary_data: salary_counts[field]+=1
            work=clean(r.get('formatted_work_type') or r.get('full_time_remote'))
            kind='Internship' if re.search(r'intern',title+' '+work,re.I) else 'Apprenticeship' if re.search(r'apprentice',title+' '+work,re.I) else 'Part-time' if 'part-time' in work.lower() else 'Contract' if 'contract' in work.lower() else 'Full-time' if 'full-time' in work.lower() else 'Not specified'
            url=clean(r.get('job_posting_url'))
            # Do not infer levels from prose. Five is a disclosed learning baseline,
            # shared by all extracted skill mentions, not an employer assertion.
            jobs.append({'id':identity,'title':title,'company':company,'location':location,'type':kind,
                'skills':skills,'description':description,'salary':salary_text,'salary_data':salary_data,
                'url':url,'source':filename,'demo':False,'historical':True,'field':field,
                **describe_experience(r),
                'skill_source':skill_source,'category_codes':codes,'category_fields':category_fields,'category_tracks':category_tracks,'company_id':company_key(r.get('company_id')),
                'requirement_basis':('Description mentions mapped to heuristic learning targets: 6/10 once, 7/10 for 3+ mentions. These are not employer-stated levels.' if skill_source=='description_parsed' else 'Broad category fallback: these skills and 5/10 targets are inferred template assumptions, not stated job requirements.'),
                'industries':industries.get(company_key(r.get('company_id')),[]),'benefits':benefits.get(raw_id,[]),
                'eligibility_note':'Skill similarity does not establish qualifications, work authorization, registration or professional licensing. Check the original role requirements.',
                'listed_timestamp':r.get('original_listed_time') or None,'extraction_version':'description-category-v3'})
            counts[f'{filename}:retained']+=1
    assert len(jobs)>=2000, f'Only {len(jobs)} usable jobs; do not claim 2000+.'
    columns=list(jobs[0])
    with (output/'jobs.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for job in jobs: w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) or v is None or isinstance(v,bool) else v for k,v in job.items()})
    frequency=Counter(s for j in jobs for s in j['skills'])
    report={'prepared_at':datetime.now(timezone.utc).isoformat(),'jobs':len(jobs),'unique_skills':len(SKILLS),'extracted_skills':len(frequency),'counts':dict(counts),
        'fields':{TRACKS.get(k,{'label':'Other fields'})['label']:v for k,v in field_counts.items()},'salary_jobs':sum(salary_counts.values()),'salary_by_field':dict(salary_counts),
        'source_sha256':{name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in sources},
        'method':'Deterministic cosine similarity over shared skill axes. Description mentions use heuristic 6/7 targets; category fallback uses disclosed 5 targets. Company/category joins use supplied IDs.',
        'excluded_sources':{'clean_data.parquet':'1,415,533 rows but inspected samples contain skill/benefit fragments in title/description, no role IDs, salary, employer or location. Held out rather than represented as reliable job listings.',
          'employee_income.csv':'50 age/experience/income rows without currency, pay period, role or location. Not suitable for role-based salary prediction; age is not used in matching.',
          'linkdin_Job_data.xlsx':'Duplicate-format source of the supplied LinkedIn CSV; not double-counted.',

          'job_industries.csv':'Industry ID lookup not supplied. Company industry labels used where a company ID joins.',
          'company_specialities.csv':'Employer specialties do not prove requirements of an individual role.',
          'employee_counts.csv':'Company size is not an individual skill requirement.',
          'Largest_Companies.csv':'No compatible company ID join; not used to invent company names.',
          'skill_taxonomy.json':'Original technology-heavy extraction counts are not proficiency labels. Demand counts recomputed from the prepared corpus.'}}
    (output/'dataset_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (output/'skill_demand.json').write_text(json.dumps(dict(frequency.most_common()),indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return jobs,report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,default=Path(__file__).parent/'data')
    args=parser.parse_args();prepare(args.source,args.output)
