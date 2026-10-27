"""Private internship evidence. No portfolio, assessment or matching dependencies."""
import base64
import binascii
import re
import secrets
from datetime import datetime, timezone
from pathlib import PurePath
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .accounts import connection

router=APIRouter(prefix='/api/internships')
MAX_FILE=5*1024*1024
MAX_BODY=7*1024*1024
MAX_DOCUMENTS=20

class InternshipUploadLimit:
    """Bound uploads before session middleware decodes the JSON body."""
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope.get('method')!='POST' or not re.fullmatch(r'/api/internships/[^/]+/documents/?',scope.get('path','')):
            return await self.app(scope,receive,send)
        chunks=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            chunk=message.get('body',b'');size+=len(chunk)
            if size>MAX_BODY:
                return await JSONResponse({'detail':'Upload exceeds the 5 MB file limit.'},status_code=413)(scope,receive,send)
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
    db.execute('''CREATE TABLE IF NOT EXISTS internship_documents (
        id TEXT PRIMARY KEY, internship_id TEXT NOT NULL REFERENCES internships(id),
        title TEXT NOT NULL, original_name TEXT NOT NULL, size_bytes INTEGER NOT NULL,
        uploaded_at TEXT NOT NULL, content BLOB NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS internship_documents_parent ON internship_documents(internship_id,uploaded_at)')

def public(row):
    return {**dict(row),'download_url':f"/api/internships/{row['internship_id']}/documents/{row['id']}/download"}

def list_documents(db,identity):
    rows=db.execute('''SELECT id,internship_id,title,original_name,size_bytes,uploaded_at
        FROM internship_documents WHERE internship_id=? ORDER BY uploaded_at DESC,id DESC''',(identity,)).fetchall()
    return [public(row) for row in rows]

def accessible(db,identity,user):
    if user['role'] not in ('student','faculty'):raise HTTPException(403,'Only the student and assigned faculty mentor can access internship files.')
    column='student_id' if user['role']=='student' else 'mentor_id'
    row=db.execute(f'SELECT * FROM internships WHERE id=? AND {column}=?',(identity,user['id'])).fetchone()
    if not row:raise HTTPException(404,'Internship not found.')
    return row

class Upload(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title:str=Field(min_length=1,max_length=150)
    filename:str=Field(min_length=1,max_length=180)
    content_base64:str=Field(min_length=1,max_length=4*((MAX_FILE+2)//3))
    @field_validator('title','filename')
    @classmethod
    def clean(cls,value):
        value=value.strip()
        if not value or any(ord(c)<32 for c in value):raise ValueError('Enter a title and filename without control characters.')
        return value

def decode_file(body):
    if any(c in body.filename for c in ('/','\\',':')):raise HTTPException(422,'Use a plain filename.')
    suffix=PurePath(body.filename).suffix.lower()
    signatures={'.pdf':b'%PDF-','.png':b'\x89PNG\r\n\x1a\n','.jpg':b'\xff\xd8\xff','.jpeg':b'\xff\xd8\xff','.docx':b'PK'}
    if suffix not in {*signatures,'.txt'}:raise HTTPException(422,'Use a PDF, DOCX, TXT, PNG or JPG file.')
    try:data=base64.b64decode(body.content_base64,validate=True)
    except (ValueError,binascii.Error):raise HTTPException(422,'Invalid file encoding.')
    if not data or len(data)>MAX_FILE:raise HTTPException(413,'Choose a non-empty file up to 5 MB.')
    if suffix in signatures and not data.startswith(signatures[suffix]):raise HTTPException(422,'The file does not match its extension.')
    if suffix=='.txt':
        try:data.decode('utf-8')
        except UnicodeDecodeError:raise HTTPException(422,'Text files must use UTF-8.')
        if b'\x00' in data:raise HTTPException(422,'Invalid text file.')
    return data

@router.post('/{identity}/documents',status_code=201)
def upload(identity:str,body:Upload,request:Request):
    user=request.state.user
    if user['role']!='student':raise HTTPException(403,'Only the student can submit internship evidence.')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        internship=accessible(db,identity,user)
        if internship['rejected_at'] or internship['status']!='ongoing':raise HTTPException(409,'The mentor must reopen this internship before you can upload more evidence.')
        if db.execute('SELECT count(*) FROM internship_documents WHERE internship_id=?',(identity,)).fetchone()[0]>=MAX_DOCUMENTS:
            raise HTTPException(409,'Limit reached: 20 documents per internship.')
        data=decode_file(body)
        document_id=secrets.token_hex(16)
        db.execute('INSERT INTO internship_documents VALUES (?,?,?,?,?,?,?)',
            (document_id,identity,body.title,body.filename,len(data),datetime.now(timezone.utc).isoformat(),data))
        return next(row for row in list_documents(db,identity) if row['id']==document_id)

@router.get('/{identity}/documents/{document_id}/download')
def download(identity:str,document_id:str,request:Request):
    with connection() as db:
        accessible(db,identity,request.state.user)
        row=db.execute('SELECT * FROM internship_documents WHERE id=? AND internship_id=?',(document_id,identity)).fetchone()
        if not row:raise HTTPException(404,'Document not found.')
    return Response(bytes(row['content']),media_type='application/octet-stream',headers={
        'Content-Disposition':"attachment; filename*=UTF-8''"+quote(row['original_name'],safe=''),
        'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
