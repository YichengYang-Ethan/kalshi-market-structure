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
# A threshold leg is a subject (optional) plus a comparator and a level. The grammar
# varies widely across categories -- "Republicans, 26+ pts", "6+ wins",
# "Arizona over 1.5 runs scored", "Above $150,000", "<9", "150,000 or above" -- so each
# shape gets its own pattern and a trailing unit noun is always tolerated.
_UNIT = r"(?:\s+[a-z%.\-'’ ]+)?"
_RE_THRESHOLD_PLUS = re.compile(
    rf"^(?P<subject>.*?),?\s*(?P<level>-?[\d.,]+)\+{_UNIT}$"
)
_RE_THRESHOLD_ABOVE = re.compile(
    rf"^(?P<subject>.*?)(?:^|\b)(?:above|at least|over|greater than|more than)\s*\$?"
    rf"(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?{_UNIT}$", re.I
)
_RE_THRESHOLD_OR = re.compile(
    rf"^(?P<subject>.*?)\$?(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?\s*or\s+"
    rf"(?:above|higher|more|greater){_UNIT}$", re.I
)
_RE_BELOW_WORD = re.compile(
    rf"^(?P<subject>.*?)(?:^|\b)(?:below|under|less than|fewer than)\s*\$?"
    rf"(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?{_UNIT}$", re.I
)
_RE_BELOW_OR = re.compile(
    rf"^(?P<subject>.*?)\$?(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?\s*or\s+"
    rf"(?:below|less|fewer){_UNIT}$", re.I
)
# Compact comparators used by the *TWEETS / post-count series: "<9", ">20", ">=15".
_RE_COMPACT = re.compile(r"^(?P<op>[<>]=?)\s*\$?(?P<level>[\d.,]+)\s*(?P<mult>[kmbt])?$")
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

    ``direction`` is '>=' for above/N+ style legs and '<=' for below/or-less legs.
    ``subject`` separates otherwise-identical ladders that differ by entity
    ('Republicans, 26+ pts' vs 'Democrats, 26+ pts'; 'Arizona over 1.5 runs scored' vs
    the opposing team's ladder) — comparing levels across different subjects is a
    category error, so callers must group on it.

    The level carries no information about whether the bound is inclusive: subtitles
    and rule text routinely disagree (``KXGDPYEAR`` shows '6.1% or Above' for a leg whose
    rules read 'is above 6.0%'). Use this for structure, never for a strike value that
    settles money.
    """
    if not subtitle:
        return None
    t = subtitle.strip().lower().replace("%", "")
    m = _RE_COMPACT.match(t)
    if m:
        direction = ">=" if m.group("op").startswith(">") else "<="
        return ("", _num(m.group("level"), m.group("mult")), direction)
    for rx, direction in ((_RE_THRESHOLD_PLUS, ">="), (_RE_THRESHOLD_OR, ">="),
                          (_RE_BELOW_OR, "<="), (_RE_THRESHOLD_ABOVE, ">="),
                          (_RE_BELOW_WORD, "<=")):
        m = rx.match(t)
        if not m:
            continue
        try:
            level = _num(m.group("level"), m.groupdict().get("mult"))
        except ValueError:
            continue
        return (m.group("subject").strip(" ,"), level, direction)
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


def classify_event(event: dict, *, active_only: bool = False) -> str:
    """Infer the contract template that generated an event.

    By default this reads **all** legs, including settled ones. A generator's identity
    does not change when its early rungs resolve: a six-rung deadline ladder with five
    legs finalised is still a deadline ladder, and labelling it ``binary`` because one
    leg is left describes the order book rather than the contract. 44 events in the
    2026-08-02 census were mislabelled that way.

    Pass ``active_only=True`` when the question is what can be traded right now — sizing
    a basket, counting executable legs — rather than what kind of contract this is.
    """
    legs = event.get("markets", [])
    if active_only:
        legs = [m for m in legs if m.get("status") == "active"]
    legs = legs or [m for m in event.get("markets", []) if m.get("status") == "active"]
    subs = [m.get("yes_sub_title") or "" for m in legs]
    if not legs:
        return TEMPLATE_UNKNOWN
    if len(legs) == 1:
        return TEMPLATE_BINARY

    # Combination is decided first: its legs routinely satisfy the threshold grammar
    # too ("Core CPI above X and headline above Y"), so a later branch never sees them.
    if _is_combination(legs):
        return TEMPLATE_COMBINATION

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
    return TEMPLATE_ENTITY_MENU


_RE_COMBINATION_RULE = re.compile(r"if\s+all\s+of\s+the\s+following", re.I)


def _is_combination(legs: Sequence[dict]) -> bool:
    """Detect conjunction contracts from rule text rather than from the word 'and'.

    Leg subtitles are an unreliable signal because entity names contain conjunctions
    ('Bosnia and Herzegovina', 'Antigua and Barbuda'). Combination contracts are
    generated from a template whose rule text opens 'If ALL of the following occur',
    which is unambiguous.
    """
    hits = sum(1 for m in legs if _RE_COMBINATION_RULE.search(m.get("rules_primary") or ""))
    return hits >= max(1, len(legs) * 0.5)


def partition_is_tiled(event: dict, tol: float = 1e-9) -> bool:
    """Necessary condition for a partition to be collectively exhaustive.

    Checks that the legs cover an unbounded line, never overlap, and leave only gaps
    that are negligible against the neighbouring bucket widths. Kalshi writes closed
    ranges against a quantised underlying — '0.1% to 0.5%' is followed by '0.6% to 1.0%'
    because the statistic is published to one decimal place — so a small consistent gap
    is the quantum of the underlying, not a hole.

    **This is not sufficient**, for two independent reasons. Arithmetic cannot separate a
    reporting quantum from a settlement hole, and a partition can also fail to be
    exhaustive without any numeric gap at all -- a truncated grid simply stops listing
    outcomes (a soccer correct-score event lists 17 of 36 scorelines and nothing above 5
    goals, so a 4-4 draw pays no leg). Call :func:`exhaustiveness_evidence` and read the
    contract text before relying on exhaustiveness; without it, only ``sum(P) <= 1`` is
    supported, never ``== 1``.

    The gap bound is relative to bucket width rather than to the index level. An
    absolute or level-relative tolerance makes the verdict depend on the magnitude of
    the underlying instead of its structure, which wrongly rejects low-valued ladders
    (GDP growth ~2%) while accepting identically-built high-valued ones (labour-force
    participation ~61%), and rejects the segmented tick sizes crypto ladders use
    (1e-5 in the low range, 1e-4 in the high range of the same event).
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
        if t is None:
            return False
        _, lvl, direction = t
        rngs.append((lvl, float("inf")) if direction == ">=" else (float("-inf"), lvl))
    if len(rngs) < 2:
        return False
    rngs.sort()
    if rngs[0][0] != float("-inf") or rngs[-1][1] != float("inf"):
        return False
    widths = [hi - lo for lo, hi in rngs if lo != float("-inf") and hi != float("inf")]
    if not widths:
        return False
    scale = min(w for w in widths if w > 0) if any(w > 0 for w in widths) else 0.0
    for (_, hi1), (lo2, _) in zip(rngs, rngs[1:]):
        gap = lo2 - hi1
        if gap < -tol:            # overlap: legs are not mutually exclusive by value
            return False
        # A gap comparable to a bucket is a hole; a gap orders of magnitude smaller is
        # the reporting quantum of the underlying.
        if gap > tol and gap > 0.5 * scale:
            return False
    return True


_RE_QUANTISATION = re.compile(
    r"(rounded to|to the nearest|one[- ]decimal|two[- ]decimal|decimal place|"
    r"bounds are inclusive|inclusive of (?:their|the) upper|whole (?:number|dollar|cent))",
    re.I,
)


def quantisation_evidence(event: dict) -> str | None:
    """Return the rule sentence that justifies treating gaps as a quantum, if any.

    Arithmetic alone cannot decide whether a gap is a reporting quantum or a settlement
    hole; the underlying's publication precision does, and that lives in the contract
    text. GDP growth cannot land between 0.5% and 0.6% because it is published to one
    decimal place, and an acquisition price cannot land between two billion-dollar
    buckets because the contract rounds it to the nearest billion -- neither fact is
    visible in the numbers.

    ``partition_is_tiled`` therefore establishes only that the gaps are *consistent*.
    A basket constraint that depends on exhaustiveness additionally requires this
    evidence from the contract text.
    """
    for m in event.get("markets", []):
        for field in ("rules_secondary", "rules_primary"):
            text = m.get(field) or ""
            hit = _RE_QUANTISATION.search(text)
            if hit:
                start = max(0, hit.start() - 90)
                return text[start:hit.end() + 90].strip()
    return None


def _written_precision(subtitle: str | None) -> float | None:
    """Smallest unit implied by how a bucket bound is written: 349.9999 -> 1e-4."""
    if not subtitle:
        return None
    nums = re.findall(r"\d+\.(\d+)", subtitle)
    if nums:
        return 10.0 ** -max(len(d) for d in nums)
    return 1.0 if re.search(r"\d", subtitle) else None


def exhaustiveness_evidence(event: dict, tol: float = 1e-9) -> str:
    """Grade the case that a tiled partition is genuinely collectively exhaustive.

    Returns one of:

    ``explicit``  the contract text states the reporting precision or that bounds are
                  inclusive. Safe to use for a sum-to-one constraint.
    ``implicit``  no such sentence, but every gap equals the precision to which the
                  bounds are *written* and the buckets are equal width, which is what a
                  ladder generated over a quantised feed looks like. Suggestive, not
                  sufficient.
    ``none``      neither. Only ``sum(P) <= 1`` is supported.

    The distinction matters because ``implicit`` infers the underlying's precision from
    how the bounds happen to be written, which is a weaker claim than reading it. Crypto
    range ladders grade ``implicit``: bounds to four decimals, 1e-4 gaps, uniform width,
    matching the index they settle against. That is almost certainly exhaustive, but the
    contract never says so, and a ladder whose feed carries more precision than its
    bounds suggest would look identical.

    Note that neither grade addresses a partition that is simply truncated. A soccer
    correct-score grid has no numeric gap to measure -- it stops enumerating -- so
    exhaustiveness there is a question about coverage of the outcome space, not about
    quantisation.
    """
    if quantisation_evidence(event):
        return "explicit"
    legs = [m for m in event.get("markets", []) if m.get("status") == "active"]
    rngs, precisions = [], []
    for m in legs:
        sub = m.get("yes_sub_title")
        r = parse_bucket(sub)
        if r is None:
            continue
        rngs.append(r)
        p = _written_precision(sub)
        if p is not None:
            precisions.append(p)
    if len(rngs) < 2 or not precisions:
        return "none"
    rngs.sort()
    widths = [round(hi - lo, 9) for lo, hi in rngs]
    gaps = [round(lo2 - hi1, 9) for (_, hi1), (lo2, _) in zip(rngs, rngs[1:])]
    if not gaps or len(set(widths)) != 1:
        return "none"
    q = min(precisions)
    return "implicit" if all(abs(g - q) <= tol or abs(g) <= tol for g in gaps) else "none"


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
