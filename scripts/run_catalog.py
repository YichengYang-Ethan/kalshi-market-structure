#!/usr/bin/env python3
"""Enumerate every arbitrage-capable structure on the current snapshot, price-free."""
import csv, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.universe import iter_all_events
from kalshi_structure.catalog import build_catalog

events = list(iter_all_events())
cat = build_catalog(events)
print(f"scanned {len(events):,} events\n")
print(f"arbitrage-capable relations catalogued: {len(cat.relations):,}\n")

fam = Counter(r.family for r in cat.relations)
print("by family:")
for k, v in fam.most_common():
    print(f"  {k:<18} {v:>6,}")

# monitorable pairs (a ladder of n legs is n(n-1)/2 constraints)
pairs = 0
for r in cat.relations:
    if "monitorable pairs" in r.caveat:
        pairs += int(r.caveat.split()[0].replace(",", ""))
print(f"\ntotal monitorable ladder pairs: {pairs:,}")

print("\nby board:")
bd = Counter(r.board for r in cat.relations)
for k, v in bd.most_common():
    print(f"  {k:<24} {v:>6,}")

print("\nnotes (structures examined and excluded):")
for k, v in sorted(cat.notes.items(), key=lambda x: -x[1]):
    print(f"  {k:<26} {v:>6,}")

# write the full catalog
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "relation_catalog.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["family", "kind", "board", "members", "basis", "caveat"])
    for r in cat.relations:
        w.writerow([r.family, r.kind, r.board, " | ".join(r.members), r.basis, r.caveat])
print(f"\nwrote {out} ({len(cat.relations):,} rows)")

# the P2 exhaustive baskets are the price-free synthetic dollars — list them
print("\nP2 exhaustive partitions (the only price-free synthetic $1):")
for r in cat.relations:
    if r.family == "P2-exhaustive":
        print(f"  {r.members[0]:<26} {r.members[1]}")
