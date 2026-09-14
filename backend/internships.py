"""Informational internships and faculty feedback, isolated from assessment/matching."""
import secrets
from datetime import datetime,timezone
from typing import Literal
from fastapi import APIRouter,HTTPException,Request
from pydantic import BaseModel,Field,ConfigDict,field_validator
from .accounts import connection

router=APIRouter(prefix='/api/internships')

def migrate(db):
    db.execute('''CREATE TABLE IF NOT EXISTS internships (
        id TEXT PRIMARY KEY, student_id TEXT NOT NULL, title TEXT NOT NULL,
        mentor_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ongoing'
        CHECK(status IN ('ongoing','completed')), created_at TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS internship_feedback (
        id TEXT PRIMARY KEY, internship_id TEXT NOT NULL, author TEXT NOT NULL,
        feedback_text TEXT NOT NULL, created_at TEXT NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS internships_student ON internships(student_id)')
    db.execute('CREATE INDEX IF NOT EXISTS internships_mentor ON internships(mentor_id)')
    db.execute('CREATE INDEX IF NOT EXISTS internship_feedback_parent ON internship_feedback(internship_id,created_at)')

class Create(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title:str=Field(min_length=1,max_length=200)
    mentor_id:str=Field(min_length=1,max_length=80)
    @field_validator('title')
    @classmethod
    def title_not_blank(cls,value):
        value=value.strip()
        if not value:raise ValueError('Enter an internship title.')
        return value

class Feedback(BaseModel):
    model_config=ConfigDict(extra='forbid')
    feedback_text:str=Field(min_length=1,max_length=3000)
    @field_validator('feedback_text')
    @classmethod
    def text_not_blank(cls,value):
        value=value.strip()
        if not value:raise ValueError('Enter feedback.')
        return value

class Status(BaseModel):
    model_config=ConfigDict(extra='forbid')
    status:Literal['ongoing','completed']

def require_role(request,role):
    user=request.state.user
    if user['role']!=role:raise HTTPException(403,'This action requires a '+role+' account.')
    return user

def now():return datetime.now(timezone.utc).isoformat()

@router.get('/mentors')
def mentors(request:Request):
    require_role(request,'student')
    with connection() as db:
        rows=db.execute("SELECT id,name,organization FROM accounts WHERE role='faculty' ORDER BY name,id").fetchall()
    return [dict(row) for row in rows]

@router.get('')
def internships(request:Request):
    user=request.state.user
    if user['role'] not in ('student','faculty'):raise HTTPException(403,'Internships require a student or faculty account.')
    column='student_id' if user['role']=='student' else 'mentor_id'
    with connection() as db:
        rows=db.execute(f'''SELECT i.*,s.name AS student_name,m.name AS mentor_name
            FROM internships i JOIN accounts s ON s.id=i.student_id JOIN accounts m ON m.id=i.mentor_id
            WHERE i.{column}=? ORDER BY i.created_at DESC,i.id''',(user['id'],)).fetchall()
        result=[]
        for row in rows:
            entries=db.execute('''SELECT f.*,a.name AS author_name FROM internship_feedback f
                JOIN accounts a ON a.id=f.author WHERE f.internship_id=? ORDER BY f.created_at DESC,f.id DESC''',(row['id'],)).fetchall()
            result.append({**dict(row),'feedback':[dict(entry) for entry in entries]})
    return result

@router.post('',status_code=201)
def create(body:Create,request:Request):
    user=require_role(request,'student')
    record={'id':secrets.token_hex(16),'student_id':user['id'],'title':body.title,
            'mentor_id':body.mentor_id,'status':'ongoing','created_at':now()}
    with connection() as db:
        if not db.execute("SELECT id FROM accounts WHERE id=? AND role='faculty'",(body.mentor_id,)).fetchone():
            raise HTTPException(422,'Choose an existing faculty mentor.')
        db.execute('INSERT INTO internships VALUES (?,?,?,?,?,?)',tuple(record.values()))
    return record

def assigned(db,identity,mentor):
    if not db.execute('SELECT id FROM internships WHERE id=? AND mentor_id=?',(identity,mentor)).fetchone():
        raise HTTPException(404,'Assigned internship not found.')

@router.post('/{identity}/feedback',status_code=201)
def feedback(identity:str,body:Feedback,request:Request):
    user=require_role(request,'faculty')
    entry={'id':secrets.token_hex(16),'internship_id':identity,'author':user['id'],
           'feedback_text':body.feedback_text,'created_at':now()}
    with connection() as db:
        assigned(db,identity,user['id'])
        db.execute('INSERT INTO internship_feedback VALUES (?,?,?,?,?)',tuple(entry.values()))
    return entry

@router.patch('/{identity}/status')
def status(identity:str,body:Status,request:Request):
    user=require_role(request,'faculty')
    with connection() as db:
        assigned(db,identity,user['id'])
        db.execute('UPDATE internships SET status=? WHERE id=? AND mentor_id=?',(body.status,identity,user['id']))
    return {'id':identity,'status':body.status}
