import json
import logging
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictInt, field_validator
from .domain import SKILLS, TAXONOMY, QUESTIONS, score_answers, rank_jobs, get_assessment
from .career_fields import TRACKS
from .loader import HybridJobLoader, DATA

logging.basicConfig(level=logging.INFO)
DB = DATA/'career.sqlite3'
loader = None

@contextmanager
def connection():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        with db:
            yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app):
    global loader
    DATA.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, vector TEXT, updated TEXT)')
        if 'track' not in [r['name'] for r in db.execute('PRAGMA table_info(profiles)')]:
            db.execute("ALTER TABLE profiles ADD COLUMN track TEXT DEFAULT 'technology'")
        from .addon_api import migrate
        migrate(db)
        from .accounts import migrate as migrate_accounts
        from .connector import migrate as migrate_connector
        migrate_accounts(db)
        migrate_connector(db)
        from .portfolio import migrate as migrate_portfolio
        migrate_portfolio(db)
        from .internships import migrate as migrate_internships
        migrate_internships(db)
        from .recruitment import migrate as migrate_recruitment
        migrate_recruitment(db)
        from .privacy import migrate as migrate_privacy
        migrate_privacy(db)
        db.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, student TEXT, results TEXT, created TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS applications (student TEXT, job TEXT, status TEXT, created TEXT, PRIMARY KEY(student, job))')
    loader = HybridJobLoader()
    from .addon_api import sync_jobs
    sync_jobs(loader)
    yield

app = FastAPI(title='Smart Career Matchmaker', lifespan=lifespan, docs_url=None, redoc_url=None)
from .accounts import router as auth_router, AccessBoundary
from .connector import router as connector_router
app.add_middleware(AccessBoundary)
from .portfolio import router as portfolio_router, PortfolioUploadLimit
app.add_middleware(PortfolioUploadLimit)
from .internship_documents import router as internship_documents_router, InternshipUploadLimit
app.add_middleware(InternshipUploadLimit)
app.include_router(internship_documents_router)
from .security_headers import SecurityHeaders
app.add_middleware(SecurityHeaders)
app.include_router(portfolio_router)
from .internships import router as internship_router
app.include_router(internship_router)
from .recruitment import router as recruitment_router
app.include_router(recruitment_router)
from .privacy import router as privacy_router
app.include_router(privacy_router)
app.include_router(auth_router)
app.include_router(connector_router)
from .owner import router as owner_router
app.include_router(owner_router)
from .institutions import router as institutions_router
app.include_router(institutions_router)
StudentID = Annotated[str, Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')]

class Answer(BaseModel):
    question_id: str
    value: StrictInt

class Submission(BaseModel):
    student_id: StudentID
    track: str = 'technology'
    answers: list[Answer] = Field(max_length=25)

class MatchRequest(BaseModel):
    skill_vector: dict[str, float]
    student_id: StudentID | None = None
    limit: int = Field(default=10, ge=1, le=100)
    field: str = 'all'
    search: str = Field(default='',max_length=200)
    opportunity_type: str = 'All opportunities'
    source_filter: str = 'all'
    profile_id: str | None = None

    @field_validator('skill_vector')
    @classmethod
    def valid_vector(cls, value):
        if not value or any(k not in SKILLS or not 0 <= v <= 10 for k,v in value.items()):
            raise ValueError('Provide known skills with finite scores between 0 and 10.')
        return value

class Application(BaseModel):
    student_id: StudentID
    job_id: str = Field(max_length=100)

def now(): return datetime.now(timezone.utc).isoformat()

@app.get('/api/health')
def health():
    snapshot = loader
    fields={key:sum(j.get('field')==key or key in (j.get('search_fields') or []) or key in (j.get('category_fields') or []) for j in snapshot.jobs) for key in [*TRACKS,'other']}
    return {'occupation_alignment':snapshot.alignment_status, 'cache_storage':snapshot.cache_status(), 'status':'ok', 'data_layer':snapshot.layer, 'job_count':len(snapshot.jobs), 'events':snapshot.events, 'demo_mode':snapshot.layer=='fallback', 'historical':any(j.get('historical') for j in snapshot.jobs),'fields':fields,'salary_count':sum(bool(j.get('salary_data')) for j in snapshot.jobs),'source_counts':snapshot.source_counts,'api_configured':bool(snapshot.api_url),'query_status':snapshot.query_status}

@app.get('/api/quiz/questions')
def questions(track: str='technology'):
    try: _,items,_=get_assessment(track)
    except ValueError as e: raise HTTPException(422,str(e))
    return {'questions':items, 'taxonomy':TAXONOMY,'tracks':{k:v['label'] for k,v in TRACKS.items()},'track':track, 'disclaimer':'Assessment estimates proficiency. Self-reports and short scenarios do not verify skills or professional licenses.'}

@app.post('/api/quiz/submit')
def submit(body: Submission):
    try: vector = score_answers(body.answers,body.track)
    except ValueError as e: raise HTTPException(422, str(e))
    with connection() as db:
        db.execute("INSERT INTO profiles(id,vector,updated,track) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET vector=excluded.vector, updated=excluded.updated, track=excluded.track,evidence='{}',project_notes='{}',field=''", (body.student_id,json.dumps(vector),now(),body.track))
    return {'skill_vector':vector, 'student_id':body.student_id,'track':body.track}

@app.get('/api/jobs')
def jobs(): return loader.jobs

@app.post('/api/match')
def match(body: MatchRequest):
    snapshot = loader
    evidence=None
    if body.profile_id:
        with connection() as db:
            stored=db.execute('SELECT vector,evidence FROM profiles WHERE id=?',(body.profile_id,)).fetchone()
        if not stored: raise HTTPException(404,'Profile not found.')
        body.skill_vector=json.loads(stored['vector']);evidence=json.loads(stored['evidence']) or None
    if body.field not in ['all','other',*TRACKS]: raise HTTPException(422,'Unknown career field.')
    if body.source_filter not in ['all','live','cache','kaggle']: raise HTTPException(422,'Unknown source filter.')
    indices=[i for i,j in enumerate(snapshot.jobs) if (body.source_filter=='all' or j.get('source_kind')==body.source_filter) and (body.field=='all' or j.get('field')==body.field or body.field in (j.get('search_fields') or []) or body.field in (j.get('category_fields') or [])) and (body.opportunity_type=='All opportunities' or j['type']==body.opportunity_type) and (not body.search or body.search.lower() in ' '.join([j['title'],j['company'],j['location'],*j['skills']]).lower())]
    candidates=[snapshot.jobs[i] for i in indices]
    results = rank_jobs(body.skill_vector, candidates, body.limit,snapshot.matrix[indices],evidence=evidence)
    if body.student_id:
        with connection() as db:
            if not db.execute('SELECT id FROM profiles WHERE id=?',(body.student_id,)).fetchone(): raise HTTPException(404,'Complete the assessment first.')
            db.execute('INSERT INTO history(student,results,created) VALUES (?,?,?)',(body.student_id,json.dumps([{'job_id':r['job']['id'],'match_score':r['match_score']} for r in results]),now()))
    return results

@app.get('/api/student/{student_id}/profile')
def profile(student_id: str):
    with connection() as db:
        row = db.execute('SELECT * FROM profiles WHERE id=?',(student_id,)).fetchone()
        if not row: raise HTTPException(404,'No assessment yet.')
        history = db.execute('SELECT results,created FROM history WHERE student=? ORDER BY id DESC LIMIT 10',(student_id,)).fetchall()
    return {'student_id':student_id,'skill_vector':json.loads(row['vector']),'track':row['track'],'field':row['field'],'evidence':json.loads(row['evidence']),'project_notes':json.loads(row['project_notes']),'updated':row['updated'],'match_history':[{'results':json.loads(h['results']),'created':h['created']} for h in history]}

@app.post('/api/applications')
def apply(body: Application):
    if not any(j['id']==body.job_id for j in loader.jobs): raise HTTPException(404,'Job not found.')
    with connection() as db:
        if not db.execute('SELECT id FROM profiles WHERE id=?',(body.student_id,)).fetchone(): raise HTTPException(400,'Complete your assessment first.')
        db.execute('INSERT OR IGNORE INTO applications VALUES (?,?,?,?)',(body.student_id,body.job_id,'Saved locally',now()))
    return {'status':'Saved locally', 'message':'Demo tracker only. No application has been sent to an employer.'}

@app.get('/api/student/{student_id}/applications')
def applications(student_id: str):
    with connection() as db: rows = db.execute('SELECT * FROM applications WHERE student=? ORDER BY created DESC',(student_id,)).fetchall()
    lookup = {j['id']:j for j in loader.jobs}
    return [{**dict(r),'job_detail':lookup.get(r['job'])} for r in rows]

@app.get('/api/analytics')
def analytics(request: Request):
    if request.state.user['role'] != 'institution':
        raise HTTPException(403, 'Institution access is required.')
    demand = {}
    for job in loader.jobs:
        for skill in job['skills']: demand[skill] = demand.get(skill,0)+1
    with connection() as db:
        from .institutions import institution_for
        institution_id = institution_for(db, request.state.user['id'], 'institution')
        rows = db.execute('SELECT p.vector,p.evidence FROM profiles p JOIN accounts a ON a.id=p.id WHERE a.role=? AND a.institution_id=?', ('student',institution_id)).fetchall()
        count = db.execute('SELECT COUNT(*) FROM applications p JOIN accounts a ON a.id=p.student WHERE a.role=? AND a.institution_id=?', ('student',institution_id)).fetchone()[0]
    gaps = {}
    for row in rows:
        v = json.loads(row['vector']); evidence=json.loads(row['evidence'])
        for skill in v:
            if (not evidence or evidence.get(skill,{}).get('assessed')) and v[skill] < 6: gaps[skill] = gaps.get(skill,0)+1
    return {'students':len(rows),'jobs':len(loader.jobs),'applications':count,'demand':sorted(demand.items(),key=lambda x:-x[1])[:10],'gaps':sorted(gaps.items(),key=lambda x:-x[1])[:10],'fields':health()['fields'],'salary_count':health()['salary_count']}

@app.get('/api/data/report')
def data_report():
    report=DATA/'dataset_report.json'
    if not report.exists(): return {'message':'No prepared dataset report; using the configured source.'}
    return json.loads(report.read_text(encoding='utf-8'))

from .addon_api import router as addon_router
app.include_router(addon_router)

DIST = Path(__file__).resolve().parents[1]/'frontend'/'dist'
if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST/'assets'), name='assets')
    @app.get('/')
    def index(): return FileResponse(DIST/'index.html')
