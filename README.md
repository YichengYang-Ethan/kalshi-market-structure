# kalshi-market-structure

A systematic map of how the Kalshi exchange is actually built — its taxonomy, contract
archetypes, settlement-rule grammar, fee surface, and the cross-market logical constraints
those things imply — derived from the public trade API rather than from the website's
marketing surface.

**Status:** active research. Private by design (see [Data policy](#data-policy)).

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

## Repository layout

```
docs/
  taxonomy.md              Site navigation vs API categories; the series as unit of analysis
  data-model.md            Series / event / market object model and field semantics
  fee-model.md             Verified fee formulas, per-series overrides, collateral netting
  settlement-patterns.md   Contract-template grammar and rule-text archetypes
  categories/*.md          Per-category structural profile (one file per API category)
src/kalshi_structure/
  fetch.py                 Full-exchange census fetcher (category-sharded output)
  taxonomy.py              Series/event classification and template detection
  relations.py             Cross-market logical relation extraction
  scan.py                  Constraint-violation scanner with fee-aware economics
scripts/                   One-off analysis entry points
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

## Reproducing

```bash
python3 src/kalshi_structure/fetch.py     # writes ~/Developer/kalshi-research-data/
```

No authentication is required — all endpoints used are public market data.
