# NASA POWER CERES SYN1deg Radiation

## Summary

Surface sunlight and cloud amount from NASA's CERES instruments (Terra/Aqua) via the SYN1deg product; GEWEX SRB before 2001.

## Access Methods

Same NASA POWER API (parameters ALLSKY_SFC_SW_DWN, CLOUD_AMT).

## Data Schema

Monthly values keyed YYYYMM per grid point; this project averages grid points with cos(latitude) area weights.

## Coverage

- **Jurisdiction**: Global, 1°
- **Time range**: 1981–2025 analysed
- **Update frequency**: Monthly

## Cross-Reference Potential

- **NASA POWER MERRA-2 Reanalysis** shares the API but not the retrieval

## Data Quality

Source changes from SRB to CERES in 2001; this project analyses 2001–2025 only to avoid the splice.
