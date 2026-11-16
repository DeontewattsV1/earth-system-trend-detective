# GISTEMP v4 Station Temperature

## Summary

NASA GISS Surface Temperature Analysis: GHCNv4 weather stations over land plus ERSSTv5 ship/buoy sea-surface temperature, 1200 km smoothing.

## Access Methods

https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz (netCDF, no login).

## Data Schema

Monthly values keyed YYYYMM per grid point; this project averages grid points with cos(latitude) area weights.

## Coverage

- **Jurisdiction**: Global, 2° grid
- **Time range**: 1981–2025 analysed
- **Update frequency**: Monthly

## Cross-Reference Potential

- **NASA POWER MERRA-2 Reanalysis** (independent check of T2M)

## Data Quality

Sparse stations at high latitude and in parts of Africa; values are anomalies vs 1951–1980.
