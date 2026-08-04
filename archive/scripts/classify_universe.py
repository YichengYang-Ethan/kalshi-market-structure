#!/usr/bin/env python3
"""Apply the deterministic taxonomy to every series in the universe and join it back
onto the event and market inventories."""
import csv, json, os, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from kalshi_structure.classify import as_dict, classify_series, coverage
from kalshi_structure.universe import DEFAULT_DATA

OUT = os.path.join(DEFAULT_DATA, "elections_politics")

events = list(csv.DictReader(open(f"{OUT}/events.csv")))
per_series = defaultdict(lambda: {"title": "", "template": Counter(), "src": "",
                                  "freq": "", "close": "", "events": 0, "markets": 0,
                                  "traded_events": 0, "volume": 0.0})
for e in events:
    s = per_series[e["series_ticker"]]
    s["events"] += 1
    s["markets"] += int(e["n_markets"])
    s["traded_events"] += 1 if e["ever_traded"] == "True" else 0
    s["volume"] += float(e["event_volume"] or 0)
    s["template"][e["template"]] += 1
    if not s["title"]:
        s["title"] = e["title"]
    if not s["src"] and e["settlement_sources"]:
        s["src"] = e["settlement_sources"]
    s["freq"] = e["frequency"]
    s["close"] = max(s["close"], e["latest_close"] or "")

rows = []
for tk, s in per_series.items():
    c = classify_series(tk, title=s["title"],
                        template=s["template"].most_common(1)[0][0],
                        settlement_sources=s["src"], frequency=s["freq"],
                        latest_close=s["close"])
    d = as_dict(c)
    d.update(title=s["title"][:90], n_events=s["events"], n_markets=s["markets"],
             traded_events=s["traded_events"], volume=round(s["volume"]),
             dominant_template=s["template"].most_common(1)[0][0])
    rows.append(d)

rows.sort(key=lambda r: -r["volume"])
with open(f"{OUT}/series_classification.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"wrote {OUT}/series_classification.csv ({len(rows)} series)")

from kalshi_structure.classify import Classification
cls = [Classification(**{k: v for k, v in r.items() if k in Classification.__dataclass_fields__}) for r in rows]
cov = coverage(cls)
print("\n=== field coverage (% determined, not defaulted) ===")
for k, v in cov.items():
    print(f"  {k:<24} {v:>5.1f}%")

for field in ("domain", "subject_type", "resolution_authority", "time_class"):
    c = Counter(r[field] for r in rows)
    vol = defaultdict(float)
    for r in rows: vol[r[field]] += r["volume"]
    print(f"\n=== {field} ===")
    for k, n in c.most_common():
        print(f"  {k:<34} {n:>5} series  {vol[k]:>15,.0f} contracts")

unknown = [r for r in rows if r["domain"] == "unknown"]
unknown.sort(key=lambda r: -r["volume"])
print(f"\n=== unresolved domain: {len(unknown)} series (top by volume) ===")
for r in unknown[:15]:
    print(f"  {r['series_ticker']:<24} vol={r['volume']:>12,.0f}  {r['title'][:56]}")
json.dump({"coverage": cov, "n_series": len(rows),
           "unresolved_domain": [r["series_ticker"] for r in unknown]},
          open(f"{OUT}/classification_summary.json", "w"), indent=1)
