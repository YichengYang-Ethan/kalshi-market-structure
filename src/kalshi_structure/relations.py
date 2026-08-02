"""Settlement-logic relations between Kalshi markets, and their economics.

A *relation* is a constraint that must hold between market prices because of how the
contracts settle -- not because the underlying events are correlated. Correlation is not
modelled here; a relation only earns a place in this module if a specific clause in the
contract terms makes it exact, and the ways it can fail are recorded alongside it.

Two families of constraint are represented:

``Implication``   A implies B, therefore P(A) <= P(B).
``Partition``     mutually exclusive, collectively exhaustive legs sum to 1.

Both expose the executable form (which side of which book you must cross) and the
fee-aware net edge, because a constraint that is violated only at mid prices is not a
trade.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

# Verified against the official fee schedule effective 2026-07-07 and the live
# /series endpoint. The multiplier is per-series; unknown series fail closed at 1.
TAKER_COEFFICIENT = 0.07
MAKER_COEFFICIENT = 0.0175
TICK = 0.01


def taker_fee(price: float, multiplier: float = 1.0) -> float:
    """Per-contract taker fee in dollars. Kalshi rounds up to a centicent per order;
    this returns the unrounded value, which is a lower bound on the charge."""
    return multiplier * TAKER_COEFFICIENT * price * (1.0 - price)


def maker_fee(price: float, charges_maker: bool = False) -> float:
    """Per-contract maker fee. Zero on all series except the ~130 that carry
    fee_type='quadratic_with_maker_fees'."""
    return MAKER_COEFFICIENT * price * (1.0 - price) if charges_maker else 0.0


@dataclass(frozen=True)
class Quote:
    ticker: str
    yes_bid: float | None
    yes_ask: float | None
    bid_size: float = 0.0
    ask_size: float = 0.0
    fee_multiplier: float = 1.0
    charges_maker: bool = False


@dataclass(frozen=True)
class Edge:
    """Economics of one executable package."""
    gross: float
    net_taker: float
    net_maker_first: float | None
    depth: float
    entry: str

    @property
    def is_violation(self) -> bool:
        return self.net_taker > 0


@dataclass(frozen=True)
class Implication:
    """A implies B. Requires P(A) <= P(B).

    The lock when violated: buy B YES at its ask and buy A NO at (1 - A's yes bid).
    Payout is at least $1 per unit whenever the implication holds at settlement, so the
    package is profitable iff yes_bid(A) - yes_ask(B) exceeds fees.
    """
    a: str
    b: str
    basis: str          # the clause that makes the implication exact
    failure_modes: tuple[str, ...] = ()
    exactness: Literal["exact", "needs-rule-check", "soft"] = "needs-rule-check"

    def evaluate(self, qa: Quote, qb: Quote) -> Edge | None:
        if qa.yes_bid is None or qb.yes_ask is None:
            return None
        gross = qa.yes_bid - qb.yes_ask
        fees = taker_fee(1.0 - qa.yes_bid, qa.fee_multiplier) + taker_fee(qb.yes_ask, qb.fee_multiplier)
        net_maker = None
        if qa.yes_ask is not None:
            # Rest one tick inside A's ask (selling A's YES), hedge by taking B.
            rest_px = qa.yes_ask - TICK
            net_maker = (
                rest_px
                - qb.yes_ask
                - taker_fee(qb.yes_ask, qb.fee_multiplier)
                - maker_fee(rest_px, qa.charges_maker)
            )
        return Edge(
            gross=gross,
            net_taker=gross - fees,
            net_maker_first=net_maker,
            depth=min(qa.bid_size, qb.ask_size),
            entry=f"buy {qb.ticker} YES @{qb.yes_ask:.2f} + buy {qa.ticker} NO @{1 - qa.yes_bid:.2f}",
        )


@dataclass(frozen=True)
class Partition:
    """Mutually exclusive, collectively exhaustive legs: prices must sum to 1.

    ``tiled`` must be established structurally (see taxonomy.partition_is_tiled) before
    the exhaustiveness half of this constraint may be used. A partition with a hole
    supports only the sum <= 1 direction.
    """
    legs: tuple[str, ...]
    tiled: bool
    basis: str
    failure_modes: tuple[str, ...] = ()

    def evaluate_buy_all(self, quotes: Sequence[Quote]) -> Edge | None:
        """Buy every leg's YES: pays exactly $1 if the partition is exhaustive."""
        if not self.tiled or any(q.yes_ask is None for q in quotes):
            return None
        cost = sum(q.yes_ask for q in quotes)
        fees = sum(taker_fee(q.yes_ask, q.fee_multiplier) for q in quotes)
        return Edge(
            gross=1.0 - cost,
            net_taker=1.0 - cost - fees,
            net_maker_first=None,
            depth=min(q.ask_size for q in quotes),
            entry=f"buy YES on all {len(quotes)} legs @ {cost:.4f}",
        )

    def evaluate_sell_all(self, quotes: Sequence[Quote]) -> Edge | None:
        """Buy every leg's NO: pays exactly (n-1) if exactly one leg can win."""
        if any(q.yes_bid is None for q in quotes):
            return None
        cost = sum(1.0 - q.yes_bid for q in quotes)
        fees = sum(taker_fee(1.0 - q.yes_bid, q.fee_multiplier) for q in quotes)
        floor = len(quotes) - 1
        return Edge(
            gross=floor - cost,
            net_taker=floor - cost - fees,
            net_maker_first=None,
            depth=min(q.bid_size for q in quotes),
            entry=f"buy NO on all {len(quotes)} legs @ {cost:.4f}, floor ${floor}",
        )


# --- Relation families discovered and verified against live books -------------------
# Each entry documents the clause that closes the implication and the scenarios where
# it fails. Families marked exactness='soft' are NOT arbitrage and are excluded from
# the scanner by default.

FAMILY_NOTES: dict[str, dict] = {
    "margin_implies_winner": {
        "pattern": "KXMIDTERMMOV-{race}{party}-P{n} => {winner_market}-{party}",
        "basis": (
            "ELECTIONMOV defines margin as the subject's vote percentage minus the "
            "runner-up's, so a positive margin exists only if the subject won."
        ),
        "failure_modes": (
            "MOV settles on the election result; House/Senate winner markets settle on "
            "the party of the member sworn in.",
            "Death, resignation, disqualification or refusal to serve between election "
            "and oath, followed by a special election won by the other party.",
            "Fusion voting: the party credited with the win may differ from the formal "
            "party membership of the person sworn in.",
        ),
        "exactness": "needs-rule-check",
        "mitigation": (
            "House winner markets carry an accelerated-determination clause on media "
            "consensus, which closes most of the election-to-oath window. Senate series "
            "state early close *following the swearing in*, so the window stays open."
        ),
    },
    "semantic_subset": {
        "pattern": "specific acquisition => any acquisition, matched deadlines",
        "basis": "One event's resolution condition is a strict subset of the other's.",
        "failure_modes": (
            "Verb mismatch across contracts ('acquires' vs 'gains control of').",
            "Deadline mismatch of even one day breaks the nesting.",
        ),
        "exactness": "needs-rule-check",
    },
    "combination_marginal": {
        "pattern": "P(A and B) + P(not-A and B) = P(B) over a 2x2 combination event",
        "basis": "The four combination legs partition the joint outcome space.",
        "failure_modes": (
            "Person-named combination legs settle on named candidates; if a nominee is "
            "replaced the combination leg can fail while the party market does not.",
        ),
        "exactness": "exact",
    },
    "deadline_nesting": {
        "pattern": "before T1 => before T2 for T1 < T2 within one series",
        "basis": "Earlier deadlines are subsets of later ones on identical subjects.",
        "failure_modes": (
            "Subject drift between legs (a different question with similar wording).",
        ),
        "exactness": "exact",
    },
    "threshold_nesting": {
        "pattern": ">= L1 => >= L2 for L1 > L2 within one subject",
        "basis": "Higher thresholds are subsets of lower ones.",
        "failure_modes": (
            "A hidden second dimension (different measurement window or entity) that "
            "makes two ladders non-comparable.",
        ),
        "exactness": "exact",
    },
    "departure_lattice": {
        "pattern": "resign => leaves office; convict => leaves office",
        "basis": "Specific exit routes are subsets of leaving office.",
        "failure_modes": (
            "Resignation and conviction are not mutually exclusive: the Senate may try "
            "an official after departure, so a NO/NO basket on both routes has a state "
            "in which both legs lose.",
            "Death is excluded from some 'leaves office' contracts and handled by a "
            "special last-price rule.",
        ),
        "exactness": "needs-rule-check",
    },
}
