#!/usr/bin/env python3
"""Publish a structure index: identifiers and derived classifications, no market data.

What this contains, and why each field is publishable:

  event_ticker, series_ticker   public identifiers, not data
  category, mutually_exclusive  exchange metadata that identifies a contract's shape
  template                      OUR inference, not Kalshi's — the thing to be checked
  n_markets, n_active           counts, not values
  ever_traded                   a boolean; the number behind it is not published
  tiled / evidence              OUR diagnostics of partition structure

What it deliberately omits: every price, size, volume and open-interest figure, and all
contract text. Those are the exchange's data. The index exists so a reviewer can check
the classification that every count in this repository rests on, one row at a time,
without either redistributing the corpus or re-fetching 74,000 markets.
"""
import csv, gzip, json, os, sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.taxonomy import (classify_event, exhaustiveness_evidence,
                                       partition_is_tiled)
from kalshi_structure.universe import iter_all_events, load_series

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

def fnum(x):
    try: return float(x or 0)
    except (TypeError, ValueError): return 0.0

def quoted(x):
    """True when a side carries a real price.

    Quote fields are decimal STRINGS, so bool() is not a test of whether a side is
    quoted: bool("0.0000") is True. An earlier version of this file used bool() and
    marked all 73,964 markets two-sided.
    """
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return 0.0 < v < 1.0

series = load_series()
rows, mrows = [], []
for e in iter_all_events():
    tpl = classify_event(e)
    legs = e.get("markets", [])
    active = [m for m in legs if m.get("status") == "active"]
    s = series.get(e["series_ticker"]) or {}
    tiled = partition_is_tiled(e) if tpl in ("bucket", "threshold") else False
    rows.append({
        "event_ticker": e["event_ticker"],
        "series_ticker": e["series_ticker"],
        "event_category": e.get("category") or "",
        "series_category": s.get("category") or "",
        "template": tpl,
        "mutually_exclusive": int(bool(e.get("mutually_exclusive"))),
        "collateral_return_type": e.get("collateral_return_type") or "",
        "n_markets": len(legs),
        "n_active": len(active),
        "n_traded": sum(1 for m in active if fnum(m.get("volume_fp")) > 0),
        "partition_tiled": int(tiled),
        "exhaustiveness": exhaustiveness_evidence(e) if tiled else "",
        "fee_multiplier": s.get("fee_multiplier", 1),
        "fee_type": s.get("fee_type") or "",
        "frequency": s.get("frequency") or "",
    })
    for m in legs:
        mrows.append({
            "ticker": m["ticker"],
            "event_ticker": e["event_ticker"],
            "series_ticker": e["series_ticker"],
            "status": m.get("status") or "",
            "strike_type": m.get("strike_type") or "",
            "template": tpl,
            "ever_traded": int(fnum(m.get("volume_fp")) > 0),
            "traded_24h": int(fnum(m.get("volume_24h_fp")) > 0),
            "two_sided": int(quoted(m.get("yes_bid_dollars")) and quoted(m.get("yes_ask_dollars"))),
            "can_close_early": int(bool(m.get("can_close_early"))),
        })

for name, data in (("events_index", rows), ("markets_index", mrows)):
    path = os.path.join(OUT_DIR, f"{name}.csv.gz")
    with gzip.open(path, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader(); w.writerows(data)
    print(f"wrote {path}  {len(data):,} rows  {os.path.getsize(path)/1e6:.1f} MB")

readme = """# data/

Structure index for the 2026-08-02 census: identifiers and derived classifications only.

| File | Rows | Contents |
| --- | ---: | --- |
| `events_index.csv.gz` | {ne:,} | one row per open event |
| `markets_index.csv.gz` | {nm:,} | one row per market |

**No market data is here.** No prices, no sizes, no volumes, no open interest, no
contract text — those belong to the exchange and its terms bar redistribution. What is
published is the set of identifiers plus the classifications this repository derives from
them, so that the inferences every count rests on can be checked row by row.

`template`, `partition_tiled` and `exhaustiveness` are **inferences**, produced by
`src/kalshi_structure/taxonomy.py`. They are the most likely thing in this repository to
be wrong, which is why they are the part published in full. `ever_traded` and
`traded_24h` are booleans derived from volume; the volumes themselves are not published.

To reconstruct anything else, run `src/kalshi_structure/fetch.py` against the public API.
""".format(ne=len(rows), nm=len(mrows))
open(os.path.join(OUT_DIR, "README.md"), "w").write(readme)
print(f"template mix: {dict(Counter(r['template'] for r in rows))}")
