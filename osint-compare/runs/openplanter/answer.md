Summary of robust and unverified Earth-system trends by region, with citations to ledger row IDs:

1. Svalbard & Barents Sea (Arctic):
- Robust (verified, corroborated by NASA GISTEMP):
  - Air temperature (2 m) increased by +0.6793 °C/decade (1981-2025) [ledger row svalbard:T2M].
    - Primary p-values extremely significant (p_ttest=1.67e-10, p_mk=4.17e-30).
    - Corroborated by independent NASA GISTEMP product with similar slope (+0.7434 °C/decade) and significance (p=1.5e-22).
    - Anomaly correlation 0.8605 indicates strong agreement.
- Likely chance/artifact or unverified (single source, no independent corroboration):
  - Daily max temperature increase +0.315 °C/decade [svalbard:T2M_MAX].
  - Precipitation bias-corrected +0.0178 mm/day/decade not significant in primary but significant in GPCP satellite product [svalbard:PRECTOTCORR].
  - Evaporation from land +0.00845 mm/day/decade, suggestive but unverified [svalbard:EVLAND].
  - Root-zone soil wetness +0.00724 1/decade, significant but unverified [svalbard:GWETROOT].
  - Relative humidity decreased -0.416 %/decade, significant but unverified [svalbard:RH2M].
  - Specific humidity increased +0.122 g/kg/decade, significant but unverified [svalbard:QV2M].
  - Wind speed, sunlight, cloud amount, snow depth trends unverified or not significant.

2. Central Sahel (Niger–Mali–Burkina Faso):
- Robust (verified, corroborated by NASA GISTEMP and GPCP):
  - Air temperature increased +0.124 °C/decade (1981-2025) [sahel:T2M].
  - Precipitation bias-corrected increased +0.117 mm/day/decade [sahel:PRECTOTCORR].
- Unverified but significant in primary source only:
  - Evaporation from land +0.0727 mm/day/decade [sahel:EVLAND].
  - Root-zone soil wetness +0.00831 1/decade [sahel:GWETROOT].
  - Relative humidity +0.933 %/decade [sahel:RH2M].
  - Specific humidity +0.249 g/kg/decade [sahel:QV2M].
  - Wind speed decreased -0.0443 m/s/decade [sahel:WS10M].
  - Sunlight decreased -0.199 MJ/m^2/day/decade [sahel:ALLSKY_SFC_SW_DWN].

3. Southern Amazon (Rondônia–Mato Grosso):
- Robust (verified):
  - Air temperature increased +0.482 °C/decade [amazon:T2M].
  - Precipitation decreased -0.574 mm/day/decade [amazon:PRECTOTCORR].
- Unverified:
  - Root-zone soil wetness decreased -0.0286 1/decade [amazon:GWETROOT].
  - Cloud amount decreased -3.86 %/decade [amazon:CLOUD_AMT].

4. California Central Valley & Sierra Nevada:
- Robust (verified):
  - Air temperature increased +0.314 °C/decade [california:T2M].
- Unverified:
  - Precipitation decreased -0.0434 mm/day/decade [california:PRECTOTCORR].

5. Delhi & Upper Indo-Gangetic Plain:
- Contradicted:
  - Air temperature decreased -0.0993 °C/decade [delhi:T2M].
- Unverified:
  - Precipitation increased +0.136 mm/day/decade [delhi:PRECTOTCORR].
  - Relative humidity increased +0.933 %/decade [delhi:RH2M].
  - Sunlight decreased -0.199 MJ/m^2/day/decade [delhi:ALLSKY_SFC_SW_DWN].

6. Murray–Darling Basin (SE Australia):
- Verified:
  - Air temperature increased +0.214 °C/decade [murray:T2M].
  - Precipitation decreased -0.034 mm/day/decade [murray:PRECTOTCORR].
- Unverified:
  - Root-zone soil wetness decreased -0.004 1/decade [murray:GWETROOT].

7. San Francisco Bay–Delta Estuary:
- Verified:
  - Air temperature increased +0.254 °C/decade [sfbay:T2M].
  - Precipitation decreased -0.034 mm/day/decade [sfbay:PRECTOTCORR].

Methodology and Evidence Chain:
- Robust trends are those marked "verified" in the ledger, meaning the primary trend is statistically significant (p<0.01) and corroborated by an independent NASA product (e.g. GISTEMP for temperature, GPCP for precipitation).
- Unverified trends are significant in the primary source but lack independent corroboration or have contradictory evidence.
- Contradicted trends have conflicting evidence from independent NASA products.
- The ledger rows (e.g. svalbard:T2M) provide numeric slope estimates, p-values, and corroboration status.
- The evidence_graph.json links findings to NASA products and their verification status.
- Results.json contains detailed statistics including confidence intervals and p-values supporting the verdicts.

Recommendations for users:
- Focus on verified trends for robust regional climate change signals, e.g. warming in Svalbard, Sahel, Amazon, California.
- Treat unverified trends cautiously; seek additional independent datasets or longer time series to confirm.
- For precipitation trends with mixed significance (e.g. Svalbard), collect more years or use alternative satellite products.
- Investigate contradicted trends (e.g. Delhi temperature) with further data or alternative methods.
- Check anomaly correlations and confidence intervals to assess trend reliability.
- Consider local factors and data quality issues that may affect unverified or contradictory results.

This summary is based solely on the provided ledger.csv, ledger.md, results.json, and evidence_graph.json files.
