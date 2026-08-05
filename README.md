# kalshi-market-structure

A structural map of the Kalshi exchange: which markets are **bound together by settlement
rules** (arbitrage), and which merely **move together** (correlation). Derived from the
public trade API; every claim mechanically verified.

## Start here

- ### [Layer 1 — Arbitrage](docs/layer1-arbitrage-guide.md) · [中文](docs/layer1-arbitrage-guide.zh.md)
  The catalogue of arbitrage-capable events: ~28,000 independent rule-forced price
  constraints, organized into 42 verified families, machine-readable in `data/`.
  Strategy capacity is small — this surface cannot absorb large capital — so it serves
  as a monitoring book and the risk-check library for Layer 2.

- ### [Layer 2 — Correlation](docs/layer2-correlation-guide.md) · [中文](docs/layer2-correlation-guide.zh.md)
  Seven shared-driver classes where markets co-move without binding — lead-lag, relative
  value, cross-hedging. Re-measured 2026-08-04: a 4-day ladder lag and a 47-day (ongoing)
  crossing on the slow end. Machine-readable pair
  universes ship in [`data/layer2/`](data/layer2/), with measured dollar capacity and a
  ranked research agenda per direction. **This is the open strategy space.**

Supporting references: [correlation-taxonomy.md](docs/correlation-taxonomy.md) (the layer
definitions and the trap list), [data-model.md](docs/data-model.md) (API objects and their
traps), [fee-model.md](docs/fee-model.md) (verified fee formulas per series).

## Repository layout

```
docs/       Five documents: the two guides above + taxonomy, data model, fee model
src/        Census fetcher, template parsers, constraint logic, scanner, history collector
scripts/    fetch → build_structure_index → run_scan / run_catalog / build_layer2_pairs
data/       Identifiers + derived classifications only; layer2/ pair universes
tests/      Regression tests for every parser failure this project hit
```

## Data policy

Kalshi's terms prohibit redistribution of exchange data. **No market data is committed** —
no prices, sizes, volumes, or rule text. `data/` carries only event/market identifiers
plus the classifications this repository derives from them. Raw snapshots live outside
the working tree.

## Reproducing

```bash
python3 src/kalshi_structure/fetch.py     # writes ~/Developer/kalshi-research-data/
```

No authentication required — all endpoints used are public market data.
