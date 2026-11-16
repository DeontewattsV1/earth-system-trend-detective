# NASA POWER MERRA-2 Reanalysis

## Summary

NASA POWER serves monthly variables from NASA GMAO's MERRA-2 reanalysis: a weather model continuously corrected by satellite and in-situ observations.

## Access Methods

REST API, no login: https://power.larc.nasa.gov/api/temporal/monthly/regional (one parameter per call, 2°–10° boxes).

## Data Schema

Monthly values keyed YYYYMM per grid point; this project averages grid points with cos(latitude) area weights.

## Coverage

- **Jurisdiction**: Global, 0.5° x 0.625°
- **Time range**: 1981–2025 analysed
- **Update frequency**: Monthly

## Cross-Reference Potential

- **GISTEMP v4 Station Temperature** for 2 m temperature
- **GPCP v2.3 Precipitation** for precipitation

## Data Quality

Reanalysis is a model product: trends can be affected by changes in the observing system and by missing processes (e.g. irrigation).
