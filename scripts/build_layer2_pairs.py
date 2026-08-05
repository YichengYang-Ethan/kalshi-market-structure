#!/usr/bin/env python3
"""Emit the Layer-2 (shared-driver) pair universes as machine-readable CSVs.

These are the starting datasets for correlation research: identifiers only, no prices.
"""
import csv, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kalshi_structure.universe import iter_all_events

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "layer2")
os.makedirs(OUT, exist_ok=True)

games = defaultdict(set)
races = defaultdict(set)
windows = defaultdict(set)
releases = defaultdict(set)

# Ticker-grammar matching alone drags in impostors (external audit, 2026-08-04):
# cross-underlying relative contracts are not one price path, index-composition and
# prefix-collision series are not the release stream ("FED" caught federal-employee
# markets about Trump, "GDP" caught boom/manufacturing novelty questions).
WINDOW_SUFFIX_EXCLUDE = re.compile(r"VS[A-Z]+$|^AREMOVE$")
RELEASE_SERIES_EXCLUDE = {"KXFEDTWEETS", "KXFEDEMPLOYEES", "KXGDPSHAREMANU", "KXGDPUSMAX"}

for e in iter_all_events():
    tk = e["event_ticker"]; cat = e.get("category", "")
    if cat == "Sports":
        m = re.match(r"(KX[A-Z0-9]+?)-(\d{2}[A-Z]{3}\d{2}[A-Z0-9]*)$", tk)
        if m:
            games[m.group(2)].add(m.group(1))
    elif cat in ("Elections", "Politics"):
        for pat, kind in [(r"KXMIDTERMMOV-(\w+?)[RD]$", "margin"),
                          (r"KXMIDTERMVOTETURN-(\w+)$", "turnout"),
                          (r"KXHOUSERACE-(\w+)-26$", "winner"),
                          (r"HOUSE([A-Z]{2}\d{2})-26$", "winner"),
                          (r"SENATE([A-Z]{2})-26$", "winner_senate"),
                          (r"GOVPARTY([A-Z]{2})-26$", "winner_governor")]:
            m = re.match(pat, tk)
            if m:
                races[m.group(1)].add(f"{kind}:{tk}")
    elif cat in ("Crypto", "Financials", "Commodities"):
        m = re.match(r"KX(BTC|ETH|SOL|XRP|DOGE|BNB|HYPE|SHIBA|ZEC|NEAR|INX|NASDAQ100|DJI|"
                     r"WTI|SILVER|NATGAS|COPPER|PLATINUM|GOLD|EURUSD|USDJPY|GBPUSD)([A-Z]*)-", tk)
        if m:
            suf = m.group(2) or "BASE"
            if not WINDOW_SUFFIX_EXCLUDE.search(suf):
                windows[m.group(1)].add(suf)
    if cat == "Economics":
        m = re.match(r"KX(ECONSTAT)?(CPI|U3|PAYROLLS|GDP|FED|RATECUT)\w*-", tk)
        if m:
            series = tk.split("-")[0]
            if series not in RELEASE_SERIES_EXCLUDE:
                releases[m.group(2)].add(series)

with open(f"{OUT}/game_clusters.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["game_key", "n_market_types", "series"])
    for k, v in sorted(games.items(), key=lambda kv: -len(kv[1])):
        if len(v) >= 2:
            w.writerow([k, len(v), "|".join(sorted(v))])

with open(f"{OUT}/race_clusters.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["race_key", "n_families", "members"])
    for k, v in sorted(races.items(), key=lambda kv: -len(kv[1])):
        if len(v) >= 2:
            w.writerow([k, len(v), "|".join(sorted(v))])

with open(f"{OUT}/underlying_windows.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["underlying", "n_window_series", "window_suffixes"])
    for k, v in sorted(windows.items(), key=lambda kv: -len(kv[1])):
        if len(v) >= 2:
            w.writerow([k, len(v), "|".join(sorted(v))])

with open(f"{OUT}/release_families.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["release", "n_series", "series"])
    for k, v in sorted(releases.items(), key=lambda kv: -len(kv[1])):
        if len(v) >= 2:
            w.writerow([k, len(v), "|".join(sorted(v))])

for name in ("game_clusters", "race_clusters", "underlying_windows", "release_families"):
    n = sum(1 for _ in open(f"{OUT}/{name}.csv")) - 1
    print(f"  {name}.csv: {n} rows")
