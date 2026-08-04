#!/usr/bin/env python3
"""Build the Elections + Politics inventory: every event and market, classified
structurally, with a traded/untraded verdict.

Whether a market has ever traded is already carried in the census snapshot
(`volume_fp`, `open_interest_fp`, `volume_24h_fp`), so this needs no extra API calls.
The point of the table is to separate the exchange's live surface from its listed-but-
dead surface before any research uses it.

Writes CSV (portable, diffable) plus a JSON summary. Output goes to the data directory,
never into the repository.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from kalshi_structure.taxonomy import classify_event, partition_is_tiled, quantisation_evidence
from kalshi_structure.universe import DEFAULT_DATA, build, load_series

def slug(categories):
    return "_".join(re.sub(r"[^a-z0-9]+", "", c.lower()) for c in sorted(categories))


def fnum(x) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def price(x):
    try:
        v = float(x)
        return v if 0.0 < v < 1.0 else None
    except (TypeError, ValueError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", nargs="+", default=["Elections", "Politics"],
                    help="API category values; the universe is the union of "
                         "event.category and series.category over these")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    categories = args.categories
    global OUT_DIR
    OUT_DIR = args.out or os.path.join(DEFAULT_DATA, slug(categories))
    os.makedirs(OUT_DIR, exist_ok=True)
    series = load_series()
    events = build(categories=categories)
    if not events:
        print(f"no events for {categories}")
        return

    ev_rows, mk_rows = [], []
    tpl_counts = Counter()
    traded_by_series = defaultdict(lambda: [0, 0])

    for e in events:
        tpl = classify_event(e)
        tpl_counts[tpl] += 1
        legs = e.get("markets", [])
        active = [m for m in legs if m.get("status") == "active"]
        s = series.get(e["series_ticker"]) or {}

        ev_vol = sum(fnum(m.get("volume_fp")) for m in legs)
        ev_oi = sum(fnum(m.get("open_interest_fp")) for m in legs)
        traded_legs = sum(1 for m in active if fnum(m.get("volume_fp")) > 0)
        tiled = partition_is_tiled(e) if tpl in ("bucket", "threshold") else False

        ev_rows.append({
            "event_ticker": e["event_ticker"],
            "series_ticker": e["series_ticker"],
            "title": (e.get("title") or "").replace("\n", " "),
            "sub_title": (e.get("sub_title") or "").replace("\n", " "),
            "event_category": e.get("category") or "",
            "series_category": e.get("_series_category") or "",
            "membership": e.get("_membership"),
            "template": tpl,
            "mutually_exclusive": bool(e.get("mutually_exclusive")),
            "collateral_return_type": e.get("collateral_return_type") or "",
            "n_markets": len(legs),
            "n_active": len(active),
            "n_finalized_inside_open": sum(1 for m in legs if m.get("status") == "finalized"),
            "n_traded_legs": traded_legs,
            "event_volume": round(ev_vol, 2),
            "event_open_interest": round(ev_oi, 2),
            "ever_traded": ev_vol > 0,
            "partition_gaps_consistent": tiled,
            "has_quantisation_evidence": bool(quantisation_evidence(e)) if tiled else False,
            "fee_multiplier": s.get("fee_multiplier", 1),
            "fee_type": s.get("fee_type", ""),
            "frequency": s.get("frequency", ""),
            "settlement_sources": "; ".join(
                x.get("name", "") for x in (e.get("settlement_sources") or []) if isinstance(x, dict)),
            "earliest_close": min((m.get("close_time") or "" for m in active), default=""),
            "latest_close": max((m.get("close_time") or "" for m in active), default=""),
        })

        for m in legs:
            vol = fnum(m.get("volume_fp"))
            yb, ya = price(m.get("yes_bid_dollars")), price(m.get("yes_ask_dollars"))
            st = traded_by_series[e["series_ticker"]]
            st[0] += 1
            st[1] += 1 if vol > 0 else 0
            mk_rows.append({
                "ticker": m["ticker"],
                "event_ticker": e["event_ticker"],
                "series_ticker": e["series_ticker"],
                "yes_sub_title": (m.get("yes_sub_title") or "").replace("\n", " "),
                "status": m.get("status") or "",
                "result": m.get("result") or "",
                "template": tpl,
                "strike_type": m.get("strike_type") or "",
                "yes_bid": yb if yb is not None else "",
                "yes_ask": ya if ya is not None else "",
                "spread": round(ya - yb, 4) if (yb is not None and ya is not None) else "",
                "bid_size": fnum(m.get("yes_bid_size_fp")),
                "ask_size": fnum(m.get("yes_ask_size_fp")),
                "volume": vol,
                "volume_24h": fnum(m.get("volume_24h_fp")),
                "open_interest": fnum(m.get("open_interest_fp")),
                "ever_traded": vol > 0,
                "traded_last_24h": fnum(m.get("volume_24h_fp")) > 0,
                "two_sided": yb is not None and ya is not None,
                "can_close_early": bool(m.get("can_close_early")),
                "early_close_condition": (m.get("early_close_condition") or "").replace("\n", " ")[:200],
                "close_time": m.get("close_time") or "",
                "expiration_time": m.get("expiration_time") or "",
                "settlement_timer_seconds": m.get("settlement_timer_seconds") or "",
            })

    for name, rows in (("events", ev_rows), ("markets", mk_rows)):
        path = os.path.join(OUT_DIR, f"{name}.csv")
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {path}  ({len(rows):,} rows)")

    # Rules text is large and needed for relation work; keep it in its own file.
    rules_path = os.path.join(OUT_DIR, "rules.jsonl")
    with open(rules_path, "w") as f:
        for e in events:
            for m in e.get("markets", []):
                f.write(json.dumps({
                    "ticker": m["ticker"],
                    "event_ticker": e["event_ticker"],
                    "rules_primary": m.get("rules_primary"),
                    "rules_secondary": m.get("rules_secondary"),
                    "custom_strike": m.get("custom_strike"),
                }) + "\n")
    print(f"wrote {rules_path}")

    # Elections and Politics are structurally different boards and must be reported
    # separately: one is template-generated race machinery, the other is one-off
    # binary questions. Aggregating them hides that.
    by_board = defaultdict(lambda: {"events": 0, "series": set(), "active": 0,
                                    "traded": 0, "traded_24h": 0, "volume": 0.0,
                                    "templates": Counter()})
    ev_cat = {r["event_ticker"]: (r["event_category"] or "other") for r in ev_rows}
    for r in ev_rows:
        b = by_board[r["event_category"] or "other"]
        b["events"] += 1
        b["series"].add(r["series_ticker"])
        b["templates"][r["template"]] += 1
    for r in mk_rows:
        if r["status"] != "active":
            continue
        b = by_board[ev_cat.get(r["event_ticker"], "other")]
        b["active"] += 1
        b["traded"] += 1 if r["ever_traded"] else 0
        b["traded_24h"] += 1 if r["traded_last_24h"] else 0
        b["volume"] += r["volume"]
    board_summary = {}
    for name, b in by_board.items():
        board_summary[name] = {
            "events": b["events"], "series": len(b["series"]),
            "events_per_series": round(b["events"] / max(len(b["series"]), 1), 2),
            "active_markets": b["active"],
            "traded": b["traded"],
            "traded_pct": round(b["traded"] / max(b["active"], 1) * 100, 1),
            "traded_24h": b["traded_24h"],
            "volume": round(b["volume"]),
            "template_mix": dict(b["templates"]),
        }

    active_mk = [r for r in mk_rows if r["status"] == "active"]
    traded = [r for r in active_mk if r["ever_traded"]]
    recent = [r for r in active_mk if r["traded_last_24h"]]
    dead_series = [s for s, (tot, tr) in traded_by_series.items() if tr == 0]

    summary = {
        "events": len(ev_rows),
        "markets": len(mk_rows),
        "active_markets": len(active_mk),
        "events_ever_traded": sum(1 for r in ev_rows if r["ever_traded"]),
        "active_markets_ever_traded": len(traded),
        "active_markets_traded_24h": len(recent),
        "series": len(traded_by_series),
        "series_with_zero_traded_markets": len(dead_series),
        "template_mix": dict(tpl_counts),
        "total_volume_contracts": round(sum(r["volume"] for r in mk_rows)),
        "total_open_interest": round(sum(r["open_interest"] for r in mk_rows)),
        "by_board": board_summary,
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
