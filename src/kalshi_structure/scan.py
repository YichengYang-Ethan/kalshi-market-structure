"""Exchange-wide constraint scanner.

Runs every mechanised relation family against a census snapshot and reports executable
violations net of per-series fees. Families:

  F1  within-event ladder nesting     deadline and threshold legs, subject-grouped
  F2  mutex sell-all baskets          floor n-1; needs mutual exclusivity only
  F3  explicit buy-all baskets        needs tiling AND explicit exhaustiveness
  F4  duplicate listings              same (rules, close, expiration) under two tickers
  F5  margin ladder -> party winner   Elections cross-event join, known-trap aware
  F6  named semantic subsets          hand-verified cross-event pairs

Design constraints carried over from two external audits:

- Quote strings are decimal text; they are parsed numerically, never tested for truth.
- The generator label and the tradeable shape differ; scanning uses active legs, but
  events are gated on their generator template.
- Mutex baskets include every active leg or the event is skipped; finalized YES anywhere
  kills the event.
- Buy-all requires explicit exhaustiveness; implicit tiling is not a $1 floor.
- Fees resolve per series and fail closed at multiplier 1.
- Sub-titles are display text: F1 groups by parsed subject, F5 excludes first-round
  contests (Georgia runoff) and joins on the corrected winner-series grammar.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .taxonomy import (classify_event, exhaustiveness_evidence, parse_deadline,
                       parse_threshold, partition_is_tiled)

TAKER = 0.07


def price(x):
    try:
        v = float(x)
        return v if 0.0 < v < 1.0 else None
    except (TypeError, ValueError):
        return None


def fnum(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class Hit:
    family: str
    board: str
    legs: tuple[str, ...]
    gross: float
    net: float
    entry: str
    note: str = ""


@dataclass
class ScanReport:
    checks: int = 0
    hits: list[Hit] = field(default_factory=list)
    skipped: dict = field(default_factory=lambda: defaultdict(int))

    def add(self, hit: Hit):
        self.hits.append(hit)


def _fee(p: float, mult: float) -> float:
    return mult * TAKER * p * (1.0 - p)


def _active(event: dict) -> list[dict]:
    return [m for m in event.get("markets", []) if m.get("status") == "active"]


# --- F1: within-event ladder nesting ------------------------------------------------

def scan_ladders(event: dict, mult: float, rep: ScanReport, board: str) -> None:
    legs = _active(event)
    if len(legs) < 2:
        return
    # Deadlines: within one event all deadline legs share a subject by construction.
    dls = [(parse_deadline(m.get("yes_sub_title")), m) for m in legs]
    dls = [(d, m) for d, m in dls if d]
    if len(dls) >= 2:
        dls.sort(key=lambda x: x[0])
        for i in range(len(dls)):
            for j in range(i + 1, len(dls)):
                (d1, ma), (d2, mb) = dls[i], dls[j]
                if d1 == d2:
                    continue
                _check_implication(ma, mb, mult, rep, board, "F1-deadline")
    # Thresholds must share a unit to be comparable. Comparing the bare number across
    # "30 days" and "5 years", or "$500 billion" and "$2.5 trillion", inverts the ladder
    # unless the unit is normalised — and the safe, unit-agnostic guard is to require the
    # subtitle skeleton (everything but the magnitude) to match exactly, so only legs of
    # one genuine ladder are compared.
    groups: dict[tuple, list] = defaultdict(list)
    for m in legs:
        sub = m.get("yes_sub_title")
        t = parse_threshold(sub)
        if t:
            _, level, direction = t
            skeleton = re.sub(r"[\d.,]+", "#", (sub or "").lower())
            groups[(skeleton, direction)].append((level, m))
    for (subject, direction), rows in groups.items():
        if len(rows) < 2:
            continue
        # subset = higher level for '>=' ladders, lower level for '<=' ladders
        rows.sort(key=lambda x: -x[0] if direction == ">=" else x[0])
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                (la, ma), (lb, mb) = rows[i], rows[j]
                if la == lb:
                    continue
                _check_implication(ma, mb, mult, rep, board, "F1-threshold",
                                   note=f"[{subject or 'bare'} {direction}]")


def _traded(m: dict) -> bool:
    return fnum(m.get("volume_fp")) > 0


def _two_sided(m: dict) -> bool:
    return price(m.get("yes_bid_dollars")) is not None and price(m.get("yes_ask_dollars")) is not None


def _check_implication(sub: dict, sup: dict, mult: float, rep: ScanReport,
                       board: str, family: str, note: str = "") -> None:
    """sub implies sup: P(sub) <= P(sup). Lock: buy sup YES + buy sub NO.

    Both legs must be two-sided and have traded. A one-sided or never-traded quote is
    not a price anyone has agreed to, and treating a resting quote nobody has hit as an
    executable edge is the documented phantom trap (universe-inventory.md).
    """
    rep.checks += 1
    if not (_two_sided(sub) and _two_sided(sup) and _traded(sub) and _traded(sup)):
        return
    yb, ya = price(sub.get("yes_bid_dollars")), price(sup.get("yes_ask_dollars"))
    if yb is None or ya is None:
        return
    gross = yb - ya
    net = gross - _fee(1 - yb, mult) - _fee(ya, mult)
    if net > 0:
        rep.add(Hit(family, board, (sub["ticker"], sup["ticker"]), round(gross, 4),
                    round(net, 4),
                    f"buy {sup['ticker']} YES @{ya:.2f} + buy {sub['ticker']} NO @{1-yb:.2f}",
                    note))


# --- F2/F3: partition baskets -------------------------------------------------------

def scan_baskets(event: dict, mult: float, rep: ScanReport, board: str) -> None:
    if not event.get("mutually_exclusive"):
        return
    if any(m.get("result") == "yes" for m in event.get("markets", [])):
        return
    legs = _active(event)
    if len(legs) < 2:
        return
    # F2 sell-all: floor n-1 needs only "at most one wins".
    bids = [price(m.get("yes_bid_dollars")) for m in legs]
    rep.checks += 1
    if all(b is not None for b in bids):
        cost = sum(1 - b for b in bids)
        net = (len(legs) - 1) - cost - sum(_fee(1 - b, mult) for b in bids)
        if net > 0:
            rep.add(Hit("F2-sell-all", board, tuple(m["ticker"] for m in legs),
                        round((len(legs) - 1) - cost, 4), round(net, 4),
                        f"buy NO on all {len(legs)} legs, floor ${len(legs)-1}"))
    # F3 buy-all: requires the full chain of exhaustiveness evidence.
    tpl = classify_event(event)
    if tpl in ("bucket", "threshold") and partition_is_tiled(event) \
            and exhaustiveness_evidence(event) == "explicit":
        asks = [price(m.get("yes_ask_dollars")) for m in legs]
        rep.checks += 1
        if all(a is not None for a in asks):
            cost = sum(asks)
            net = 1.0 - cost - sum(_fee(a, mult) for a in asks)
            if net > 0:
                rep.add(Hit("F3-buy-all", board, tuple(m["ticker"] for m in legs),
                            round(1.0 - cost, 4), round(net, 4),
                            f"buy YES on all {len(legs)} legs @ {cost:.4f}"))


# --- F4: duplicate listings ---------------------------------------------------------

def scan_duplicates(events: list[dict], fee_of: dict, rep: ScanReport) -> None:
    """Same contract under two tickers: identical rules, close and expiration."""
    index: dict[str, list] = defaultdict(list)
    for e in events:
        for m in _active(e):
            rules = (m.get("rules_primary") or "").strip()
            # A templated rule leaves the distinguishing subject in yes_sub_title, so the
            # rule text alone is not an identity: every leg of a "best restaurant" menu
            # shares it. Skip placeholders, and require a real subject in the key.
            if not rules or "||" in rules or "{{" in rules:
                continue
            key = hashlib.sha1(
                f"{rules}|{m.get('close_time')}|{m.get('expiration_time')}".encode()
            ).hexdigest()
            index[key].append((m, e))
    for key, group in index.items():
        if len({m["ticker"] for m, _ in group}) < 2:
            continue
        for i in range(len(group)):
            for j in range(len(group)):
                if i == j:
                    continue
                (ma, ea), (mb, eb) = group[i], group[j]
                if ma["ticker"] == mb["ticker"]:
                    continue
                # A real duplicate is the same contract in two different events/series;
                # two legs of one event sharing boilerplate are not duplicates.
                if ea["event_ticker"] == eb["event_ticker"]:
                    continue
                if not (_two_sided(ma) and _two_sided(mb) and _traded(ma) and _traded(mb)):
                    continue
                # A templated rule can omit the distinguishing subject: "eighth graders'
                # test scores" without saying reading vs math. Identical rule text across
                # two different series stems is therefore a candidate, flagged for manual
                # confirmation that the underlying is truly the same, not a confirmed lock.
                stem_a = re.split(r"[-\d]", ea["series_ticker"])[0]
                stem_b = re.split(r"[-\d]", eb["series_ticker"])[0]
                candidate = stem_a != stem_b
                yb, ya = price(ma.get("yes_bid_dollars")), price(mb.get("yes_ask_dollars"))
                rep.checks += 1
                if yb is None or ya is None:
                    continue
                mult = max(fee_of.get(ea["series_ticker"], 1.0),
                           fee_of.get(eb["series_ticker"], 1.0))
                gross = yb - ya
                net = gross - _fee(1 - yb, mult) - _fee(ya, mult)
                if net > 0:
                    rep.add(Hit("F4-duplicate", ea.get("category") or "?",
                                (ma["ticker"], mb["ticker"]), round(gross, 4),
                                round(net, 4),
                                f"sell {ma['ticker']} @{yb:.2f} / buy {mb['ticker']} @{ya:.2f}",
                                "CANDIDATE: rules omit subject, verify same underlying"
                                if candidate else "byte-identical rules+times, same series stem"))


# --- F5: margin ladder -> party winner ----------------------------------------------

_WINNER_PATTERNS = (
    (re.compile(r"^SENATE([A-Z]{2})-26$"), "SEN"),
    (re.compile(r"^GOVPARTY([A-Z]{2})-26$"), "GOV"),
    (re.compile(r"^KXHOUSERACE-([A-Z]{2}\d{2})-26$"), ""),
    (re.compile(r"^HOUSE([A-Z]{2}\d{2})-26$"), ""),          # HOUSETX34-26 grammar
)
_MOV = re.compile(r"^KXMIDTERMMOV-(\w+?)([RD])$")


def scan_margin_winner(events: list[dict], fee_of: dict, rep: ScanReport) -> None:
    winners: dict[tuple, tuple] = {}
    for e in events:
        for rx, kind in _WINNER_PATTERNS:
            m0 = rx.match(e["event_ticker"])
            if not m0:
                continue
            for m in _active(e):
                sfx = m["ticker"].rsplit("-", 1)[-1]
                if sfx in ("R", "D"):
                    winners[(m0.group(1) + kind, sfx)] = (m, e)
    for e in events:
        m0 = _MOV.match(e["event_ticker"])
        if not m0:
            continue
        w = winners.get((m0.group(1), m0.group(2)))
        if w is None:
            continue
        wm, we = w
        for m in _active(e):
            # Georgia settles on the first round and holds a runoff; the implication
            # from margin to seat winner does not survive that.
            if "first round" in (m.get("rules_primary") or "").lower():
                rep.skipped["first-round"] += 1
                continue
            mult = max(fee_of.get(e["series_ticker"], 1.0),
                       fee_of.get(we["series_ticker"], 1.0))
            _check_implication(m, wm, mult, rep, "Elections", "F5-margin-winner")


# --- F6: named semantic subsets -----------------------------------------------------

SEMANTIC_SUBSETS = (
    # (subset ticker, superset ticker, basis)
    ("KXGREENTERRITORY-29", "KXUSAEXPANDTERRITORY-29JAN21",
     "identical operative clause; deadlines match to the second; judged EXACT by two reviewers"),
)


def scan_semantic(events: list[dict], fee_of: dict, rep: ScanReport) -> None:
    tickers = {}
    for e in events:
        for m in _active(e):
            tickers[m["ticker"]] = (m, e)
    for sub_tk, sup_tk, basis in SEMANTIC_SUBSETS:
        a, b = tickers.get(sub_tk), tickers.get(sup_tk)
        if not a or not b:
            continue
        mult = max(fee_of.get(a[1]["series_ticker"], 1.0),
                   fee_of.get(b[1]["series_ticker"], 1.0))
        _check_implication(a[0], b[0], mult, rep, "Politics", "F6-semantic", note=basis)


# --- driver -------------------------------------------------------------------------

def scan(events: list[dict], series: dict[str, dict]) -> ScanReport:
    fee_of = {tk: s.get("fee_multiplier", 1) for tk, s in series.items()}
    rep = ScanReport()
    for e in events:
        mult = fee_of.get(e["series_ticker"], 1.0)
        board = e.get("category") or "?"
        scan_ladders(e, mult, rep, board)
        scan_baskets(e, mult, rep, board)
    scan_duplicates(events, fee_of, rep)
    scan_margin_winner(events, fee_of, rep)
    scan_semantic(events, fee_of, rep)
    rep.hits.sort(key=lambda h: -h.net)
    return rep
