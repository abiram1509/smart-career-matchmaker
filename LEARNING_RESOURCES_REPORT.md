# Learning resources — 8 October 2026

## Latest expansion — 8 October 2026

The catalogue now contains **114 unique links across 221 populated exact skill labels**, up from 75 links and 146 labels in the initial pass documented below. Added 39 reachable URLs; all returned HTTP 200 in this pass. Two candidates (Azure learning path: 404; MySQL tutorial: 403) were excluded. Details are in LEARNING_LINK_EXPANSION.json. The eight blocked-access links from the initial pass remain flagged, not newly verified.

Added coverage includes Tableau, training evaluation, job analysis, Excel, Power BI, accounting, finance and additional development/cloud tools. Some existing readings are reused under relevant exact skill labels; these do not create scoring/taxonomy aliases. Maximum two resources per skill remains unchanged. Context/project-verification metadata labels are not treated as standalone teachable skills.

This expansion changes only the resource catalogue and reports; no frontend rebuild is needed. Reload the student workspace to fetch fresh match resources. Initial-pass statistics and browser observations below are historical (Training and Tableau now have resources).

## What changed

The catalogue previously contained zero populated entries. The existing backend attaches resources to job skill gaps, but My learning did not render them. This change populates the catalogue and renders the existing gap resources on learning cards; it does not change scoring, matching, question content or selection.

## Authored track baseline coverage

| Track | Baseline skills with resources |
|---|---|
| backend | 15/15 |
| frontend | 15/15 |
| data-ml | 15/15 |
| health-admin | 15/15 |
| legal-support | 15/15 |
| business-development | 15/15 |
| marketing | 15/15 |
| hr | 15/15 |

Coverage means at least one relevant introductory reading/course, not a complete curriculum or validated proficiency. Exact source skill labels remain unchanged. Shared readings do not create taxonomy aliases.

There are 146 populated exact skill labels and 75 unique URLs.

## Link checks

67 URLs returned HTTP 200. The URLs below returned HTTP 403 to the automated checker; their content was corroborated through official indexed pages, but normal-browser access remains unverified:
- https://www.ahrq.gov/evidencenow/tools/workflow-mapping.html
- https://www.ahrq.gov/health-literacy/improve/precautions/index.html
- https://www.cms.gov/training-education/medicare-learning-networkr-mln/resources-training/mln-publications-multimedia
- https://www.hhs.gov/hipaa/for-professionals/training/index.html
- https://www.law.georgetown.edu/academics/academic-resources/the-writing-center/guides-and-handouts/
- https://www.oecd.org/en/publications/g20-oecd-principles-of-corporate-governance-2023_ed750b30-en/full-report.html
- https://www.oecd.org/en/topics/sub-issues/due-diligence-guidance-for-responsible-business-conduct.html
- https://www.sap.com/resources/what-is-hris

HTTP 200 is a reachability check, not proof that every course lesson is accessible. Some sites use JavaScript, free registration or member-only sections. Course signups and paid access were not tested. Detailed status and destination records are in LEARNING_LINK_CHECKS.json.

## Remaining boundaries

- My learning still displays the existing top three gaps for the selected job; this change does not broaden gap selection. Other gaps can expose resources in the match details.
- US/UK healthcare, legal and HR examples are identified in link titles. These are learning materials, not Indian regulatory guidance or professional credentials.
- Broad textbooks and toolkits are starting points, not bespoke courses for each label.
- Starter tracks are not comprehensively covered. Their exact shared skills can reuse these links.
- No automatic enrolment, progress tracking or certificate import was added.

### Authored question labels without a resource (including context/verification labels)

- backend: Adaptive / Project Context
- frontend: Adaptive / Project Context, HTML/CSS
- data-ml: Adaptive / Project Context, Data Cleaning / EDA
- health-admin: Adaptive / Project Context, Healthcare Support / Project Verification, Medical Records / Data
- legal-support: Adaptive / Project Context, Due Diligence / Governance, Legal / Compliance Project Verification, Legal Risk Analysis
- business-development: Adaptive / Project Context, Business Development / Project Verification, Lead Generation / Prospecting
- marketing: A/B Testing, Adaptive / Project Context, Marketing Analytics / Project Verification, Marketing Strategy / Project Verification
- hr: Adaptive / Project Context, HR Analytics / Project Verification, Job Analysis, Training Evaluation

## Validation

- Backend loader: 15/15 Tier-1 labels covered in each of eight authored tracks.
- Existing rank_jobs: Python and Patient Safety gaps returned catalogue resources.
- Live browser: signed in as the existing demo student, opened My learning and verified the Python tutorial link and explicit empty states for Training/Tableau. Those job-source skills are outside the authored baseline coverage; no skill aliases were invented.
- Vite production build passed (1,584 modules). Windows realpath restrictions required a one-off preserveSymlinks build into work/learning-build; compiled files were copied to frontend/dist after filesystem permission was granted. No Vite configuration or package changes.
- No scoring/matching, quiz, taxonomy, question-bank, authentication or database files were edited for this task.
