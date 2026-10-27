"""Privacy notices and request intake; independent of assessment/matching."""
import html, os, secrets
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

router=APIRouter()
VERSION='2026-09-15'

def connection():
    from .accounts import connection as connect
    return connect()

def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS privacy_acknowledgements (account_id TEXT PRIMARY KEY, version TEXT NOT NULL, created_at TEXT NOT NULL)')
    db.execute("CREATE TABLE IF NOT EXISTS privacy_requests (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, kind TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'received')")

def acknowledge(db, identity):
    db.execute('INSERT INTO privacy_acknowledgements VALUES (?,?,?)',(identity,VERSION,datetime.now(timezone.utc).isoformat()))

class PrivacyRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind:Literal['access','correction','deletion','withdrawal','complaint']
    message:str=Field(default='',max_length=2000)

@router.post('/api/privacy/requests',status_code=201)
def submit(body:PrivacyRequest,request:Request):
    identity=secrets.token_hex(16)
    with connection() as db:
        if db.execute("SELECT COUNT(*) FROM privacy_requests WHERE account_id=? AND status='received'",(request.state.user['id'],)).fetchone()[0]>=10:
            raise HTTPException(429,'You have 10 pending requests. Please wait for operator review.')
        db.execute('INSERT INTO privacy_requests VALUES (?,?,?,?,?,?)',(identity,request.state.user['id'],body.kind,body.message.strip(),datetime.now(timezone.utc).isoformat(),'received'))
    return {'id':identity,'status':'received','message':'Request recorded for manual operator review. No data has been deleted or changed. No email was sent.'}

@router.get('/api/privacy/requests')
def requests(request:Request):
    with connection() as db:
        if request.state.user['role']=='owner':
            rows=db.execute('SELECT r.*,a.name FROM privacy_requests r JOIN accounts a ON a.id=r.account_id ORDER BY r.created_at DESC LIMIT 200').fetchall()
        else:
            rows=db.execute('SELECT * FROM privacy_requests WHERE account_id=? ORDER BY created_at DESC LIMIT 200',(request.state.user['id'],)).fetchall()
    return [dict(r) for r in rows]

PAGES={
'privacy':('Privacy Policy',[
('About this notice','Bridge / Smart Career Matchmaker is an assessment and academia-industry collaboration prototype. This notice describes the implemented application, not a certification of legal compliance. Operator identity, contact information, hosting location, retention periods and intended age/jurisdiction scope must be finalized before public service launch.'),
('Accounts and security','We store your name, email, selected role, organization if supplied, password hash and creation time in the server SQLite database. Faculty/industry organization is required; student organization is optional. Passwords are hashed using scrypt. The server stores hashes of session tokens and login-throttle identifiers derived from IP/email. Authentication sessions expire after eight hours. Ordinary server logs may include IP address, request path and time. Hosting/proxy logging and backup practices are not yet verified.'),
('Assessments and personal workspace','Choosing an assessment stores your field/track, answers, confidence ratings, project counts and optional context, plus a derived skill vector/evidence and assessment history. Saved opportunities and in-app alert preferences/results are stored for your workspace. Avoid patient information, identity documents, confidential employer material or other people’s personal data in free text. No student assessment is sent to an AI training provider by this implementation.'),
('Who sees collaboration information','Published faculty profiles (name, organization, expertise, bio, location and availability) and open company requests are visible to signed-in members. Faculty names and organizations also appear in students’ mentor selectors. Interest messages and decisions are visible to the faculty member and request owner. Unpublishing expertise removes it from the general directory, but does not withdraw existing messages or remove mentor-selector entries.'),
('Documents and internships','Portfolio uploads store the file, original filename, title, digest, size and review metadata. The student, platform owner and faculty with the same owner-assigned institution membership can download them. Manual reviewer verification does not confirm authenticity with an issuer. Internships store a title, student, assigned faculty mentor, status, feedback and any rejection reason. Supporting evidence files, filenames, titles, sizes and submission dates are stored separately from portfolio documents and are accessible only to the student and assigned mentor. Both participants can view the internship record; uploaded evidence requires manual review and is not automatic proof of completion. Do not upload unnecessary sensitive information. File deletion and internship changes beyond the existing controls require operator review.'),
('Recruitment sharing','Applying to an internal company role requires an unchecked consent control. It shares your name, assessment snapshot and evidence, eligibility declaration and application time with that role’s recruiter. Review decisions, human qualification labels and entered review time are stored. Withdraw profile sharing in Student recruitment to stop access and clear the stored vector/evidence snapshot. The application row and review metadata remain. Copies already downloaded or noted by recipients cannot be recalled automatically. Retaking an assessment does not update the shared snapshot; withdrawal and reapplication are required.'),
('Analytics and external recipients','Institution accounts can see assessment and saved-interest statistics only for students assigned to their verified institution by the owner. Job-market statistics remain platform-wide. Owner accounts see aggregate activity and document reviews. Small groups can still be identifiable. JSearch/RapidAPI and optional O*NET requests are made by the server using field searches/occupation codes, not student profiles. Those providers receive server IP/request metadata and configured credentials. External job/course sites receive your browser connection information when you follow their links and apply their own policies. No ad tracking SDK, embedded video or payment service is integrated.'),
('Cookies and device storage','The app uses a first-party authentication cookie, bridge_session. It does not implement analytics/advertising cookies, localStorage or sessionStorage. Assets and fonts are served locally or use system fonts. See the Cookie Policy for expiry and controls.'),
('Retention and security limits','There is no general automated account, assessment, document or activity deletion schedule. Data remains until manually removed by the operator, except explicit existing withdrawal controls and expiry cleanup of login sessions. Backup retention, legal holds and provider retention are not determined. Access controls, hashed passwords and request protections reduce risk but do not guarantee security. HTTPS and deployment hardening remain prerequisites for public hosting.'),
('Choices, requests and withdrawal','You can sign out, unsubscribe from in-app job alerts, unpublish your faculty expertise and withdraw recruitment sharing using their existing controls. Signed-in users can submit access, correction, deletion, consent-withdrawal or complaint requests through Privacy requests at the bottom of the app. Requests go to the owner inbox for manual review; submission does not itself erase an account, pause all processing or send email. Operator response timing and a contact route for people unable to sign in remain unresolved. Do not send passwords or sensitive documents in a request.'),
('Children, international access and updates','Age eligibility and parental-consent procedures are not implemented. The operator must decide the intended audience before admitting minors. India is the project context; overseas targeting, hosting and legal bases require review. This notice must be revised when data practices change. New-account notice acknowledgements are versioned; existing accounts are not retroactively marked as having consented.')]),
 'terms':('Terms & Conditions',[
('Status and operator','These are prototype service-use terms describing current behavior. The legal operator, contact details and any binding governing-law/dispute arrangements have not been confirmed. These unresolved items must be reviewed before public launch; no invented company identity or jurisdiction is asserted.'),
('Service and limitations','The app provides questionnaires, skill estimates, cosine similarity, job-source links, learning references, portfolios, collaboration, internship feedback and optional company recruitment. Similarity is not hiring probability or a credential. Historical and demo listings may not be open jobs. Learning durations and extracted skill levels are estimates. Neither a 40% screening reduction nor a 60% application-failure reduction is established.'),
('Accounts and acceptable use','Provide information you are entitled to share, keep credentials private and do not impersonate an institution, employer or another person. Do not upload malicious files, confidential patient material or content you lack permission to use. Public signup roles and display organizations are self-declared. Institution membership is assigned only by the platform owner; professional identity verification is not automated.'),
('Applications and decisions','External Apply links take you to another provider; saved tracker interests do not submit applications. Internal recruitment shares a consented assessment snapshot with one recruiter. Recruiters make manual decisions and remain responsible for checking qualifications, licensing, eligibility and fair selection. Faculty collaboration acceptance is not an employment contract or proof of completed work.'),
('Payments and refunds','This application has no checkout, paid subscription, renewal or payment collection flow. No refund guarantee is offered or invented. Any purchase made on an external learning or employer website is subject to that provider’s terms. Reassess these terms if paid services are introduced.'),
('Content and intellectual property','Keep ownership/permission for material you submit. Upload only what is needed for the selected feature and permitted recipients. External assets and datasets have their own licenses. O*NET attribution is on the Credits page. A public GitHub repository does not establish permission for all third-party material; unresolved dataset and question-asset rights are flagged for review.'),
('Leaving and contacting the operator','Sign out to end a session. Recruitment sharing and alert subscriptions have withdrawal controls; other correction, deletion and complaints use the manual Privacy requests workflow. No fixed retention or response guarantee is asserted. Operator identity/contact details below must be supplied.')]),
 'cookies':('Cookie Policy',[
('Authentication cookie','bridge_session is set on registration/sign-in by this site. It contains a random session token, with a hash stored server-side. Its purpose is authenticated access to your account. It lasts up to eight hours, uses Path=/, HttpOnly and SameSite=Strict, and Secure when the request is HTTPS. Sign-out invalidates the current server session and clears the cookie.'),
('Controls','You can sign out or clear/block the cookie in your browser. Blocking it prevents authenticated features. Clearing the browser cookie does not erase your account or immediately revoke a server session token; sign out before clearing cookies where possible.'),
('Other storage and consent','No advertising, analytics or optional tracking cookies, localStorage or sessionStorage are implemented. No optional-tracking consent banner is shown because no such tracker is loaded. This is a technical assessment, not a claim that every jurisdiction treats cookies identically. Reassess and obtain required consent before introducing non-essential tracking. External websites opened by links have separate cookie practices.')]),
 'accessibility':('Accessibility and help',[
('Current safeguards','The app includes labelled form controls, keyboard-operable controls, visible focus, dialog focus management, reduced-motion support and responsive layouts. Text contrast has been improved. These changes are not a WCAG certification or a claim of complete conformance.'),
('Assessment visuals','Some questions use visual diagrams with existing alternative text. Equivalent nonvisual assessment validity has not been independently established. Question wording and scoring were not changed during this audit.'),
('Report a barrier','Signed-in users can submit a complaint through Privacy requests. Include the screen, control and assistive technology involved; do not include passwords or sensitive documents. A public accessibility contact email and operator response process remain to be supplied.')]),
 'credits':('Sources and asset credits',[
('O*NET database','This app includes adapted information from the O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under Creative Commons Attribution 4.0 International. O*NET is a trademark of USDOL/ETA. Astra/Bridge mapping, filtering and skill-level adaptations have not been approved, endorsed or tested by USDOL/ETA. Source: https://www.onetcenter.org/database.html ; license: https://creativecommons.org/licenses/by/4.0/ . Mapping details are in ONET_ALIGNMENT.md and MARKETING_SKILL_MAPPING.md in the project repository.'),
('Software and graphics','React, React DOM, Scheduler and Lucide license notices are retained in THIRD_PARTY_NOTICES.txt. Icons are bundled locally. Typography uses installed system fonts, with no external font request. Ten local SVG quiz diagrams and supplied question-bank rights require owner provenance confirmation; no claim of a verified license is made for those assets.'),
('Other data','Kaggle dataset source URLs/licenses and JSearch API display, caching and redistribution permissions require confirmation against the actual datasets/subscription. Historical data is not proof of a live vacancy. External course/provider names do not imply a partnership or endorsement.')])}

def page(name):
    title,sections=PAGES[name]
    operator=html.escape(os.getenv('SITE_OPERATOR_NAME','Not supplied — required before public launch'))
    contact=html.escape(os.getenv('SITE_PRIVACY_EMAIL','Not supplied — signed-out contact route unresolved'))
    body=''.join('<section><h2>'+html.escape(h)+'</h2><p>'+html.escape(t)+'</p></section>' for h,t in sections)
    nav=' '.join('<a href="/'+p+'">'+html.escape(v[0])+'</a>' for p,v in PAGES.items())
    if name=='credits':body+='<p><a href="https://www.onetcenter.org/database.html" rel="noreferrer">O*NET database</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="noreferrer">CC BY 4.0</a> · <a href="/third-party-notices">Bundled software license notices</a></p>'
    return HTMLResponse('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+title+' | Bridge</title><style>body{font:1rem/1.7 system-ui,sans-serif;color:#203d31;background:#fafbf7;margin:0}main,nav{max-width:850px;margin:auto;padding:24px}nav{display:flex;flex-wrap:wrap;gap:16px}a{color:#214c3c;text-decoration:underline}a:focus-visible{outline:3px solid #214c3c;outline-offset:4px}h1{line-height:1.2}p{overflow-wrap:anywhere}</style><nav aria-label="Policy navigation"><a href="/">Back to app</a>'+nav+'</nav><main><h1>'+title+'</h1><p>Notice version '+VERSION+'</p><p><strong>Operator:</strong> '+operator+'<br><strong>Privacy contact:</strong> '+contact+'</p>'+body+'</main></html>')

def policy_endpoint(name):
    def endpoint(): return page(name)
    return endpoint

for name in PAGES:
    router.add_api_route('/'+name,policy_endpoint(name),methods=['GET'],response_class=HTMLResponse,include_in_schema=False)

@router.get('/third-party-notices',include_in_schema=False)
def notices():
    from pathlib import Path
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse((Path(__file__).resolve().parent.parent/'THIRD_PARTY_NOTICES.txt').read_text(encoding='utf-8'))
