"""Series/event/market classification for the Kalshi exchange.

The unit of analysis on Kalshi is the *series*, not the category. A series carries the
contract template, the fee model, the settlement sources and the ticker grammar; the
category field is a display attribute and is demonstrably unreliable (see
docs/taxonomy.md). This module infers structural type from metadata rather than trusting
labels.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Sequence

# --- Contract templates ------------------------------------------------------------
# Inferred from leg-subtitle shape, strike_type, custom_strike and mutual exclusivity.

TEMPLATE_BINARY = "binary"                 # single yes/no proposition
TEMPLATE_DEADLINE_LADDER = "deadline"      # "Before <date>" legs, nested by time
TEMPLATE_THRESHOLD_LADDER = "threshold"    # "X or above" / "N+ pts" legs, nested by level
TEMPLATE_BUCKET_PARTITION = "bucket"       # "A to B" ranges tiling a number line
TEMPLATE_ENTITY_MENU = "entity_menu"       # one leg per candidate/person/option
TEMPLATE_COMBINATION = "combination"       # conjunction of two or more base outcomes
TEMPLATE_UNKNOWN = "unknown"

_MONTHS = {}
for _i, _m in enumerate(
    ["january", "february", "march", "april", "may", "june",
     "july", "august", "september", "october", "november", "december"], start=1
):
    _MONTHS[_m] = _i
    _MONTHS[_m[:3]] = _i

_RE_DEADLINE_FULL = re.compile(r"^(?:before|by)\s+([a-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$")
_RE_DEADLINE_YEAR = re.compile(r"^(?:before|by)\s+(\d{4})$")
_RE_THRESHOLD_PLUS = re.compile(r"^(?P<subject>.*?),?\s*(?P<level>-?[\d.]+)\+\s*(?:pts|points|%)?$")
_RE_THRESHOLD_ABOVE = re.compile(
    r"^(?:above|at least|over|greater than)\s*\$?(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?", re.I
)
_RE_THRESHOLD_OR = re.compile(
    r"^\$?(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?\s*(?:or\s+(?:above|higher|more))$", re.I
)
_RE_BELOW = re.compile(r"^(?:below|under)\s*\$?(?P<level>[\d.,]+)|^\$?(?P<level2>[\d.,]+)\s*or\s+(?:below|less)$", re.I)
_RE_BUCKET = re.compile(
    r"^\$?(?P<lo>-?[\d.,]+)\s*(?P<lm>[kmbt])?\s*(?:to|-|–)\s*\$?(?P<hi>-?[\d.,]+)\s*(?P<hm>[kmbt])?", re.I
)
_MULT = {"k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}


def _num(text: str, mult: str | None) -> float:
    return float(text.replace(",", "")) * (_MULT.get((mult or "").lower(), 1.0))


def parse_deadline(subtitle: str | None):
    """Return a (year, month, day) tuple for 'Before <date>' legs, else None."""
    if not subtitle:
        return None
    t = subtitle.strip().lower().rstrip("?")
    m = _RE_DEADLINE_FULL.match(t)
    if m and m.group(1) in _MONTHS:
        return (int(m.group(3)), _MONTHS[m.group(1)], int(m.group(2)))
    m = _RE_DEADLINE_YEAR.match(t)
    if m:
        return (int(m.group(1)), 1, 1)
    return None


def parse_threshold(subtitle: str | None):
    """Return (subject, level, direction) for one-sided threshold legs, else None.

    direction is '>=' for 'above'/'N+' style legs and '<=' for 'below'/'or less' legs.
    subject separates otherwise-identical ladders that differ by entity, e.g.
    'Republicans, 26+ pts' vs 'Democrats, 26+ pts'.
    """
    if not subtitle:
        return None
    t = subtitle.strip().lower().replace("%", "")
    m = _RE_THRESHOLD_PLUS.match(t)
    if m:
        return (m.group("subject").strip(" ,"), float(m.group("level")), ">=")
    m = _RE_THRESHOLD_ABOVE.match(t)
    if m:
        return ("", _num(m.group("level"), m.group("mult")), ">=")
    m = _RE_THRESHOLD_OR.match(t)
    if m:
        return ("", _num(m.group("level"), m.group("mult")), ">=")
    m = _RE_BELOW.match(t)
    if m:
        lvl = m.group("level") or m.group("level2")
        return ("", _num(lvl, None), "<=")
    return None


def parse_bucket(subtitle: str | None):
    """Return (lo, hi) for range legs like '95,000 to 99,999.99' or '0.1% to 0.5%'."""
    if not subtitle:
        return None
    t = subtitle.strip().lower().replace("%", "")
    m = _RE_BUCKET.match(t)
    if not m:
        return None
    return (_num(m.group("lo"), m.group("lm")), _num(m.group("hi"), m.group("hm")))


def classify_event(event: dict) -> str:
    """Infer the contract template of an event from its legs."""
    legs = [m for m in event.get("markets", []) if m.get("status") == "active"]
    subs = [m.get("yes_sub_title") or "" for m in legs]
    if not legs:
        return TEMPLATE_UNKNOWN
    if len(legs) == 1:
        return TEMPLATE_BINARY

    n_dead = sum(1 for s in subs if parse_deadline(s))
    n_bucket = sum(1 for s in subs if parse_bucket(s))
    n_thresh = sum(1 for s in subs if parse_threshold(s) and not parse_bucket(s))
    n = len(legs)

    if n_dead >= max(2, n * 0.6):
        return TEMPLATE_DEADLINE_LADDER
    if n_bucket >= max(2, n * 0.5):
        return TEMPLATE_BUCKET_PARTITION
    if n_thresh >= max(2, n * 0.6):
        return TEMPLATE_THRESHOLD_LADDER
    if any(re.search(r"\band\b", s, re.I) for s in subs) and event.get("mutually_exclusive"):
        return TEMPLATE_COMBINATION
    return TEMPLATE_ENTITY_MENU


def partition_is_tiled(event: dict, tol: float = 1e-6) -> bool:
    """True when bucket legs tile a contiguous line with no gap and no overlap.

    A tiled partition of a mutually exclusive event is the precondition for
    sum-to-one basket constraints; an untiled one is not (a hole means no leg pays).
    """
    legs = [m for m in event.get("markets", []) if m.get("status") == "active"]
    rngs = []
    for m in legs:
        sub = m.get("yes_sub_title")
        r = parse_bucket(sub)
        if r:
            rngs.append(r)
            continue
        t = parse_threshold(sub)
        if t:
            _, lvl, direction = t
            rngs.append((lvl, float("inf")) if direction == ">=" else (float("-inf"), lvl))
        else:
            return False
    if len(rngs) < 2:
        return False
    rngs.sort()
    if rngs[0][0] != float("-inf") or rngs[-1][1] != float("inf"):
        return False
    for (lo1, hi1), (lo2, _) in zip(rngs, rngs[1:]):
        gap = lo2 - hi1
        scale = max(1.0, abs(hi1))
        if gap < -tol or gap > 0.011 * scale:
            return False
    return True


# --- Ticker grammar ----------------------------------------------------------------

_RE_DERIVATIVE = re.compile(r"^KX(?P<kind>PRIMARYMOV|PRIMARYPLACE|VOTEPRIMARY|MIDTERMMOV|LAMOV)-(?P<rest>.+)$")


def derivative_parent(event_ticker: str, known_events: Sequence[str]) -> str | None:
    """Recover the base event a derivative series refers to.

    Several derivative families embed their parent event in the ticker
    (e.g. KXPRIMARYPLACE-KXGOVFLNOMR-4 -> KXGOVFLNOMR-26). The embedding is not
    normalized, so candidates are generated and matched against the live event set.
    """
    m = _RE_DERIVATIVE.match(event_ticker)
    if not m:
        return None
    rest = m.group("rest")
    rest = re.sub(r"-(\d|\dRD|\dND|\dTH)$", "", rest)  # placement suffix
    known = set(known_events)
    cands = [rest]
    mm = re.match(r"^(KX[A-Z]+?)(\d{2})$", rest)
    if mm:
        cands.append(f"{mm.group(1)}-{mm.group(2)}")
    mm = re.match(r"^([A-Z]{2})(\d{1,2})([RD])(\d{2})$", rest)
    if mm:
        cands.append(f"KX{mm.group(1)}PRIMARY-{int(mm.group(2)):02d}{mm.group(3)}{mm.group(4)}")
    mm = re.match(r"^([A-Z]+?)(\d{2})([A-Z]*)$", rest)
    if mm:
        cands.append(f"KX{mm.group(1)}-{mm.group(2)}")
    for c in cands:
        if c in known:
            return c
    hits = [k for k in known if k.replace("-", "") == rest]
    return hits[0] if len(hits) == 1 else None


@dataclass
class SeriesProfile:
    ticker: str
    category: str
    title: str
    fee_type: str
    fee_multiplier: float
    frequency: str
    n_events: int = 0
    n_markets: int = 0
    templates: Counter = field(default_factory=Counter)
    mutex_events: int = 0
    settlement_sources: list = field(default_factory=list)

    @property
    def zero_fee(self) -> bool:
        return self.fee_multiplier == 0

    @property
    def charges_maker(self) -> bool:
        return self.fee_type == "quadratic_with_maker_fees"

    @property
    def dominant_template(self) -> str:
        return self.templates.most_common(1)[0][0] if self.templates else TEMPLATE_UNKNOWN


def build_series_profiles(series: Iterable[dict], events: Iterable[dict]) -> dict[str, SeriesProfile]:
    profiles: dict[str, SeriesProfile] = {}
    for s in series:
        profiles[s["ticker"]] = SeriesProfile(
            ticker=s["ticker"],
            category=s.get("category") or "",
            title=s.get("title") or "",
            fee_type=s.get("fee_type") or "",
            fee_multiplier=s.get("fee_multiplier", 1),
            frequency=s.get("frequency") or "",
            settlement_sources=s.get("settlement_sources") or [],
        )
    for e in events:
        p = profiles.get(e.get("series_ticker"))
        if p is None:
            continue
        p.n_events += 1
        p.n_markets += len(e.get("markets", []))
        p.templates[classify_event(e)] += 1
        if e.get("mutually_exclusive"):
            p.mutex_events += 1
    return profiles
