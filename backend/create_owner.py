"""Provision the platform owner locally; never available through public signup."""
import argparse,getpass,secrets,time,sqlite3
from .accounts import migrate,password_hash,Registration
from . import main

def run():
 parser=argparse.ArgumentParser(description='Create a platform-owner account')
 parser.add_argument('--email',required=True);parser.add_argument('--name',required=True);parser.add_argument('--organization',default='Platform team')
 args=parser.parse_args();password=getpass.getpass('Owner password (at least 10 characters): ')
 if password!=getpass.getpass('Repeat password: '):raise SystemExit('Passwords do not match.')
 details=Registration(email=args.email,name=args.name,organization=args.organization,password=password)
 if len(details.name)<2:raise SystemExit('Enter a valid name.')
 main.DB.parent.mkdir(parents=True,exist_ok=True)
 try:
  with main.connection() as db:
   migrate(db);db.execute('INSERT INTO accounts VALUES (?,?,?,?,?,?,?)',('account-'+secrets.token_hex(16),details.email,details.name,details.organization,'owner',password_hash(password),int(time.time())))
 except sqlite3.IntegrityError:raise SystemExit('Email already registered. No existing role was changed.')
 print('Owner account created. Sign in through the app to open the owner overview.')
if __name__=='__main__':run()
