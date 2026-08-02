#!/usr/bin/env python3
"""Full-exchange census fetch: all open events (nested markets) + all series metadata.
Writes category-sharded JSONL so downstream analysis never loads the whole corpus.
"""
import json, os, time, urllib.request, urllib.parse, gzip, sys
from collections import defaultdict

BASE = "https://api.elections.kalshi.com/trade-api/v2"
OUT = os.path.expanduser("~/Developer/kalshi-research-data")
os.makedirs(OUT, exist_ok=True)

EV_F = ["event_ticker","series_ticker","title","sub_title","category","mutually_exclusive",
        "collateral_return_type","strike_period","settlement_sources"]
MK_F = ["ticker","event_ticker","market_type","title","yes_sub_title","no_sub_title","custom_strike",
        "strike_type","status","result","can_close_early","early_close_condition",
        "open_time","close_time","expiration_time","expected_expiration_time","settlement_timer_seconds",
        "yes_bid_dollars","yes_ask_dollars","no_bid_dollars","no_ask_dollars","last_price_dollars",
        "yes_bid_size_fp","yes_ask_size_fp","volume_fp","volume_24h_fp","open_interest_fp",
        "liquidity_dollars","notional_value_dollars","rules_primary","rules_secondary"]

def get(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sk-research/0.2"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except Exception as e:
            w = min(2 ** i, 30)
            print(f"  retry {i+1}: {e} (sleep {w})", flush=True)
            time.sleep(w)
    raise RuntimeError(url)

def fetch_series():
    """All series metadata in one unfiltered listing (fee model, category, tags, contract terms)."""
    d = get(f"{BASE}/series")
    out = d.get("series") or []
    print(f"  series (unfiltered): {len(out)}", flush=True)
    return out

def fetch_events():
    evs, cursor, page = [], None, 0
    while True:
        page += 1
        q = {"status": "open", "with_nested_markets": "true", "limit": "200"}
        if cursor: q["cursor"] = cursor
        d = get(f"{BASE}/events?{urllib.parse.urlencode(q)}")
        batch = d.get("events", [])
        for ev in batch:
            e = {k: ev.get(k) for k in EV_F}
            e["markets"] = [{k: m.get(k) for k in MK_F} for m in (ev.get("markets") or [])]
            evs.append(e)
        cursor = d.get("cursor")
        if page % 5 == 0 or not cursor:
            print(f"  page {page}: total {len(evs)} events", flush=True)
        if not cursor or not batch: break
        time.sleep(0.15)
    return evs

if __name__ == "__main__":
    t0 = time.time()
    print("== series ==", flush=True)
    series = fetch_series()
    with open(f"{OUT}/series.json", "w") as f:
        json.dump(series, f)
    print(f"series: {len(series)}", flush=True)

    print("== events ==", flush=True)
    evs = fetch_events()
    by_cat = defaultdict(list)
    for e in evs:
        by_cat[(e.get("category") or "NULL").replace("/", "_").replace(" ", "_")].append(e)

    manifest = {"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "n_events": len(evs), "n_markets": sum(len(e["markets"]) for e in evs),
                "n_series": len(series), "categories": {}}
    os.makedirs(f"{OUT}/by_category", exist_ok=True)
    for cat, rows in sorted(by_cat.items()):
        nm = sum(len(r["markets"]) for r in rows)
        manifest["categories"][cat] = {"events": len(rows), "markets": nm}
        with gzip.open(f"{OUT}/by_category/{cat}.jsonl.gz", "wt") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    with open(f"{OUT}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps(manifest, indent=1))
    print(f"DONE {time.time()-t0:.0f}s -> {OUT}", flush=True)
