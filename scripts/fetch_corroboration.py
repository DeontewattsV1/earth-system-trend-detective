"""Independent corroboration sources, reduced to the same regions.

  * NASA GISS GISTEMP v4 (1200 km smoothing, GHCNv4 + ERSSTv5) — station/ship
    temperature anomalies, independent of the MERRA-2 reanalysis.
  * GPCP v2.3 monthly (NASA GSFC / UMD, distributed by NOAA NCEI) — satellite +
    rain-gauge precipitation.

Usage: python fetch_corroboration.py DATA_DIR
Writes DATA_DIR/corroboration.json
"""
import hashlib, json, re, sys, tempfile, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import netCDF4 as nc

sys.path.insert(0, str(Path(__file__).parent))
from regions import REGIONS, START_YEAR, END_YEAR

GPCP_ROOT = "https://www.ncei.noaa.gov/data/global-precipitation-climatology-project-gpcp-monthly/access/"
GISTEMP_URL = "https://data.giss.nasa.gov/pub/gistemp/gistemp1200_GHCNv4_ERSSTv5.nc.gz"


def overlap_weights(lats, lons, dlat, dlon, box_lat, box_lon):
    """Area weights = (fraction of each grid cell inside the box) x cos(lat)."""
    la0, la1 = box_lat; lo0, lo1 = box_lon
    flat = np.clip(np.minimum(lats + dlat / 2, la1) - np.maximum(lats - dlat / 2, la0), 0, None) / dlat
    flon = np.clip(np.minimum(lons + dlon / 2, lo1) - np.maximum(lons - dlon / 2, lo0), 0, None) / dlon
    return np.outer(flat * np.cos(np.radians(lats)), flon)


def wmean(field, w):
    f = np.ma.masked_invalid(np.ma.asarray(field, dtype=float))
    m = ~np.ma.getmaskarray(f) & (w > 0)
    if not m.any():
        return None
    return float((f.filled(0) * w * m).sum() / (w * m).sum())


def gistemp(data_dir):
    import gzip, shutil
    gz = data_dir / "gistemp" / "gistemp1200_GHCNv4_ERSSTv5.nc.gz"
    path = gz.with_suffix("")
    if not gz.exists():
        gz.parent.mkdir(parents=True, exist_ok=True)
        gz.write_bytes(urllib.request.urlopen(GISTEMP_URL, timeout=300).read())
    if not path.exists():
        with gzip.open(gz) as src, open(path, "wb") as dst:
            shutil.copyfileobj(src, dst)
    d = nc.Dataset(path)
    lats, lons = d["lat"][:].data, d["lon"][:].data
    times = nc.num2date(d["time"][:], d["time"].units)
    ta = d["tempanomaly"]
    out = {}
    for reg, r in REGIONS.items():
        w = overlap_weights(lats, lons, 2.0, 2.0, r["lat"], r["lon"])
        rows = []
        for i, t in enumerate(times):
            if START_YEAR <= t.year <= END_YEAR:
                v = wmean(ta[i], w)
                if v is not None:
                    rows.append([f"{t.year}-{t.month:02d}", round(v, 4)])
        out[reg] = rows
    sha = hashlib.sha256((data_dir / "gistemp" / "gistemp1200_GHCNv4_ERSSTv5.nc.gz").read_bytes()).hexdigest()
    return dict(product="NASA GISS Surface Temperature Analysis v4 (GISTEMP), 1200 km smoothing",
                variable="tempanomaly", units="°C anomaly vs 1951–1980", url=GISTEMP_URL,
                file_history=d.history, sha256=sha, series=out)


def list_gpcp(year):
    html = urllib.request.urlopen(f"{GPCP_ROOT}{year}/", timeout=60).read().decode()
    return sorted(set(re.findall(r'href="(gpcp_v02r03_monthly_d\d{6}_c\d{8}\.nc)"', html)))


def download(year_fname):
    year, fname = year_fname
    url = f"{GPCP_ROOT}{year}/{fname}"
    for attempt in range(4):
        try:
            return fname, url, urllib.request.urlopen(url, timeout=120).read()
        except Exception:
            if attempt == 3:
                raise


def gpcp_file(fname, url, body):
    # HDF5 is not thread-safe: parse sequentially in the main thread
    with tempfile.NamedTemporaryFile(suffix=".nc") as tmp:
        tmp.write(body); tmp.flush()
        d = nc.Dataset(tmp.name)
        lats, lons = d["latitude"][:].data, d["longitude"][:].data
        pr = d["precip"][0]
        lons180 = np.where(lons > 180, lons - 360, lons)
        order = np.argsort(lons180)
        lons180, pr = lons180[order], pr[:, order]
        vals = {reg: wmean(pr, overlap_weights(lats, lons180, 2.5, 2.5, r["lat"], r["lon"]))
                for reg, r in REGIONS.items()}
        d.close()
    ym = re.search(r"_d(\d{4})(\d{2})_", fname)
    return f"{ym.group(1)}-{ym.group(2)}", vals, url, hashlib.sha256(body).hexdigest()


def gpcp():
    files = [(y, f) for y in range(START_YEAR, END_YEAR + 1) for f in list_gpcp(y)]
    with ThreadPoolExecutor(8) as ex:
        res = [gpcp_file(*dl) for dl in ex.map(download, files)]
    out = {reg: [] for reg in REGIONS}
    for ym, vals, _, _ in sorted(res):
        for reg, v in vals.items():
            if v is not None:
                out[reg].append([ym, round(v, 4)])
    manifest = hashlib.sha256("".join(s for *_, s in sorted(res)).encode()).hexdigest()
    return dict(product="Global Precipitation Climatology Project (GPCP) Monthly v2.3 — NASA GSFC/UMD, via NOAA NCEI",
                variable="precip", units="mm/day", url=GPCP_ROOT, n_files=len(res),
                manifest_sha256=manifest, series=out)


if __name__ == "__main__":
    data_dir = Path(sys.argv[1])
    doc = dict(fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               gistemp=gistemp(data_dir), gpcp=gpcp())
    (data_dir / "corroboration.json").write_text(json.dumps(doc, indent=1))
    print({k: len(v) for k, v in doc["gpcp"]["series"].items()}, {k: len(v) for k, v in doc["gistemp"]["series"].items()})
