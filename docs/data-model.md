# Data model

Everything here is from the public trade API at
`https://api.elections.kalshi.com/trade-api/v2`. No authentication is required for market
data. Field notes reflect behaviour observed on 2026-07-31 → 2026-08-02.

## Object hierarchy

```
series          KXMIDTERMMOV          template, fee model, settlement sources, frequency
  └── event     KXMIDTERMMOV-NY02D    one question instance; carries mutual exclusivity
        └── market  KXMIDTERMMOV-NY02D-P2   one binary yes/no leg with its own book
```

A **market** is always binary — yes/no with a $1 payout. Multi-outcome questions are
represented as an event holding one binary market per outcome, with
`mutually_exclusive` telling you whether at most one may resolve YES.

## Fields that matter, and their traps

### Event

| Field | Note |
| --- | --- |
| `mutually_exclusive` | **The only valid gate for sum-to-one logic.** Event shape is not evidence: `KXTRUMPPARDONS-29JAN21` has 52 candidate legs and is `false`, because many people can be pardoned. |
| `collateral_return_type` | `MECNET` on netting-eligible mutex events, `DIRECNET` or empty otherwise |
| `category` | Display only — contradicts `series.category` on 100+ live events (see [taxonomy.md](../archive/docs/taxonomy.md)) |
| `settlement_sources` | Named resolving authority; present at event and series level |
| `markets` | Only populated when `with_nested_markets=true` — **and ignored for settled events**, where the array comes back empty and you must fetch via `/markets?event_ticker=` |

### Market

| Field | Note |
| --- | --- |
| `rules_primary` / `rules_secondary` | The full contract terms, already present in nested markets. `GET /markets/{ticker}` returns the same schema with no extra rules. The legal PDF lives on the **series** (`contract_terms_url`). |
| `yes_bid_dollars` / `yes_ask_dollars` | Decimal strings, not floats. A YES bid at `x` is the NO ask at `1−x` with the same size — there is one book per market, quoted from both sides. |
| `*_size_fp`, `volume_fp`, `open_interest_fp` | Fixed-point decimal strings; parse as float, do not assume integers |
| `status` | Query parameter values map to *different* field values: `unopened→initialized`, `open→active`, `paused→inactive`, `closed→closed`, `settled→finalized` |
| `result` | `''`, `'yes'` or `'no'` |
| `can_close_early` / `early_close_condition` | Load-bearing for cross-market logic — see below |
| `custom_strike` | Structured strike, e.g. `{"Candidate": "..."}` or `{"political_party": "<uuid>"}`. Party UUIDs are stable across events and are a better join key than displayed names. |
| `strike_type` | Present but has been observed mislabelled in non-mutex events; verify against `rules_primary` |

### The displayed name is not the settlement subject

`KXHOUSERACE-NY02-26-D` displays `yes_sub_title = "Patrick Halpin"` but its
`rules_primary` reads:

> "If the House member sworn in for NY-02 for the term beginning in 2027 is a member of
> the Democratic Party, then the market resolves to Yes."

It settles on **party**, not on that person. `KXCAELECTION-2640-KCAL`, by contrast,
settles on the person ("If Ken Calvert wins…"). Two markets that look identical in the
UI can have different settlement subjects, so any relation built from displayed names
without reading `rules_primary` is unsound.

### `early_close_condition` changes what a contract measures

Two series asking apparently the same question can resolve at different times:

- `KXHOUSERACE-*`: `rules_secondary` — *"eligible for accelerated determination after a
  consensus of media organizations project the winner"*
- `SENATEMI-26-D`: `early_close_condition` — *"This market will close early following
  the swearing in of the Senator for the seat in question."*
- `KXMIDTERMMOV-*`: `early_close_condition` — *"will close and expire early if certified
  election results are published."*

The House market can therefore settle on the election call while the Senate market waits
for the oath. Any implication between an election-result contract and a
who-holds-the-seat contract has a window whose width is set by these clauses, not by the
question text.

## Endpoint behaviour

| Need | Call | Caveat |
| --- | --- | --- |
| Full open universe | `/events?status=open&with_nested_markets=true&limit=200` + cursor | ~46 pages; **no server-side category filter** — `?category=` is silently ignored on `/events` |
| Series catalog | `/series` unfiltered | Returns all 12,370 in one response, no cursor |
| Series by category | `/series?category=X` | Works, but only for API category values; site labels return `null`. ~3% of returned series carry a different `.category` value than requested. |
| Newly listed markets | `/markets?min_created_ts=<unix>` | Catches new legs added to **existing** events, which event-set diffing misses |
| Retired markets | `/events?status=open` diff, confirm via `/markets?event_ticker=` | Settled events stay queryable but nested markets come back empty |
| Fee change history | `/series/fee_changes?show_historical=true` | Authoritative over the published PDF |
| Order book depth | `/markets/{ticker}/orderbook?depth=N` | Levels are under **`orderbook_fp`**, not `orderbook`; the latter is always empty. Returns `no_dollars` / `yes_dollars` as `[price, size]`, up to 50+ levels, no auth required |

## Lifecycle facts a scanner must encode

1. **Losing legs settle early inside open events.** 1,301 markets with
   `status=finalized` and `result` set were sitting inside events still listed as open.
   An N-way basket must be reduced to the still-active legs, and its floor recomputed,
   or the arithmetic is wrong.
2. **Expiry horizons run to 2099.** Politics/Elections alone: 1,253 markets closing in
   2026, 10,753 in 2027, 749 in 2028, 667 in 2029, with a tail at 2045, 2070 and 2099
   (`KXELONMARS-99`). Date handling cannot assume a near horizon.
3. **`settlement_timer_seconds` varies by domain** — 1,800s (30 min) on politics
   markets, 14s on fast-track series. It is the delay between determination and payout.
4. **Snapshots are not atomic.** Two markets fetched in sequence have different
   timestamps; any cross-market comparison needs a freshness bound and a re-verification
   against a live pull before it is believed.
