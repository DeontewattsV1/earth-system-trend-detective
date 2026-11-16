# Release Audit — 2026-11-15 (America/Los_Angeles)

Status: **LOCALLY TESTED; PUBLIC REGISTRATION AND JUDGING SUBMISSION NOT VERIFIED**.

| Check | Result | Evidence / limitation |
|---|---|---|
| ZIP archive opened, 77 data series | PASS | 7 regions × 11 variables in `data/series.json` |
| Applicable analysis series | PASS | 72; 5 excluded by methodology |
| Reported verdict counts | PASS | 42 significant; 11 suggestive; 19 not significant |
| Python result reproduction from packaged reduced source data | PASS | `python scripts/analyze.py data` generated same JSON object as provided ZIP |
| Browser/Python statistic parity | PASS | `node tests/test_parity.mjs`: 72 cases, no verdict mismatches |
| Demo caption numbers | PASS | `node tests/check_demos.mjs` |
| Independent OLS slope check | PASS | statsmodels 72 cases; maximum absolute slope deviation ~4.2×10⁻¹⁴ units/decade |
| Reference Mann-Kendall regression | NOT RUN | `pymannkendall` unavailable here; original prior-test claim is not independently certified in this audit |
| NASA raw response SHA verification | NOT RUN | `data/raw` and original 540 GPCP file bytes omitted from supplied ZIP |
| Live NASA API refresh | NOT RUN | No original raw responses; no re-fetch in this local audit |
| 30-second demo requirement | PASS | ffprobe: 28.5667 seconds |
| 7-slide limit | PASS | corrected deck and PDF both 7 slides |
| Visible AI presentation disclosure | PASS | corrected deck footer all 7 slides |
| Headless Chromium runtime smoke test | PASS | 7 regions, 15 variable chips, valid chart, click interaction and zero JavaScript page errors |
| Actual app deployment link | NOT VERIFIED | URL not supplied; public search not sufficient to establish this project |
| Actual demo public link | NOT VERIFIED | URL not supplied |
| Team enrollment and final Submit for Judging | NOT VERIFIED | Authentication required on organizer website |

**Statistical cautions:** The `contradicted` code classifies a suggestive, negative Delhi primary temperature slope against a significant positive GISTEMP comparison; this is a directional disagreement, not definitive falsification of an established significant negative trend. The rain comparison is not fully independent of MERRA-2 bias correction. The seasonal Mann-Kendall test does not independently adjust for serial correlation; users should not treat p-values as proof of causal mechanisms. At a per-test cutoff of 0.05, multiple tests create false discovery exposure. A supplementary Benjamini–Hochberg procedure, applied separately to the OLS and MK p-value families, retained 41 of the 42 raw jointly significant results; this sensitivity check does not cure every statistical dependency assumption.

**Originality:** Local test results establish software coherence, not discovery novelty or NASA endorsement. The scientific methods are established prior art; the implemented integration is an application. Author/presenting participant status and permitted SI provenance require team confirmation.

**Build/metadata:** AI assistance is declared in `AI_DISCLOSURE.md`, `ai_assistance.json`, and the self-contained HTML header/footer. Dataset snapshot dates of 2026-11-16 UTC correspond to 2026-11-15 local Pacific time.
