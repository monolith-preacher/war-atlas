#!/usr/bin/env python3
"""Download and simplify the open geodata shipped with War Atlas.

Outputs (committed to the repository so that the app runs offline):
  data/boundaries/world_1914.geojson, world_1938.geojson
      from aourednik/historical-basemaps (GPL-3.0) — approximate historical borders
  frontend/public/basemap/land.geojson, lakes.geojson, rivers.geojson
      from Natural Earth 1:50m (public domain) — physical basemap without modern borders

Usage:  python scripts/prepare_geodata.py [--download-dir DIR]
Requires: shapely (installed with the backend requirements).
"""

import argparse
import json
import pathlib
import urllib.request

from shapely.geometry import mapping, shape
from shapely.validation import make_valid

ROOT = pathlib.Path(__file__).resolve().parents[1]
HB = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson/world_{year}.geojson"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{name}.geojson"

HISTORICAL_YEARS = [1914, 1938]
BOUNDARY_TOLERANCE = 0.01  # degrees (~1 km); the source precision is far coarser anyway
BASEMAP = {
    "land": ("ne_50m_land", 0.005),
    "lakes": ("ne_50m_lakes", 0.005),
    "rivers": ("ne_50m_rivers_lake_centerlines", 0.002),
}


def fetch(url: str, dest: pathlib.Path) -> dict:
    if not dest.exists():
        print(f"downloading {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "WarAtlas geodata script"})
        dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return json.loads(dest.read_text())


def round_coords(obj, ndigits=4):
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, (list, tuple)):
        return [round_coords(o, ndigits) for o in obj]
    return obj


def simplify_features(features, tolerance, keep_props=None):
    out = []
    for f in features:
        if not f.get("geometry"):
            continue
        geom = make_valid(shape(f["geometry"])).simplify(tolerance, preserve_topology=True)
        if geom.is_empty:
            continue
        g = mapping(geom)
        props = f.get("properties") or {}
        if keep_props is not None:
            props = {k: props.get(k) for k in keep_props}
        out.append({"type": "Feature", "properties": props, "geometry": {"type": g["type"], "coordinates": round_coords(g["coordinates"])}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--download-dir", default=str(ROOT / ".geodata-cache"))
    args = ap.parse_args()
    cache = pathlib.Path(args.download_dir)
    cache.mkdir(parents=True, exist_ok=True)

    bdir = ROOT / "data" / "boundaries"
    bdir.mkdir(parents=True, exist_ok=True)
    for year in HISTORICAL_YEARS:
        src = fetch(HB.format(year=year), cache / f"world_{year}.geojson")
        feats = simplify_features(src["features"], BOUNDARY_TOLERANCE, ["NAME", "SUBJECTO", "PARTOF", "BORDERPRECISION"])
        feats = [f for f in feats if f["properties"].get("NAME")]
        (bdir / f"world_{year}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
        print(f"world_{year}: {len(feats)} features")

    mdir = ROOT / "frontend" / "public" / "basemap"
    mdir.mkdir(parents=True, exist_ok=True)
    for out_name, (ne_name, tol) in BASEMAP.items():
        src = fetch(NE.format(name=ne_name), cache / f"{ne_name}.geojson")
        keep = ["name"] if out_name != "land" else []
        feats = simplify_features(src["features"], tol, keep)
        (mdir / f"{out_name}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
        print(f"{out_name}: {len(feats)} features")


if __name__ == "__main__":
    main()
