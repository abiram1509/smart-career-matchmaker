# Compliance, privacy, accessibility and trust audit

Audit date: 15 September 2026. Scope: repository implementation, not a certification or external penetration test. Findings below were recorded before implementation changes. Operator and deployment details are not established by a GitHub username.

## Pre-change findings

- Accounts collect name, email, role, organization and a password (scrypt hash stored). Session token hashes expire in eight hours. IP/email hashes support login throttling; expired throttle rows are not automatically purged. Server access logs can contain IP addresses, paths and timestamps.
- SQLite stores assessment sessions (answers and context), profiles/vectors/evidence, history, saved interests, alert subscriptions and notices. Scores are deterministic; no hiring-outcome model is trained. Sample profiles and historical/demo listings are labelled. No proven 40%/60% impact claim found in current UI.
- Bridge stores published faculty expertise, bios, location, availability, company requests and private interest messages/decisions. New faculty publication was preselected. Faculty names/organizations are also exposed to students through the mentor picker, independent of expertise publication.
- Portfolios store private original files and metadata/digests, accessible to student and owner; manual verification is not issuer authentication. There is no malware scanner or automatic deletion schedule.
- Internships store student/mentor identities, title, status and feedback. Only assigned participants see records through the UI. No self-service deletion or mentor reassignment.
- Recruitment stores consent timestamps and copies of assessment vector/evidence; only the posting company receives consenting applicants. Withdrawal removes vectors/evidence and hides the applicant but retains the row, review metadata and decision. Downloaded recipient copies cannot be recalled.
- Institution analytics are authenticated but global, not institution-isolated; owner analytics aggregate activity. Small cohorts may be identifiable. No analytics SDK, ad pixel, third-party login, payment/checkout or embedded video found. No browser localStorage/sessionStorage usage found.
- Browser requests are same-origin except a Google Fonts CSS import and font downloads. Job/course links leave the site on click. API calls to JSearch/RapidAPI and optional O*NET occur on the server and use field searches/occupation codes, not student profiles. Providers receive server connection metadata/credentials. Deployment proxies/logging are unknown.
- Missing public policies, operator contact details and privacy-request workflow. No jurisdiction/age scope or defensible retention schedule configured. No refund terms warranted by the implemented payment-free flow.
- Dialogs lack focus containment/restoration; mobile off-screen navigation can remain keyboard reachable; numerous small/light text styles have contrast issues. Forms mostly use wrapping labels; radios/ratings have semantic controls. Existing SVG question visuals have alternate descriptions; question content must remain unchanged.
- Google Fonts provenance/license files are absent locally. Bundled Lucide/React licenses exist. Ten local SVG question diagrams have no independent provenance record; owner confirmation required. Kaggle source dataset licensing and JSearch redistribution permissions are not established. O*NET database licensing is separately verifiable.

Implementation, testing and remaining findings are recorded below after verification. No conclusion here states that the app is fully legally compliant.
