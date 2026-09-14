# Debugging verification — 13 September 2026

- Cache inspection found 90 unique jobs: a combined snapshot plus nine per-field snapshots containing 10 jobs each. These are copies of the same jobs, not additional openings.
- Health and owner overview now distinguish stored backups from cached jobs currently served. Live records still take priority; Kaggle combines with real API records, and demo is the final fallback.
- Missing/corrupt per-field snapshots can recover that field from the combined snapshot even when other live fields succeed.
- Cache writes use unique temporary files and atomic replacement. Failed writes preserve the last good snapshot, clean up temporary files, and report failure accurately.
- A match request now uses one loader snapshot so a simultaneous job refresh cannot mix job records and their matching vectors.
- Unsubscribe errors are displayed through the authenticated API client. Unassessed skills no longer receive estimated learning durations. Source health and matching results refresh when navigating between student pages.
- Removed obsolete UI text claiming the application has no authentication.

Verification: 60 backend tests passed, including four new regression tests; frontend production build passed. Isolated owner-account browser check confirmed cache diagnostics render and sign-out works. Tests use temporary databases/cache files. Core domain.py and adaptive_quiz.py hashes are unchanged. No question-bank content, scoring formulas, adaptive selection, or eligibility logic was changed.

Cache files: backend/data/jobs-cache.json and backend/data/jobs-cache-<field>.json. Health endpoint: /api/health, cache_storage object. Last saved is a disk-write timestamp; it does not verify whether a posting is still open.

O*NET alignment, UI/UX redesign, and public deployment remain deferred. This was a focused regression/debugging pass, not a claim that every possible application issue has been eliminated.
