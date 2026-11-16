# Earth System Trend Detective — Frontier Intelligence Lab

**Live app:** https://deontewattsv1.github.io/earth-system-trend-detective/  
**Demo deck (PDF):** https://deontewattsv1.github.io/earth-system-trend-detective/presentation/Demo_7slides_AIdisclosed.pdf  
**Demo video (28s):** https://deontewattsv1.github.io/earth-system-trend-detective/presentation/demo_walkthrough_28s.mp4  
**Source repository:** https://github.com/DeontewattsV1/earth-system-trend-detective

NASA Space Apps challenge *Be an Earth System Trend Detective!* A tool that selects
NASA Earth-science variables, acquires regional data, visualizes the time series,
measures the rate of change and tests its significance. It then checks each claim
against an independent NASA product and labels it verified, unverified or contradicted.

## Reproduce (about 1 minute, no logins)

```bash
pip install numpy scipy netCDF4 networkx statsmodels pymannkendall playwright
git clone --depth 1 https://github.com/ShinMegamiBoson/OpenPlanter.git /tmp/OpenPlanter
python scripts/fetch_power.py data            # NASA POWER: 7 regions x 11 variables, 1981–2025
python scripts/fetch_corroboration.py data    # GISTEMP v4 + GPCP v2.3 (540 monthly files)
python scripts/analyze.py data                # trend tests + evidence ledger -> data/results.json
python scripts/build_wiki.py data wiki /tmp/OpenPlanter   # OpenPlanter-format wiki + graph
python scripts/build_app.py data app <ne_110m_land.geojson> dist/index.html
python tests/test_reference.py                # vs statsmodels / pymannkendall
node tests/test_parity.mjs                    # browser engine vs Python
node tests/check_demos.mjs                    # numbers quoted in demo captions
python scripts/capture.py dist/index.html screenshots demo_input/power_colorado_plateau_T2M.json
```

Land outline: Natural Earth 110 m land (public domain), from
`https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson`.

## Data

| Product | Source | Used for | Access |
|---|---|---|---|
| NASA POWER v2.10.0 | MERRA-2 (NASA GMAO) | T2M, T2M_MAX, PRECTOTCORR, EVLAND, GWETROOT, QV2M, RH2M, WS10M, SNODP | power.larc.nasa.gov monthly regional API |
| NASA POWER v2.10.0 | CERES SYN1deg (GEWEX SRB before 2001) | ALLSKY_SFC_SW_DWN, CLOUD_AMT (2001–2025 only) | same |
| GISTEMP v4 | NASA GISS, GHCNv4 + ERSSTv5 | independent check of T2M | data.giss.nasa.gov |
| GPCP v2.3 | NASA GSFC / UMD via NOAA NCEI | independent check of PRECTOTCORR | ncei.noaa.gov |

Each raw POWER response is stored with its request URL and SHA-256; retrieval times are in
`data/series.json` and `data/corroboration.json`.

## Method

1. Regional mean: cos(latitude)-weighted average of grid points in the box (GISTEMP/GPCP: area-overlap weights).
2. Seasonal cycle removed: each calendar month's mean over the analysed years is subtracted.
3. OLS slope on anomalies; t-test and 95% CI with effective sample size n(1−r1)/(1+r1) (Santer et al., 2000).
4. Seasonal Mann-Kendall (Hirsch et al., 1982) + seasonal Sen slope; Mann-Kendall on annual means.
5. Verdict: significant = both tests p < 0.05; suggestive = one test, or both p < 0.10.
6. Years needed to detect: Weatherhead et al. (1998).
7. Corroboration: verified = independent product significant with the same sign; contradicted = independent product significant with the opposite sign; otherwise unverified.

## Limitations

- Reanalysis trends can drift with changes in the observing system; MERRA-2 can miss processes such as irrigation.
- MERRA-2 corrected precipitation is partly nudged toward observations, so GPCP agreement is not fully independent.
- Linear trends only; no step changes, cycles (ENSO) or non-linear change.
- 72 tests at p < 0.05: about 3–4 significant results are expected by chance.
- GPCP's 2.5° cells mean small regions rest on 1–4 cells.
- Snow depth is marked not applicable where its long-term mean is under 1 cm.
- OpenPlanter is used for its wiki format and graph parser; its LLM agent (needs API keys) was not run.
  The OSINT tool comparison (OpenPlanter vs Flowsint vs GPT Researcher–OpenAleph) is proposed, not done.

## Important snapshot, disclosure and release notes (audit supplement)

This archive contains **reduced monthly series and analysis results**, but **does not include** the original NASA POWER API response bytes (`data/raw/`) or all original GPCP netCDF files. SHA-256 entries are preserved for traceability; an independent reviewer must re-fetch the source files to verify those particular hashes. A full from-empty-directory rebuild needs network access, Python dependencies and access to upstream data services.

AI/SI assistance is disclosed in `AI_DISCLOSURE.md` and `ai_assistance.json`; refer to `RELEASE_AUDIT.md` for checks that passed, were not run, or require action. The HTML file is static and must be hosted at a publicly accessible URL before NASA judging.
