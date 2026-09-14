# Backend question bank import

Imported the supplied Backend content: 15 confidence ratings, 5 project counts, 5 context questions and 60 applied candidates (85 total). The 667 questions belonging to the other 29 tracks are unchanged. The complete bank now contains 752 questions.

At most 15 eligible applied questions are served. Zero project flags skips context and verification; available coverage can make other quizzes shorter than 40 questions. Flags are ordered by confidence, with balanced selection across eligible clusters and scored dimensions. Authentication project context (or heavy AI use) prioritizes Q15. No new question content or difficulty levels were invented.

Scoring labels remain distinct from project eligibility flags. For example, Deployment unlocks Git questions, which score Git. The composite Java / Node.js label does not assign separate Java or Node.js scores.

Backend Testing and Adaptive / Project Context have no Tier 1 confidence baseline in the supplied bank. Their selected checks retain correct/total evidence, visible in the profile, but do not assign numeric proficiency or verification status. Their zero vector values mean unassessed, not a measured zero.

The taxonomy now has 190 dimensions. Eleven supplied labels were added without merging them into existing labels. The prepared 18,030-job Kaggle CSV and its 5,701 salary-bearing records are unchanged. The numeric index was aligned to 190 dimensions; new labels absent from existing job records have zero target values. No model training, extraction pipeline, matching formula or database schema changed.

Validation: 48 unit/API tests passed; all 30 adaptive tracks passed offline corpus matching checks. Other-track question content and the prepared CSV were compared against their pre-import values. These tests establish functional behavior, not recommendation accuracy.
