"""Create an institution account locally; never grants this role through public signup."""
import argparse,getpass,secrets,time,sqlite3
from .accounts import migrate,password_hash,Registration
from . import main
from .institutions import create, assign

def run():
 parser=argparse.ArgumentParser(description='Create a local institution account')
 parser.add_argument('--email',required=True);parser.add_argument('--name',required=True);parser.add_argument('--organization',required=True)
 parser.add_argument('--owner-email',required=True,help='Existing owner authorizing this local provisioning')
 parser.add_argument('--institution-id',help='Existing institution ID; omit to create a new institution named by --organization')
 args=parser.parse_args();password=getpass.getpass('Password (at least 10 characters): ')
 if password!=getpass.getpass('Repeat password: '):raise SystemExit('Passwords do not match.')
 details=Registration(email=args.email,name=args.name,organization=args.organization,password=password)
 if not details.organization:raise SystemExit('Organization is required.')
 main.DB.parent.mkdir(parents=True,exist_ok=True)
 try:
  with main.connection() as db:
   migrate(db)
   actor=db.execute("SELECT id FROM accounts WHERE email=? AND role='owner'",(args.owner_email.strip().lower(),)).fetchone()
   if not actor:raise SystemExit('An existing owner email is required. No changes made.')
   institution_id=args.institution_id or create(db,details.organization)
   identity='account-'+secrets.token_hex(16)
   db.execute('INSERT INTO accounts (id,email,name,organization,role,password_hash,created_at) VALUES (?,?,?,?,?,?,?)',(identity,details.email,details.name,details.organization,'institution',password_hash(password),int(time.time())))
   assign(db,identity,institution_id,actor['id'])
 except sqlite3.IntegrityError:raise SystemExit('An account with that email already exists. No changes made.')
 print('Institution account created. Sign in through the app.')
if __name__=='__main__':run()
