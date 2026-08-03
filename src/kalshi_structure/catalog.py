"""Catalogue of arbitrage-capable structures, independent of price.

The scanner (`scan.py`) answers "where is a constraint violated right now". This answers
the prior question: "where *could* a violation appear at all". A relation is listed here
if the contracts' settlement rules bind their prices together, so that any future
divergence is an arbitrage — regardless of whether they are divergent today.

This is the monitorable surface. It is price-free and therefore stable: it changes only
when Kalshi lists or settles events, not when quotes move. Every entry is something worth
watching; the scanner decides when to act.

Families, and what makes each one arbitrage-capable:

  L  ladder nesting        two legs of one event where one outcome implies the other
  P1 mutex partition       at-most-one-wins: NO-basket floors at n-1 (price-free true)
  P2 exhaustive partition  exactly-one-wins: YES-basket is a synthetic $1 (needs explicit
                           exhaustiveness evidence in the rule text)
  D  duplicate listing     two markets whose rules, close and expiration are identical
  X  derivative -> base    a margin/placement/share leg implying its base contest winner
  S  semantic subset       one resolution condition contained in another's (rule-read)
  C  combination marginal  a 2x2 combination event vs its two base markets

Only structural facts gate membership: the mutual-exclusivity flag, the contract
template, exhaustiveness evidence, ticker grammar, and rule text. No price is read.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .taxonomy import (classify_event, exhaustiveness_evidence, parse_deadline,
                       parse_threshold, partition_is_tiled)


@dataclass
class Relation:
    family: str
    kind: str                 # what the binding is: "implication" | "partition" | "equality"
    board: str
    members: tuple[str, ...]  # tickers, or a representative + leg count for baskets
    basis: str                # why the rule makes it arbitrage-capable
    caveat: str = ""          # what must still be checked before trusting it


@dataclass
class Catalog:
    relations: list[Relation] = field(default_factory=list)
    notes: dict = field(default_factory=lambda: defaultdict(int))

    def add(self, r: Relation):
        self.relations.append(r)


def _active(e: dict) -> list[dict]:
    return [m for m in e.get("markets", []) if m.get("status") == "active"]


# --- L: within-event ladder nesting -------------------------------------------------

def catalog_ladders(e: dict, cat: Catalog) -> None:
    board = e.get("category") or "?"
    legs = _active(e)
    if len(legs) < 2:
        return
    # deadline ladder: every ordered pair is one implication (earlier => later)
    dls = [m for m in legs if parse_deadline(m.get("yes_sub_title"))]
    if len(dls) >= 2:
        cat.add(Relation("L-deadline", "implication", board,
                         (e["event_ticker"], f"{len(dls)} legs"),
                         "earlier deadline implies later within one event",
                         f"{len(dls) * (len(dls) - 1) // 2} monitorable pairs"))
    # threshold ladder: group by identical skeleton so units never mix
    groups: dict[str, int] = defaultdict(int)
    for m in legs:
        sub = m.get("yes_sub_title")
        if parse_threshold(sub):
            groups[re.sub(r"[\d.,]+", "#", (sub or "").lower())] += 1
    for skel, n in groups.items():
        if n >= 2:
            cat.add(Relation("L-threshold", "implication", board,
                             (e["event_ticker"], f"{n} legs"),
                             f"nested thresholds on one subject: {skel.strip()}",
                             f"{n * (n - 1) // 2} monitorable pairs"))


# --- P1 / P2: partition baskets -----------------------------------------------------

def catalog_partitions(e: dict, cat: Catalog) -> None:
    if not e.get("mutually_exclusive"):
        return
    board = e.get("category") or "?"
    legs = _active(e)
    if len(legs) < 2:
        cat.notes["mutex-too-small"] += 1
        return
    if any(m.get("result") == "yes" for m in e.get("markets", [])):
        cat.notes["mutex-already-decided"] += 1
        return
    # P1: at most one wins -> a NO-basket floors at n-1. True for every live mutex event.
    cat.add(Relation("P1-mutex", "partition", board,
                     (e["event_ticker"], f"{len(legs)} legs"),
                     "mutually exclusive: NO on all legs floors at (n-1)",
                     "sell-all direction; needs all legs quoted at trade time"))
    # P2: exactly one wins -> a YES-basket is a synthetic $1, but only with explicit
    # exhaustiveness evidence in the rule text.
    tpl = classify_event(e)
    if tpl in ("bucket", "threshold") and partition_is_tiled(e):
        grade = exhaustiveness_evidence(e)
        if grade == "explicit":
            cat.add(Relation("P2-exhaustive", "partition", board,
                             (e["event_ticker"], f"{len(legs)} legs"),
                             "tiled partition with explicit precision clause: YES-basket = $1",
                             "the only price-free synthetic dollar; buy-all direction"))
        else:
            cat.notes[f"tiled-but-{grade}"] += 1


# --- D: duplicate listings ----------------------------------------------------------

def catalog_duplicates(events: list[dict], cat: Catalog) -> None:
    index: dict[str, list] = defaultdict(list)
    for e in events:
        for m in _active(e):
            rules = (m.get("rules_primary") or "").strip()
            if not rules or "||" in rules or "{{" in rules:
                continue
            key = hashlib.sha1(
                f"{rules}|{m.get('close_time')}|{m.get('expiration_time')}".encode()
            ).hexdigest()
            index[key].append((m, e))
    for group in index.values():
        tickers = {m["ticker"] for m, _ in group}
        events_in = {e["event_ticker"] for _, e in group}
        if len(tickers) < 2 or len(events_in) < 2:
            continue
        stems = {re.split(r"[-\d]", e["series_ticker"])[0] for _, e in group}
        board = group[0][1].get("category") or "?"
        same_stem = len(stems) == 1
        cat.add(Relation("D-duplicate", "equality", board,
                         tuple(sorted(tickers))[:6],
                         "byte-identical rules, close and expiration across markets",
                         "same series stem — likely a true re-listing" if same_stem
                         else "different series — rules may omit the subject; verify identical underlying"))


# --- X: derivative -> base (margin, primary) ----------------------------------------

_WINNER_PATTERNS = (
    (re.compile(r"^SENATE([A-Z]{2})-26$"), "SEN"),
    (re.compile(r"^GOVPARTY([A-Z]{2})-26$"), "GOV"),
    (re.compile(r"^KXHOUSERACE-([A-Z]{2}\d{2})-26$"), ""),
    (re.compile(r"^HOUSE([A-Z]{2}\d{2})-26$"), ""),
)
_MOV = re.compile(r"^KXMIDTERMMOV-(\w+?)([RD])$")


def catalog_derivatives(events: list[dict], cat: Catalog) -> None:
    winners: dict[tuple, dict] = {}
    for e in events:
        for rx, kind in _WINNER_PATTERNS:
            m0 = rx.match(e["event_ticker"])
            if m0:
                winners[(m0.group(1) + kind, None)] = e
    for e in events:
        m0 = _MOV.match(e["event_ticker"])
        if not m0:
            continue
        we = winners.get((m0.group(1), None))
        if we is None:
            cat.notes["mov-no-winner-event"] += 1
            continue
        n = len(_active(e))
        runoff = any("first round" in (m.get("rules_primary") or "").lower()
                     for m in _active(e))
        if runoff:
            cat.notes["mov-first-round-excluded"] += 1
            continue
        cat.add(Relation("X-margin-winner", "implication", "Elections",
                         (e["event_ticker"], we["event_ticker"]),
                         "any margin leg for a party implies that party holds the seat",
                         f"{n} margin legs; BROKEN family (party-switch/oath tail) — monitor, do not treat as lock"))


# --- S: named semantic subsets (rule-verified) --------------------------------------

SEMANTIC_SUBSETS = (
    ("KXGREENTERRITORY-29", "KXUSAEXPANDTERRITORY-29JAN21", "Politics",
     "acquiring part of Greenland is contained in acquiring any territory; identical "
     "operative clause, deadlines matched; judged EXACT by two reviewers"),
)


def catalog_semantic(events: list[dict], cat: Catalog) -> None:
    live = {m["ticker"] for e in events for m in _active(e)}
    for sub, sup, board, basis in SEMANTIC_SUBSETS:
        if sub in live and sup in live:
            cat.add(Relation("S-semantic", "implication", board, (sub, sup), basis,
                             "hand-verified; the exact-lock exemplar"))


# --- C: combination -> marginals ----------------------------------------------------

def catalog_combinations(events: list[dict], cat: Catalog) -> None:
    for e in events:
        if classify_event(e) != "combination":
            continue
        cat.add(Relation("C-combination", "partition", e.get("category") or "?",
                         (e["event_ticker"],),
                         "2x2 combination: each marginal equals a sum of combination legs",
                         "priced against the two base markets; needs those to be listed"))


# --- driver -------------------------------------------------------------------------

def build_catalog(events: list[dict]) -> Catalog:
    cat = Catalog()
    for e in events:
        catalog_ladders(e, cat)
        catalog_partitions(e, cat)
    catalog_duplicates(events, cat)
    catalog_derivatives(events, cat)
    catalog_semantic(events, cat)
    catalog_combinations(events, cat)
    return cat
