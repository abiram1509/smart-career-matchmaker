"""Read-only platform-owner overview. No student answers or credentials are exposed."""
import time
from datetime import datetime,timezone,timedelta
from fastapi import APIRouter,Request,HTTPException
from .accounts import connection
router=APIRouter(prefix='/api/owner')

@router.get('/overview')
def overview(request:Request):
 if request.state.user['role']!='owner':raise HTTPException(403,'Platform-owner access is required.')
 from . import main,addon_api
 now=datetime.now(timezone.utc);start=now-timedelta(days=6);days=[(start+timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
 with connection() as db:
  def count(sql,args=()):return db.execute(sql,args).fetchone()[0]
  roles={role:0 for role in ['student','faculty','industry','institution','owner']}
  roles.update({r['role']:r['n'] for r in db.execute('SELECT role,COUNT(*) AS n FROM accounts GROUP BY role')})
  profiles=count('SELECT COUNT(*) FROM profiles')
  account_profiles=count('SELECT COUNT(*) FROM profiles p JOIN accounts a ON a.id=p.id WHERE a.role="student"')
  completions={r['day']:r['n'] for r in db.execute("SELECT substr(created_at,1,10) AS day,COUNT(*) AS n FROM assessment_sessions WHERE json_extract(state,'$.phase')='complete' GROUP BY day")}
  registrations={r['day']:r['n'] for r in db.execute("SELECT strftime('%Y-%m-%d',created_at,'unixepoch') AS day,COUNT(*) AS n FROM accounts GROUP BY day")}
  total_assessments=count("SELECT COUNT(*) FROM assessment_sessions WHERE json_extract(state,'$.phase')='complete'")
  in_progress=count("SELECT COUNT(*) FROM assessment_sessions WHERE json_extract(state,'$.phase')!='complete'")
  faculty={'published':count('SELECT COUNT(*) FROM faculty_profiles WHERE published=1'),'unpublished':count('SELECT COUNT(*) FROM faculty_profiles WHERE published=0')}
  requests={'Open':0,'Closed':0};requests.update({r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) AS n FROM collaboration_requests GROUP BY status')})
  interests={'Pending':0,'Accepted':0,'Declined':0};interests.update({r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) AS n FROM collaboration_interests GROUP BY status')})
  totals={'accounts':sum(roles.values()),'account_profiles':account_profiles,'legacy_profiles':profiles-account_profiles,'completed_assessments':total_assessments,'in_progress_assessments':in_progress,'saved_jobs':count('SELECT COUNT(*) FROM applications'),'alert_subscriptions':count('SELECT COUNT(*) FROM job_alert_subscriptions'),'unread_alerts':count('SELECT COUNT(*) FROM match_alerts WHERE read=0')}
  active_sessions=count('SELECT COUNT(DISTINCT account_id) FROM login_sessions WHERE expires_at>?',(int(time.time()),))
  questions={'total':count('SELECT COUNT(*) FROM questions'),'tracks':count('SELECT COUNT(DISTINCT track) FROM questions'),'verification_candidates':count('SELECT COUNT(*) FROM questions WHERE tier=3')}
 loader=main.loader
 return {'generated_at':now.isoformat(),'roles':roles,'totals':totals,'active_sessions':active_sessions,'faculty':faculty,'requests':requests,'interests':interests,'questions':questions,'activity':[{'day':day,'registrations':registrations.get(day,0),'completed_assessments':completions.get(day,0)} for day in days],'data_sources':{'cache_storage':loader.cache_status(),'layer':loader.layer,'jobs':len(loader.jobs),'counts':loader.source_counts,'field_queries':loader.query_status,'api_configured':bool(loader.api_url),'refresh_state':addon_api.refresh_status.get('state','idle')},'activity_note':'Assessment activity is grouped by session start date (UTC). Active sessions are unexpired logins, not a live online-user count.'}
