# Capacity analysis: the confirmed families price to zero

The eight relation families that survived three audits were priced against the live
order book (full depth via `orderbook_fp`) and each was adversarially debated by a
separate agent instructed to attack the capacity number. Snapshot 2026-08-04T06:02Z.

## Result

| Family | Live instances | Net-positive | Capacity | Verdict |
| --- | ---: | ---: | ---: | --- |
| `award-nom-win` | 189 | 0 | $0 | ILLUSORY |
| `teamtotal-implies-total` | 520 | 0 | $0 | ILLUSORY |
| `btts-implies-teamtotal` | 118 | 0 | $0 | ILLUSORY |
| `correct-score-refines-outcome` | 21,240 | 0 | $0 | ILLUSORY |
| `severity-nested-count` | 7 | 0 | $0 | ILLUSORY |
| `chart-rank-equality` | 14 | 0 | $0 | ILLUSORY |
| `yt-window-nest` | 21 | 0 | $0 | ILLUSORY |
| `all-of-threshold-vector-dominance` | 1 | 0 | $0 | ILLUSORY |
| **Total** | **22,110** | **0** | **$0** | |

Twenty-two thousand structurally present instances, zero tradeable. The debate did not
reach this by "fees ate a thin edge" — it reached it structurally, and the reason is the
same one that made these families survive the audits.

## Why exact and tradeable are nearly mutually exclusive here

Every confirmed family is a **logical identity or near-identity**: winning an award is a
subset of being nominated; both teams scoring is a subset of one team scoring; a major
hurricane is a subset of a named storm; a weekly window is a subset of the month; a
stricter threshold vector is a subset of a looser one. That is exactly why they passed
three rounds of settlement-rule audit — the containment is guaranteed by the words.

But a lock on `A ⊆ B` requires buying B-YES and A-NO for less than $1, which needs the
**subset priced richer than the superset** — the book saying winning is more likely than
being nominated. That is not a fleeting mispricing; it is a statement no attentive market
maker ever posts, because the containment is *obvious*. Across all 189 award pairs, all
118 BTTS pairs, all 7 hurricane pairs, the books are correctly ordered with the no-arb
gap sitting 3 to 77 cents on the safe side. The relation is real and the violation is
structurally absent.

**The more obviously exact a relation is, the more reliably the market already respects
it.** The families rigorous enough to survive audit are precisely the ones too obvious to
be mispriced. This is not a failure of the search; it is what the search converged to.

## Two findings from the debate worth keeping

1. **The equalities carry settlement-source basis risk.** `correct-score` was the largest
   family by instance count (21,240) and the pricing agent marked its 0-0 ≡ Under-0.5
   equality as a clean lock. The debate verified it is not: for the same game,
   `KXLEAGUESCUPSCORE` settles off **ESPN** and `KXLEAGUESCUPTOTAL` settles off **FIFA**
   (confirmed live). Two sources can disagree on a goal (VAR, disallowed, own-goal
   attribution), so even a logically identical pair is basis risk, not riskless
   arbitrage. Settlement *source* must be checked alongside settlement *rules* — a
   relation-verification axis this project had not been using.

2. **Some locks are unbuyable, not just unprofitable.** `chart-rank-equality` needs a NO
   leg, which on Kalshi means lifting resting YES bids; all 28 books have empty
   `yes_dollars`, so the NO side cannot be bought at any size. The relation is correctly
   priced and also structurally inexecutable.

## The complete picture across the whole investigation

- **Confirmed-exact families (identities): ~$0 capacity, structurally.** Identities are
  priced correctly by construction.
- **Broken families (e.g. margin → winner): transient violations do appear** — a few
  cents, low depth, on news days when one leg reprices before the other — but they are
  not riskless, because the relation has a real settlement tail (a certified winner can
  switch party before the oath).
- **Net: there is no riskless-arbitrage strategy with meaningful capacity on this
  exchange.** The tightly-priced identities offer no edge; the only edges that appear
  carry a tail and micro capacity.

This reproduces, at maximum rigor and across the whole exchange, the conclusion the
earlier World Cup work reached on one corner: riskless but breakeven, do not scale. The
value of the structural map is not a standing arbitrage book — it is knowing, with proof,
that there isn't one.
