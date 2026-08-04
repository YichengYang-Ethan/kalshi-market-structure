# The arbitrage-capable surface

`scripts/run_catalog.py` enumerates every structure on the exchange whose settlement
rules bind two or more contract prices together, so that any future price divergence is
an arbitrage. It reads **no prices**. A relation is here because the rules make it
*possible* for an arb to appear, not because one exists today.

This is the monitoring surface, and it is what "how many opportunities are there" actually
asks. The scanner (`scan.py`) watches this surface and fires on the handful that are
divergent at any moment; the catalogue is the whole watchlist.

## The count

On the 2026-08-03 snapshot (9,410 open events):

| Family | What binds the prices | Relations |
| --- | --- | ---: |
| `P1-mutex` | at most one leg wins → NO-basket floors at n−1 | **3,978** |
| `L-threshold` | nested thresholds on one subject | **3,685** |
| `X-margin-winner` | a margin leg implies its party won the seat | 425 |
| `L-deadline` | earlier deadline implies later | 250 |
| `D-duplicate` | identical rules/close/expiration under two tickers | 51 |
| `C-combination` | 2×2 combination equals a sum of its legs | 18 |
| `P2-exhaustive` | tiled + explicit precision → YES-basket = $1 | 14 |
| `S-semantic` | one resolution condition contained in another | 1 |
| **Total** | | **8,422** |

A ladder of n legs is n(n−1)/2 pairwise constraints, and the ladder events' full closure
ran to **351,909 pairs** on this snapshot (854,085 a day later, when 400-leg hourly index
ladders were open — the closure swings with the hour). Three honesty notes on that number:
the **independent** constraint count is Σ(n−1) ≈ **28,000** (chains imply the rest by
transitivity); **85% of the closure sits in the top 50 events** (hourly Nasdaq and crypto
ladders, the tightest-priced products on the venue); and pairs where both legs have ever
traded number ≈ **68,000**. Quote the 28k figure, not the closure.

By board, the surface follows the generators: Sports (4,246) and Elections (2,536) carry
80% of it, because their templates stamp out ladders and mutex menus at scale.

## What the number does and does not mean

**It means:** there are ~8,400 standing relations and ~350,000 price constraints worth
monitoring continuously. That is a large, real surface, and it is stable — it changes
only when Kalshi lists or settles events, not when quotes move.

**It does not mean 8,400 arbs exist today.** A constraint being *monitorable* is different
from being *violated*. On the same snapshot the price scanner found ~11 net-positive
violations, most of them a few cents on low-liquidity legs. The gap between 8,422 capable
and ~11 live is the whole point: the exchange holds its constraints tight almost
everywhere, and the value is in watching the large surface so you catch the rare, brief
divergence when it happens — typically on a news day that reprices one leg before the
other follows.

## The reliability gradient

Not every catalogued relation is equally trustworthy, and the catalogue records why:

- **Price-free certain** — `P2-exhaustive` (14). A tiled partition with an explicit
  precision clause is a synthetic $1 by the rules alone. These are the only relations
  where the floor needs no price to be certain, and they are almost all the annual GDP
  ladders plus `KXWTIW`, `KXLFPRATE`, `KXM2GROWTH`, `KXPSAVERT`, `KXSCFI`.
- **Structurally certain** — `P1-mutex` (3,978) and the ladders (3,935). The
  at-most-one-wins floor and the nesting are guaranteed by the flag and the grammar; only
  execution (all legs quoted, fills) is uncertain.
- **Rule-verified** — `S-semantic` (1), `D-duplicate` same-stem. Checked by reading the
  contract text.
- **Monitor, do not trust as a lock** — `X-margin-winner` (425). The implication is real
  but the family is BROKEN: a certified winner can switch party before the oath. Watch
  for divergence, price the tail before acting.
- **Candidate** — `D-duplicate` cross-stem. Identical rules that may omit the
  distinguishing subject (`KXUSTESTSREADING` / `KXUSTESTSMATH` never say reading or math).
  Verify the underlying is the same before treating as one contract.

## Reproduce

```bash
python3 scripts/run_catalog.py    # writes data/relation_catalog.csv, no prices read
```

The full catalogue is published at `data/relation_catalog.csv` — 8,422 rows, each a
relation with its family, the members, the rule that binds them, and the caveat.
