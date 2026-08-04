#!/usr/bin/env python3
"""Exchange-wide structural profile: template mix, fee surface, category coherence."""
import gzip, json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kalshi_structure.taxonomy import (classify_event, partition_is_tiled, build_series_profiles)

DATA = os.path.expanduser("~/Developer/kalshi-research-data")

def load_events():
    for fn in sorted(os.listdir(f"{DATA}/by_category")):
        with gzip.open(f"{DATA}/by_category/{fn}", "rt") as f:
            for line in f:
                yield json.loads(line)

series = json.load(open(f"{DATA}/series.json"))
events = list(load_events())
profiles = build_series_profiles(series, events)

print(f"events={len(events)} markets={sum(len(e['markets']) for e in events)} series={len(series)}")

# --- template mix per category ---
tpl = defaultdict(Counter)
tiled = Counter(); untiled = Counter()
for e in events:
    c = e.get("category") or "NULL"
    t = classify_event(e)
    tpl[c][t] += 1
    if t in ("bucket", "threshold") and e.get("mutually_exclusive"):
        (tiled if partition_is_tiled(e) else untiled)[c] += 1

print("\n== template mix by category (events) ==")
kinds = ["binary","deadline","threshold","bucket","entity_menu","combination","unknown"]
print(f"{'category':<24}{'tot':>6}" + "".join(f"{k[:9]:>11}" for k in kinds))
for c, cnt in sorted(tpl.items(), key=lambda kv: -sum(kv[1].values())):
    tot = sum(cnt.values())
    print(f"{c:<24}{tot:>6}" + "".join(f"{cnt.get(k,0):>11}" for k in kinds))

print("\n== mutex partitions: tiled vs untiled (sum-to-one usable?) ==")
for c in sorted(set(tiled) | set(untiled), key=lambda x: -(tiled[x]+untiled[x])):
    print(f"  {c:<24} tiled={tiled[c]:>4}  untiled={untiled[c]:>4}")

# --- series with most events (the workhorses) ---
print("\n== top series by market count ==")
tops = sorted(profiles.values(), key=lambda p: -p.n_markets)[:25]
print(f"{'series':<22}{'cat':<22}{'ev':>5}{'mkts':>7}  {'template':<13}{'fee':<6}{'freq'}")
for p in tops:
    fee = "ZERO" if p.zero_fee else ("MAKER" if p.charges_maker else "std")
    print(f"{p.ticker:<22}{p.category[:20]:<22}{p.n_events:>5}{p.n_markets:>7}  {p.dominant_template:<13}{fee:<6}{p.frequency}")

# --- category coherence: series whose category disagrees with its events' ---
print("\n== category mismatches (series.category vs event.category) ==")
mism = Counter()
examples = defaultdict(list)
for e in events:
    p = profiles.get(e.get("series_ticker"))
    if p and p.category and e.get("category") and p.category != e.get("category"):
        mism[(p.category, e["category"])] += 1
        if len(examples[(p.category, e["category"])]) < 3:
            examples[(p.category, e["category"])].append(e["event_ticker"])
for k, v in mism.most_common(12):
    print(f"  series={k[0]:<22} event={k[1]:<22} n={v:<5} e.g. {', '.join(examples[k])}")
if not mism: print("  (none)")

# --- fee surface with live inventory ---
print("\n== fee surface (series carrying open markets) ==")
live = [p for p in profiles.values() if p.n_markets > 0]
print(f"  live series: {len(live)} / {len(profiles)}")
print(f"  zero-fee live: {[p.ticker for p in live if p.zero_fee]}")
mk = [p for p in live if p.charges_maker]
print(f"  maker-fee live: {len(mk)}")
bycat = Counter(p.category for p in mk)
print(f"    by category: {dict(bycat.most_common())}")
