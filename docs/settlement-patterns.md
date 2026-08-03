# Settlement patterns and the constraint grammar

> **Scope.** Every figure here describes the events that were *open* at the
> 2026-08-02 snapshot. Roughly 100,000+ settled events exist and none are included,
> so nothing below is a statement about the exchange's history. Crypto alone has
> settled over 43,000 events against 108 open ones — a board can look small here and
> be among the most active by turnover.

Kalshi generates contracts from a small number of templates. Once the templates are
enumerated, most settlement behaviour is predictable from metadata, and the logical
constraints between markets become machine-extractable. This document is the
cross-category synthesis; per-category detail lives in [categories/](categories/).

## The six templates

| Template | Leg grammar | Native constraint |
| --- | --- | --- |
| `binary` | one yes/no proposition | none internal |
| `deadline` | "Before \<date\>" | earlier ⊆ later |
| `threshold` | "Above X", "N+ pts", "\<9" | higher level ⊆ lower level |
| `bucket` | "A to B" ranges | sum = 1 **if** exhaustive |
| `entity_menu` | one leg per candidate/team/option | sum ≤ 1 when mutex; = 1 only if exhaustive |
| `combination` | "If ALL of the following occur…" | marginal identities against the bases |

Template is inferred from leg grammar rather than declared. Two detection rules earned
their place the hard way:

- **Combinations are detected from rule text, not from the word "and".** Team names
  contain conjunctions — "Bosnia and Herzegovina", "Antigua and Barbuda" — and a
  subtitle-based test misclassified 11 of 19 candidate events in Sports. The template's
  rule text opens *"If ALL of the following occur"*, which is unambiguous.
- **Threshold grammar varies by category.** "Republicans, 26+ pts" (Elections),
  "6+ wins" and "Arizona over 1.5 runs scored" (Sports), "\<9" and "\>20" (post-count
  series), "$150,000 or above" (Financials) are all the same structure. A parser tuned
  on one category matched only 49.6% of Sports ladder legs.

## Constraint families

### Within a series

**Ladder nesting** (`threshold`, `deadline`) is the most common structure on the
exchange and the most reliably priced. Both legs live in one event, so they share
postponement and void language — there is no rule-mismatch risk, only price risk.

```
P(≥ L_hi) ≤ P(≥ L_lo)          for L_hi > L_lo, same subject
P(before T1) ≤ P(before T2)     for T1 < T2, same subject
```

The subject qualifier is load-bearing. "Republicans, 26+ pts" and "Democrats, 26+ pts"
sit in one event but are different ladders; comparing across them is a category error.

**Partition baskets** (`bucket`, `entity_menu` + mutex) require exhaustiveness, which is
where most naive scanners break — see [Exhaustiveness](#exhaustiveness-is-the-main-trap).

### Across series

**Derivative → base.** A derivative series names its parent in the event ticker:
`KXPRIMARYPLACE-KXGOVFLNOMR-4` refers to `KXGOVFLNOMR-26`. Any winning-margin,
placement, or vote-share leg for candidate X implies X won the base contest.

**Duplicate listings.** The same contract is sometimes listed twice under different
series. `KXAAAGASD-26AUG03` and `KXAAAGASW-26AUG03` carry byte-identical rule sentences,
close times and expiration times across 7 shared strikes. `KXYTVIEWS` legs are
byte-identical to legs inside the corresponding `KXYTVIEWSHIGH` ladder. Detection must
key on `(rules_primary, close_time, expiration_time)` — **never on series ticker**.

**Semantic subsets.** One contract's resolution condition is strictly contained in
another's: winning ⊆ being nominated; reaching the final ⊆ reaching the semifinal;
acquiring part of Greenland ⊆ acquiring any territory. These are the richest family and
the most dangerous, because containment must be established from rule text and the
deadlines must match exactly.

**Combination marginals.** A 2×2 combination event gives
`P(A) = P(A∧B) + P(A∧¬B)`, executable in both directions against the base markets.

**Point-mass ⊆ threshold.** Where a statistic is listed both as an "Above X" ladder and
as an "Exactly X" menu (every US macro release is dual-listed this way),
`Σ_{v>x} P(exactly v) ≤ P(above x)`. The menus are truncated at both ends, so only the
one-sided direction is a constraint.

## Exhaustiveness is the main trap

`mutually_exclusive = true` says **at most one** leg resolves YES. It says nothing about
whether **at least one** does. Buying every leg's YES is a synthetic $1 only under
exhaustiveness, and most menus are not exhaustive:

- **Open-universe menus.** "Which team will X join", "next coach", "next Attorney
  General" — the answer need not be on the board. Eight Entertainment events currently
  price with `Σ ask + fees < 1` and every one is an open-universe menu, not an arb.
  The most extreme, `KXNETFLIXRANKSHOWGLOBAL-26AUG03`, sits at `Σ ask = 0.150` with
  1,138 contracts of depth — a naive scanner would report an 85-cent lock.
- **Truncated grids.** The soccer correct-score grid stops at 5 goals per side and omits
  4-4, 5-3, 5-4, 5-5 and everything above; the implication to the 1X2 market runs one
  way only.
- **Genuine holes.** A soccer correct-score grid such as `KXBRASILEIROSCORE-26AUG09FLAVIT`
  lists 30 legs covering 17 of the 36 cells in the 0-5 x 0-5 scoreline grid, and nothing
  above 5 goals. A 4-4 draw pays no leg. This is the cleanest non-exhaustive partition on
  the exchange because the omission is in the enumeration, with no gap arithmetic to
  misread.
- **Quantum gaps that are not holes.** `KXGDPYEAR` jumps from "0.1% to 0.5%" to
  "0.6% to 1.0%", but GDP is published to one decimal place and `rules_secondary` says
  the bounds are inclusive, so nothing can land in between. `KXGREENLANDPRICE` looks like
  a hole for the same reason and is not one: it rounds values to the nearest billion.

Gap arithmetic cannot separate the last two cases — only the contract text can, and this
repository got `KXGREENLANDPRICE` wrong for several passes by trusting the arithmetic.
See
[taxonomy.md](taxonomy.md#exhaustiveness-cannot-be-decided-by-arithmetic) for why the
structural check is necessary but never sufficient, and how an earlier tolerance bug in
this repo manufactured a false finding about Economics.

## Displayed text is not the contract

Three independent failures of the same kind, each found in a different category:

| Displayed | Settles on |
| --- | --- |
| `KXHOUSERACE-NY02-26-D` shows "Patrick Halpin" | the **party** of whoever is sworn in |
| `KXGDPYEAR` leg shows "6.1% or Above" | `rules_primary`: *"is above 6.0%"* |
| `SENATELA-26` is titled "Kentucky Senate winner?" | the **Kentucky** Senate seat; Louisiana 2026 is `KXSENATELA-26NOV` |

Joining on rules text rather than tickers raised `KXMIDTERMMOV` parent coverage from
511/522 to 520/520 and removed a silent wrong-entity match. **Every relation must be
built from `rules_primary`.**

## Timing asymmetry decides how a relation unwinds

Two contracts on the same underlying fact can resolve weeks apart, because early-close
behaviour is set per series:

| Family | Early close | Media-consensus acceleration | Settlement timer |
| --- | --- | --- | --- |
| `KXHOUSERACE` | none (0/704 legs) | 704/704 | 1,800s |
| `SENATE{ST}` | swearing-in (136/136) | 15/136 (11%) | 1,800s |
| `GOVPARTY{ST}` | inauguration (101/101) | 11/101 | 1,800s |
| `HOUSE{ST}{N}` | swearing-in (150/150) | 98/150 | **14s** |
| `KXMIDTERMMOV` | certified results published | — | 1,800s |

A margin-versus-winner package can therefore have its two legs settle in three different
weeks. The hedge is not symmetric in time even when it is exact in logic.

## What the exchange-wide scan found

Roughly 120,000 executable constraint checks were run across all categories against the
2026-08-02 snapshot, using per-series fees and executable sides. The price inputs are not
committed — Kalshi bars redistributing them — so these totals are not reproducible from
this repository alone, only from a fresh scan.

| Category | Checks | Gross violations | Survive fees | Realisable |
| --- | --- | --- | --- | --- |
| Financials + Crypto | ~90,600 | 0 | 0 | — |
| Sports | 19,530 | 3 | 2 | < $0.42 |
| Economics + Commodities | 2,935 | 16 | 8 | < $5 |
| Entertainment + Mentions | ~2,000 | 1 | 0 | — |
| **Elections + Politics** | ~4,000 | **~17** | **~12** | **~$46** |

**On the open surface at this snapshot, the constraints scanned held almost everywhere.** Crypto and
Financials — 90,000 checks across perfectly nested ladders and 39 tiling partitions —
produced not one violation. `KXBTCY-27JAN0100` is the tightest structure on the venue:
zero fee, tenth-cent ticks, two-sided on all 28 legs, sum-of-bids 0.9960, i.e. 0.4 cents
from a riskless lock with no fee cushion at all.

The violations are concentrated almost entirely in **Elections and Politics**, and the
few found elsewhere are tick-floor artefacts (a 6-leg partition where each leg's 1-cent
minimum bid sums above the whole) rather than mispricings.

This reframes the earlier politics findings. They are not evidence that the exchange is
loosely priced; they are evidence that Elections and Politics are the one corner where
long-dated, low-attention derivative ladders sit beside actively-quoted base markets and
nobody is enforcing consistency between them. Sizes remain small — the largest single
package found by these scans is worth about $25.
