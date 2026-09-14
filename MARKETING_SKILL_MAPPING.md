# Marketing O*NET skill mapping — final approved decisions

## Coverage

**10/15 actual Marketing Tier-1 skills mapped** across Marketing Managers (`11-2021.00`) and Market Research Analysts and Marketing Specialists (`13-1161.00`). Four use direct rated task evidence; six use the explicitly approved occupation-specific proxy mappings below. These are not literal O*NET skill-name equivalences or verified proficiency.

Marketing Managers: **7/15**. Market Research Analysts: **8/15**. Their union covers **10/15**. Coverage is calculated against the actual question-bank Tier-1 labels, including `Search Engine Optimization` and `Search Engine Marketing`; the separate `SEO` question-bank label is not merged or renamed.

All mapped dimensions retain the existing occupation-derived 5/10 input baseline. Raw source ratings remain evidence and do not change scoring, weights or proficiency calculations.

## Six approved proxy mappings

| Added Tier-1 skill | Exact source evidence | Scope |
|---|---|---|
| Digital Marketing | Google Ads; Marketo Marketing Automation | Both occupations |
| Search Engine Marketing | Google Ads | Both occupations |
| Social Media Marketing | Facebook; Instagram | Both occupations |
| Email Marketing | Oracle Eloqua in both; Constant Contact additionally in Managers | Both occupations |
| Customer Segmentation | Task 5433: analyze customer demographics, preferences, needs and buying habits to identify markets; importance 3.88 | Analysts |
| Campaign Management | Task 20709: direct/coordinate marketing activities; importance 4.08. Task 961: coordinate promotional activities/trade shows; importance 3.16 | Managers |

These mappings were explicitly approved by the user. The adapter requires both the `marketing` track and one of the two approved occupation codes. Exact software names/task IDs are matched; no universal software aliases were introduced. Evidence records for these mappings carry `mapping_basis: user-approved occupation-specific proxy`. Task proxies retain the existing suppression and importance checks. Software evidence does not invent numeric O*NET ratings.

## Implemented evidence

| Actual Tier-1 label | Occupation | Task ID | Source importance (1–5) | Meaning supporting this mapping |
|---|---|---|---:|---|
| Market Research | Marketing Managers | 963 | 3.71 | Initiate market research studies or analyze their findings |
| Marketing Strategy | Marketing Managers | 951 | 3.89 | Identify, develop, or evaluate marketing strategy |
| Market Research | Market Research Analysts | 5439 | 3.94 | Conduct research on consumer opinions and marketing strategies |
| Customer Research | Market Research Analysts | 5439 | 3.94 | Conduct research on consumer opinions |
| Customer Research | Market Research Analysts | 5433 | 3.88 | Collect and analyze customer demographics, preferences, needs and buying habits |
| Marketing Analytics | Market Research Analysts | 5438 | 3.36 | Measure marketing, advertising and communications effectiveness |
| Marketing Analytics | Market Research Analysts | 5436 | 3.12 | Forecast and track marketing/sales trends, analyzing collected data |

## Five skills deliberately left unmapped

| Actual Tier-1 label | Final decision |
|---|---|
| Content Marketing | Rejected: CMS usage is too generic to establish content marketing work. |
| Marketing Communications | Rejected: measuring communications effectiveness does not establish creating/managing communications. |
| Search Engine Optimization | Unsupported: no explicit SEO evidence in the reviewed material. |
| Brand Management | Unsupported: no specific brand-management evidence. |
| Conversion Rate Optimization | Unsupported: no specific conversion-optimization evidence. |

No pending Marketing skill approvals remain from this review. Do not force these five dimensions or reconsider rejected interpretations without a new explicit instruction. These decisions are recorded in `MARKETING_UNMAPPED` in the alignment configuration. They concern occupation-derived additions, not deleting independently sourced employer skills.

## Verification and boundaries

- Policy and approved proxies: `backend/onet_policy.py`.
- Mapping adapter: `backend/prepare_onet.py`, shared by local, API and cached occupation-profile processing.
- Generated occupation vectors: `backend/data/onet-corpus.json`.
- Source validation and raw-file hashes: `ONET_COMPATIBILITY_REPORT.json`.
- Rebuild: `python -m backend.prepare_onet`.
- Tests: `python -m unittest discover -s tests -v`.
- Count verification: intersect the 15 Marketing Tier-1 labels with the union of the two occupations' `track_vectors["marketing"]` keys.
- Only real job listings with an unambiguous supported occupation join are enriched. Source job values, IDs, application URLs and listing count are preserved.
- Other occupations and tracks are unaffected by these proxies. Question banks, taxonomy, cosine scoring, adaptive selection and the 15-question cap are unchanged.
- The requested Essential/Transferable/Software tables have no literal equivalents covering these 15 labels. Direct task evidence plus the six approved proxy interpretations provide this 10/15 coverage; it is not a claim of 10 exact O*NET element-name matches.

Source: O*NET 31.0, National Center for O*NET Development, https://www.onetcenter.org/database.html, CC BY 4.0. Application mappings are not an O*NET endorsement.
