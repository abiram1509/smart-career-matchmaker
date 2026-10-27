"""Account/session boundary; assessment and matching algorithms remain independent."""
import hashlib,hmac,secrets,sqlite3,time,re,os
from urllib.parse import urlsplit
from typing import Literal
from fastapi import APIRouter,Request,Response,HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel,Field,StrictBool,field_validator

router=APIRouter(prefix='/api/auth')
COOKIE='bridge_session'
TTL=8*60*60

def connection():
 from .main import connection as connect
 return connect()

def migrate(db):
 db.execute('CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,organization TEXT NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL,created_at INTEGER NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS login_sessions (token_hash TEXT PRIMARY KEY,account_id TEXT NOT NULL,expires_at INTEGER NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS login_attempts (bucket TEXT PRIMARY KEY,started INTEGER NOT NULL,count INTEGER NOT NULL)')
 from .institutions import migrate as migrate_institutions
 migrate_institutions(db)

def password_hash(password):
 salt=secrets.token_bytes(16);key=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1,dklen=32)
 return salt.hex()+':'+key.hex()

def password_valid(password,encoded):
 try:
  salt,expected=encoded.split(':');actual=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1,dklen=32)
  return hmac.compare_digest(actual.hex(),expected)
 except (ValueError,TypeError):return False

def public_user(row):return {k:row[k] for k in ('id','name','email','organization','role','institution_id')}

def session_user(token):
 if not token or len(token)>200:return None
 with connection() as db:
  row=db.execute('SELECT a.* FROM accounts a JOIN login_sessions s ON a.id=s.account_id WHERE s.token_hash=? AND s.expires_at>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
 return public_user(row) if row else None

def issue_session(response,user_id,secure=False):
 token=secrets.token_urlsafe(32)
 with connection() as db:
  db.execute('DELETE FROM login_sessions WHERE expires_at<=?',(int(time.time()),))
  db.execute('INSERT INTO login_sessions VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,int(time.time())+TTL))
 response.set_cookie(COOKIE,token,max_age=TTL,httponly=True,samesite='strict',secure=secure,path='/')
 return token

class Credentials(BaseModel):
 email:str=Field(min_length=3,max_length=254)
 password:str=Field(min_length=1,max_length=128)
 @field_validator('email')
 @classmethod
 def email_format(cls,v):
  v=v.strip().lower()
  if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',v):raise ValueError('Enter a valid email address.')
  return v
class Registration(Credentials):
 privacy_consent:StrictBool=False
 terms_accepted:StrictBool=False
 name:str=Field(min_length=2,max_length=100)
 organization:str=Field(default='',max_length=150)
 role:Literal['student','faculty','industry']='student'
 @field_validator('name','organization')
 @classmethod
 def trim(cls,v):return v.strip()
 @field_validator('password')
 @classmethod
 def length(cls,v):
  if len(v)<10:raise ValueError('Use at least 10 characters for your password.')
  return v

def throttle(request,email):
 now=int(time.time());ip=request.client.host if request.client else 'local'
 with connection() as db:
  for label,limit in [('ip:'+ip,50),('account:'+email,10)]:
   bucket=hashlib.sha256(label.encode()).hexdigest();row=db.execute('SELECT * FROM login_attempts WHERE bucket=?',(bucket,)).fetchone()
   if row and now-row['started']<900 and row['count']>=limit:raise HTTPException(429,'Too many attempts. Try again in 15 minutes.')
  for label,limit in [('ip:'+ip,50),('account:'+email,10)]:
   bucket=hashlib.sha256(label.encode()).hexdigest()
   db.execute('INSERT INTO login_attempts VALUES (?,?,1) ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN started<? THEN 1 ELSE count+1 END,started=CASE WHEN started<? THEN excluded.started ELSE started END',(bucket,now,now-900,now-900))

def secure(request):return request.url.scheme=='https'

@router.post('/register',status_code=201)
def register(body:Registration,request:Request,response:Response):
 throttle(request,body.email)
 if not body.privacy_consent or not body.terms_accepted:raise HTTPException(422,'Read the privacy notice and terms, then select both acknowledgements to register.')
 if len(body.name)<2:raise HTTPException(422,'Enter your name.')
 if body.role in ('faculty','industry') and not body.organization:raise HTTPException(422,'Enter your institution or company.')
 identity='account-'+secrets.token_hex(16);encoded=password_hash(body.password)
 try:
  with connection() as db:
   db.execute('INSERT INTO accounts (id,email,name,organization,role,password_hash,created_at) VALUES (?,?,?,?,?,?,?)',(identity,body.email,body.name,body.organization,body.role,encoded,int(time.time())))
   from .privacy import acknowledge
   acknowledge(db,identity)
 except sqlite3.IntegrityError:raise HTTPException(409,'This email cannot be registered. Try signing in.')
 issue_session(response,identity,secure(request))
 return {'user':{'id':identity,'email':body.email,'name':body.name,'organization':body.organization,'role':body.role}}

@router.post('/login')
def login(body:Credentials,request:Request,response:Response):
 throttle(request,body.email)
 with connection() as db:row=db.execute('SELECT * FROM accounts WHERE email=?',(body.email,)).fetchone()
 encoded=row['password_hash'] if row else '00'*16+':'+'00'*32
 if not password_valid(body.password,encoded) or not row:raise HTTPException(401,'Email or password is incorrect.')
 old=request.cookies.get(COOKIE)
 if old:
  with connection() as db:db.execute('DELETE FROM login_sessions WHERE token_hash=?',(hashlib.sha256(old.encode()).hexdigest(),))
 issue_session(response,row['id'],secure(request));return {'user':public_user(row)}

@router.get('/me')
def me(request:Request):return {'user':request.state.user}

@router.post('/logout')
def logout(request:Request,response:Response):
 token=request.cookies.get(COOKIE,'')
 with connection() as db:db.execute('DELETE FROM login_sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
 response.delete_cookie(COOKIE,path='/');return {'status':'signed out'}

class AccessBoundary(BaseHTTPMiddleware):
 async def dispatch(self,request,call_next):
  path=request.url.path
  if not path.startswith('/api/'):return await call_next(request)
  def reject(code,message):return JSONResponse({'detail':message},status_code=code,headers={'Cache-Control':'no-store'})
  if request.method not in ('GET','HEAD','OPTIONS'):
   if request.headers.get('x-bridge-request')!='1':return reject(403,'Missing request protection header.')
   origin=request.headers.get('origin')
   if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):return reject(403,'Cross-site request rejected.')
  public=path in ('/api/health','/api/auth/login','/api/auth/register')
  user=session_user(request.cookies.get(COOKIE));request.state.user=user
  if not public:
   if not user:return reject(401,'Sign in to continue.')
   if path.startswith('/api/owner/') and user['role']!='owner':return reject(403,'Platform-owner access is required.')
   if path=='/api/analytics' and user['role']!='institution':return reject(403,'Institution access is required.')
   if path.startswith('/api/student/'):
    if path.split('/')[3]!=user['id']:return reject(404,'Record not found.')
   if request.method in ('POST','PUT','PATCH'):
    try:body=await request.json()
    except (ValueError,UnicodeDecodeError):return reject(400,'Invalid JSON body.')
    if not isinstance(body,dict):return reject(422,'Expected a JSON object.')
    for key in ('student_id','profile_id'):
     if body.get(key) is not None and body[key]!=user['id']:return reject(404,'Record not found.')
   if request.query_params.get('student_id') and request.query_params['student_id']!=user['id']:return reject(404,'Record not found.')
   if (path.startswith('/api/assessment/') and path!='/api/assessment/catalog' or path in ('/api/quiz/submit','/api/applications','/api/alerts/subscribe')) and user['role']!='student':return reject(403,'A student account is required.')
  response=await call_next(request);response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff'
  return response
