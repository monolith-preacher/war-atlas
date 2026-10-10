#!/usr/bin/env python3
"""Cross-check every `wikidata_id` in backend/seed/*.json against Wikidata labels.

Prints each QID with its English label next to the seed name so a human can spot a
wrong identifier. Exit code 1 if any QID does not exist.

Usage: python scripts/verify_wikidata_ids.py
"""

import json
import pathlib
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
UA = "WarAtlas seed verification (https://github.com/)"


def collect():
    out = []
    for f in sorted((ROOT / "backend" / "seed").glob("*.json")):
        data = json.loads(f.read_text())
        for section, rows in data.items():
            if not isinstance(rows, list):
                continue
            for r in rows:
                if isinstance(r, dict) and r.get("wikidata_id"):
                    out.append((section, r.get("slug"), r.get("name") or r.get("title"), r["wikidata_id"]))
    return out


def main() -> int:
    rows = collect()
    ids = sorted({r[3] for r in rows})
    labels: dict[str, str | None] = {}
    for i in range(0, len(ids), 50):
        q = urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]), "props": "labels", "languages": "en", "format": "json"})
        req = urllib.request.Request("https://www.wikidata.org/w/api.php?" + q, headers={"User-Agent": UA})
        data = json.load(urllib.request.urlopen(req, timeout=60))
        for qid, ent in data.get("entities", {}).items():
            labels[qid] = None if "missing" in ent else ent.get("labels", {}).get("en", {}).get("value")
    missing = 0
    for section, slug, name, qid in rows:
        label = labels.get(qid)
        flag = "MISSING" if label is None else ""
        missing += bool(flag)
        print(f"{qid:>10}  {section:<14} {slug:<34} {name[:40]:<40} → {label} {flag}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
