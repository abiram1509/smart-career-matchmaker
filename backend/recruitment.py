"""Opt-in recruitment and manual screening evaluation. Existing matcher is read-only."""
import json,secrets,sqlite3
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,HTTPException,Request
from pydantic import BaseModel,ConfigDict,Field,StrictBool,field_validator
from .accounts import connection
from .domain import SKILLS,rank_jobs

router=APIRouter(prefix='/api/recruitment')

def migrate(db):
    db.execute('''CREATE TABLE IF NOT EXISTS recruitment_roles (
        id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
        required_skills TEXT NOT NULL, eligibility TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
        baseline_seconds REAL, created_at TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS recruitment_applications (
        id TEXT PRIMARY KEY, role_id TEXT NOT NULL, student TEXT NOT NULL, vector TEXT NOT NULL,
        evidence TEXT NOT NULL, assessment_updated TEXT NOT NULL, eligibility_response TEXT NOT NULL,
        consent_at TEXT NOT NULL, withdrawn INTEGER NOT NULL DEFAULT 0,
        decision TEXT NOT NULL DEFAULT 'pending', reviewed INTEGER NOT NULL DEFAULT 0,
        review_seconds REAL NOT NULL DEFAULT 0, evaluation_label TEXT NOT NULL DEFAULT 'unlabelled',
        UNIQUE(role_id,student))''')
    db.execute('CREATE INDEX IF NOT EXISTS recruitment_owner ON recruitment_roles(owner)')
    db.execute('CREATE INDEX IF NOT EXISTS recruitment_role_applicants ON recruitment_applications(role_id,withdrawn)')

class Model(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Role(Model):
    title:str=Field(min_length=3,max_length=150)
    description:str=Field(min_length=10,max_length=2000)
    required_skills:dict[str,float]=Field(min_length=1,max_length=20)
    eligibility:str=Field(default='',max_length=1000)
    @field_validator('title','description')
    @classmethod
    def text(cls,value):
        if not value.strip():raise ValueError('Enter a title and description.')
        return value.strip()
    @field_validator('required_skills')
    @classmethod
    def known_skills(cls,value):
        if any(k not in SKILLS or not 1<=v<=10 for k,v in value.items()):raise ValueError('Choose known skills with levels from 1 to 10.')
        return value

class Apply(Model):
    consent:StrictBool
    eligibility_response:Literal['meets','unsure','does_not_meet']
    @field_validator('consent')
    @classmethod
    def require_consent(cls,value):
        if not value:raise ValueError('Consent is required to share your profile for this role.')
        return value

class Review(Model):
    decision:Literal['pending','shortlisted','not_shortlisted']
    reviewed:StrictBool
    review_seconds:float=Field(default=0,ge=0,le=86400,allow_inf_nan=False)
    evaluation_label:Literal['unlabelled','qualified','not_qualified']='unlabelled'

class RoleState(Model):
    status:Literal['open','closed']
    baseline_seconds:float|None=Field(default=None,gt=0,le=31536000,allow_inf_nan=False)

def now():return datetime.now(timezone.utc).isoformat()
def user_role(request,role):
    user=request.state.user
    if user['role']!=role:raise HTTPException(403,'This action requires a '+role+' account.')
    return user
def owned(db,identity,user):
    row=db.execute('SELECT * FROM recruitment_roles WHERE id=? AND owner=?',(identity,user['id'])).fetchone()
    if not row:raise HTTPException(404,'Recruitment role not found.')
    return row

@router.get('/skills')
def skills(request:Request):
    user_role(request,'industry');return SKILLS

@router.post('/roles',status_code=201)
def create(body:Role,request:Request):
    user=user_role(request,'industry');identity=secrets.token_hex(16)
    with connection() as db:
        db.execute('INSERT INTO recruitment_roles VALUES (?,?,?,?,?,?,?,?,?)',
            (identity,user['id'],body.title,body.description,json.dumps(body.required_skills),body.eligibility,'open',None,now()))
    return {'id':identity}

@router.get('/roles')
def roles(request:Request):
    user=request.state.user
    if user['role'] not in ('student','industry'):raise HTTPException(403,'A student or industry account is required.')
    with connection() as db:
        condition='r.owner=?' if user['role']=='industry' else "(r.status='open' OR EXISTS(SELECT 1 FROM recruitment_applications a WHERE a.role_id=r.id AND a.student=? AND a.withdrawn=0))"
        rows=db.execute('SELECT r.*,a.name AS recruiter_name,a.organization FROM recruitment_roles r JOIN accounts a ON a.id=r.owner WHERE '+condition+' ORDER BY r.created_at DESC,r.id',(user['id'],)).fetchall()
        result=[]
        for row in rows:
            item={**dict(row),'required_skills':json.loads(row['required_skills'])}
            if user['role']=='student':
                own=db.execute('SELECT id,decision,consent_at,assessment_updated,eligibility_response FROM recruitment_applications WHERE role_id=? AND student=? AND withdrawn=0',(row['id'],user['id'])).fetchone()
                item['application']=dict(own) if own else None
                item.pop('baseline_seconds');item.pop('owner')
            result.append(item)
    return result

@router.post('/roles/{identity}/apply',status_code=201)
def apply(identity:str,body:Apply,request:Request):
    user=user_role(request,'student')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute("SELECT 1 FROM recruitment_roles WHERE id=? AND status='open'",(identity,)).fetchone():raise HTTPException(409,'Role is closed or unavailable.')
        profile=db.execute('SELECT vector,evidence,updated FROM profiles WHERE id=?',(user['id'],)).fetchone()
        if not profile:raise HTTPException(400,'Complete your existing skill assessment before applying.')
        existing=db.execute('SELECT id,withdrawn FROM recruitment_applications WHERE role_id=? AND student=?',(identity,user['id'])).fetchone()
        if existing and not existing['withdrawn']:raise HTTPException(409,'You have already opted in to this role.')
        application_id=existing['id'] if existing else secrets.token_hex(16)
        db.execute('''INSERT INTO recruitment_applications(id,role_id,student,vector,evidence,assessment_updated,eligibility_response,consent_at)
            VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(role_id,student) DO UPDATE SET vector=excluded.vector,evidence=excluded.evidence,
            assessment_updated=excluded.assessment_updated,eligibility_response=excluded.eligibility_response,consent_at=excluded.consent_at,
            withdrawn=0,decision='pending',reviewed=0,review_seconds=0,evaluation_label='unlabelled' ''',
            (application_id,identity,user['id'],profile['vector'],profile['evidence'],profile['updated'],body.eligibility_response,now()))
        # A changed applicant pool invalidates a previously entered comparison baseline.
        db.execute('UPDATE recruitment_roles SET baseline_seconds=NULL WHERE id=?',(identity,))
    return {'id':application_id,'status':'pending'}

@router.delete('/applications/{identity}')
def withdraw(identity:str,request:Request):
    user=user_role(request,'student')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        application=db.execute('SELECT role_id FROM recruitment_applications WHERE id=? AND student=? AND withdrawn=0',(identity,user['id'])).fetchone()
        if not application:raise HTTPException(404,'Application not found.')
        count=db.execute("UPDATE recruitment_applications SET withdrawn=1,vector='{}',evidence='{}' WHERE id=? AND student=? AND withdrawn=0",(identity,user['id'])).rowcount
        if not count:raise HTTPException(404,'Application not found.')
        db.execute('UPDATE recruitment_roles SET baseline_seconds=NULL WHERE id=?',(application['role_id'],))
    return {'status':'withdrawn'}

def metrics(role,rows):
    total=len(rows);reviewed=sum(bool(r['reviewed']) for r in rows);shortlisted=sum(r['decision']=='shortlisted' for r in rows)
    labelled=sum(r['evaluation_label']!='unlabelled' for r in rows)
    qualified=[r for r in rows if r['evaluation_label']=='qualified']
    retained=sum(r['decision']=='shortlisted' for r in qualified)
    complete=total>0 and labelled==total
    closed=role['status']=='closed';seconds=sum(r['review_seconds'] for r in rows if r['reviewed'])
    baseline=role['baseline_seconds']
    return {'applicants':total,'reviewed':reviewed,'shortlisted':shortlisted,'unreviewed':total-reviewed,
        'review_reduction_percent':round(100*(total-reviewed)/total,1) if closed and total and reviewed else None,
        'recorded_review_seconds':seconds,'baseline_seconds':baseline,
        'time_reduction_percent':round(100*(baseline-seconds)/baseline,1) if closed and baseline and reviewed and seconds>0 else None,
        'evaluation_labelled':labelled,'evaluation_complete':complete,
        'qualified_total':len(qualified) if complete else None,'qualified_shortlisted':retained if complete else None,
        'qualified_missed':len(qualified)-retained if complete else None,
        'qualified_retention_percent':round(100*retained/len(qualified),1) if complete and qualified else None,
        'note':'Review reduction compares manually recorded reviews with reviewing every current opt-in applicant. Time baseline and evaluation labels are human-entered. This is not a validated hiring outcome or a claim of 40% improvement. Withdrawn applicants are excluded.'}

@router.get('/roles/{identity}/applicants')
def applicants(identity:str,request:Request):
    user=user_role(request,'industry')
    with connection() as db:
        role=owned(db,identity,user)
        rows=db.execute('SELECT p.*,a.name FROM recruitment_applications p JOIN accounts a ON a.id=p.student WHERE p.role_id=? AND p.withdrawn=0',(identity,)).fetchall()
    job={'id':role['id'],'skills':json.loads(role['required_skills'])};result=[]
    for row in rows:
        vector=json.loads(row['vector']);evidence=json.loads(row['evidence'])
        match=rank_jobs(vector,[job],limit=1,evidence=evidence or None)[0]
        comparisons=[{key:skill[key] for key in ['skill','actual','required','delta','assessed','evidence']} for skill in match['matched_skills']+match['gaps']]
        result.append({**{k:row[k] for k in ['id','name','decision','reviewed','review_seconds','evaluation_label','assessment_updated','eligibility_response','consent_at']},
            'match_score':match['match_score'],'skills':comparisons})
    result.sort(key=lambda r:(-r['match_score'],r['id']))
    return {'applicants':result,'metrics':metrics(role,rows)}

@router.patch('/applications/{identity}/review')
def review(identity:str,body:Review,request:Request):
    user=user_role(request,'industry')
    if not body.reviewed and body.review_seconds:raise HTTPException(422,'Record time only for a reviewed application.')
    with connection() as db:
        changed=db.execute('''UPDATE recruitment_applications SET decision=?,reviewed=?,review_seconds=?,evaluation_label=?
            WHERE id=? AND withdrawn=0 AND role_id IN (SELECT id FROM recruitment_roles WHERE owner=?)''',
            (body.decision,body.reviewed,body.review_seconds,body.evaluation_label,identity,user['id'])).rowcount
        if not changed:raise HTTPException(404,'Applicant not found.')
    return {'status':'saved'}

@router.patch('/roles/{identity}')
def role_state(identity:str,body:RoleState,request:Request):
    user=user_role(request,'industry')
    with connection() as db:
        owned(db,identity,user)
        db.execute('UPDATE recruitment_roles SET status=?,baseline_seconds=? WHERE id=? AND owner=?',(body.status,body.baseline_seconds,identity,user['id']))
    return {'status':body.status}
