"""Authenticated fixtures only; never imported by production code."""
import time
from fastapi import Response
from backend import accounts

def sign_in(client,identity='test',role='student'):
 with accounts.connection() as db:
  db.execute('INSERT OR IGNORE INTO accounts (id,email,name,organization,role,password_hash,created_at) VALUES (?,?,?,?,?,?,?)',(identity,identity+'@example.test','Test member','Test organization',role,accounts.password_hash('test-password-123'),int(time.time())))
 token=accounts.issue_session(Response(),identity)
 client.cookies.set(accounts.COOKIE,token)
 client.headers['X-Bridge-Request']='1'
 return identity
