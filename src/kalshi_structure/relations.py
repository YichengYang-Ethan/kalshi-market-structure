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
    """Mutually exclusive legs. Prices sum to 1 only when they are also exhaustive.

    Two separate facts are needed and they are not the same fact:

    ``tiled``           the legs leave no gap a value could fall into. Necessary.
    ``exhaustiveness``  'explicit' when the contract text states the underlying's
                        reporting precision or that bounds are inclusive; 'implicit'
                        when only the way the bounds are written implies it; 'none'
                        otherwise. Only 'explicit' is sufficient.

    Buying every leg's YES is a synthetic $1 solely in the explicit case. Requiring only
    ``tiled`` puts 'implicit' and 'none' partitions on a payoff path that can pay zero,
    which is what this class previously did.
    """
    legs: tuple[str, ...]
    tiled: bool
    basis: str
    exhaustiveness: str = "none"
    failure_modes: tuple[str, ...] = ()

    @property
    def supports_sum_to_one(self) -> bool:
        return self.tiled and self.exhaustiveness == "explicit"

    def evaluate_buy_all(self, quotes: Sequence[Quote]) -> Edge | None:
        """Buy every leg's YES: a synthetic $1 only under an explicit guarantee.

        Returns None rather than an edge when exhaustiveness is not established, because
        the payoff of the package is undefined in that case, not merely uncertain.
        """
        if not self.supports_sum_to_one or any(q.yes_ask is None for q in quotes):
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
            "The margin contract resolves on the certified election result; the winner "
            "contract resolves on the party of the member sworn in. Any path that "
            "separates those two facts breaks the implication.",
            "The certified winner changes party registration before the oath and is "
            "sworn in as an independent or as the other party. This needs no vacancy "
            "and no special election, which makes it the cheapest counterexample.",
            "Death, resignation, disqualification or refusal to serve between "
            "certification and oath, followed by a special election won by the other "
            "party.",
            "Fusion voting: the party credited with the electoral win and the formal "
            "party membership of the person sworn in need not be the same. Still open "
            "-- deciding it needs the series glossary, which the contract text does not "
            "contain.",
        ),
        "exactness": "broken",
        "review": (
            "Two independent reviewers returned BROKEN on 2026-08-02, both quoting the "
            "contracts' different named resolution events, and both passed the "
            "calibration anchors. Estimated 1e-4 to 1e-3 per pair per cycle. The "
            "relation still holds in almost every state, but 'almost every' is not what "
            "a lock means, so packages built on it carry an unhedged tail rather than a "
            "floor."
        ),
        "timing": (
            "Early-close behaviour is per winner-series, not per chamber, and the "
            "difference is large. HOUSE{ST}{N} closes on the swearing in (TX-34 is in "
            "this family). KXHOUSERACE carries no early-close condition at all on any "
            "of its 704 legs and relies on media-consensus accelerated determination. "
            "The margin leg closes on publication of certified results. A package can "
            "therefore have its legs settle weeks apart, and which weeks depends on "
            "which winner-series the district happens to use."
        ),
    },
    "semantic_subset": {
        "pattern": "specific acquisition => any acquisition, matched deadlines",
        "basis": (
            "Both contracts define the operative test in identical words -- the "
            "territory 'must come under formal governance or jurisdiction of the United "
            "States, either as a state, territory, or other classification within the "
            "US system, where it was not previously' -- and both exclude leases with "
            "the same sentence about a military base on leased territory. The headline "
            "verbs differ ('acquires' vs 'gains control of') but neither carries "
            "independent weight: the payout criterion is the same operative clause."
        ),
        "failure_modes": (
            "Deadline mismatch of even one day breaks the nesting. Verified identical "
            "to the second for the Greenland pair.",
        ),
        "exactness": "exact",
        "review": (
            "Two independent reviewers returned EXACT on 2026-08-02. The verb-mismatch "
            "concern this repo previously recorded is resolved by the contract text and "
            "has been withdrawn."
        ),
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
            "Conviction and departure are not the same instant. The removal contract "
            "requires the subject to be sitting on the day the Senate votes, but the "
            "contract text does not say when conviction becomes effective removal, so "
            "there may be a window in which removal resolves Yes while the office is "
            "not yet vacated.",
            "Death is excluded from the 'leaves office' contract and settled at the "
            "last traded price, or by committee determination of fair allocation. The "
            "long leg's payoff is therefore undefined in that state rather than zero.",
            "The route contracts and the departure contract express their deadlines "
            "differently ('before his term ends' vs 'before January 20, 2029'), and a "
            "resignation on the final day may satisfy one and not the other.",
        ),
        "exactness": "needs-rule-check",
        "review": (
            "Reviewers split on 2026-08-02: one returned BROKEN, the other "
            "NEEDS-RULE-CHECK. Both passed the calibration anchors, so the "
            "disagreement is substantive rather than a quality signal, and it is "
            "recorded here unresolved. Settling it requires three documents the audit "
            "pack did not contain: the full KXTRUMPREMOVE definition and its primary "
            "settlement source establishing when conviction becomes effective removal; "
            "the exact expiration timestamps and time zones of the resignation and "
            "departure contracts; and the complete death-allocation provision. Until "
            "those are read, this family must not be treated as a floor."
        ),
    },
}
