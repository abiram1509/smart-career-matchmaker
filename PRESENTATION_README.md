# Smart Career Matchmaker
## Project brief for presentations

**Project name:** Smart Career Matchmaker  
**Working names:** Astra (project name used during development); Bridge (current interface branding)  
**Purpose:** Connect skill development, career discovery and academia–industry collaboration.  
**Stage:** Working local hackathon prototype; source code is public, application hosting is pending.  
**Repository:** https://github.com/abiram1509/smart-career-matchmaker

## 1. Elevator pitch

Smart Career Matchmaker helps students understand their assessed skills, discover relevant opportunities and identify areas for development. It combines tiered questionnaires, explainable cosine-similarity matching, real job datasets and live job APIs with faculty–industry collaboration tools. Companies can also post internal roles and review consenting applicants using the same skill-matching engine.

**Suggested opening:** “We help students see why a role matches their skills, and help companies review applicants with clearer skill evidence.”

## 2. The problem

- Students navigate fragmented job portals, learning resources and institutional processes.
- A resume alone may not clearly show a candidate’s current skills or gaps.
- Students may apply without understanding skill requirements or eligibility.
- Companies spend time reviewing applicants with limited comparable skill evidence.
- Faculty and industry need a shared place to discover expertise and practical collaboration opportunities.

These describe the problems the project addresses. They are not statistics from a validated user study.

## 3. The solution

A shared portal with distinct student, faculty, industry, institution and platform-owner accounts. The student journey links assessment, skill profiling, relevant opportunities and learning references. Separate collaboration, portfolio, internship and recruiter modules support the wider academia–industry workflow.

The prototype serves multiple disciplines, not only engineering. Content completeness and occupation mapping coverage vary by track.

## 4. Users and implemented capabilities

| Account | What it can do |
|---|---|
| Student | Complete assessments, see matches/gaps, follow learning links, save external opportunities, opt into in-app alerts, upload portfolio documents, log internships and apply to internal company roles with consent. |
| Faculty | Publish expertise, browse industry requests, express interest and give feedback on assigned student internships. |
| Industry | Post categorized collaboration requests, accept/decline faculty interests, publish student recruitment roles and manually shortlist consenting applicants. |
| Institution | Access protected, platform-wide aggregate assessment and opportunity analytics. Institution-specific data isolation is deferred. |
| Platform owner | View platform activity, manually review portfolio documents and administer the prototype. |

Public signup supports students, faculty and industry. Institution and owner accounts are provisioned separately. Organizations and roles are self-declared; signup does not verify professional credentials.

## 5. Core student workflow

1. Sign in and choose a field and assessment track.
2. Answer confidence ratings and project/experience questions.
3. Provide context where applicable and complete eligible applied checks.
4. Receive a numeric skill vector with assessment-evidence labels.
5. Compare that vector with job skill vectors using cosine similarity.
6. Inspect the match explanation, skill gaps, experience information and source details.
7. Follow relevant learning references, save opportunities or visit the original job site.

Retaking an assessment can update the student’s profile. It does not silently update assessment snapshots already shared with recruiters.

## 6. Assessment design and verified content scope

The configured engine currently loads **9 fields, 31 tracks, 306 skill dimensions and 1,209 question records**. These counts were checked against the current Python configuration and loaded question-bank JSON when this document was created; they are not a fresh query of an independently deployed service.

Eight tracks contain a complete supplied 85-question bank:

| Track | Internal ID | Tier 1 | Tier 2a | Tier 2b | Tier 3 stored | Total |
|---|---|---:|---:|---:|---:|---:|
| Backend | backend | 15 | 5 | 5 | 60 | 85 |
| Frontend | frontend | 15 | 5 | 5 | 60 | 85 |
| Data / ML | data-ml | 15 | 5 | 5 | 60 | 85 |
| Human Resources | hr | 15 | 5 | 5 | 60 | 85 |
| Marketing | marketing | 15 | 5 | 5 | 60 | 85 |
| Healthcare Support | health-admin | 15 | 5 | 5 | 60 | 85 |
| Legal & Compliance Support | legal-support | 15 | 5 | 5 | 60 | 85 |
| Business Development | business-development | 15 | 5 | 5 | 60 | 85 |

The remaining 23 tracks retain starter content. Do not describe all 31 tracks as fully authored.

- **Tier 1:** Self-rated confidence establishes skill baselines.
- **Tier 2a:** Project/experience counts identify claimed experience.
- **Tier 2b:** Context informs eligible question selection where supported.
- **Tier 3:** Applied questions are checked against supplied answer keys.
- All **60 Tier-3 candidates stay stored** for each full bank; **at most 15 eligible Tier-3 questions are served** in an assessment.
- Question coverage, missing baselines and some imported context integration remain limitations. They are not filled with invented questions or scores.

These assessments provide quiz evidence, not certified expertise, clinical competence or verified employment history.

## 7. How matching works

The application represents the student and each job using a shared skill vocabulary. It compares their vectors with the existing cosine-similarity implementation:

`similarity = dot(student_vector, job_vector) / (norm(student_vector) × norm(job_vector))`

The existing engine expresses the result as a percentage rounded to one decimal place. It also compares individual skill levels to explain requirements met and gaps.

**Important interpretation:** Cosine similarity measures vector direction. It is not a hiring probability and does not independently establish proficiency, qualifications, licensing or work authorization. An unassessed skill may use zero in the matching vector; that is not proof the student lacks the skill.

### Is this a trained ML model?

The core matcher uses deterministic cosine similarity from scikit-learn. Preparing datasets, extracting skills and building vectors/index artifacts is not supervised training of a hiring-outcome model. No validated predictive hiring model or placement-success percentage should be claimed.

## 8. Real job data, APIs and cache

The prepared local Kaggle corpus contains **18,030 deduplicated job records**. Historical salary information is displayed where supplied; salaries are not predicted.

Actual source strategy:

1. Use live API jobs together with the local Kaggle corpus.
2. When a live field fetch fails, use its cached API records alongside Kaggle.
3. Use demo jobs only when no usable real source is available.
4. Deduplicate overlapping records, preferring live copies.

JSearch through RapidAPI supplies live jobs. Nine broad field searches target ten usable jobs each; provider supply can produce fewer. This is not a guarantee of ten openings for every role.

A previous local load contained 90 API/cache records plus 18,030 Kaggle records. Current totals depend on API access, cache state and available local files. Check the app’s data strip or `/api/health` during the demo rather than presenting a fixed live count.

**Source-code sharing limitation:** The GitHub repository excludes API keys, account databases, private uploaded documents, live caches and bulk source datasets, including the prepared jobs CSV. A fresh clone will not automatically contain the original machine’s complete job inventory. See DATA_SETUP.md.

## 9. O*NET occupation alignment

O*NET 31.0 occupation, skill, software and task data provides an additional mapping layer between occupation requirements and Astra’s existing skill labels. Numeric source evidence and explicit mapping decisions support that layer.

- The alignment enriches real job vectors; it does not turn occupations into fictional vacancies.
- Ambiguous mappings require approval; unsupported skills remain unmapped.
- HR, general Sales and Business Development are treated distinctly.
- Marketing has approved coverage for 10 of its 15 Tier-1 skill dimensions; the remaining five are explicitly unsupported/rejected.
- Occupation alignment does not change quiz scoring or the cosine formula.

O*NET is a source of occupational evidence, not a partner endorsement. Mapping coverage remains uneven across tracks.

## 10. Company recruitment and screening

1. Industry creates a role with required skills and target levels.
2. A student chooses to apply and explicitly shares an assessment snapshot.
3. Recruitment calls the existing `backend.domain.rank_jobs` function for each applicant against that role.
4. Returned scores order applicants by compatibility; the recruiter can inspect skill comparisons and evidence.
5. The recruiter manually records a shortlist decision, review status and optional actual review time.
6. Students can view their own decision and withdraw shared assessment access.

This module does not duplicate the cosine formula, parse resumes or automatically reject applicants. It does not read old external-job match percentages: it calculates a fresh score for the internal company role using the unchanged engine.

External Kaggle/API job links and internal recruitment applications are separate flows.

## 11. Impact goals and how to evaluate them

### Goal: reduce company screening effort

The evaluation panel records applicant totals, reviews, shortlist decisions and review time. It can compare reviews performed with reviewing every applicant after applications close.

**Illustrative example only:** reviewing 60 of 100 applicants is 40% fewer reviews. This is not a measured project outcome.

A credible evaluation also checks whether qualified candidates were missed. Qualification labels must come from independent human assessment of the role criteria, not copied similarity scores or shortlist decisions.

### Goal: reduce unsuccessful applications

A proposed 60% reduction in failed applications is not demonstrated. First define failure, then collect actual application outcomes and compare against a defensible baseline. Testing realistic profiles for relevant recommendations is useful but does not prove this impact percentage.

**Safe slide wording:** “Designed to reduce screening effort and poorly aligned applications; impact validation is the next evaluation stage.”

## 12. Other implemented modules

### Faculty–industry Bridge

Industry requests have category labels and filters: FDP, Industrial Training, Consultancy, Collaborative Research, Mentorship, Workshop / Guest Lecture and Live Project. Legacy requests can retain a generic Collaboration label. Faculty publish expertise, express interest and see industry acceptance/decline decisions.

This is a collaboration workflow; acceptance does not itself constitute an internship placement or signed contract.

### Document portfolios

Students upload supporting documents, and the platform owner can mark documents manually reviewed/verified. Files are private to the student and owner. The flag is not independent issuer verification and does not alter skill scores or matches.

### Internship and mentor feedback

Students manually log an internship they have secured and choose a faculty mentor. The mentor adds text feedback and updates ongoing/completed status. This is separate from job applications; clicking Apply does not automatically create an internship. No milestone engine or placement verification is claimed.

### Learning and alerts

The app offers curated external learning references and estimated learning steps. Learning-provider API integration remains deferred. Alerts are opt-in and appear within the app; no email/SMS delivery is implemented.

## 13. Architecture and technology

```text
React interface
    |
    | Same-origin HTTP/JSON with authenticated sessions
    v
FastAPI backend
    |-- Accounts and role boundaries
    |-- Tiered assessment -> skill vector and evidence
    |-- Existing cosine matcher -> matches and explanations
    |-- Bridge / recruitment / portfolio / internship modules
    |
    |-- SQLite: accounts, assessments, profiles and feature records
    |-- Private document storage
    |-- Job loader: live JSearch + Kaggle / cached API / final demo fallback
    |-- O*NET mapping corpus: occupation-to-skill alignment
```

| Layer | Technology |
|---|---|
| Interface | React 19, JavaScript/JSX, CSS, Lucide icons |
| Frontend build | Vite 6 |
| Backend | Python, FastAPI, Uvicorn |
| Vector matching | scikit-learn cosine similarity; numeric vector operations |
| External HTTP | HTTPX |
| Persistence | SQLite, local JSON/CSV/vector artifacts, private document files |
| Live jobs | JSearch / RapidAPI |
| Occupational data | O*NET 31.0 |
| Tests | Python unittest and FastAPI TestClient |

## 14. Security and scope

Implemented protections include password hashing, expiring HttpOnly sessions, role-based access, request-origin/header protections and account ownership checks. Recruitment sharing is opt-in, with withdrawal. These are technical safeguards, not proof of production security or legal compliance.

Institution-specific isolation, verified organization membership, broader identity verification, production hosting and operational processes remain open. The recent privacy/accessibility audit was stopped at the owner’s request; its local changes are unfinished as an audit deliverable and must not be presented as a completed compliance certification. This document does not resume that audit.

## 15. Testing and current development state

- Last complete local test run: **107 tests passed**, including six new privacy tests added after the earlier 101-test recruitment baseline.
- The frontend production build passed during the latest local work.
- Tests cover functional behavior, authentication/ownership, assessment and import behavior, data-source fallbacks, recruitment and supporting modules.
- Passing tests do not prove recommendation quality, accessibility conformance, legal compliance or real-world hiring impact.
- GitHub contains the pushed project baseline. Later local privacy/accessibility changes have not been pushed.
- UI/UX redesign is next; application deployment remains pending.

## 16. Suggested live demonstration (5–7 minutes)

1. **Student assessment:** Choose one of the eight full-content tracks; show confidence, experience and applied checks. Use a previously completed demo profile if time is limited.
2. **Explainable matching:** Open a result and explain score, source, experience information and skill gaps. Distinguish historical/demo records from live availability.
3. **Company screening:** Open a prepared internal role, show a consenting applicant and inspect evidence. Save a manual shortlist decision.
4. **Collaboration:** Show a categorized industry request and a faculty expression of interest.
5. **Internship or portfolio:** Show mentor feedback or an administrator’s manual document-review flag.
6. **Close with evaluation:** Explain that measurement infrastructure exists, while the 40%/60% targets remain unvalidated.

Prepare a faculty profile, company role, student assessment and consented application before presenting. Use clearly labelled demo accounts and sample information; never show passwords or API keys on slides.

## 17. Suggested PPT outline

1. **Title:** Smart Career Matchmaker — Connecting Skills, Careers and Industry
2. **Problem:** Fragmented opportunities and limited comparable skill evidence
3. **Users and solution:** Students, faculty, companies and institutions
4. **Student journey:** Assessment -> skill vector -> matching -> explainable next steps
5. **Assessment depth:** Eight complete banks, adaptive applied checks, 15-question serving cap
6. **Data and architecture:** Kaggle + live API + cache; O*NET alignment; React/FastAPI/SQLite
7. **Recruiter value:** Consented skill profiles, ranked applicants, manual shortlisting
8. **Collaboration ecosystem:** Bridge categories, portfolios and mentor feedback
9. **Validation and limitations:** Functional tests; unproven impact targets; uneven track coverage
10. **Roadmap:** UI/UX refinement, realistic-profile evaluation, pilot impact measurement and deployment

## 18. Presentation claims checklist

| Say | Avoid |
|---|---|
| Explainable skill-vector similarity | “90% match means a 90% chance of getting hired” |
| Eight complete supplied question banks | “All 31 tracks are fully authored” |
| Historical jobs plus provider-dependent live opportunities | “Every dataset record is an active vacancy” |
| Ranked consenting applicants with manual decisions | “Automatic rejection of unsuitable candidates” |
| Manual administrator document review | “Certified or issuer-verified credentials” |
| Targeting lower screening effort | “We have already reduced resume reviews by 40%” |
| Deterministic matching using prepared data | “A trained predictive hiring AI with proven accuracy” |
| Source code published on GitHub | “The website is deployed and publicly hosted” |

## 19. Local setup

From the project folder, follow README.md and DATA_SETUP.md. The supplied PowerShell launcher is `./start.ps1`. After dependencies and the frontend build are ready, the backend command is:

```sh
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ on that machine. API credentials belong in the private `.env` file; never in a presentation or public repository.

## 20. Details for the team to add

- Team name, members and institution
- Problem-statement identifier, if applicable
- Screenshots from the actual current app
- Demo URL after deployment
- Any measured pilot results, clearly separated from targets

Do not invent these details or present future work as implemented functionality.
