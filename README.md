# Smart Career Matchmaker

> Backend update: imported 85 supplied questions, including 60 applied candidates (maximum 15 served). The other 29 tracks retain their starter banks. Taxonomy/index: 190 dimensions. See [BACKEND_IMPORT.md](BACKEND_IMPORT.md) for scoring and validation details.

A local React + FastAPI + SQLite application implementing:

**Field and track selection → tiered questionnaire → numeric skill vector → deterministic cosine matching → explainable gaps.**

The matching calculation has no training step. Quiz checks use predefined answer keys. Passing examples is not a credential or proof of employment experience.

## Platform-owner overview

A dedicated owner account opens the read-only platform overview after login. See [OWNER_OVERVIEW.md](OWNER_OVERVIEW.md) to create your owner account locally. Public signup cannot grant this role.

## Login and collaboration

Student, faculty and industry accounts can sign up in the app. Faculty can publish expertise; industry can post collaboration requests and review faculty interests. Institution access is provisioned locally. See [LOGIN_AND_CONNECTOR.md](LOGIN_AND_CONNECTOR.md) for setup and limitations.

## Run

From this project directory, run `./start.ps1`, then open http://127.0.0.1:8000/. The script installs dependencies and builds the frontend. Keep the server running. After updating the app, refresh the browser to load the new screens. Existing local profiles are retained; retake the assessment to get the new evidence metadata.

For an already configured environment:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## What the addendums add

- Nine broad assessment fields, 30 narrower tracks and 190 shared skill dimensions. Existing domain skill names remain compatible.
- Tier 1: 15 confidence ratings (10 track skills + 5 universal skills).
- Tier 2a: five project/assignment/case counts. Only claims of 2+ flag a skill for applied checks.
- Tier 2b: five context questions when skills are flagged. Two optional notes are stored without grading. Structured tool-use and focus answers guide question selection.
- Tier 3: a balanced mix of project and pure-skill questions from the editable bank, capped at 15. Heavy tool use selects deeper project questions where supplied. Only flagged skills can be selected.
- All selected checks correct: retain the self-rating and mark quiz evidence as passed. Any incorrect check: cap that skill at 4. No check: retain the rating as self-reported. Untested dimensions stay 0 with `assessed: false`.
- Versioned server-side sessions prevent duplicate step submissions. Correct answer keys are never included in question responses. Evidence is stored separately from the numeric vector and used in explanations and exports.
- Local opt-in job alerts, curated resource lookup and link-out-only applications.

### Content intentionally left for you

The other 29 tracks have three illustrative Tier 3 questions each, generally yielding two questions per attempt for the first track skill. The remaining flagged skills need your reviewed questions. With this starter bank, a quiz usually contains 20 questions without project claims or 27 when the first skill is flagged. It is not represented as a complete 40-question assessment.

Edit **backend/question_bank.json** to expand the bank. See **CONTENT_GUIDE.md** for the schema and routing rules. The file contains confidence/count questions as well as examples. Clinical examples cover safe workflow and record handling only; they do not assess clinical competence.

Edit **backend/resources.json** to add your curated links. Every taxonomy skill has an empty list ready for content. Empty entries produce no resource block. No course or video is hosted or embedded.

## Real data and provenance

The prepared corpus contains **18,030 deduplicated jobs**, **190 index dimensions**, and **5,701 structured salary records**. The base posting descriptions and company/category IDs are joined to the supplied `companies.csv` and `job_skills.csv`; all 35 category codes have explicit mappings.

- 16,693 records use description-extracted skill mentions. Targets of 6/10 or 7/10 for repeated mentions are heuristic learning targets, not employer proficiency statements.
- 1,337 records use broad category templates when description extraction is sparse. These inferred skills and 5/10 targets are explicitly labelled `category_template`.
- `category_codes`, `category_fields`, `category_tracks`, `company_id` and `skill_source` preserve the join provenance. Company names come from matching IDs; missing names are not invented.
- Original salaries preserve currency and period. Salary is displayed, not predicted.
- Original source files remain untouched. Raw company speciality text is not treated as an individual job requirement. Other exclusions are recorded in `backend/data/dataset_report.json`.

Rebuild offline:

```powershell
python -m backend.prepare_data --source 'C:\Users\abira\Downloads\archive (1)'
python -m backend.validate_corpus
```

## Live jobs and cache

Your live-first setup remains: live API + Kaggle, per-field cached API + Kaggle on failure, and demo records only if every real source is unavailable/empty. Deduplication prefers the live copy. Nine JSearch field queries target ten usable jobs each, following up to two extra cursor pages when needed. Provider supply can still yield fewer. This is nine broad searches, not ten jobs for every individual title or every assessment track.

The latest verified load contained **90 live + 18,030 Kaggle = 18,120** records. Counts and source kinds are available in `/api/health`; career filters can overlap because jobs may have several field tags. Historical Kaggle records are not claimed to be current vacancies.

Configure the private `.env` beside this README:

```dotenv
JOBS_API_URL=https://jsearch.p.rapidapi.com/search-v2?query=jobs%20in%20India&country=in
JOBS_API_KEY=YOUR_PRIVATE_RAPIDAPI_KEY
JOBS_API_SEARCH_MODE=fields
```

The JSearch adapter supplies the RapidAPI host and key headers. Requests use timeouts and bounded retries. Startup can take several minutes. `backend/field_queries.json` holds the nine queries. `.env`, all API caches and the local SQLite database are excluded from the downloadable archive.

## Alerts and applications

Open a job detail and opt in at a threshold (default 75%). There is one active field subscription per local profile; opting in on another field replaces it. The subscription records a vector snapshot and prior job scores. The Job alerts page provides **Refresh jobs & check alerts**; it refreshes the hybrid loader and compares new jobs/current profile scores. Alerts appear for new jobs above threshold or a previously seen job crossing from below to above it. Repeating an unchanged check produces no duplicate alert. Unsubscribe stops future checks for that profile.

Notifications stay in this app. No email or SMS is sent. **Apply on original site** opens the supplied job URL. Missing URLs show a suggested title/company search. **Save to tracker** is a local bookmark, not an application submission.

## Storage and endpoints

SQLite stores profiles (including field, track, evidence, project notes and alert preference), assessment sessions, questions, jobs, resources, subscriptions, notifications and local bookmarks. Accounts now collect name/email and use session-based login. See LOGIN_AND_CONNECTOR.md for role access and institution account setup. Legacy quiz endpoints remain for compatibility with earlier local profiles; the current UI uses the adaptive endpoints.

- GET `/api/assessment/catalog`
- POST `/api/assessment/start` with student_id, field, track
- POST `/api/assessment/{session_id}/advance` with student_id, version, answers
- POST `/api/match` with skill_vector and optional profile_id, field, search, opportunity_type, source_filter and limit. A profile_id uses its stored vector/evidence.
- GET `/api/match/job?student_id=...&job_id=...`
- POST `/api/alerts/subscribe`; POST `/api/alerts/check`
- GET `/api/student/{id}/alerts`; DELETE `/api/student/{id}/alerts/subscription`
- GET `/api/resources`, `/api/health`, `/api/analytics`, `/api/data/report`

## Validation and limits

```powershell
python -m unittest discover -s tests -q
python -m backend.validate_corpus
npm.cmd --prefix frontend run build
```

Functional tests are not evidence of real-world recommendation accuracy. Similarity is not a hiring probability, and untested skills are not established weaknesses. This is a localhost hackathon MVP with basic login and role access, but without credential verification or third-party application submission. Use sample profile information.
