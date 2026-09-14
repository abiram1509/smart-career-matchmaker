"""Addendum persistence, adaptive quiz routes and local in-app match alerts."""
import json,sqlite3,uuid,threading
from pathlib import Path
from fastapi import APIRouter,HTTPException,BackgroundTasks
from pydantic import BaseModel,Field
from . import adaptive_quiz as quiz
from .assessment_config import FIELDS,ASSESSMENT_TRACKS
from .domain import SKILLS
from .learning_resources import resources
from .bank_status import summarize,notice
router=APIRouter(prefix='/api')
refresh_lock=threading.Lock()
refresh_status={'state':'idle'}

def main():
 from . import main as module
 return module

def migrate(db):
 columns={r['name'] for r in db.execute('PRAGMA table_info(profiles)')}
 for name,spec in {'name':"TEXT DEFAULT ''",'email':"TEXT DEFAULT ''",'field':"TEXT DEFAULT ''",'evidence':"TEXT DEFAULT '{}'",'project_notes':"TEXT DEFAULT '{}'",'interested_in_alerts':'INTEGER DEFAULT 0','created_at':"TEXT DEFAULT ''"}.items():
  if name not in columns:db.execute(f'ALTER TABLE profiles ADD COLUMN {name} {spec}')
 db.execute('CREATE TABLE IF NOT EXISTS assessment_sessions (id TEXT PRIMARY KEY, student TEXT NOT NULL, state TEXT NOT NULL, version INTEGER DEFAULT 0, created_at TEXT NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS questions (id TEXT PRIMARY KEY, track TEXT, skill TEXT, tier INTEGER, type TEXT, prompt_text TEXT, options TEXT, correct_option INTEGER, requires_tier2_flag TEXT, payload TEXT)')
 db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY,title TEXT,company TEXT,description TEXT,source_url TEXT,field TEXT,skill_vector TEXT,source TEXT,created_at TEXT)')
 db.execute('CREATE TABLE IF NOT EXISTS resources (id TEXT PRIMARY KEY, skill_name TEXT, resource_type TEXT, title TEXT, url TEXT)')
 db.execute('CREATE TABLE IF NOT EXISTS job_alert_subscriptions (id TEXT PRIMARY KEY, student_id TEXT UNIQUE, min_match_threshold REAL, skill_vector TEXT, seen_scores TEXT, field TEXT, created_at TEXT, last_notified_at TEXT)')
 db.execute('CREATE TABLE IF NOT EXISTS match_alerts (id TEXT PRIMARY KEY, student_id TEXT, job_id TEXT, title TEXT, company TEXT, score REAL, url TEXT, reason TEXT, created_at TEXT, read INTEGER DEFAULT 0)')
 db.execute('DELETE FROM questions')
 db.executemany('INSERT INTO questions VALUES (?,?,?,?,?,?,?,?,?,?)',[(q['id'],q['track'],q['skill'],q['tier'],q['type'],q['prompt_text'],json.dumps(q.get('options')),q.get('correct_option'),q.get('requires_tier2_flag'),json.dumps(q)) for q in quiz.bank()])
 db.execute('DELETE FROM resources')
 for skill,items in resources().items():
  for i,r in enumerate(items):db.execute('INSERT INTO resources VALUES (?,?,?,?,?)',(skill+'-'+str(i),skill,r['type'],r['title'],r['url']))

class Start(BaseModel):
 student_id:str=Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
 field:str
 track:str
class Advance(BaseModel):
 student_id:str
 version:int
 answers:list[dict]=Field(max_length=30)

@router.get('/assessment/catalog')
def catalog():
 with main().connection() as db:
  rows=[json.loads(row['payload']) for row in db.execute('SELECT payload FROM questions')]
 tracks={track:{**config,'bank_summary':summarize(q for q in rows if q['track']==track)} for track,config in ASSESSMENT_TRACKS.items()}
 return {'fields':FIELDS,'tracks':tracks,'taxonomy':SKILLS,'bank_notice':'Bank counts reflect the stored questions for each track. Up to 15 eligible Tier-3 checks per assessment.'}

def assessment_view(state):
 # Override presentation only. In-progress sessions retain their original bank snapshot.
 result=quiz.view(state)
 summary=summarize(q for q in state['bank'] if q['track']==state['track'])
 result.update(bank_summary=summary,notice=notice(summary))
 return result
@router.post('/assessment/start')
def start(body:Start):
 try:state=quiz.initial(body.field,body.track)
 except ValueError as error:raise HTTPException(422,str(error))
 identity=uuid.uuid4().hex
 with main().connection() as db:db.execute('INSERT INTO assessment_sessions VALUES (?,?,?,?,?)',(identity,body.student_id,json.dumps(state),0,main().now()))
 return {**assessment_view(state),'session_id':identity,'version':0}
@router.post('/assessment/{identity}/advance')
def advance(identity:str,body:Advance):
 with main().connection() as db:
  row=db.execute('SELECT * FROM assessment_sessions WHERE id=? AND student=?',(identity,body.student_id)).fetchone()
  if not row:raise HTTPException(404,'Assessment session not found.')
  if row['version']!=body.version:raise HTTPException(409,'This step was already submitted. Restart the assessment if needed.')
  state=json.loads(row['state'])
  try:state=quiz.advance(state,body.answers)
  except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,str(error))
  updated=db.execute('UPDATE assessment_sessions SET state=?,version=version+1 WHERE id=? AND version=?',(json.dumps(state),identity,body.version))
  if updated.rowcount!=1:raise HTTPException(409,'This assessment changed in another request.')
  result={**assessment_view(state),'session_id':identity,'version':body.version+1}
  if state['phase']=='complete':
   vector,evidence=quiz.score(state);notes={k:v for k,v in state['answers'].items() if k.startswith(('context-','backend-user-context-'))}
   db.execute('INSERT INTO profiles(id,vector,updated,track,field,evidence,project_notes,created_at) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET vector=excluded.vector, updated=excluded.updated, track=excluded.track,field=excluded.field,evidence=excluded.evidence,project_notes=excluded.project_notes',(body.student_id,json.dumps(vector),main().now(),state['track'],state['field'],json.dumps(evidence),json.dumps(notes),main().now()))
   result.update(skill_vector=vector,evidence=evidence,project_notes=notes,job_field=ASSESSMENT_TRACKS[state['track']]['job_field'])
 return result

class Subscription(BaseModel):
 student_id:str=Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
 min_match_threshold:float=Field(default=75,ge=0,le=100)
 job_id:str

def scores(loader,vector,field):
 import numpy as np
 from sklearn.metrics.pairwise import cosine_similarity
 result=cosine_similarity(np.array([[vector.get(s,0) for s in SKILLS]],dtype=np.float32),loader.matrix)[0]
 return {j['id']:round(float(result[i])*100,1) for i,j in enumerate(loader.jobs) if field=='all' or j.get('field')==field or field in (j.get('category_fields') or []) or field in (j.get('search_fields') or [])}
@router.post('/alerts/subscribe')
def subscribe(body:Subscription):
 module=main();job=next((j for j in module.loader.jobs if j['id']==body.job_id),None)
 if not job:raise HTTPException(404,'Job not found.')
 with module.connection() as db:
  profile=db.execute('SELECT vector FROM profiles WHERE id=?',(body.student_id,)).fetchone()
  if not profile:raise HTTPException(400,'Complete an assessment first.')
  vector=json.loads(profile['vector']);field=job.get('field','all');baseline=scores(module.loader,vector,field)
  db.execute('INSERT INTO job_alert_subscriptions VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(student_id) DO UPDATE SET min_match_threshold=excluded.min_match_threshold,skill_vector=excluded.skill_vector,seen_scores=excluded.seen_scores,field=excluded.field',(uuid.uuid4().hex,body.student_id,body.min_match_threshold,json.dumps(vector),json.dumps(baseline),field,module.now(),None))
  db.execute('UPDATE profiles SET interested_in_alerts=1 WHERE id=?',(body.student_id,))
 return {'status':'subscribed','field':field,'threshold':body.min_match_threshold}
@router.get('/student/{student}/alerts')
def alerts(student:str):
 with main().connection() as db:
  sub=db.execute('SELECT min_match_threshold,field,created_at,last_notified_at FROM job_alert_subscriptions WHERE student_id=?',(student,)).fetchone()
  rows=db.execute('SELECT * FROM match_alerts WHERE student_id=? ORDER BY created_at DESC',(student,)).fetchall()
 return {'subscription':dict(sub) if sub else None,'alerts':[dict(r) for r in rows],'refresh':refresh_status}
@router.delete('/student/{student}/alerts/subscription')
def unsubscribe(student:str):
 with main().connection() as db:
  db.execute('DELETE FROM job_alert_subscriptions WHERE student_id=?',(student,));db.execute('UPDATE profiles SET interested_in_alerts=0 WHERE id=?',(student,))
 return {'status':'unsubscribed'}

def check_alerts(loader):
 module=main();lookup={j['id']:j for j in loader.jobs};count=0
 with module.connection() as db:
  subs=db.execute('SELECT s.*,p.vector FROM job_alert_subscriptions s JOIN profiles p ON p.id=s.student_id').fetchall()
  for sub in subs:
   vector=json.loads(sub['vector']);previous=json.loads(sub['seen_scores']);current=scores(loader,vector,sub['field']);notified=False
   for identity,value in current.items():
    if value>=sub['min_match_threshold'] and (identity not in previous or previous[identity]<sub['min_match_threshold']):
     j=lookup[identity];reason='New job match' if identity not in previous else 'Your score crossed the threshold'
     db.execute('INSERT INTO match_alerts(id,student_id,job_id,title,company,score,url,reason,created_at) VALUES (?,?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,sub['student_id'],identity,j['title'],j['company'],value,j.get('url',''),reason,module.now()));count+=1;notified=True
   # Retain IDs of temporarily unavailable listings to avoid repeat "new" alerts.
   previous.update(current)
   db.execute('UPDATE job_alert_subscriptions SET seen_scores=?,skill_vector=?,last_notified_at=? WHERE id=?',(json.dumps(previous),json.dumps(vector),module.now() if notified else sub['last_notified_at'],sub['id']))
 return count

def sync_jobs(loader):
 with main().connection() as db:
  db.execute('DELETE FROM jobs')
  db.executemany('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',[(j['id'],j['title'],j['company'],j.get('description',''),j.get('url',''),j.get('field','other'),json.dumps(j['skills']),j.get('source_kind','fallback'),j.get('fetched_at') or main().now()) for j in loader.jobs])

def refresh_and_check():
 try:
  module=main();replacement=module.HybridJobLoader();sync_jobs(replacement);module.loader=replacement
  refresh_status.update(state='complete',alerts_created=check_alerts(replacement),finished_at=module.now())
 except Exception:
  refresh_status.update(state='failed',message='Refresh failed. Existing jobs remain available; retry later.')
 finally:refresh_lock.release()
@router.post('/alerts/check')
def check(background:BackgroundTasks):
 if not refresh_lock.acquire(blocking=False):raise HTTPException(409,'A refresh is already running.')
 refresh_status.clear();refresh_status.update(state='running')
 background.add_task(refresh_and_check)
 return {'status':'running','message':'Refreshing real sources and checking opted-in profiles. No messages are sent outside this app.'}
@router.get('/resources')
def get_resources():return resources()

@router.get('/match/job')
def match_one(job_id:str,student_id:str):
 from .domain import rank_jobs
 job=next((j for j in main().loader.jobs if j['id']==job_id),None)
 if not job:raise HTTPException(404,'This listing is no longer in the loaded sources. Use the original source link if available.')
 with main().connection() as db:profile=db.execute('SELECT vector,evidence FROM profiles WHERE id=?',(student_id,)).fetchone()
 if not profile:raise HTTPException(404,'Profile not found.')
 return rank_jobs(json.loads(profile['vector']),[job],evidence=json.loads(profile['evidence']) or None)[0]
