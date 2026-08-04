# kalshi-market-structure

A systematic map of how the Kalshi exchange is actually built — its taxonomy, contract
archetypes, settlement-rule grammar, fee surface, and the cross-market logical constraints
those things imply — derived from the public trade API rather than from the website's
marketing surface.

**Status:** research handoff. **New readers: begin at [docs/START-HERE.md](docs/START-HERE.md)** —
it routes you to the arbitrage track, the correlation track, or the audit record.

## Why this exists

Most work on prediction markets starts from a strategy and looks for markets to run it on.
This repo inverts that: it starts from the *structure* of the exchange and asks what the
structure itself makes possible. Concretely:

- The website's navigation categories are **not** the API's categories. The mapping is
  lossy in both directions, and category is the wrong primitive for analysis anyway —
  the `series` is.
- Kalshi's contract terms are generated from a small number of **templates**
  (`ELECTION`, `ELECTIONMOV`, threshold ladders, mutually-exclusive menus, combination
  contracts). Once the templates are enumerated, a large fraction of settlement behavior
  becomes predictable from metadata alone.
- Where two markets are generated from templates over the same underlying fact, their
  prices are bound by **settlement logic**, not merely correlated. Those bindings are
  machine-checkable at scale.
- The fee surface is not uniform: a per-series `fee_multiplier` (including zero-fee
  series) and a maker/taker asymmetry change which structures are economically live.

## What it found, in three sentences

1. **Binding (Layer 1):** ~28,000 independent rule-forced constraints; the market holds
   them tight — standing riskless capacity ≈ $0, transient exact arb ~$0.64 best
   observed, a millisecond-scale harvester already works the fast end.
2. **Shared drivers (Layer 2):** 539 multi-market game clusters, 505 race clusters,
   20 underlying window families; measured lead-lag of 3–8 days on the slow end — this
   is the open strategy space, with pair universes in `data/layer2/`.
3. **Spurious (Layer 3):** 10+ documented look-alike relations with refuting states —
   the do-not-trade list and the QC gate for any new relation.

Full findings, per-board profiles and the complete audit trail: [`archive/`](archive/).

## Repository layout

```
docs/
  START-HERE.md            Entry point — routes by intent
  layer1-arbitrage-guide.md   The binding surface: families, verification axes, capacity
  layer2-correlation-guide.md The shared-driver surface: seven classes, measured dynamics
  correlation-taxonomy.md  The three layers of relatedness, with the trap list
  data-model.md            API object model, field semantics, and their traps
  fee-model.md             Verified fee formulas, per-series overrides, collateral rules
  audit-response.md        Four external audit rounds: findings, verification, changes
src/kalshi_structure/      Census, parsers, constraints, scanner, history collector
scripts/                   fetch → build_structure_index → run_scan / run_catalog / build_layer2_pairs
data/                      Identifiers + classifications only; layer2/ pair universes
tests/                     Regression tests for every failure this project hit
archive/                   The full research log (unmaintained, kept for audit)
```

## Method

1. **Census** — paginate every open event with nested markets plus the full series
   catalog; shard by category so no analysis step needs the whole corpus in memory.
2. **Classify** — group series by contract template inferred from ticker grammar,
   `strike_type`, `custom_strike`, leg-subtitle shape, and rule text.
3. **Profile** — per category: series families, market-type mix, settlement sources,
   liquidity distribution, expiry horizon, fee surface.
4. **Constrain** — for each template pair, state the settlement-logic relation as an
   explicit price inequality, record which rule clause makes it exact, and record the
   scenarios where it fails.
5. **Scan** — evaluate constraints against live books with correct per-series fees and
   executable depth; every reported violation is re-verified live before it is believed.

Findings are only recorded here after mechanical verification. Claims sourced from a
language model are marked as such and are not treated as evidence.

## Data policy

Kalshi's terms prohibit redistribution of exchange data. **No market data is committed
to this repository** — `.gitignore` excludes all data formats, and snapshots live outside
the working tree. What is committed: code, schemas, documented structure, and analysis
conclusions expressed in aggregate.

`data/` carries the one publishable slice: every event and market identifier with the
template, partition and activity classifications this repository derives, and with every
price, size, volume and contract text stripped. Those classifications are inferences and
are the most likely thing here to be wrong, which is why they are published in full.

This is also why [verification.md](archive/docs/verification.md) publishes assertions and the
calls that regenerate them rather than the corpus itself. Handing a reviewer the data
lets them check it is internally consistent; it cannot reveal that an entire slice was
never fetched. Independent reproduction can.

## Reproducing

```bash
python3 src/kalshi_structure/fetch.py     # writes ~/Developer/kalshi-research-data/
```

No authentication is required — all endpoints used are public market data.
