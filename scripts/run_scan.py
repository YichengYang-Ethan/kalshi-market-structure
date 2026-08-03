#!/usr/bin/env python3
"""Run the full constraint scan against the current census snapshot."""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.universe import iter_all_events, load_series
from kalshi_structure.scan import scan

events = list(iter_all_events())
series = load_series()
print(f"scanning {len(events):,} events / "
      f"{sum(len(e['markets']) for e in events):,} markets ...")
rep = scan(events, series)
print(f"\nchecks: {rep.checks:,}   net-positive hits: {len(rep.hits)}   skipped: {dict(rep.skipped)}")
by_fam = Counter(h.family for h in rep.hits)
print("by family:", dict(by_fam))
by_board = Counter(h.board for h in rep.hits)
print("by board :", dict(by_board))
total = sum(h.net for h in rep.hits)
print(f"sum of net edges (per-contract, unsized): {total:.4f}\n")
for h in rep.hits[:40]:
    legs = h.legs if len(h.legs) <= 2 else (h.legs[0], f"...{len(h.legs)} legs")
    print(f"  [{h.family:<16}] net={h.net:+.4f} gross={h.gross:+.4f} {h.board:<12} {' -> '.join(legs)} {h.note[:50]}")
