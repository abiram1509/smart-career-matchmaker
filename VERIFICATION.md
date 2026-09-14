# Verification — addendums 1 and 2

> Backend update: imported 85 supplied questions, including 60 applied candidates (maximum 15 served). The other 29 tracks retain their starter banks. Taxonomy/index: 190 dimensions. See [BACKEND_IMPORT.md](BACKEND_IMPORT.md) for scoring and validation details.

Updated 13 September 2026.

- 48 unit/API tests pass. Coverage includes all 30 field/track choices, universal ratings, project-count flags, context-dependent question selection, a balanced 15-question cap, unflagged-skill exclusion, scoring penalties, evidence metadata, hidden answer keys, session replay protection and legacy evidence clearing.
- Alerts are tested with controlled local jobs and profiles: new jobs, updated scores crossing thresholds, repeated checks without duplicate notifications and unsubscribe behaviour. The hybrid loader is covered by live/cache/Kaggle/fallback tests, including per-field failures and pagination.
- Resource lookup accepts valid public links and skips missing entries or unsupported URL schemes. No real resource URLs have been curated into the registry yet, as requested.
- Offline corpus validation passes across all 30 adaptive tracks: 18,030 unique jobs, 190 skill dimensions and 5,701 structured salary records. This is a functional check, not a measured recommendation-accuracy result.
- All 13,552 available company-name joins match the supplied companies table. All 1,337 category-template records have category-code provenance. The remaining 16,693 records use description extraction.
- Production frontend build passes.
- Before the Backend content import, browser checks verified field → track selection, three confidence pages including universal skills, project counts, optional context notes and heavy-tool-use routing into the deeper Python example. No zero-project SQL checks were served. The browser verification stopped before submitting the final tier, preserving the user's existing profile; completion and persistence were verified in isolated API tests.
- The running addendum app was observed with 90 live jobs + 18,030 Kaggle records and no demo jobs. Live counts vary on subsequent provider refreshes.

Content deliberately pending: domain-reviewed expansions to backend/question_bank.json and curated URLs in backend/resources.json. Outside Backend, the three applied examples per track are explicitly labelled examples and do not form a full 40-question quiz. The engine uses actual available coverage; it does not pad with repeated or fabricated questions.

No employer application submission, credential verification, clinical-competence verification or learned prediction system is claimed. See README.md and CONTENT_GUIDE.md.
