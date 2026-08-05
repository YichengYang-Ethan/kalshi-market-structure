# Layer 1: the arbitrage track

> **[中文版 →](layer1-arbitrage-guide.zh.md)**

The catalogue of every family of Kalshi markets whose settlement rules bind their
prices together — the exchange's arbitrage-capable surface, found by scanning all
~9,800 open events and verified through four audit rounds. The families and their
member events are machine-readable in `data/` and rebuildable with the tooling below.
Numbers dated 2026-08-04 drift with listings; methods do not.

## 1. What was found

42 discovered families plus 9 base mechanisms, graded after four audit rounds and a
16-agent reality check (`data/discovered_families.csv`, columns `reaudit_verdict` +
`reality_check`):

| Grade | Families | What the binding is |
| --- | --- | --- |
| REAL-EXACT | chart-rank equality (+ within-event ladders, the base mechanisms) | two-sided locks |
| REAL-ONE-DIRECTIONAL | ~13 incl. award⇒nomination, matchup-outcome splits, spread⇒moneyline, pointmass⊆ladder | one-way locks |
| CONDITIONAL | ~20 incl. the whole same-game sports lattice | locks **after** the named condition dies (see §3) |
| Salvaged-BROKEN | 8 conditional forms (player starts, game played…) | same treatment |
| NOT-REAL | 1 (pres-vp mutex) + 10 rejected look-alikes | not rule-bound — [the trap list](correlation-taxonomy.md) |

Together these generate ~28,000 independent rule-bound price constraints across the
open surface — every one a machine-checkable invariant that any pricing model, market
maker, or Layer-2 book can use as a free consistency check.

## 2. The four verification axes — run ALL before trusting any pair

Each axis exists because skipping it produced a real loss-shaped error in this project:

1. **Rule text, not display text** — legs settle on `rules_primary`; subtitles lie
   (person shown, party settled).
2. **Payout-branch parity** — cancellation/FMP/void clauses must match; a 1H leg with an
   FMP branch against a binary FT leg breaks the floor without any logical violation.
3. **Settlement-source parity** — `GET /series` both legs; ESPN-vs-FIFA splits make even
   0-0 ≡ ¬Over0.5 basis-risky. Mismatched in every sports league pair checked.
4. **Executability** — both legs two-sided AND ever-traded (`data/markets_index`);
   depth from `orderbook_fp` (the `orderbook` key is always empty); min across legs.

## 3. The condition-expiry clock — the practical edge

Most CONDITIONAL pairs promote to true locks when their condition dies **during the
event's life**: kickoff kills the cancellation branch, the posted lineup kills the
scratch branch, a confirmed single-match round kills the format branch. Monitoring the
promotion moment is cheaper than pricing the tail.

## 4. Tooling

```bash
python3 src/kalshi_structure/fetch.py       # census → ~/Developer/kalshi-research-data
python3 scripts/run_scan.py                 # all families, per-series fees, violations
python3 scripts/run_catalog.py              # price-free watchlist (relation_catalog.csv)
```

`Partition.evaluate_buy_all()` refuses non-explicit exhaustiveness and quote/leg
mismatches by construction — both were audit findings, do not bypass them.

## 5. Capacity

Strategy capacity on this surface is small: the bindings are tightly priced and the
fast end is competitive, so it cannot absorb large capital. Right-sized uses: a
monitoring-scale book over the family watchlist (transient violations do appear —
a live multi-leg basket was observed and verified during this project), the
condition-expiry promotions of §3, and — the highest-leverage use — as the risk-check
library that gates every Layer-2 correlation trade.
