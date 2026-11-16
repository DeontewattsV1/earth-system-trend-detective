# NASA Space Apps 2026 — Project Page Fields

**Team:** Frontier Intelligence Lab

**Project Name:** Earth System Trend Detective

**Selected Challenge:** Be An Earth System Trend Detective!

## High-Level Project Summary

Earth System Trend Detective is an interactive Earth-data analysis tool that lets users choose a NASA environmental variable, a geographic region, and a time span. It charts the observed or modeled monthly series, removes the seasonal cycle, estimates a linear trend and 95% confidence interval, and applies two statistical tests. Where available, it checks the trend against a second NASA-associated data product and records agreement or disagreement. The current bundled snapshot covers seven study regions and 11 variables, with reproducible Python/JavaScript calculations. The project is designed to help students and the science-curious public understand local Earth-system change and uncertainty.

## Detailed Project Description

**What we built:** A self-contained HTML/JavaScript application with seven mapped study regions, 11 variables, year selection, trend visualization, significance testing, an evidence ledger, guided examples, and a NASA POWER request builder with JSON-file import. Python scripts acquire NASA POWER data, compute area-weighted regional means, analyze trends, process GISTEMP/GPCP comparison products and build the self-contained HTML. An evidence wiki is produced using a documented third-party parser format.

**Method:** Seasonal anomalies are calculated by subtracting calendar-month means. Trend magnitude is estimated by ordinary least squares in physical units per decade. The reported t-test and confidence interval use an AR(1)-adjusted effective sample size; a seasonal Mann-Kendall test provides a second statistical test, and Sen's slope offers a robust slope estimate. Results are classed significant when both p values are below 0.05, suggestive under the stated partial-significance criterion, or not significant otherwise. The selected range is recalculated in the browser.

**What the user learns:** Regional changes may have different directions and magnitudes even for the same variable. Illustrative cases include increasing Sahel rainfall, decreasing Amazon rainfall, and a disagreement between two temperature datasets for Delhi. These are results of the particular methods and datasets, not universal scientific conclusions.

**Constraints and limits:** The downloaded data snapshot is fixed at the recorded retrieval time. The browser has no live NASA API access; fresh data must be downloaded separately and imported. The comparison products are not always fully independent (notably rainfall). OLS-based linear trends omit structural breaks and ENSO cycles; some p-values are vulnerable to autocorrelation and multiple comparisons. 'Contradicted' is a product-comparison label and, in the Delhi case, the primary slope is only suggestive rather than statistically significant under both tests.

**Implementation:** Python, NumPy/SciPy, HTML, CSS, JavaScript, SVG, NASA POWER monthly regional API, GISTEMP and GPCP products. Supporting checks: a locally rerun 72/72 JavaScript/Python parity check and an independent statsmodels comparison for 72 OLS slopes. Full raw NASA responses are not included in the submitted ZIP, so source-file hash authentication is not independently reproduced here.

## NASA Data and Resources

1. NASA POWER (Prediction Of Worldwide Energy Resources), monthly regional API, https://power.larc.nasa.gov/ — MERRA-2 reanalysis data for temperature, precipitation, evaporation, root-zone moisture, humidity, wind and snow depth.
2. NASA CERES SYN1deg through POWER for sunlight and cloud amount, restricted to 2001–2025 for consistent source period.
3. NASA GISS GISTEMP v4, https://data.giss.nasa.gov/gistemp/ — gridded temperature anomalies used as a comparison product.
4. GPCP monthly v2.3, distributed by NOAA NCEI, https://www.ncei.noaa.gov/data/global-precipitation-climatology-project-gpcp-monthly/access/ — precipitation comparison.

## Space Agency Partner Data and Other References

Natural Earth 110 m land outlines (public domain), https://www.naturalearthdata.com/ . OpenPlanter (MIT licensed, subject to checking its official license), https://github.com/ShinMegamiBoson/OpenPlanter ; only its wiki format/graph parser was used, not the LLM agent. Python scientific dependencies: NumPy, SciPy, statsmodels and pymannkendall for reference tests; networkx for graph processing. Statistical methods attributed in the README: Santer et al. (2000); Hirsch et al. (1982); Weatherhead et al. (1998). Verify exact bibliographic references before public release.

## Use of Super Intelligence / AI tools

Yes. AI-assisted development was used for software implementation, documentation, analysis explanation, design decisions and preparation of presentation materials. The NASA observations and model data are real external sources, not synthetic measurements. The program's quantitative outputs are generated by deterministic code, and reproducibility checks are provided. Visible disclosures are included on the audited deck and app. Exact concept origination and final originality certification must be confirmed by the team; do not claim that an AI-originated solution idea was independently human-originated. The earlier AI-generated team logo is not used in this package.

## Link to Final Project

**REQUIRES PUBLIC URL.** Upload `dist/index.html` as a web page or into a public repository and confirm it opens in private/incognito mode without login. A sandbox file link is not a compliant public competition URL.

## Link to Project Demo

**REQUIRES PUBLIC URL.** Publish `Earth_System_Trend_Detective_Audit_Corrected_7slides.pdf` or `demo_walkthrough.mp4` (28.57 s). Verify the public link in private/incognito mode and check the video/slide limitations.

## Submission Verification

Team/event registration, actual live project/demo URLs, terms and originality confirmations, and clicking Submit for Judging have **NOT BEEN VERIFIED**. Do not claim submission was completed based on a downloaded ZIP or Save Progress alone.
