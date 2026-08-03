# Elections + Politics: universe inventory

The research universe and its traded surface, as of the 2026-08-02 census. Built by
`scripts/build_universe_inventory.py`; outputs land in
`~/Developer/kalshi-research-data/elections_politics/` and are not committed.

## Defining the universe

`category` cannot define a scan universe on its own — `series.category` and
`event.category` disagree, in both directions. The universe is therefore the **union**:

```
event.category ∈ {Elections, Politics}  ∪  series.category ∈ {Elections, Politics}
```

| | Events | Markets | Series |
| --- | --- | --- | --- |
| Union universe | **2,733** | **13,699** (13,401 active) | **1,092** |
| Naive `event.category` filter | 2,719 | — | — |
| Recovered by the union | +14 | | |

The 14 recovered events are filed under `Social`, `Economics`, `World`, `Financials`,
`Companies`, `Entertainment` and `Health` at the event level while their series sits in
Elections or Politics: `KXELONMARS-99`, `EUEXPANSION`, `KXNYCBILLIONAIRES-26`,
`KXTRUMPAPOLOGY-26`, `KXSUBWAY-27`, `KXPOPCHANGESTATE10-35`, the New York gas-price
pair, and others. Every row records a `membership` column saying which side put it in
scope.

## Files

| File | Rows | Contents |
| --- | --- | --- |
| `events.csv` | 2,733 | one row per event: template, mutual exclusivity, collateral type, leg counts, volume/OI, traded flag, partition diagnostics, fee model, settlement sources, close window |
| `markets.csv` | 13,699 | one row per market: quotes, top-of-book sizes, volume/OI, traded flags, early-close condition, expiry, settlement timer |
| `rules.jsonl` | 13,699 | `rules_primary`, `rules_secondary` and `custom_strike` per market, kept separate because relation work needs the full text |
| `summary.json` | — | aggregate counts |

`markets.csv` carries three separate activity flags, because they answer different
questions: `ever_traded` (lifetime volume > 0), `traded_last_24h`, and `two_sided`
(both sides quoted right now). A market can be quoted on both sides and have never
traded — most of this universe is exactly that.

Depth beyond the touch is **not** available: `/markets/{ticker}/orderbook` returns an
empty book without authentication, so `bid_size`/`ask_size` are top-of-book only.

## Elections and Politics are two different exchanges

They share a research universe but almost nothing else, and reporting them together
hides the single most important fact about each. Split by `event_category`:

| | Elections | Politics |
| --- | --- | --- |
| Events | 2,226 | 493 |
| Series | 636 | 443 |
| **Events per series** | **3.50** | **1.11** |
| Active markets | 11,356 | 1,995 |
| **Ever traded** | **56.6%** | **95.9%** |
| Traded in 24h | 1,114 | 753 |
| Median volume of a traded market | 1,204 | 3,805 |
| Volume | 597.7M | 145.0M |

The events-per-series ratio is the tell. Elections runs at 3.5 — its series are
**generators**: one `KXHOUSERACE` template stamped out across 350 districts, one
`KXMIDTERMMOV` across 522 contests. Politics runs at 1.11 — nearly every series is a
**single bespoke question** ("Will the SAVE Act pass?", "Who is the next Attorney
General?") that is written once and never repeated.

That difference propagates into everything:

| Template share | Elections | Politics |
| --- | --- | --- |
| `entity_menu` | 49% | 18% |
| `threshold` | 46% | 12% |
| `binary` | 4% | **47%** |
| `deadline` | 1% | **21%** |

Elections is menus and ladders over races. Politics is "will this happen" and "by when",
which is why 96% of its markets trade while only 57% of Elections' do — a bespoke
question is listed because someone wanted to trade it, whereas a generated ladder leg is
listed because the template produced it.

The subject matter diverges just as sharply. By volume:

| Elections | | Politics | |
| --- | --- | --- | --- |
| `us_primary` | 45.4% | `geopolitics` | 42.5% |
| `us_local_election` | 14.7% | `personnel` | 16.7% |
| `us_federal_legislative_election` | 11.6% | `legislation` | 15.0% |
| `us_federal_executive_election` | 9.6% | `executive_action` | 7.4% |
| `us_state_election` | 9.5% | `scandal_legal` | 5.9% |

Elections' largest single markets are the 2028 nomination contests
(`KXPRESNOMD` alone is 167M contracts) and big-city mayoral races. Politics' largest are
the Strait of Hormuz and a US–Iran agreement — `KXHORMUZNORM` and `KXUSAIRANAGREEMENT`
together are 45M contracts, nearly a third of the board.

**Practical consequence:** any statistic computed over the combined universe is a
weighted average of two unlike populations, and the weights are set by Elections'
template machinery rather than by anything meaningful. Report the two boards separately.
`events.csv` and `markets.csv` carry `event_category` and `series_category` on every row
so this split is always available, and `summary.json` now reports `by_board`.

## The traded surface

Of 13,401 active markets, **8,388 (62.6%) have ever traded** and **1,876 (14.0%) traded
in the last 24 hours**. 408 events — 14.9% — have never traded at all.

Activity is not spread evenly across contract templates. It is almost entirely a
function of whether the contract is a base question or a derivative ladder:

| Template | Active | Ever traded | Traded 24h |
| --- | --- | --- | --- |
| `bucket` | 68 | 98.5% | 75.0% |
| `combination` | 56 | 98.2% | 39.3% |
| `deadline` | 404 | 96.8% | 46.3% |
| `binary` | 328 | 96.6% | 45.4% |
| `entity_menu` | 5,363 | 96.1% | 22.6% |
| **`threshold`** | **7,182** | **33.4%** | **3.6%** |

Threshold ladders are 54% of the listed universe and two-thirds of them have never
traded. Every one of the largest never-traded events is a `KXMIDTERMMOV` margin ladder
(Wyoming Governor, Wisconsin 5th, Utah 1st…), nine legs each, quoted but untouched.

Volume is correspondingly concentrated: the top 10 markets are 19.3% of all volume, the
top 50 are 49.7%, and the top 200 are 83.6%. Three 2028 presidential series
(`KXPRESNOMD`, `KXPRESPERSON`, `KXPRESNOMR`) account for 278 million contracts between
them across 114 markets.

## Why this matters for the constraint work

Earlier passes found persistent price violations between `KXMIDTERMMOV` margin ladders
and their base winner markets, and read their multi-day persistence as a slow-moving
mispricing. Given that two-thirds of threshold ladders have never traded, the obvious
hypothesis is that these violations simply sit on undiscovered quotes.

Checking it against the inventory shows that hypothesis is **only sometimes right**, and
that is the useful result:

| Pair | Derivative leg volume | OI | Traded 24h |
| --- | --- | --- | --- |
| `KXMIDTERMMOV-TX34R-P2` (largest violation, +4.29¢) | **0** | 0 | no |
| `KXMIDTERMMOV-VA06D-P3` | 178 | 178 | no |
| `KXMIDTERMMOV-NY02D-P2` | 599 | 308 | no |
| `KXMIDTERMMOV-OH07R-P1` | 7,193 | 1,567 | **yes** |
| `KXGREENTERRITORY-29` | 2,806,120 | 397,975 | **yes** |

The single largest violation found rests on a leg that has **never traded** —
a quote nobody has ever hit is not a stale price, it is a price that was never
discovered, and the "edge" exists only to the extent that quote is real and will fill.
But the Ohio pair traded 7,193 contracts and was active within the day, and the Greenland
subset violation sits on a market with 2.8 million contracts of lifetime volume. Those
are not undiscovered quotes.

So violations of the same logical family fall into at least two populations with
different meanings, and quoted spread alone cannot tell them apart. Any future study
must condition on the traded flags in this inventory and report the two populations
separately. Treating them as one — in either direction — produces a wrong conclusion.
