# Preview update — 2026-10-27

Frontend production build passed. Full unittest run: 127 tests, 124 passed and 3 failed.
Outstanding failures: BackendBankTests.test_cluster_gate_and_separate_scoring (0 != 8); FrontendImportTests.test_source_code_answers_flags_and_loaded_bank and MarketingImportTests.test_exact_parse_and_source_ids_options_flags (import validators still expect a Tier-3 cap of 15; configured cap is 20).
These failures have not been fixed in this preview. It is not a production-readiness claim.
The cancelled, unfinished institution proposal-review module is excluded and disconnected. Private databases, uploaded documents, runtime logs and API keys are not published.
