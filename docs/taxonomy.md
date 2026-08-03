# Taxonomy: how Kalshi is actually organised

Snapshot: 2026-08-02T20:52Z — 8,478 open events, 73,964 open markets, 12,370 series.

## Three layers, only one of which is load-bearing

Kalshi presents three different groupings, and they do not agree with each other.

| Layer | Where it lives | Count | Reliable? |
| --- | --- | --- | --- |
| Site navigation | kalshi.com header | 12 labels | No — a marketing surface |
| `category` | `event.category`, `series.category` | 17 values + null | No — self-contradictory (below) |
| `series` | `series_ticker`, `/series/{ticker}` | 12,370 (3,083 with open markets) | **Yes** — carries template, fee model, settlement sources |

### Site navigation does not map onto the API

The website's category bar advertises: Trending, Elections, Politics, Sports, Culture,
Crypto, Commodities, Climate, Economics, Mentions, Finance, Tech & Science.

The API's `category` field takes different values. Querying `/series?category=<label>`
with the site's labels returns `null` for four of them:

| Site label | API category | Series |
| --- | --- | --- |
| Culture | `Entertainment` | 2,490 |
| Finance | `Financials` (+ `Companies`) | 715 (+173) |
| Climate | `Climate and Weather` | 291 |
| Tech & Science | `Science and Technology` | 283 |
| Trending | *(no API equivalent — a dynamic ranking)* | — |

The API additionally exposes categories with no navigation entry at all: `World` (143
series), `Health` (96), `Social` (52), `Transportation` (38), `Exotics` (10),
`Education` (1). These are reachable by direct link but are not surfaced in the category
bar, so navigation is not a partition of the exchange.

### `category` contradicts itself

`series.category` and `event.category` disagree for over a hundred live events. The
disagreement is not random noise at the margin — it systematically affects whole families:

| `series.category` | `event.category` | Events | Examples |
| --- | --- | --- | --- |
| Financials | Companies | 31 | `KXJPMCEONEW`, `KXTAKEOVERNEE-28JAN01` |
| Politics | Elections | 22 | `KXPERSONPRESMAM-45`, `EUEXIT` |
| Financials | Economics | 20 | `KXIPOAIRTABLE`, `KXIPOWHOOP` |
| Elections | Politics | 14 | `KXNEXTDNCCHAIR-45`, `ECMOV-28NOV07` |
| Science and Technology | Health | 5 | `KXPOLIOELIM-30`, `KXFDATYPE1DIABETES-33` |
| Economics | World | 3 | `KXCBDECISIONCANADA-26OCT` |

Individual assignments are also plainly wrong: `KXPAHLAVIHEAD` — "who will lead Iran" —
is categorised `Financials` at the series level.

**Consequence for analysis.** Any study that filters by category silently gets the wrong
universe. A scan restricted to Elections + Politics misses `KXPAHLAVIHEAD` entirely; a
scan of Financials picks it up as though it were an equity market. Category is usable
for describing the exchange to a reader, never for defining a scan universe. Group by
series ticker grammar instead.

## The series is the unit of analysis

A series carries everything that determines how its markets behave:

- **Contract template** — the generator that produces leg structure and rule text
- **Fee model** — `fee_type` and `fee_multiplier`, per series (see [fee-model.md](fee-model.md))
- **Settlement sources** — the named authority whose publication resolves the contract
- **Frequency** — how new events are minted: `custom` (5,314), `one_off` (4,828),
  `annual` (1,353), `monthly` (325), `weekly` (272), `daily` (202), `hourly` (55),
  `fifteen_min` (19), `quarterly` (2)
- **Ticker grammar** — how subject, strike and date are encoded in market tickers, which
  is what makes programmatic relation extraction possible at all

Only 3,083 of 12,370 series (25%) currently have open markets. The rest are dormant
seasonal or retired series. Any inventory figure that counts all series overstates the
live exchange four-fold.

## Contract templates

Every event resolves into one of a small number of generated shapes. Classification is
inferred from leg-subtitle grammar and, for combinations, from rule text
(`classify_event()` in `src/kalshi_structure/taxonomy.py`). It does **not** currently
read `strike_type`, `custom_strike` or `mutually_exclusive`, though all three are
available and `strike_type` in particular would be a stronger signal than the subtitle
grammar for numeric ladders. Counts below are the generator label, taken over all legs
including settled ones; pass `active_only=True` for the currently tradeable shape, which
differs for 44 events whose ladders have all but one rung finalised.

| Template | Events | Leg grammar | Structural constraint it supports |
| --- | --- | --- | --- |
| `entity_menu` | 4,087 | one leg per candidate/person/team/option | sum-to-one when mutex **and** exhaustive |
| `threshold` | 2,961 | "N+ pts", "Above $X", "X or above" | nesting: higher level implies lower |
| `binary` | 1,098 | single yes/no proposition | none internally; cross-event only |
| `deadline` | 245 | "Before \<date\>" | nesting: earlier deadline implies later |
| `bucket` | 69 | "A to B" ranges tiling a line | sum-to-one when tiled |
| `combination` | 18 | conjunction of two base outcomes | marginal identities against the bases |

Template mix differs sharply by category — Mentions is 100% `entity_menu`, Crypto is
dominated by `bucket`/`threshold`, Politics is unusually `binary`-heavy (233 of 493) —
which is why the per-category documents in [categories/](categories/) treat each domain
separately.

### Exhaustiveness cannot be decided by arithmetic

A mutually exclusive partition only supports a sum-to-one constraint if its legs are
collectively exhaustive. Checking that structurally is subtler than it looks.

| Category | Tiled | `explicit` | `implicit` | `none` |
| --- | ---: | ---: | ---: | ---: |
| Crypto | 31 | 0 | 31 | 0 |
| Economics | 18 | 13 | 5 | 0 |
| Financials | 8 | 0 | 6 | 2 |
| Elections | 2 | 0 | 2 | 0 |
| Climate and Weather | 2 | 0 | 0 | 2 |
| Commodities | 1 | 1 | 0 | 0 |
| Politics | 1 | 0 | 0 | 1 |

Only 14 partitions in this snapshot carry an explicit guarantee; see
[boards.md](boards.md#exhaustiveness-graded).

Kalshi writes **closed** ranges against a **quantised** underlying. `KXGDPYEAR` lists
"0.1% to 0.5%" and then "0.6% to 1.0%"; the 0.1 gap is not a hole, because
`rules_secondary` says *"All stated bounds are inclusive"* and the statistic is
published to one decimal place. Nothing can land between the buckets.

The trap is that this cannot be checked by looking at the numbers. `KXGREENLANDPRICE`
looks like the same construction — "$1 billion to $9 billion" then "$10 billion to $99
billion" — and this repository initially recorded it as a partition with a hole, on the
reasoning that a $9.5B acquisition falls between the buckets. **That was wrong.** Its
`rules_secondary` says *"Values are rounded to the nearest $1 billion USD"*, so $9.5B
rounds into a listed bucket, and a separate sentence assigns the no-acquisition case to
the `$0` leg. The partition is exhaustive. The error survived several passes because the
gap arithmetic looked decisive and nobody re-read the clause.

Two ladders with identical gap structure can differ in exhaustiveness, and the numbers
never say which is which. Any purely numeric tiling test must
therefore either accept both or reject both, and which way it errs is decided by an
arbitrary tolerance. An early version of this repo's checker used a tolerance relative
to the *index level*, which made the verdict depend on the magnitude of the underlying
rather than its structure: it rejected GDP growth (values ~2, gap 0.1) while accepting
labour-force participation (values ~61, gap 0.1) despite identical construction. That
produced a headline finding — "16 of 18 Economics partitions have settlement gaps" —
which was entirely an artefact. The corrected figure is 18 of 20.

The working rule is therefore split in two:

1. `partition_is_tiled()` — a **necessary** condition: unbounded at both ends, no
   overlaps, and every gap negligible against neighbouring bucket widths. The bound is
   relative to bucket width, not index level, which also accommodates the segmented tick
   sizes crypto ladders use within a single event (1e-5 in the low range, 1e-4 in the
   high range).
2. `exhaustiveness_evidence()` — grades the **sufficient** condition, found only in the contract
   text: a sentence like *"rounded to one decimal place"* or *"all stated bounds are
   inclusive"*. Without it, only `sum(P) <= 1` may be used, never `== 1`.

The general lesson generalises past this one check: **displayed strikes are not
settlement strikes.** `KXGDPYEAR` shows "6.1% or Above" on a leg whose `rules_primary`
reads *"is above 6.0%"*. Never take a number that settles money from `yes_sub_title`.
