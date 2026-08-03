"""Definition of the Elections + Politics research universe.

The `category` field cannot define a scan universe on its own: `series.category` and
`event.category` disagree on over a hundred live events, in both directions. This module
takes the union of the two, which is the only definition that neither drops markets that
belong (a politics question filed under `Financials`) nor silently changes size when
Kalshi re-files a series.

Membership is recorded per event so downstream work can tell why something is in scope.
"""
from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass
from typing import Iterable, Iterator

DEFAULT_DATA = os.path.expanduser("~/Developer/kalshi-research-data")
TARGET_CATEGORIES = frozenset({"Elections", "Politics"})


@dataclass(frozen=True)
class Membership:
    """Why an event is in the universe."""
    by_event_category: bool
    by_series_category: bool

    @property
    def reason(self) -> str:
        if self.by_event_category and self.by_series_category:
            return "both"
        return "event_category" if self.by_event_category else "series_category"


def load_series(data_dir: str = DEFAULT_DATA) -> dict[str, dict]:
    with open(os.path.join(data_dir, "series.json")) as f:
        return {s["ticker"]: s for s in json.load(f)}


def iter_all_events(data_dir: str = DEFAULT_DATA) -> Iterator[dict]:
    """Stream every event in the census without holding the corpus in memory."""
    shard_dir = os.path.join(data_dir, "by_category")
    for name in sorted(os.listdir(shard_dir)):
        if not name.endswith(".jsonl.gz"):
            continue
        with gzip.open(os.path.join(shard_dir, name), "rt") as f:
            for line in f:
                yield json.loads(line)


def in_universe(event: dict, series: dict[str, dict],
                categories: Iterable[str] = TARGET_CATEGORIES) -> Membership | None:
    cats = frozenset(categories)
    by_event = event.get("category") in cats
    series_cat = (series.get(event.get("series_ticker")) or {}).get("category")
    by_series = series_cat in cats
    if not (by_event or by_series):
        return None
    return Membership(by_event_category=by_event, by_series_category=by_series)


def build(data_dir: str = DEFAULT_DATA,
          categories: Iterable[str] = TARGET_CATEGORIES) -> list[dict]:
    """Return every in-scope event, annotated with `_membership` and `_series_category`."""
    series = load_series(data_dir)
    out = []
    for event in iter_all_events(data_dir):
        m = in_universe(event, series, categories)
        if m is None:
            continue
        event["_membership"] = m.reason
        event["_series_category"] = (series.get(event["series_ticker"]) or {}).get("category")
        out.append(event)
    return out


def active_markets(events: Iterable[dict]) -> list[dict]:
    """Markets still open for trading, with their event context attached.

    Finalized legs sit inside open events — 1,301 of them exchange-wide — so anything
    that counts legs or sizes a basket must filter on status first.
    """
    rows = []
    for e in events:
        for m in e.get("markets", []):
            if m.get("status") != "active":
                continue
            rows.append({**m,
                         "series_ticker": e["series_ticker"],
                         "event_title": e.get("title"),
                         "event_category": e.get("category"),
                         "mutually_exclusive": e.get("mutually_exclusive"),
                         "collateral_return_type": e.get("collateral_return_type")})
    return rows
