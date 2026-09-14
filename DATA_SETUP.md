# Local data setup

This repository excludes `.env`, account/session databases, private portfolio uploads, live API caches, dependencies, build output, and bulk source datasets.

Copy `.env.example` to `.env` and configure your own API credentials. Never commit `.env`.

To reproduce the local Kaggle-backed inventory, prepare or restore `backend/data/jobs.csv` using the instructions in TRAINING_GUIDE.md. To rebuild the O*NET mapping, restore the O*NET export spreadsheets to `onet/onet_data/` and follow ONET_ALIGNMENT.md. The derived `backend/data/onet-corpus.json` is included.

Without the local CSV, real-data coverage differs from the original machine; available API/cache/fallback behavior still applies. The SQLite database is initialized by the application; create your own accounts. See README.md for installation and startup, and LOGIN_AND_CONNECTOR.md for account setup.
