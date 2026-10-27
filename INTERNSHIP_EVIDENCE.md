# Internship evidence and rejection

Implemented 8 October 2026. This extends informational internship mentoring only.

## Student workflow

Open Overview > My internship. In an ongoing internship, use Supporting documents to upload a report, thesis, resume, completion letter or other supporting file. PDF, DOCX, TXT, PNG and JPG are accepted, up to 5 MB each and 20 files per internship. Files are private to the student and their assigned faculty mentor. Submission is not automatic verification or proof of completion.

## Faculty workflow

Open Internship mentoring from the faculty workspace navigation. Each assigned internship shows the submitted file count, titles, filenames and submission dates, with Download controls. Review these manually and use existing mentor feedback to request more evidence. Mark completed when satisfied, or choose Reject internship, give a reason, and Confirm rejection.

Both participants see a prominent REJECTED badge and the reason. Rejection retains evidence and feedback and closes uploads. The mentor can Reopen internship; rejection and reopening remain in the feedback timeline. Completed internships also need reopening before further uploads. Rejection is a manual action: inactivity is not monitored or automatically judged.

## Storage and authorization

Migration adds nullable rejection_reason, rejected_at and rejected_by columns; the legacy ongoing/completed CHECK constraint and all existing rows remain intact. API status is rejected while rejected_at is set, otherwise the stored status. Existing consumers use this API status. Queries written later against raw SQLite must apply the same interpretation.

A new internship_documents table holds evidence metadata and file bytes as SQLite BLOBs, with an internship foreign key. Include the SQLite database in backups; evidence is not stored in the separate portfolio directory. Document list queries exclude file bytes. Downloads are attachments, non-cacheable and restricted server-side to the owning student or assigned mentor. Other students/faculty, institutions, industry and owner accounts do not gain access through these endpoints. This retains the internship's existing assignment-based permissions rather than applying portfolio membership rules.

Uploads have a bounded request-body middleware, base64 and size checks, filename checks, extension/signature checks and per-internship limits. These checks are not malware scanning or certificate authentication. No automatic issuer verification is provided.

## Changes and validation

Added backend/internship_documents.py, frontend/src/InternshipEvidence.jsx and frontend/src/InternshipEvidence.css. Updated backend/internships.py, backend/main.py (middleware/router registration only), frontend/src/Internships.jsx and tests/test_internships.py.

30 targeted tests passed: 11 internship tests (previously 5), plus institution-isolation, account/Bridge and portfolio tests. Tests cover file access/downloads, foreign document IDs, upload validation/limits, rejection reasons and authorization, reopening, preservation of old migration rows, repeated migrations, and unchanged protected data tables. This is not a full-suite run. Production frontend build passed with 1,589 modules.

Scoring, adaptive selection, quiz configuration, loader, recruitment and portfolio backend hashes matched the pre-feature snapshot. Question banks and matching code were not edited.

The faculty/industry layout work is separate: PartnerLayout.jsx and PartnerLayout.css add role overviews and navigation, wired only for faculty and industry in AccountsConnector.jsx. Existing functional components stay mounted after first visit so switching sections does not discard drafts. Student, owner and institution layouts retain their existing rendering.

The user-run app needs a backend restart for the migration and new endpoints; a frontend refresh alone is insufficient. No accounts or real internship decisions were modified for testing.

The existing privacy notice was updated only to disclose the new internship evidence and rejection data.
