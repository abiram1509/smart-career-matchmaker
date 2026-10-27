# Membership update — 8 October 2026

Faculty with owner-assigned membership can now list, download and review documents belonging to students in the same institution. Owner access remains unrestricted; unassigned faculty and cross-institution access are denied. See INSTITUTION_MEMBERSHIP.md for setup and tests. The original implementation notes below describe the earlier owner-only version.

# Document portfolios

Students: sign in and open **Overview â†’ My document portfolio**. Enter a title, choose a file, and upload. New documents are **self-reported**. The list and download links are visible only to the uploading student and the platform owner.

Reviewers: use the existing **owner** account and scroll to **Document review**. Download the file, review it, then choose **Mark verified**. The owner can also revert it to self-reported. This is the explicitly permitted simple administrator-toggle workflow; faculty, industry and institution accounts do not receive access to student files. Institution membership/isolation remains deferred. Owner account setup is in `OWNER_OVERVIEW.md`.

Verified means an administrator manually set the status. There is no automated issuer validation or malware scanning, and this status never changes assessment evidence, skill vectors or job matching.

## Storage and limits

- Separate SQLite table: `portfolio_documents`. No profile/results schema changes.
- Fields: id, student_id, file_reference, title, status, uploaded_at, original_name, size_bytes, sha256, verified_by, verified_at.
- Private files: `backend/data/portfolio-documents/`, with generated storage names. This directory is not mounted as static content and is ignored by Git. Exclude it from any shared demo/source archive.
- Keep both the database and private files when backing up or moving the app. Do not publish either.
- Supported uploads: PDF, PNG, JPG/JPEG, UTF-8 TXT, ZIP and DOCX; 5 MB/file, 30 documents/student. Basic extension/signature checks are not malware detection. Archives are never extracted by the server.
- Downloads require the existing authenticated session and are served as attachments with `nosniff`. Owner/student restrictions are checked server-side.
- Uploads use bounded JSON/base64 transport to remain compatible with the existing JSON-only authentication middleware. No new authentication or multipart dependency was introduced.

## API

- GET `/api/portfolio?offset=0`: own documents; owner sees all students, 100 per page.
- POST `/api/portfolio/upload`: student only; title, filename, content_base64.
- GET `/api/portfolio/{id}/download`: student owner or platform owner.
- PATCH `/api/portfolio/{id}/status`: platform owner only; status is self-reported or verified.

All writes use the existing session and request-protection header. Files are informational only. Run `python -m unittest discover -s tests -v` for the regression suite, including role isolation, verification, upload limits, missing files and unchanged assessment/job data. Tests use temporary databases and upload directories.
