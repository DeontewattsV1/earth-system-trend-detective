"""Download NASA POWER monthly regional data and build area-weighted regional series.

Usage:  python fetch_power.py OUT_DIR
Writes  OUT_DIR/raw/<region>_<param>.json   (verbatim API response)
        OUT_DIR/series.json                 (regional monthly means + provenance)
"""
import hashlib, json, math, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from regions import REGIONS, VARIABLES, START_YEAR, END_YEAR

BASE = "https://power.larc.nasa.gov/api/temporal/monthly/regional"


def url_for(reg, param):
    r = REGIONS[reg]
    return (f"{BASE}?parameters={param}&community=AG"
            f"&latitude-min={r['lat'][0]}&latitude-max={r['lat'][1]}"
            f"&longitude-min={r['lon'][0]}&longitude-max={r['lon'][1]}"
            f"&start={START_YEAR}&end={END_YEAR}&format=JSON")


def fetch(job, raw_dir):
    reg, param = job
    path = raw_dir / f"{reg}_{param}.json"
    url = url_for(reg, param)
    if not path.exists():
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=300) as resp:
                    body = resp.read()
                json.loads(body)
                path.write_bytes(body)
                break
            except Exception as e:  # retry transient failures
                print("retry", reg, param, e, file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"failed {reg} {param}")
    body = path.read_bytes()
    return reg, param, url, hashlib.sha256(body).hexdigest(), json.loads(body)


def regional_mean(doc, param, fill):
    """cos(latitude)-weighted mean over grid points, per month; skips fill values."""
    sums, wts = {}, {}
    for f in doc["features"]:
        lon, lat = f["geometry"]["coordinates"][:2]
        w = math.cos(math.radians(lat))
        for key, v in f["properties"]["parameter"][param].items():
            if key.endswith("13") or v is None or v == fill:
                continue  # month 13 = annual mean in POWER
            sums[key] = sums.get(key, 0.0) + w * v
            wts[key] = wts.get(key, 0.0) + w
    keys = sorted(sums)
    return [[f"{k[:4]}-{k[4:]}", round(sums[k] / wts[k], 4)] for k in keys], len(doc["features"])


def main(out):
    out = Path(out); raw = out / "raw"; raw.mkdir(parents=True, exist_ok=True)
    jobs = [(r, p) for r in REGIONS for p in VARIABLES]
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda j: fetch(j, raw), jobs))
    series = {}
    for reg, param, url, sha, doc in results:
        fill = doc["header"].get("fill_value", -999.0)
        data, npts = regional_mean(doc, param, fill)
        series.setdefault(reg, {})[param] = dict(
            data=data, n_gridpoints=npts, url=url, sha256=sha,
            api=doc["header"]["api"], sources=doc["header"]["sources"],
            units=doc["parameters"][param]["units"], longname=doc["parameters"][param]["longname"],
        )
    (out / "series.json").write_text(json.dumps(dict(
        fetched_at=fetched_at, provider="NASA POWER (Prediction Of Worldwide Energy Resources), NASA LaRC",
        regions=REGIONS, variables=VARIABLES, series=series), indent=1))
    print("wrote", out / "series.json", len(results), "series")


if __name__ == "__main__":
    main(sys.argv[1])
