"""Owner-assigned institution membership. No assessment or matching dependencies."""
import secrets
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .accounts import connection

router = APIRouter(prefix='/api/owner/institutions')

def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS institutions (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at INTEGER NOT NULL)')
    columns = {r['name'] for r in db.execute('PRAGMA table_info(accounts)')}
    for name, declaration in {
        'institution_id': 'TEXT REFERENCES institutions(id) ON DELETE RESTRICT',
        'institution_assigned_by': 'TEXT REFERENCES accounts(id) ON DELETE RESTRICT',
        'institution_assigned_at': 'INTEGER',
    }.items():
        if name not in columns:
            db.execute(f'ALTER TABLE accounts ADD COLUMN {name} {declaration}')
    db.execute('CREATE INDEX IF NOT EXISTS accounts_institution ON accounts(institution_id,role)')
    db.execute('''CREATE TABLE IF NOT EXISTS institution_membership_events (
        id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
        previous_institution_id TEXT REFERENCES institutions(id),
        institution_id TEXT REFERENCES institutions(id),
        assigned_by TEXT NOT NULL REFERENCES accounts(id), created_at INTEGER NOT NULL)''')

def owner(request):
    user = request.state.user
    if not user or user['role'] != 'owner':
        raise HTTPException(403, 'Platform-owner access is required.')
    return user

def institution_for(db, account_id, role=None):
    row = db.execute('''SELECT a.institution_id,a.role FROM accounts a
        JOIN institutions i ON i.id=a.institution_id WHERE a.id=?''', (account_id,)).fetchone()
    if not row or (role and row['role'] != role):
        raise HTTPException(403, 'Verified institution membership is required. Contact the platform owner.')
    return row['institution_id']

def create(db, name):
    name = name.strip()
    if not name or len(name) > 150:
        raise HTTPException(422, 'Enter an institution name of 1–150 characters.')
    if db.execute('SELECT 1 FROM institutions WHERE lower(name)=lower(?)', (name,)).fetchone():
        raise HTTPException(409, 'That institution already exists. Select it instead.')
    identity = 'institution-' + secrets.token_hex(16)
    db.execute('INSERT INTO institutions VALUES (?,?,?)', (identity,name,int(time.time())))
    return identity

def assign(db, account_id, institution_id, actor_id):
    actor = db.execute('SELECT role FROM accounts WHERE id=?',(actor_id,)).fetchone()
    if not actor or actor['role'] != 'owner':
        raise HTTPException(403, 'Only the platform owner may assign membership.')
    account = db.execute('SELECT role,institution_id FROM accounts WHERE id=?',(account_id,)).fetchone()
    if not account:
        raise HTTPException(404, 'Account not found.')
    if account['role'] not in ('student','faculty','institution'):
        raise HTTPException(422, 'Membership is for student, faculty and institution accounts.')
    if institution_id is not None and not db.execute('SELECT 1 FROM institutions WHERE id=?',(institution_id,)).fetchone():
        raise HTTPException(404, 'Institution not found.')
    if account['institution_id'] == institution_id:
        return
    now = int(time.time())
    db.execute('UPDATE accounts SET institution_id=?,institution_assigned_by=?,institution_assigned_at=? WHERE id=?',
               (institution_id,actor_id,now,account_id))
    db.execute('INSERT INTO institution_membership_events VALUES (?,?,?,?,?,?)',
               (secrets.token_hex(16),account_id,account['institution_id'],institution_id,actor_id,now))

class InstitutionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1,max_length=150)

class MembershipInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    institution_id: str | None = Field(default=None,max_length=80)

@router.get('')
def listing(request: Request):
    owner(request)
    with connection() as db:
        return {'institutions':[dict(r) for r in db.execute('SELECT * FROM institutions ORDER BY name,id')],
                'accounts':[dict(r) for r in db.execute('''SELECT id,name,email,role,organization,institution_id,
                   institution_assigned_at FROM accounts WHERE role IN ('student','faculty','institution') ORDER BY role,name,id''')]}

@router.post('',status_code=201)
def new_institution(body: InstitutionInput, request: Request):
    owner(request)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        identity = create(db,body.name)
        return dict(db.execute('SELECT * FROM institutions WHERE id=?',(identity,)).fetchone())

@router.put('/members/{account_id}')
def set_membership(account_id: str, body: MembershipInput, request: Request):
    actor = owner(request)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        assign(db,account_id,body.institution_id,actor['id'])
    return {'status':'updated','account_id':account_id,'institution_id':body.institution_id}
