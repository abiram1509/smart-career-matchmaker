"""Private informational document portfolios. No assessment or matching imports."""
import base64
import binascii
import hashlib
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from .accounts import connection

router=APIRouter(prefix='/api/portfolio')
STORAGE=Path(__file__).resolve().parent/'data'/'portfolio-documents'
MAX_FILE=5*1024*1024
MAX_BODY=7*1024*1024
ALLOWED={'.pdf','.png','.jpg','.jpeg','.txt','.zip','.docx'}

class PortfolioUploadLimit:
    """Bound JSON upload bytes before existing session middleware parses them."""
    def __init__(self,app): self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope.get('path','').rstrip('/')!='/api/portfolio/upload':
            return await self.app(scope,receive,send)
        chunks=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            chunk=message.get('body',b'');size+=len(chunk)
            if size>MAX_BODY:
                return await JSONResponse({'detail':'Upload exceeds the 5 MB file limit.'},status_code=413,headers={'Cache-Control':'no-store'})(scope,receive,send)
            chunks.append(chunk)
            if not message.get('more_body'):break
        delivered=False
        async def buffered():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':b''.join(chunks),'more_body':False}
            return await receive()
        await self.app(scope,buffered,send)

def migrate(db):
    db.execute('''CREATE TABLE IF NOT EXISTS portfolio_documents (
        id TEXT PRIMARY KEY, student_id TEXT NOT NULL, file_reference TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'self-reported' CHECK(status IN ('self-reported','verified')),
        uploaded_at TEXT NOT NULL, original_name TEXT NOT NULL, size_bytes INTEGER NOT NULL,
        sha256 TEXT NOT NULL, verified_by TEXT, verified_at TEXT)''')
    db.execute('CREATE INDEX IF NOT EXISTS portfolio_student ON portfolio_documents(student_id,uploaded_at)')

class Upload(BaseModel):
    title:str=Field(min_length=1,max_length=150)
    filename:str=Field(min_length=1,max_length=180)
    content_base64:str=Field(min_length=1,max_length=4*((MAX_FILE+2)//3))
    @field_validator('title','filename')
    @classmethod
    def clean(cls,value):
        value=value.strip()
        if not value or any(ord(c)<32 for c in value):raise ValueError('Use a non-empty title and filename without control characters.')
        return value

class Review(BaseModel):
    status:Literal['self-reported','verified']

def public(row):
    return {**{key:row[key] for key in ['id','title','status','uploaded_at','original_name','size_bytes','verified_at']},
            'download_url':'/api/portfolio/'+row['id']+'/download'}

def student_or_owner(request):
    user=request.state.user
    if user['role'] not in ('student','owner','faculty'):raise HTTPException(403,'Document access requires the student owner or platform administrator.')
    if user['role']=='faculty':
        from .institutions import institution_for
        with connection() as db: institution_for(db,user['id'],'faculty')
    return user

@router.get('')
def documents(request:Request,offset:int=0):
    user=student_or_owner(request)
    if offset<0:raise HTTPException(422,'Invalid offset.')
    with connection() as db:
        if user['role']=='owner':
            rows=db.execute('''SELECT d.*,a.name AS student_name FROM portfolio_documents d
                JOIN accounts a ON a.id=d.student_id ORDER BY d.uploaded_at DESC,d.id LIMIT 100 OFFSET ?''',(offset,)).fetchall()
            return [{**public(r),'student_name':r['student_name']} for r in rows]
        if user['role']=='faculty':
            from .institutions import institution_for
            institution_id=institution_for(db,user['id'],'faculty')
            rows=db.execute('''SELECT d.*,a.name AS student_name FROM portfolio_documents d
                JOIN accounts a ON a.id=d.student_id WHERE a.role='student' AND a.institution_id=?
                ORDER BY d.uploaded_at DESC,d.id LIMIT 100 OFFSET ?''',(institution_id,offset)).fetchall()
            return [{**public(r),'student_name':r['student_name']} for r in rows]
        rows=db.execute('SELECT * FROM portfolio_documents WHERE student_id=? ORDER BY uploaded_at DESC,id LIMIT 100 OFFSET ?',(user['id'],offset)).fetchall()
    return [public(r) for r in rows]

@router.post('/upload',status_code=201)
def upload(body:Upload,request:Request):
    user=request.state.user
    if user['role']!='student':raise HTTPException(403,'Only students can upload portfolio documents.')
    if any(c in body.filename for c in ('/','\\',':')):raise HTTPException(422,'Use a plain filename.')
    suffix=Path(body.filename).suffix.lower()
    if suffix not in ALLOWED:raise HTTPException(422,'Supported files: PDF, PNG, JPG, TXT, ZIP and DOCX.')
    try:data=base64.b64decode(body.content_base64,validate=True)
    except (ValueError,binascii.Error):raise HTTPException(422,'Invalid file encoding.')
    if not data or len(data)>MAX_FILE:raise HTTPException(413,'Choose a non-empty file up to 5 MB.')
    signatures={'.pdf':b'%PDF-','.png':b'\x89PNG\r\n\x1a\n','.jpg':b'\xff\xd8\xff','.jpeg':b'\xff\xd8\xff','.zip':b'PK','.docx':b'PK'}
    if suffix in signatures and not data.startswith(signatures[suffix]):raise HTTPException(422,'The file does not match its extension.')
    if suffix=='.txt':
        try:data.decode('utf-8')
        except UnicodeDecodeError:raise HTTPException(422,'Text files must use UTF-8.')
        if b'\x00' in data:raise HTTPException(422,'Invalid text file.')
    identity=secrets.token_hex(16);reference=identity+suffix
    STORAGE.mkdir(parents=True,exist_ok=True)
    path=STORAGE/reference
    now=datetime.now(timezone.utc).isoformat()
    try:
        with connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM portfolio_documents WHERE student_id=?',(user['id'],)).fetchone()[0]>=30:
                raise HTTPException(409,'Portfolio limit reached: 30 documents per student.')
            with path.open('xb') as stream:stream.write(data)
            db.execute('INSERT INTO portfolio_documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                (identity,user['id'],reference,body.title,'self-reported',now,body.filename,len(data),hashlib.sha256(data).hexdigest(),None,None))
            row=db.execute('SELECT * FROM portfolio_documents WHERE id=?',(identity,)).fetchone()
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return public(row)

def accessible(db,identity,user):
    row=db.execute('SELECT * FROM portfolio_documents WHERE id=?',(identity,)).fetchone()
    if not row:raise HTTPException(404,'Document not found.')
    if user['role']=='faculty':
        from .institutions import institution_for
        institution_id=institution_for(db,user['id'],'faculty')
        student=db.execute("SELECT 1 FROM accounts WHERE id=? AND role='student' AND institution_id=?",(row['student_id'],institution_id)).fetchone()
        if not student:raise HTTPException(404,'Document not found.')
    elif user['role']!='owner' and row['student_id']!=user['id']:
        raise HTTPException(404,'Document not found.')
    return row

@router.get('/{identity}/download')
def download(identity:str,request:Request):
    user=student_or_owner(request)
    with connection() as db:row=accessible(db,identity,user)
    path=(STORAGE/row['file_reference']).resolve()
    if path.parent!=STORAGE.resolve() or not path.is_file():raise HTTPException(404,'Document file is unavailable.')
    return FileResponse(path,filename=row['original_name'],media_type='application/octet-stream',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@router.patch('/{identity}/status')
def review(identity:str,body:Review,request:Request):
    user=request.state.user
    if user['role'] not in ('owner','faculty'):raise HTTPException(403,'Only authorized reviewers can verify documents.')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        accessible(db,identity,user)
        verified=body.status=='verified'
        db.execute('UPDATE portfolio_documents SET status=?,verified_by=?,verified_at=? WHERE id=?',
            (body.status,user['id'] if verified else None,datetime.now(timezone.utc).isoformat() if verified else None,identity))
        return public(db.execute('SELECT * FROM portfolio_documents WHERE id=?',(identity,)).fetchone())
