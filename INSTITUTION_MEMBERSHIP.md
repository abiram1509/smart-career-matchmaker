# Institution membership and faculty document review

Implemented 8 October 2026. Membership is explicitly assigned by the platform owner. A matching organization string never grants access.

## Schema and migration

- `institutions(id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at INTEGER NOT NULL)`.
- `accounts.institution_id` is a nullable foreign key to institutions; `institution_assigned_by` references the owner account and `institution_assigned_at` records the timestamp. The display `organization` is retained.
- `institution_membership_events` records account, old/new institution, authorizing owner and timestamp, with foreign keys.
- The pre-migration `PRAGMA foreign_key_check` returned no rows. Global foreign-key enforcement is now enabled in the shared database connection. The post-migration check also returned no rows.
- Migration is additive and repeatable. No automatic organization-name matching occurs.
- A SQLite backup was saved outside the repository in `work/institution-backup/before-membership.sqlite3`. Do not restore it over newer user activity without separately preserving that activity.

## Owner workflow

Sign in as the platform owner and scroll to **Institution membership**. Create an institution, then select the verified institution for each eligible account and click **Save membership**. Check affiliation before assigning: this grants faculty access to documents belonging to the institution's students. Select **Unassigned** to revoke membership. Assignments and revocations are checked against current database membership, not a stale client value or cached login claim.

Student and faculty signup remains available, but signup cannot assign institution membership. The account can use its existing non-institution features while unassigned.

Institution-role accounts are provisioned locally:

```powershell
python -m backend.create_institution --email admin@example.edu --name "Institution Admin" --organization "Example Institution" --owner-email YOUR_EXISTING_OWNER_EMAIL
```

This creates a new Institution and linked institution account. To use an existing Institution, also supply `--institution-id EXISTING_ID`. Passwords are prompted privately. The CLI is an operator tool requiring local project/database access; the owner email identifies the authorizer, not an independent authentication factor. Browser membership endpoints require an authenticated owner session.

## Scope of isolation

- `/api/analytics`: assessed profiles, saved interests and gap aggregates are filtered by the authenticated institution account's current membership. Legacy profiles and unassigned students are excluded. Job counts, salary counts and demand remain shared market data, labelled accordingly.
- Faculty portfolio list, download and status-update endpoints require a non-null verified institution matching the student's current institution. Unknown and out-of-institution document IDs return 404; unassigned faculty receive 403.
- Student access stays limited to the student's own files; institution and industry roles do not gain document access.
- Owner access remains unrestricted. Both authorized faculty and owners can mark a document verified or revert it to self-reported. Existing `verified_by` and `verified_at` capture the reviewer. This is manual review, not issuer certification.
- No institution ID supplied by a client controls analytics or faculty document scope.
- Bridge collaboration, consented recruitment sharing and assigned internship mentoring retain their existing permissions; this is not a redesign of those cross-institution workflows.

## Approved demo setup

| Institution | Account | Role |
|---|---|---|
| Bridge Demo | student.demo@bridge.test | Student |
| Bridge Demo | faculty.demo@bridge.test | Faculty |
| Bridge Demo | institution.demo@bridge.test | Institution |
| Demo Institution B | student.demo.b@bridge.test | Student |
| Demo Institution B | faculty.demo.b@bridge.test | Faculty |
| Demo Institution B | institution.demo.b@bridge.test | Institution |

The extra B institution login supports the analytics demonstration. New random passwords are saved outside the repository in `work/institution-backup/DEMO_B_CREDENTIALS.json`; do not publish that file. Existing account passwords were not changed. All 14 other accounts remain unassigned, including tkr/tkr college, stanford and the blank-organization student.

Demo sequence:

1. Sign in as Bridge Demo faculty; its student's existing document appears under **My institution’s student documents**.
2. Sign in as B faculty; Bridge Demo's documents are absent. A direct request for an A document ID returns 404.
3. Upload a clearly labelled demonstration document as B student; B faculty can review it, A faculty cannot.
4. Compare institution logins under **Institution insights**. B initially has zero assessed students because its new student has not completed an assessment; do not manufacture a profile to populate the dashboard.
5. Owner **Document review** remains able to review both institutions. Use separate browser profiles/private windows for simultaneous roles because sessions use cookies.

## Validation

28 targeted tests passed: 10 in `test_institutions.py`, plus 18 account/Bridge, portfolio, owner and privacy regressions. This is not a claim that the entire project test suite was rerun.

Isolation tests cover forged analytics parameters, trailing-slash requests, guessed cross-institution document IDs, same-institution review, unrestricted owner review, unassigned accounts, removal and transfer with existing sessions, owner-only assignment, signup injection, old-schema preservation, repeatable migrations, foreign-key integrity and unchanged protected tables in controlled fixtures.

After the user restarted the app, live checks confirmed:

- All three B accounts can sign in; student/faculty portfolio lists are empty initially.
- B faculty cannot download the existing A document (404).
- B institution cannot switch analytics to A via an `institution_id` query parameter (still zero B assessed students).
- The faculty document-review UI and owner membership UI render with the approved assignments.

Frontend production build passed (1,585 modules) using a one-off Vite `preserveSymlinks` override to work around Windows sandbox path resolution; generated files were copied into the served `frontend/dist`. Project build configuration was not changed.

Protected file hashes matched the pre-task snapshot for `domain.py`, `adaptive_quiz.py`, `assessment_config.py`, `question_bank.json`, `loader.py`, `onet_alignment.py` and `recruitment.py`. The existing Tier-1 limit 10 and Tier-3 limit 20 remain unchanged. `main.py` did change: Request import, foreign-key connection setting, membership router registration and institution-scoped analytics. No matching/scoring route logic was changed.

The live database was active during this work. A snapshot comparison found one updated profile, one additional assessment session and two additional saved applications; these were not written by the membership migration. They were preserved. Do not claim a byte-identical live database. Controlled regression fixtures prove membership/document review does not alter assessment or matching data.

## Files changed for this feature

- Added: `backend/institutions.py`, `frontend/src/InstitutionMembership.jsx`, `tests/test_institutions.py`, this document.
- Updated: `backend/accounts.py`, `backend/main.py`, `backend/portfolio.py`, `backend/create_institution.py`, `backend/create_owner.py`, `backend/privacy.py`, `frontend/src/AccountsConnector.jsx`, `frontend/src/OwnerOverview.jsx`, `frontend/src/Portfolio.jsx`, `tests/auth_fixture.py`, `tests/test_accounts_connector.py`, `LOGIN_AND_CONNECTOR.md`, `PORTFOLIO.md`.
- Local-only: migration/seed helper, backup, test logs and demo credentials under `work/institution-backup` / `work`.

Run targeted tests from the project folder:

```powershell
python -m unittest discover -s tests -p test_institutions.py -v
python -m unittest discover -s tests -p test_accounts_connector.py -v
python -m unittest discover -s tests -p test_portfolio.py -v
python -m unittest discover -s tests -p test_owner.py -v
python -m unittest discover -s tests -p test_privacy.py -v
```

Sandbox testing required a writable workspace temporary directory and local-network permission; ordinary local PowerShell does not normally need that workaround.
