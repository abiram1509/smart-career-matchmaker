"""Faculty expertise and industry collaboration requests, independent of quiz scoring."""
import json,secrets,time
from typing import Literal
from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel,Field,field_validator
from .accounts import connection
router=APIRouter(prefix='/api/connector')
RequestCategory=Literal['Faculty Development Program (FDP)','Industrial Training','Consultancy','Collaborative Research','Mentorship','Workshop / Guest Lecture','Live Project','Collaboration']

def migrate(db):
 db.execute('CREATE TABLE IF NOT EXISTS faculty_profiles (owner TEXT PRIMARY KEY,headline TEXT NOT NULL,expertise TEXT NOT NULL,bio TEXT NOT NULL,location TEXT NOT NULL,availability TEXT NOT NULL,published INTEGER NOT NULL,updated INTEGER NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS collaboration_requests (id TEXT PRIMARY KEY,owner TEXT NOT NULL,title TEXT NOT NULL,kind TEXT NOT NULL,skills TEXT NOT NULL,description TEXT NOT NULL,location TEXT NOT NULL,mode TEXT NOT NULL,duration TEXT NOT NULL,status TEXT NOT NULL,created INTEGER NOT NULL)')
 if 'request_type' not in [r[1] for r in db.execute('PRAGMA table_info(collaboration_requests)')]:
  db.execute("ALTER TABLE collaboration_requests ADD COLUMN request_type TEXT NOT NULL DEFAULT 'Collaboration'")
 db.execute('CREATE TABLE IF NOT EXISTS collaboration_interests (id TEXT PRIMARY KEY,request_id TEXT NOT NULL,faculty TEXT NOT NULL,message TEXT NOT NULL,status TEXT NOT NULL,created INTEGER NOT NULL,UNIQUE(request_id,faculty))')

def role(request,expected):
 user=request.state.user
 if user['role']!=expected:raise HTTPException(403,'This action requires a '+expected+' account.')
 return user
class Faculty(BaseModel):
 headline:str=Field(min_length=3,max_length=150)
 expertise:str=Field(min_length=2,max_length=500)
 bio:str=Field(min_length=10,max_length=1500)
 location:str=Field(default='',max_length=150)
 availability:str=Field(default='Open to collaboration',max_length=200)
 published:bool=False
 @field_validator('headline','expertise','bio')
 @classmethod
 def not_blank(cls,v):
  if not v.strip():raise ValueError('This field cannot be blank.')
  return v.strip()
class Opportunity(BaseModel):
 request_type:RequestCategory='Collaboration'
 title:str=Field(min_length=3,max_length=150)
 kind:Literal['Training','Mentorship','Workshop','Guest lecture','Live project']='Training'
 skills:str=Field(min_length=2,max_length=500)
 description:str=Field(min_length=10,max_length=2000)
 location:str=Field(default='',max_length=150)
 mode:Literal['Remote','In person','Hybrid']='Remote'
 duration:str=Field(default='',max_length=150)
 status:Literal['Open','Closed']='Open'
 @field_validator('title','skills','description')
 @classmethod
 def not_blank(cls,v):
  if not v.strip():raise ValueError('This field cannot be blank.')
  return v.strip()
class Interest(BaseModel):
 message:str=Field(min_length=10,max_length=1000)
class Decision(BaseModel):
 status:Literal['Accepted','Declined']

@router.get('/faculty')
def faculty_list(request:Request,search:str=''):
 with connection() as db:
  rows=db.execute('SELECT f.*,a.name,a.organization FROM faculty_profiles f JOIN accounts a ON a.id=f.owner WHERE f.published=1 OR f.owner=? ORDER BY f.updated DESC',(request.state.user['id'],)).fetchall()
 result=[dict(r) for r in rows]
 return [r for r in result if search.lower() in ' '.join(str(r[k]) for k in ('name','organization','expertise','headline','location')).lower()]
@router.get('/faculty/me')
def faculty_me(request:Request):
 user=role(request,'faculty')
 with connection() as db:row=db.execute('SELECT * FROM faculty_profiles WHERE owner=?',(user['id'],)).fetchone()
 return dict(row) if row else None
@router.put('/faculty/me')
def faculty_save(body:Faculty,request:Request):
 user=role(request,'faculty');v=body.model_dump()
 with connection() as db:db.execute('INSERT INTO faculty_profiles VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(owner) DO UPDATE SET headline=excluded.headline,expertise=excluded.expertise,bio=excluded.bio,location=excluded.location,availability=excluded.availability,published=excluded.published,updated=excluded.updated',(user['id'],v['headline'],v['expertise'],v['bio'],v['location'],v['availability'],v['published'],int(time.time())))
 return {'status':'saved'}
@router.get('/requests')
def requests_list(request:Request,search:str='',request_type:RequestCategory|None=None):
 with connection() as db:rows=db.execute('SELECT r.*,a.name,a.organization FROM collaboration_requests r JOIN accounts a ON a.id=r.owner WHERE r.status="Open" OR r.owner=? ORDER BY r.created DESC',(request.state.user['id'],)).fetchall()
 return [dict(r) for r in rows if (request_type is None or r['request_type']==request_type) and search.lower() in ' '.join(str(r[k]) for k in ('title','organization','skills','kind','location','request_type')).lower()]
@router.post('/requests',status_code=201)
def create_request(body:Opportunity,request:Request):
 user=role(request,'industry');identity='request-'+secrets.token_hex(12);v=body.model_dump()
 with connection() as db:db.execute('INSERT INTO collaboration_requests (id,owner,title,kind,skills,description,location,mode,duration,status,created,request_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(identity,user['id'],v['title'],v['kind'],v['skills'],v['description'],v['location'],v['mode'],v['duration'],v['status'],int(time.time()),v['request_type']))
 return {'id':identity}
@router.put('/requests/{identity}')
def update_request(identity:str,body:Opportunity,request:Request):
 user=role(request,'industry');v=body.model_dump()
 with connection() as db:
  changed=db.execute('UPDATE collaboration_requests SET title=?,kind=?,skills=?,description=?,location=?,mode=?,duration=?,status=?,request_type=COALESCE(?,request_type) WHERE id=? AND owner=?',(v['title'],v['kind'],v['skills'],v['description'],v['location'],v['mode'],v['duration'],v['status'],v['request_type'] if 'request_type' in body.model_fields_set else None,identity,user['id'])).rowcount
  if not changed:raise HTTPException(404,'Request not found.')
 return {'status':'saved'}
@router.post('/requests/{identity}/interest',status_code=201)
def express_interest(identity:str,body:Interest,request:Request):
 user=role(request,'faculty')
 with connection() as db:
  if not db.execute('SELECT 1 FROM faculty_profiles WHERE owner=? AND published=1',(user['id'],)).fetchone():raise HTTPException(400,'Publish your expertise profile first.')
  db.execute('BEGIN IMMEDIATE')
  interest_id='interest-'+secrets.token_hex(12)
  # Check and insert in one statement, so a closed request cannot receive a new interest.
  changed=db.execute('INSERT OR IGNORE INTO collaboration_interests SELECT ?,id,?,?,"Pending",? FROM collaboration_requests WHERE id=? AND status="Open"',(interest_id,user['id'],body.message,int(time.time()),identity)).rowcount
  if not changed:raise HTTPException(409,'Request is closed, unavailable, or you already expressed interest.')
 return {'status':'Pending'}
@router.get('/interests')
def interests(request:Request):
 user=request.state.user
 if user['role'] not in ('faculty','industry'):return []
 with connection() as db:rows=db.execute('SELECT i.*,r.title,r.owner,r.request_type,r.status AS request_status,a.name,a.organization FROM collaboration_interests i JOIN collaboration_requests r ON r.id=i.request_id JOIN accounts a ON a.id=i.faculty WHERE i.faculty=? OR r.owner=? ORDER BY i.created DESC',(user['id'],user['id'])).fetchall()
 return [dict(r) for r in rows]
@router.patch('/interests/{identity}')
def decide(identity:str,body:Decision,request:Request):
 user=role(request,'industry')
 with connection() as db:
  changed=db.execute('UPDATE collaboration_interests SET status=? WHERE id=? AND status="Pending" AND request_id IN (SELECT id FROM collaboration_requests WHERE owner=?)',(body.status,identity,user['id'])).rowcount
  if not changed:raise HTTPException(409,'Interest is unavailable or has already been reviewed.')
 return {'status':body.status}
