# GPCP v2.3 Precipitation

## Summary

Global Precipitation Climatology Project monthly analysis (NASA GSFC / University of Maryland) merging satellite estimates with rain gauges.

## Access Methods

https://www.ncei.noaa.gov/data/global-precipitation-climatology-project-gpcp-monthly/access/ (netCDF per month).

## Data Schema

Monthly values keyed YYYYMM per grid point; this project averages grid points with cos(latitude) area weights.

## Coverage

- **Jurisdiction**: Global, 2.5° grid
- **Time range**: 1981–2025 analysed
- **Update frequency**: Monthly

## Cross-Reference Potential

- **NASA POWER MERRA-2 Reanalysis** (independent check of PRECTOTCORR)

## Data Quality

Coarse 2.5° cells; small regions are covered by 1–4 cells. MERRA-2 corrected precipitation is partly nudged toward observations, so agreement is not fully independent.
