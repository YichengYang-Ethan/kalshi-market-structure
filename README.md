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

## What the first full pass found

A census of the exchange's **open surface** on 2026-08-02 — 8,478 open events, 73,964
open markets, 12,370 series — followed by roughly 120,000 executable constraint checks.
Settled events are excluded: a full crawl found **516,232** of them, so this census
covers **1.6%** of everything the exchange has listed and nothing below is a statement
about its history:

- **The constraints scanned held almost everywhere on that surface.** Crypto and
  Financials produced zero violations across ~90,600 checks. Sports produced two, both
  tick-floor artefacts, together worth under $0.42. The price inputs are not committed,
  so these totals are not reproducible from this repository alone.
- **Violations concentrate in Elections and Politics** (~12 surviving fees, ~$46 total).
  Not because the venue is loose, but because that is the one corner where long-dated,
  low-attention derivative ladders sit beside actively-quoted base markets with nobody
  enforcing consistency between them.
- **Category is not a usable grouping key.** `series.category` and `event.category`
  disagree on 100+ live events, and "who will lead Iran" is filed under `Financials`.
- **Exhaustiveness cannot be decided arithmetically.** A quantised ladder and a ladder
  with a genuine settlement hole are indistinguishable by numbers alone; only the
  contract text separates them. An early tolerance bug here manufactured a false
  finding, documented in [taxonomy.md](docs/taxonomy.md).
- **Displayed text is not the contract.** A market showing a candidate's name settles on
  party; a leg showing "6.1% or Above" settles at "above 6.0%"; a series called
  `SENATELA-26` is titled "Kentucky Senate winner?" and settles on Kentucky.

Start with [settlement-patterns.md](docs/settlement-patterns.md) for the synthesis, then
the per-category profiles.

## Repository layout

```
docs/
  taxonomy.md              Site navigation vs API categories; the series as unit of analysis
  data-model.md            Series / event / market object model and field semantics
  fee-model.md             Verified fee formulas, per-series overrides, collateral netting
  settlement-patterns.md   Contract-template grammar and the constraint grammar it implies
  boards.md                Every API category compared on the same measurements
  verification.md          Every asserted count with the public API call that reproduces it
  scan-results.md          What a full constraint scan of the open surface returns
  relation-catalog.md      Every arbitrage-capable structure, price-free (the watchlist)
  discovered-families.md   41 new relation families found by parallel discovery + verify
  correlation-taxonomy.md  The four layers of relatedness between Kalshi markets
  capacity-analysis.md     Pricing the confirmed families: zero tradeable capacity, and why
  audit-response.md        External audit findings, verification, and what changed
  universe-inventory.md    Elections + Politics universe and its traded surface
  classification.md        The research taxonomy and its coverage
  categories/*.md          Per-category structural profile
src/kalshi_structure/
  fetch.py                 Full-exchange census fetcher (category-sharded output)
  universe.py              Union definition of the Elections + Politics universe
  taxonomy.py              Contract-template detection and partition diagnostics
  classify.py              Deterministic research taxonomy (domain, subject, authority)
  relations.py             Settlement-logic constraints and their fee-aware economics
  history.py               Candlestick / trade-tape collection with checkpointing
scripts/                   Analysis entry points (profile, inventory, classification)
tests/                     Regression tests for every parser grammar that once failed
data/                      Structure index: identifiers + derived classifications only
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

This is also why [verification.md](docs/verification.md) publishes assertions and the
calls that regenerate them rather than the corpus itself. Handing a reviewer the data
lets them check it is internally consistent; it cannot reveal that an entire slice was
never fetched. Independent reproduction can.

## Reproducing

```bash
python3 src/kalshi_structure/fetch.py     # writes ~/Developer/kalshi-research-data/
```

No authentication is required — all endpoints used are public market data.
