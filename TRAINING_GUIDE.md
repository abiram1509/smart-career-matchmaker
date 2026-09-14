# About the matching calculation

> Backend update: imported 85 supplied questions, including 60 applied candidates (maximum 15 served). The other 29 tracks retain their starter banks. Taxonomy/index: 190 dimensions. See [BACKEND_IMPORT.md](BACKEND_IMPORT.md) for scoring and validation details.

This version uses deterministic cosine similarity over structured skill vectors. Cosine similarity has no training phase and requires no training dataset. The supplied Kaggle records are the searchable job corpus.

The adaptive quiz checks selected answers against predefined keys, stores evidence metadata and computes numeric scores using explicit rules. There is no automated grading of project notes and no execution of submitted code.

For this build, the additional material to provide is reviewed domain questions and curated learning links. See CONTENT_GUIDE.md. A future learned ranking system would be a separate project requiring labelled relevance examples and independent evaluation; it is not part of this implementation.
