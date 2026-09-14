# Editing the assessment content

> Backend update: imported 85 supplied questions, including 60 applied candidates (maximum 15 served). The other 29 tracks retain their starter banks. Taxonomy/index: 190 dimensions. See [BACKEND_IMPORT.md](BACKEND_IMPORT.md) for scoring and validation details.

## Question bank

Edit `backend/question_bank.json`. Use unique IDs and exact track/skill names from `backend/assessment_config.py` and `backend/domain.py`. Start a new attempt after editing; existing sessions keep their question snapshot. Restart synchronizes the SQLite question catalog.

A Tier 3 question uses this structure:

```json
{
  "id": "backend-sql-project-standard-01",
  "track": "backend",
  "skill": "SQL",
  "tier": 3,
  "type": "code_output_prediction",
  "prompt_text": "Your reviewed question goes here",
  "options": ["First answer", "Second answer", "Third answer", "Fourth answer"],
  "correct_option": 1,
  "requires_tier2_flag": "SQL",
  "verification_kind": "project",
  "difficulty": "standard",
  "context_tags": ["implementation"],
  "example": false
}
```

`correct_option` is a zero-based index: 1 means the second option. Do not place correct-answer explanations in the prompt or options. For each of the five project-count skills in a track, supply several `skill` and `project` checks. Project variants may use `standard` or `deep` difficulty. Heavy reported tool use selects `deep` questions when available. Optional context tags are `implementation`, `debugging` and `planning`; they prioritize relevant project checks. Free text is stored as notes and is not scored or interpreted as proof.

Supported displayed types include `code_output_prediction`, `numerical_case`, `scenario_judgment`, `visual_critique`, `applied_calculation` and `clinical_scenario`. Every applied check is a single-answer multiple-choice question; no submitted code is executed. Optional `visual_url` should point to a local static asset under `frontend/public/assets/`, with a corresponding `visual_alt` description. Rebuild the frontend after changing assets.

The engine distributes up to 15 checks across flagged skills, prioritizing stronger self-ratings when necessary. It never duplicates a question to reach the cap. Outside Backend, the starter bank provides three examples per track, concentrated on its first skill; more content is needed for broad applied coverage. Each missed selected check caps that skill at 4/10; passing all selected checks preserves its confidence rating. No selected check means self-reported evidence only. Soft skills stay self-reported.

Review questions with people qualified in the relevant domain before using them to evaluate students. In particular, replace or expand clinical examples only after suitable expert review. A quiz pass remains a quiz result, not credential or clinical-competence verification.

## Learning resources

Edit `backend/resources.json`. Each skill maps to up to two objects:

```json
{
  "SQL": [
    {"type": "doc", "title": "Your curated SQL reference", "url": "https://example.org/replace-with-your-reviewed-link"}
  ]
}
```

The example URL above is documentation only; it is not inserted into the app. Use your actual public resource URL. Allowed types are `video`, `course` and `doc`. HTTP(S) links only; empty or missing entries are skipped. Resource links are looked up for displayed gaps, without embedding or copying any material. No live learning-platform API is required. Restart synchronizes the optional SQLite resource catalog; JSON lookup itself reads your updated file on subsequent matching requests.


## Future import ID convention (approved)

Namespace bare source IDs in the import adapter before writing them. Frontend uses `FE-Q1` through `FE-Q60`; retain the bare label in `source_id`. Future tracks use a stable track prefix (the `namespaced_id` helper in `backend/import_frontend_bank.py` defaults to the uppercase internal track ID). Validate uniqueness across the whole loaded bank before committing. Never rename previously imported IDs or other tracks. Marketing keeps `Q1` through `Q60`. Preserve wording, source order, options, answers, labels and eligibility flags. This convention does not authorize importing any excluded track.
