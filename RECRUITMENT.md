# Student recruitment and screening — isolated demo module

## Demo flow

1. Sign in as Industry. Expand **Student recruitment and shortlisting** above the existing Bridge requests.
2. Expand **Post a student recruitment role**. Enter its title, description, eligibility criteria, and required skills/levels from the existing taxonomy. Publish.
3. Sign in as Student and complete the existing assessment if necessary. Open **Connections → Student recruitment — share your assessment for a company role**.
4. Read the role, declare whether its eligibility criteria are met, and explicitly consent before applying. The recruiter receives a snapshot of the assessment, not raw quiz answers, documents, portfolio status or internship feedback. This is separate from external job links and the saved-job tracker.
5. The owning Industry account opens **Review applicants**. Candidates are ranked by the unchanged cosine calculation. Review the required-skill comparison and evidence, then manually record a shortlist decision. All active applicants remain accessible, including low-scoring and not-shortlisted applicants.
6. Students can see their own decision and withdraw profile sharing. Withdrawal removes the applicant from the recruiter's view and clears the shared vector/evidence. Reapplying requires a fresh opt-in and resets the old review. Retaking the quiz never silently changes an already shared snapshot.

## Evaluation, not an unearned 40% claim

The evaluation panel reports applicant, reviewed, shortlisted and unreviewed counts. Recruiters can enter actual review seconds; zero means no usable timing measurement. They can enter a separately measured total review-time baseline for the same applicant pool. No time is fabricated from button clicks.

Closing applications prevents new opt-ins and enables a count comparison: `(total applicants - manually recorded reviews) / total applicants × 100`. This compares with reviewing everyone. It is not a before/after experiment or proof of better hiring outcomes. With no applicants or no recorded reviews, the percentage is withheld.

Time reduction is reported only for a closed role with an entered baseline and positive recorded review time. Adding/withdrawing applicants invalidates the old time baseline because the pool changed. The report states that all timings and evaluation labels are human-entered.

Use a separate human-labelled benchmark to evaluate qualified-candidate retention. Every active applicant must receive a human label (qualified/not qualified); missing labels withhold retention and missed-candidate totals. Shortlist decisions are not used as ground-truth labels. With complete labels, the panel reports how many labelled-qualified candidates were shortlisted and how many were not. If none is labelled qualified, retention percentage is undefined, not 100%.

Download the aggregate JSON report for the demo. No candidate identifiers or assessment contents are included in this export. The automated 40%-reduction example is a **synthetic test fixture**, not a production result. No validated 40% screening reduction, 60% fewer failed applications, or hiring-success rate is claimed. The module screens consented assessment profiles; it does not parse or transmit resumes.

## Boundaries

- New tables only: `recruitment_roles`, `recruitment_applications`.
- Existing sessions, CSRF protection and role identities are reused.
- Only a role's industry owner can inspect/review its active opt-in applicants. Students see only their own application status; other roles cannot browse applicant records.
- Role requirements and eligibility text are recruiter-entered. Eligibility answers are self-declarations for human review, not inferred qualifications or automated rejection rules.
- Ranking calls the existing `domain.rank_jobs` with the stored student vector and the recruitment role's required skills. No formula, weighting, quiz, taxonomy or source-job pipeline is modified.
- No automatic shortlist cutoff, mass hiding, application notifications, portfolio access or internship integration.
- Required skills are immutable once published in this simple version; create a new role if requirements change so existing consent remains tied to the original requirements.
- Existing CSS is unchanged. The module reuses current panel, form, button, card and tag classes in an expandable section.

Files: `backend/recruitment.py`, `frontend/src/Recruitment.jsx`, `tests/test_recruitment.py`; additive router/migration registration in `backend/main.py` and entry points in the existing student/industry components.

Run `python -m unittest discover -s tests -v` and `npm.cmd run build --prefix frontend` from the project root. Tests use temporary data; no demo candidates are inserted into the real database.
