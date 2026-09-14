# Login and faculty–industry connector

Create an account on the opening screen as Student, Faculty / academician, or Industry representative. Sign in with that account on subsequent visits; sign out from the workspace header or sidebar. Student accounts retain their own assessments, history, saved jobs and alerts across sign-ins. Previous anonymous demo records are preserved separately and are not automatically claimable; take a new assessment under your account.

Faculty can publish or unpublish an expertise profile, browse industry requests, express interest with a short message, and track Pending / Accepted / Declined responses. Industry members can publish and edit training, mentorship, workshop, guest-lecture and live-project requests, close requests, review responses to their own requests, and accept or decline pending interests. Students and institution members can browse the directory and requests. All collaboration messages and responses remain inside this app; no email, SMS or third-party job application is sent.

Institution members have protected aggregate analytics for this local deployment. This is not a multi-tenant institutional system. Public signup does not grant institution privileges. To create the institution account, run this from the project folder, replacing the example details:

```powershell
python -m backend.create_institution --email admin@example.edu --name "Institution Admin" --organization "Your Institution"
```

The command prompts for and confirms a password without echoing it. It creates a new institution account only; an existing email is rejected. No default privileged credentials are shipped.

Accounts use salted scrypt password hashes. Sessions use random tokens, store only token hashes in SQLite, expire after eight hours, and use HttpOnly / SameSite=Strict cookies (Secure on HTTPS). Login and registration are rate-limited. State-changing API calls require `X-Bridge-Request: 1`; cross-origin browser writes are rejected. Protected APIs verify the logged-in user against student/profile identifiers and enforce connector ownership/roles. Account emails are not exposed in directory or request listings. No role is inferred from client-side localStorage.

Roles/organizations are self-declared for faculty and industry. Email verification, password-recovery delivery, production hosting/security hardening, institutional tenant isolation and institutional identity verification are not included in this local hackathon login. An accepted expression of interest records a collaboration response, not a contract or employment decision.

Implementation: backend/accounts.py, backend/connector.py, backend/create_institution.py, frontend/src/AccountsConnector.jsx; main.py only wires new migrations, routers and the access boundary. Assessment, cosine matching, eligibility, selection and context-note algorithms remain unchanged.

Validation: 53 unit/API tests passed, including password hashing, login/logout, session expiry, CSRF checks, role/ownership enforcement, rate limiting, profile publication, request editing/closure, duplicate-interest prevention and accepted-response visibility. Production frontend build passed. Browser checks used a separate test database and verified faculty login/profile publishing, industry login/request publishing, student login/assessment access, and sign-out. No test users or connector posts were added to the production database.
