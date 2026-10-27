# Deployment preparation

Status: prepared locally, not published. Hosting choice/payment approval is pending.

The Docker image builds the existing frontend and serves it with FastAPI. No scoring, question selection, matching or application modules are changed.

## Persistent storage
Mount a persistent disk at `/app/backend/data`. It contains SQLite, caches and uploaded documents. Use one service instance and one worker. Do not use ephemeral storage for real accounts.

The container seeds missing packaged reference files on startup; it never overwrites existing data. If packaged O*NET/reference data changes later, explicitly replace the relevant reference file on the disk after backing up; do not replace the database.

## Render proposal
Connect the GitHub repository and use render.yaml after approving paid hosting. Enter API settings directly in the hosting dashboard, never in Git. Forwarded proxy headers are trusted here only because the service is reached through Render's managed ingress; do not reuse the wildcard on an untrusted directly exposed server.

## Local data is NOT automatically deployed
The Docker image excludes secrets, databases, uploaded documents, raw Kaggle jobs and API caches. Upload the authorized jobs.csv privately into `/app/backend/data/jobs.csv` to restore local job coverage; verify source redistribution/use rights. Without it, API/cache/fallback coverage differs from the laptop. Do not claim identical inventory until checked.

Existing accounts are not migrated. Decide whether to migrate a backed-up database or create a fresh installation. The earlier request to retain only the named owner has NOT yet been executed. Do not upload the unfiltered laptop database assuming it has been cleared.

For a fresh installation, provision the owner interactively in the service shell:
`python -m backend.create_owner --email owner@example.com --name Owner`
Enter the password privately when prompted. Do not put it in command arguments or source.

## Verification before publishing
Build Docker image, verify startup and HTTPS registration/login/logout, verify cookies and same-origin POST checks, and verify storage survives a redeploy. Check that question banks and job-source counts match the intended deployment. Local Docker is unavailable in the current environment, so image build remains unverified.

Use SQLite's online backup API for backups, plus a copy of uploaded documents; keep backups private. Render disk snapshots are not a substitute for tested database backups.

## Budget update
Paid hosting rejected. render.yaml now describes a FREE, EPHEMERAL demo only. Earlier paid-disk instructions are alternatives, not the selected plan. Do not deploy this free configuration with an expectation that accounts/uploads survive restarts. User acceptance of this limitation and hosting login are still needed. Vercel alone does not supply a persistent SQLite filesystem; durable free hosting would require a separate storage/database solution or a different host.
