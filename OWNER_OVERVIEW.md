# Platform-owner overview

Open http://127.0.0.1:8000/ and sign in with a platform-owner account. The owner overview opens automatically; there is no public Owner signup option. Student, faculty, industry and institution accounts cannot access it.

To create your owner account, open a terminal in this project folder and run the command below, replacing the email and name with yours:

```powershell
python -m backend.create_owner --email your-email@example.com --name "Your Name"
```

Enter and confirm a password of at least 10 characters at the hidden prompts. The command creates a new owner account; it refuses to overwrite or promote an existing account with the same email. Use a separate owner email if you already registered it as a student. No default owner password is shipped and no owner account was created in your real database during testing.

The overview shows account counts by role, completed and in-progress assessments, published faculty expertise, open/closed requests, pending/accepted/declined collaboration interests, seven-day aggregate activity, question-bank coverage, saved job interests, alert subscriptions and current job-source status. Refresh overview reads current records only and does not trigger paid provider calls.

Active sessions means unexpired logins, not live visitors. Completed assessments are counted from completed adaptive sessions and grouped by session-start date for the seven-day UTC chart; legacy quiz submissions are not counted as adaptive sessions. Legacy/unlinked profile counts are shown separately. An accepted interest is a response, not proof of a completed collaboration.

This overview deliberately returns aggregates, not student answers, passwords, emails, session tokens or private messages. It is read-only and cannot change accounts, roles, scores or questions. The separate institution view remains available only to institution accounts.

Validation: 56 unit/API tests passed; production frontend build passed; owner login, displayed metrics, refresh and logout verified in an isolated browser test database. Assessment and matching algorithms are unchanged. Online hosting is deferred until the end, as requested.
