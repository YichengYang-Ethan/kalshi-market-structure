#!/usr/bin/env python3
"""Emit every count this repository asserts, with the exact public API call that
reproduces it.

The point is independent reproduction, not inspection. Showing a reviewer our data lets
them check internal consistency; it cannot reveal that a whole slice was never fetched.
Publishing the assertions plus the commands to regenerate them lets anyone with a
network connection contradict us.

Contains only aggregate counts and series identifiers, no market data.
"""
import gzip, json, os, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.taxonomy import classify_event, partition_is_tiled, exhaustiveness_evidence
from kalshi_structure.universe import DEFAULT_DATA, iter_all_events, load_series

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "verification.md")
BASE = "https://api.elections.kalshi.com/trade-api/v2"

series = load_series()
events = list(iter_all_events())
by_cat = defaultdict(list)
for e in events:
    by_cat[e.get("category") or "NULL"].append(e)

lines = []
w = lines.append
w("# Verification manifest")
w("")
import json as _json
_snap = _json.load(open(os.path.join(DEFAULT_DATA, "manifest.json")))["fetched_utc"]
w("Every count this repository asserts, and the public API call that reproduces it. No")
w(f"authentication is required for any of these. Snapshot taken {_snap}; counts")
w("drift as Kalshi lists and settles markets, so reproduce the *method*, not the digits —")
w("a mismatch of a few percent on a later date is expected, a mismatch of a category is not.")
w("")
w("## How the corpus was collected")
w("")
w("```")
w(f"GET {BASE}/events?status=open&with_nested_markets=true&limit=200")
w("    then follow the `cursor` field until it is empty (46 pages on this snapshot)")
w(f"GET {BASE}/series")
w("    returns the full catalog in one response, no cursor")
w("```")
w("")
w("Three properties of this that a reviewer should check rather than take on trust:")
w("")
w("1. **`status=open` is the only status fetched.** Settled and unopened events are")
w("   excluded by construction. Any claim here about the exchange is a claim about its")
w("   open surface.")
w("2. **`/events` ignores `category`.** Passing `?category=Elections` returns mixed")
w("   categories — the filter is silently dropped. All category filtering in this repo is")
w("   client-side, which is why the full corpus must be paginated before any board can be")
w("   analysed.")
w("3. **Nested markets come back empty for settled events**, so the same call cannot be")
w("   reused for historical work.")
w("")
w("## Assertions")
w("")
w(f"| Quantity | Value | Reproduce |")
w(f"| --- | ---: | --- |")
w(f"| Open events | {len(events):,} | count rows after full pagination |")
w(f"| Open markets | {sum(len(e['markets']) for e in events):,} | sum `len(event.markets)` |")
w(f"| Active markets | {sum(1 for e in events for m in e['markets'] if m.get('status')=='active'):,} | filter `market.status == 'active'` |")
w(f"| Series in catalog | {len(series):,} | `len(GET /series)` |")
w(f"| Series with open markets | {len({e['series_ticker'] for e in events}):,} | distinct `event.series_ticker` |")
w(f"| Distinct `event.category` values | {len(by_cat)} | `set(event.category)` |")
w(f"| Events where series.category != event.category | {sum(1 for e in events if (series.get(e['series_ticker']) or {}).get('category') not in (None, e.get('category'))):,} | join events to series on ticker |")
w("")
w("## Per-board counts")
w("")
w("Attributed by `event.category`, one board per event.")
w("")
w("| Board | Events | Markets | Active | Ever traded | Series |")
w("| --- | ---: | ---: | ---: | ---: | ---: |")
def f(x):
    try: return float(x or 0)
    except: return 0.0
for cat, evs in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
    mk = [m for e in evs for m in e["markets"]]
    act = [m for m in mk if m.get("status") == "active"]
    tr = sum(1 for m in act if f(m.get("volume_fp")) > 0)
    w(f"| {cat} | {len(evs):,} | {len(mk):,} | {len(act):,} | {tr:,} | {len({e['series_ticker'] for e in evs}):,} |")
w("")
w("## Contract-template mix")
w("")
w("Templates are inferred, not published. `classify_event()` in")
w("`src/kalshi_structure/taxonomy.py` is the definition; disagreement with these numbers")
w("most likely means disagreement with that classifier, which is the useful thing to argue")
w("about.")
w("")
tpl = Counter(classify_event(e) for e in events)
w("| Template | Events |")
w("| --- | ---: |")
for k, v in tpl.most_common():
    w(f"| `{k}` | {v:,} |")
w("")
w("## Partition diagnostics")
w("")
tiled = [e for e in events if e.get("mutually_exclusive")
         and classify_event(e) in ("bucket", "threshold") and partition_is_tiled(e)]
ev = Counter(exhaustiveness_evidence(e) for e in tiled)
w(f"- mutually exclusive events: **{sum(1 for e in events if e.get('mutually_exclusive')):,}**")
w(f"- of those, numeric partitions passing the structural tiling check: **{len(tiled)}**")
w(f"- graded `explicit` / `implicit` / `none`: **{ev['explicit']} / {ev['implicit']} / {ev['none']}**")
w("")
w("The explicit set is the only one where a buy-all-YES basket is supported by contract")
w("text rather than inference. Tickers, so this is checkable one by one:")
w("")
for e in sorted(tiled, key=lambda x: x["event_ticker"]):
    if exhaustiveness_evidence(e) == "explicit":
        w(f"- `{e['event_ticker']}` ({e['series_ticker']})")
w("")
w("## Fee surface")
w("")
zf = sorted(s["ticker"] for s in series.values() if s.get("fee_multiplier") == 0)
mkf = sorted(s["ticker"] for s in series.values() if s.get("fee_type") == "quadratic_with_maker_fees")
live = {e["series_ticker"] for e in events}
w(f"Resolve per series from `GET {BASE}/series/{{ticker}}`; the published PDF has lagged the")
w("API at least twice.")
w("")
w(f"- zero-fee series in catalog: **{len(zf)}** — {', '.join('`'+t+'`' for t in zf)}")
w(f"- of those, currently listing open markets: **{len([t for t in zf if t in live])}**")
w(f"- maker-fee series in catalog: **{len(mkf)}**, live: **{len([t for t in mkf if t in live])}**")
w("")
w("## What would falsify the collection")
w("")
w("- A series with open markets that appears in `GET /series` but in none of our events.")
w("- An `event.category` value we do not list.")
w("- A page of `/events` reachable by cursor that our page count cannot account for.")
w("- A market with `status='active'` inside an event we classify as having none.")
w("")
w("Any of these means the corpus is incomplete and every count above is suspect.")

open(OUT, "w").write("\n".join(lines) + "\n")
print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")
