# Economics and Commodities

Structural profile of the `Economics` and `Commodities` API categories.
Snapshot: **2026-08-02T20:52Z**. All prices are top-of-book from that snapshot;
every "live check" below is reproducible from it.

Fee model used throughout (verified against the schedule effective 2026-07-07 and the
live `/series` endpoint): taker fee per contract per leg =
`ceil_to_centicent(fee_multiplier * 0.07 * P * (1-P))`; maker fee = 0 unless
`fee_type == 'quadratic_with_maker_fees'` (coefficient 0.0175); no settlement fee.
`fee_multiplier == 0` means the series is free on both sides.

---

## Inventory — events, markets, series count; how much of the exchange this is

| | events | markets | active markets | distinct series with live events |
|---|---|---|---|---|
| Economics | 352 | 3,337 | 3,265 | 228 |
| Commodities | 29 | 807 | 801 | 26 |
| **slice total** | **381** | **4,144** | **4,066** | **254** |
| exchange total | 8,478 | 73,964 | — | — |
| slice share | 4.5% | **5.6%** | — | — |

Economics alone is 4.5% of exchange markets (5th largest category by markets, behind
Sports 47.8%, Elections 15.5%, Financials 11.0%, Entertainment 9.2%). Commodities is
1.1% of markets but only 29 events — it is the most *market-dense* category in the
exchange (27.8 markets/event vs 8.7 exchange-wide), because almost every Commodities
event is a 20–90-rung price ladder.

`series.json` catalogues 614 series with `category == "Economics"` and 77 with
`category == "Commodities"`; only 228 and 26 respectively have a live event in this
snapshot (37% and 34%). The rest are dormant templates.

**Category labels disagree with each other.** Of the 352 events in the `Economics`
shard, 329 belong to a series whose `series.category` is also `Economics`, but **20 belong
to `Financials` series and 3 to `Politics` series**. Conversely the `Commodities` shard
contains six AI-token-price series (`KXOPUS48Y`, `KXOPUS48OY`, `KXGPT55Y`, `KXGBT55OY`,
`KXGEMINI35Y`, `KXGEMINI35OY` — "How low will the Claude Opus 4.8 input token price get
in 2026?", settled off `Anthropic` / `OpenAI` / `Google Gemini Developer API pricing`)
which are commodities only by analogy. The `Economics` shard likewise contains
`KXFLYCANCJFK` (JFK flight cancellations — the 2nd-largest open-interest series in the
whole category), `KXCOSTCOHOTDOG`, `KXBKNUGGETS`, `KXPOPCHICKSAND`, `KXAKSALMON`,
`KXNETWORTHROYLEE`, and a 17-series IPO-timing block. **Neither category field is a safe
grouping key; the series ticker prefix is.**

Active-market status mix: `active` 4,066, `finalized` 76, `closed` 1. 78 non-active legs
sit inside 30 otherwise-open events (see Traps).

---

## Series families — what they actually do

Grouped by function, not by label. Counts are markets in this snapshot.

### 1. US macro release ladders — "one series per statistic per reference month"

| Series | events | mkts | template | fee | frequency | what settles it |
|---|---|---|---|---|---|---|
| `KXCPI` | 5 | 50 | threshold `Above X%` | **maker-fee** | monthly | BLS CPI-U MoM |
| `KXCPICORE` | 5 | 55 | threshold | quadratic | monthly | BLS core CPI MoM |
| `KXCPIYOY` | 4 | 89 | threshold | **maker-fee** | monthly | BLS CPI-U YoY |
| `KXCPICOREYOY` | 4 | 61 | threshold | quadratic | monthly | BLS core CPI YoY |
| `KXCPINDEX` | 1 | 18 | threshold on the **index level** (`Above 333.4`) | quadratic | monthly | BLS CPI-U index |
| `KXU3` | 5 | 70 | threshold `Above X%` | **maker-fee** | monthly | BLS U-3, Employment Situation |
| `KXUE` | 9 | 78 | threshold | quadratic | monthly | unemployment, incl. non-US (`KXUE-CHN26JUL`) |
| `KXPAYROLLS` | 5 | 65 | threshold | **maker-fee** | monthly | BLS nonfarm payrolls |
| `KXADP` | 5 | 35 | threshold | quadratic | custom | ADP employment change |
| `KXPCECORE` | 5 | 30 | threshold | quadratic | monthly | BEA core PCE |
| `KXGDP` | 4 | 36 | threshold | **maker-fee** | custom | BEA quarterly GDP |
| `KXGDPNOM` | 12 | 158 | threshold | quadratic | one_off | nominal GDP level |
| `KXJOBLESSCLAIMS`, `KXISMPMI`, `KXUSPPIYOY`, `KXUSRETAIL`, `KXHOUSINGSTART`, `KXBUILDPERMS`, `KXNHSALES`, `KXEHSALES`, `KXLFPRATE`, `KXPSAVERT`, `KXM2GROWTH`, `KXSAHM`, `KXTEMPHELP` | 1 each | 1–7 | threshold / bucket | quadratic | mixed | one release each |

Ticker grammar: `KX<STAT>-<YY><MON>-T<strike>`.
`KXCPICORE-26JUL-T0.3` = core CPI, **reference month** July 2026, "Above 0.3%".
The `T` prefix marks a one-sided threshold; the numeric tail is the strike written exactly
as it appears in the rule text. Negative strikes drop the `T` and keep the sign in a
mangled form: `KXCPI-26JUL-T-0.4` for "Above -0.4%" but also bare `KXCPI-26AUG-0.4`
appears — do not assume a stable prefix, parse from the right.

There is a second, structurally different generation of the same statistics:

| Series | events | mkts | template | leg grammar |
|---|---|---|---|---|
| `KXECONSTATCPI` | 5 | 46 | **point-mass menu**, mutex | `Exactly 0.1%` |
| `KXECONSTATCPICORE` | 5 | 45 | point-mass menu, mutex | `Exactly 0.2%` |
| `KXECONSTATCPIYOY` | 4 | 84 | point-mass menu, mutex | `Exactly 2.4%` |
| `KXECONSTATCORECPIYOY` | 4 | 64 | point-mass menu, mutex | `Exactly 2.8%` |
| `KXECONSTATU3` | 5 | 115 | point-mass menu, mutex | `Exactly 4.3%` |

Ticker grammar `KXECONSTAT<STAT>-<YY><MON>-T<value>` (with `-0.2` rendered as the tail
`0.2` on the negative legs, e.g. `KXECONSTATCPI-26JUL-T-0.2`). These are the **same
release** as the `KX<STAT>` ladders — `KXECONSTATU3-26SEP` and `KXU3-26SEP` have identical
`close_time` (2026-10-02T12:29:00Z) and identical `expiration_time`
(2027-01-01T14:00:00Z) — expressed as a partition of the printed value rather than a
ladder of thresholds. That duality is the source of the strongest constraints in the
category (§ Structural constraints C3).

### 2. Fed policy complex

| Series | events | mkts | template | fee | leg grammar |
|---|---|---|---|---|---|
| `KXFED` | 6 | 87 | threshold on post-meeting rate | **maker-fee** | `Above 3.75%` |
| `KXFEDDECISION` | 12 | 60 | mutex 5-way action menu | **maker-fee** | `Cut >25bps / Cut 25bps / Fed maintains rate / Hike 25bps / Hike >25bps` |
| `KXFEDFUNDSYEAR` | 10 | 210 | threshold on year-end rate | quadratic | `Above 2.50%` |
| `KXEFFR` | 1 | 5 | threshold on **effective** FF rate | quadratic | `Above 3.50%` |
| `KXRATECUTCOUNT` | 1 | 21 | mutex count menu | **maker-fee** | `Exactly 3 cuts` |
| `KXFEDCHGCOUNT` | 1 | 13 | mutex count menu | quadratic | `Exactly 2` |
| `KXFOMCDISSENTCOUNT` | 1 | 5 | mutex count menu | quadratic | `0 … 4` |
| `KXFEDDISSENT` | 1 | 12 | **non-mutex** person menu | quadratic | `Michelle Bowman` |
| `KXFEDCOMBO` | 1 | 6 | mutex 3×2 combination | quadratic | `Rate: 25bp cut, Dissents: >0` |
| `KXDOTPLOT` / `KXDOTPLOTPUB` | 2 | 13 | threshold on median dot | quadratic | `Above 3.8%` |
| `KXRATECUT`, `KXLARGECUT`, `KXFEDHIKE`, `KXZERORATE`, `KXFEDMEET`, `KXEMERCUTS`, `KXBALANCESHEET` | 1 each | 1–12 | binary / deadline / threshold | quadratic | mixed |

Ticker grammar: `KXFED-<YY><MON>` and `KXFEDDECISION-<YY><MON>` key on the **FOMC meeting
month**, and the two are paired 1:1 for the six meetings that have both. `KXFEDFUNDSYEAR`
keys on the **January 1 following** the year in question: `KXFEDFUNDSYEAR-28JAN01` is
"Fed funds rate at end of **2027**" — an off-by-one that a scanner must encode.
`KXFEDDECISION` leg suffixes are `C26 / C25 / H0 / H25 / H26` where `C`=cut, `H`=hike,
`0`=no change, `25`=exactly 25bp, `26`=strictly more than 25bp.

The foreign central-bank clones share the grammar: `KXCBDECISION<COUNTRY>-<YY><MON><DD>`
(`EU, JAPAN, ENGLAND, KOREA, INDIA, BRAZIL, MEXICO, AUSTRALIA, NZ, RUSSIA`), plus
`KXCBDSA`, `KXCBDISRAEL`, `KXCBRATEHIKE`, `KXCANCUTS`, `KXBRRATECUT`, `KXCHCUTS`,
`KXCHAICUTS`, `KXEMERCUTS`. All are mutex 5–7-leg action menus, all `quadratic`.

### 3. Multi-year annual-outcome partitions (the zero-fee block)

| Series | events | mkts | fee_multiplier | template |
|---|---|---|---|---|
| `KXGDPYEAR` | 11 | 154 | **0 (free both sides)** | mutex 14-leg bucket partition, one event per calendar year 2026–2036 |
| `KXLAYOFFSYINFO` | 1 | 1 | **0** | single binary |
| `KXCITRINI` | 0 | 0 | **0** | Economics-category series, no live event in snapshot |
| `KXUSCPIYEAR` | 10 | 130 | 1 | threshold ladder, year-end CPI |
| `KXFEDFUNDSYEAR` | 10 | 210 | 1 | threshold ladder, year-end rate |

`KXGDPYEAR-<YY>` where `<YY>` is the two-digit calendar year (`KXGDPYEAR-26` = 2026).
Legs `T0.1` (bottom), `B<midpoint>` for the 12 interior buckets, `T6.0` (top) — the `B`
suffix is the **bucket midpoint**, not an endpoint: `KXGDPYEAR-26-B2.3` is the
"2.1% to 2.5%" leg. `KXUSCPIYEAR-<YY+1>FEB01` and `KXFEDFUNDSYEAR-<YY+1>JAN01` both key
on the settlement date, not the reference year.

These three zero-fee series are the only ones in the slice where a basket trade is not
immediately fee-dominated. `KXCITRINI` ("Will the Citrini scenario materialize?",
`contract_terms_url` → `POLITICALOUTCOMESINSET.pdf`) has `fee_multiplier: 0` and
`fee_type: quadratic` but no open event.

### 4. Commodity price ladders

| Family | series | mkts | horizon | settlement source |
|---|---|---|---|---|
| Daily | `KXGOLDD` 40, `KXSILVERD` 40, `KXCOPPERD` 50, `KXNATGASD` 90, `KXBRENTD` 30 | 250 | next session | Pyth |
| Weekly | `KXGOLDW` 40, `KXSILVERW` 40, `KXCOPPERW` 40, `KXNATGASW` 40, `KXBRENTW` 20 | 180 | Friday | Pyth |
| Monthly | `KXGOLDMON` 40, `KXSILVERMON` 40, `KXCOPPERMON` 40, `KXNATGASMON` 40, `KXBRENTMON` 20 | 180 | month-end | Pyth |
| WTI | `KXWTI` 3 ev/105, `KXWTIW` 27, `KXWTIDIRY` 11, `KXWTIWHEN` 2 ev/17 | 160 | daily/weekly/year-end/first-touch | ICE |
| Direction-to-year-end | `KXGOLDDIRY` 13, `KXWTIDIRY` 11 | 24 | Dec 31 2026 | Pyth / ICE |
| AI token prices | `KXOPUS48Y/OY`, `KXGPT55Y`, `KXGBT55OY`, `KXGEMINI35Y/OY` | 24 | 2026 | vendor price pages |

Ticker grammar: `KX<ASSET><D|W|MON>-<YY><MON><DD><HH>` — the trailing two digits are the
**observation hour in ET**: `KXGOLDMON-26AUG3117` = gold on 2026-08-31 at 17:00 EDT.
Legs are `T<strike>` for `Above $X`. `KXWTIW-26AUG0714` uses `14` (14:30 ET settle) and
is the one mutex bucket event in Commodities (`T<floor>` / `B<midpoint>` / `T<cap>`).
`KXWTIDIRY-26DEC31H1430` inserts an explicit `H<HHMM>`.
`KXWTIWHEN-<level>` is a *first-touch deadline ladder* keyed on the price level, with
legs `-<YY><MON><DD>`: `KXWTIWHEN-100-26DEC31` = "WTI front-month settle above \$100 on
any market day through Dec 31 2026".

Every commodity series in the slice is `fee_type: quadratic`, `fee_multiplier: 1`.

### 5. Gasoline / consumer-price ladders

`KXAAAGASD` (17), `KXAAAGASW` (29), `KXAAAGASM` (26, **maker-fee**), `KXAAAGASED` (11,
election day), `KXAAAGASMAX` (13), `KXAAAGASMIN` (9), plus per-state
`KXAAAGASMAX{CA,FL,NY,TX}` / `KXAAAGASMIN{CA,FL,NY,TX}`. All settle on "average regular
gas prices … according to AAA". `KXAAAGASMAX`/`MIN` are running-extremum ladders over the
calendar year ("the maximum price … at any time from Issuance through Dec 31").
**`KXAAAGASD-26AUG03` and `KXAAAGASW-26AUG03` settle on the identical fact** (see C1).

### 6. Deadline ladders — IPO timing and first-touch

17 `KXIPO*` / `KXSTRIPEIPO` / `KXFREDDIE` series, 13 legs each, one leg per month:
`KXIPOOPENAI-27JAN01` … Template `Before <Mon> <D>, <YYYY>`. Plus `KXWTIWHEN`,
`KXFEDHIKE`, `KXMEXCUBOIL`, `KXCOSTCOHOTDOG`. 23 deadline-ladder events, 170 nested pairs.

### 7. Combination contracts

`KXCPICOMBO` (15 legs = 5 headline × 3 core), `KXFEDCOMBO` (6 = 3 rate × 2 dissent),
`KXEMPLOYMENTCOMBO` (12). Ticker tails encode the cell:
`KXCPICOMBO-26JULB-0203` = headline exactly 0.2%, core 0.3% or above;
`N0101` = headline −0.1% or below, core 0.1% or below (the leading `N` is the sign).
`KXFEDCOMBO-26SEPB-25C-T0` = 25bp cut × more-than-zero dissents. The `B` before the leg
suffix is a series revision marker, not a date.

### 8. Long-tail one-offs (≈130 series, 1 event each)

Recession calls (`KXRECSSNBER`, `KXNBERRECESSQ`, `KXWRECSS`, `KXIMFRECESS`, `KXSAHM`),
net-worth ladders (`KXMUSKNW`, `KXMUSKWEALTH`, `KXNWSAYLOR`, `KXNEXTTRILLIONAIRE`,
`KXTOP3WEALTH`), housing (`KXUSHOME`, `KXCANHOME`, `KXVANCONDO`, `KXTORCONDO`,
`KXMTLHOME`, `KXEDMHOME`, `KXOTTAWAHOME`, `KXCALHOME`, `KXFM30YMTG`, `KXMORTGAGERATE`),
trade/tariffs (`KXEFFTARIFF`, `KXTARIFFREVENUE`, `KXTRADEDEFICIT`, `KXCNIMPORT`,
`KXIRANIMPORTS`), social-media post counts (`KXFEDTWEETS`, `KXIMFTWEETS`, `KXWEFTWEETS`),
groceries (`KXEGGS` **maker-fee**, `KXAMSAVO`, `KXCOSTCOHOTDOG`, `KXBKNUGGETS`).

**Fee surface for the whole slice:** 244 series `quadratic`, 10
`quadratic_with_maker_fees` (`KXAAAGASM`, `KXCPI`, `KXCPIYOY`, `KXEGGS`, `KXFED`,
`KXFEDDECISION`, `KXGDP`, `KXPAYROLLS`, `KXRATECUTCOUNT`, `KXU3`), 252 with
`fee_multiplier == 1`, **2 with `fee_multiplier == 0`** (`KXGDPYEAR`, `KXLAYOFFSYINFO`).
Frequency: `one_off` 67, `custom` 65, `annual` 57, `monthly` 43, `weekly` 14, `daily` 7,
`quarterly` 1.

---

## Contract templates and their leg grammar

`classify_event()` over the slice returns:

| template | Economics | Commodities |
|---|---|---|
| `threshold` | 188 | 20 |
| `entity_menu` | 68 | 7 |
| `binary` | 56 | 0 |
| `deadline` | 22 | 1 |
| `bucket` | 18 | 1 |

`market_type` is `binary` for all 4,144 markets. `strike_type` mix: Economics `greater`
2,029, `custom` 743, `between` 232, null 157, `greater_or_equal` 115, `less` 61;
Commodities `greater` 740, `between` 25, `less_or_equal` 24, null 17, `less` 1.

### T1 — One-sided threshold ladder (`strike_type: greater`) — 208 events, 2,877 legs

Legs `Above X` at a fixed step, non-mutex, `collateral_return_type: DIRECNET`.

> `KXCPICORE-26JUL-T0.2` — "If the seasonally adjusted Consumer Price Index for All Urban
> Consumers: All Items less Food and Energy for July 2026, as published by the Bureau of
> Labor Statistics, increases by above 0.2%, then the market resolves to Yes."

Note "**above** 0.2%", strict. The `KXCPI` family adds the rounding basis inline:

> `KXCPIYOY-26SEP-T3.0` — "If the Consumer Price Index (CPI) increases by more than 3.0%
> in the twelve months ending September 2026 (**as represented by the one-decimal place
> value reported by the Bureau of Labor Statistics**), then the market resolves to Yes."

### T2 — Bucket partition (`strike_type: between` + `less`/`greater` caps) — 19 events

Mutex, `MECNET`, tiling the reported value. Bounds are inclusive **and the rule text
closes the endpoints even though the subtitle does not**:

> `KXGDPYEAR-26-B2.3` (subtitle "2.1% to 2.5%") — "If the United States real GDP growth in
> 2026 is between 2.1% to 2.5%, then the market resolves to Yes."
> `KXGDPYEAR-26-T0.1` (subtitle "0.0% or Below") — "…is **below 0.1%**…"
> `KXGDPYEAR-26-T6.0` (subtitle "6.1% or Above") — "…is **above 6.0%**…"
> rules_secondary — "**All stated bounds are inclusive.** For example, '5.6% to 6.0%'
> includes both 5.6% and 6.0%, '6.1% or above' includes 6.1%, and '0.0% or below'
> includes 0.0%."

### T3 — Point-mass menu (`strike_type: custom`, `Exactly X`) — the `KXECONSTAT*` family

Mutex, `MECNET`, one leg per printable value, **no catch-all leg at either end**.

> `KXECONSTATU3-26SEP-T4.3` — "If the Unemployment rate is exactly 4.3% in Sep 2026, then
> the market resolves to Yes."

`classify_event()` labels these `entity_menu`; structurally they are truncated partitions
(see Traps).

### T4 — Mutex action menu — `KXFEDDECISION` and the `KXCBDECISION*` clones

> `KXFEDDECISION-26SEP-C25` — "If the Federal Reserve does a Cut of 25bps on
> September 16, 2026, then the market resolves to Yes."
> rules_secondary — "This market is mutually exclusive. Therefore, if the Federal Reserve
> hikes by 50bps, the 50bps market will resolve to Yes and the 25bps market will resolve
> to No. Only one bucket, at maximum, can resolve to Yes. Note 4/28/25: … **if a scheduled
> FOMC meeting is canceled and does not occur on its scheduled date, then the strike for
> 'Fed maintains rate' will resolve to Yes and all others will resolve to No.**"

Note "**at maximum**" — Kalshi's own text declines to assert completeness.

### T5 — Count menu — `KXRATECUTCOUNT`, `KXFEDCHGCOUNT`, `KXFOMCDISSENTCOUNT`

> `KXRATECUTCOUNT-26DEC31-T0` — "If the Fed cuts 0 times starting Jan 1, 2026 and before
> 2027, then the market resolves to Yes."

### T6 — Combination — `KXCPICOMBO`, `KXFEDCOMBO`, `KXEMPLOYMENTCOMBO`

> `KXCPICOMBO-26JULB-N0101` — "If **ALL of the following occur** for before Jul 2026:
> Headline: -0.1% or below, Core: 0.1% or below, then the market resolves to Yes."

### T7 — Deadline / first-touch ladder

> `KXWTIWHEN-100-26AUG31` — "If ICE reports that the WTI front-month settle price is above
> \$100 **on any market day between Issuance and Aug 31, 2026**, then the market resolves
> to Yes."
> `KXIPOOPENAI-27JAN01` legs: `Before <Mon> <D>, <YYYY>`.

### T8 — Running extremum

> `KXU3MAX-27-4.5` — "If **any** U.S. seasonally adjusted U-3 unemployment rate for a
> month in 2026 is above 4.5%, the market resolves to Yes."
> `KXAAAGASMAX-26DEC31` — "If AAA reports that the **maximum** price of national average
> regular gas for the US is greater than \$4.60 **at any time from Issuance through
> Dec 31**…"

---

## Settlement

**Sources** (by market count; events carry 1–8 sources each, 0 events have none):

Economics — Trading Economics 522, Bureau of Labor Statistics 394, BLS–Consumer Price
Index 382, Federal Reserve Board of Governors 328, BLS–Employment Situation 270,
Bureau of Economic Analysis 223, AAA 223, FRED 157, Federal Reserve 135, Forbes 69,
BLS 65, ADP 35. A large block of judgement-call markets carries a *media panel* instead
of a statistical agency: The Wall Street Journal 242, Reuters 242, ABC 237, Bloomberg 235,
CNBC 232, the New York Times 230, BBC 226, Financial Times 226.

Commodities — Pyth 370, ICE 160, Pyth–Gold 133, Pyth–Silver 120, Anthropic 8, OpenAI 8,
Google Gemini Developer API pricing 8. **Note the split:** WTI settles on ICE
front-month settle; gold/silver/copper/natgas/Brent settle on Pyth oracle prints. Two
different price references for what look like the same asset class.

Several series name Trading Economics as primary with an agency fallback:

> `KXLFPRATE-27JAN08` rules_secondary — "…as represented by the one-decimal place value
> reported by Trading Economics… If Trading Economics is unavailable or does not publish
> the relevant December 2026 value, Kalshi may use the corresponding value from the U.S.
> Bureau of Labor Statistics…"

**First-print only.** Nearly every macro series pins resolution to the first publication:

> `KXGDPYEAR` — "The Expiration Value will be the **first-published** annual percent change
> in real GDP for 2026 from BEA's GDP release… **Revisions published after expiration will
> not be considered.**"
> `KXPSAVERT` — "This market will use the first value published by Federal Reserve Economic
> Data for December 2026. Revisions released after the first publi[cation]…"
> `KXM2GROWTH` — "…December 2026 M2SL divided by December 2025 M2SL, minus one, expressed
> as a percentage and **rounded to one decimal place**."

**Early close.** `can_close_early` is `true` for **all 4,066 active markets**. Distinct
conditions: Economics — none 1,082, "This market will close and expire early if the
economic data…" 945, "…if the event occurs." 932, "If this event occurs, the market will
close the following 10[…]" 103, "…if the central bank […]" 66. Commodities — none 766,
"…if the price data is[…]" 24, "…the following 10[…]" 11.

**Settlement timer.** Economics: 1800s ×2,307, 300s ×509, 3600s ×338, 297s ×60, 500s ×21,
10800s ×12, 3599s ×12, 3596s ×6. Commodities: 3600s ×777, 1800s ×24. The odd values
(297, 3596, 3599) are per-market drift, not a distinct policy.

**Expiry horizons** (days from snapshot to `close_time`):

| | min | p10 | median | p90 | max |
|---|---|---|---|---|---|
| Economics | 0.30 | 8.6 | 123.7 | 1,643 | 4,169 (2037-11) |
| Commodities | 0.90 | 1.0 | 5.0 | 93 | 242 |

307 Economics markets close within 7 days, 843 within 30 days, and **554 close more than a
year out** — the `KXGDPYEAR` / `KXFEDFUNDSYEAR` / `KXUSCPIYEAR` / `KXGDPNOM` multi-decade
blocks. Commodities has no market beyond 242 days; 518 of 801 close within 7 days.

`collateral_return_type`: Economics `DIRECNET` 161 events, `MECNET` 79, empty 112;
Commodities `DIRECNET` 20, `MECNET` 1, empty 8. `MECNET` tracks `mutually_exclusive` 1:1
(79 = 79 in Economics) and is the netting flag that makes multi-leg mutex baskets
capital-efficient.

---

## Liquidity

`liquidity_dollars` is **0 for all 4,066 active markets** and `notional_value_dollars` is
**1 for all of them** in this snapshot — both fields are unpopulated and must not be used.
Depth has to be read from `yes_bid_size_fp` / `yes_ask_size_fp`, which are **decimal
strings**, not integers (`"1292.00"`, `"0.01"`, `"2382.97"`) — Kalshi supports fractional
contracts and the smallest observed ask depth in the slice is 0.01 contracts.

| | Economics (3,265 active) | Commodities (801 active) |
|---|---|---|
| open interest: median / p90 / total | 171 / 3,770 / 18.18M | 75 / 3,121 / 792k |
| cumulative volume: median / total | 321 / 64.85M | 100 / 1.47M |
| 24h volume: median / total / share with >0 | 0 / 657k / **30%** | 0 / 424k / **49%** |
| two-sided book (0 < bid, 0 < ask < 1) | 2,531 = **77.5%** | 599 = **74.8%** |
| median spread \| p25 \| p75 | 6.0c \| 3.0c \| 11.0c | **2.0c** \| 1.0c \| 6.0c |
| spread ≤ 2c \| ≤ 5c | 449 \| 1,083 | 251 \| 437 |
| **tradeable** (two-sided, ≤5c, ≥10 contracts both sides) | 746 = **22.8%** | 378 = **47.2%** |

**Genuinely tradeable fraction: 1,124 of 4,066 active markets = 27.6% of the slice.**

Liquidity is a strong function of horizon, and in opposite directions for the two
categories:

Economics, by days to close:

| bucket | n | two-sided | median spread | tradeable | open interest | 24h vol |
|---|---|---|---|---|---|---|
| ≤7d | 307 | 60% | 4.0c | 18% | 867k | 293k |
| 7–30d | 536 | 62% | 6.0c | 9% | 1.38M | 93k |
| 30–90d | 612 | 63% | 6.0c | 21% | 5.24M | 142k |
| 90–365d | 1,256 | 87% | 6.0c | 27% | 10.26M | 90k |
| >1y | 554 | 97% | 6.0c | 32% | 438k | 40k |

The long-dated blocks look "two-sided" because a single market maker posts a full grid
(`KXFEDFUNDSYEAR-31JAN01` has 250-contract quotes 12 years out); 24h volume there is
essentially nil. The apparent dip at 7–30d is the far-forward CPI months, whose books are
placeholder grids — `KXCPIYOY-26SEP` quotes `Above 3.5%` at 0.00/0.92 with 24h volume 0.

Commodities, by days to close:

| bucket | n | two-sided | median spread | tradeable | open interest | 24h vol |
|---|---|---|---|---|---|---|
| ≤7d | 518 | 69% | **1.0c** | **59%** | 425k | 414k |
| 7–30d | 184 | 77% | 6.0c | 31% | 11k | 3.7k |
| 30–90d | 4 | 100% | 18.0c | 0% | 624 | 202 |
| 90–365d | 95 | 99% | 6.0c | 18% | 356k | 6.4k |

Open-interest concentration. Economics: `KXRATECUTCOUNT` 4.46M (24.5%), `KXFLYCANCJFK`
3.02M (16.6%), `KXFEDDECISION` 1.95M (10.7%), `KXRECSSNBER` 897k (4.9%), `KXFEDHIKE` 797k
(4.4%), `KXAAAGASMAX` 618k (3.4%), `KXCPIYOY` 559k (3.1%) — top 7 = 67.6%.
Commodities: `KXWTI` 452k (**57.0%**), `KXGOLDDIRY` 64k (8.1%), `KXBRENTD` 53k (6.7%),
`KXWTIW` 40k (5.1%), `KXGOLDD` 33k (4.1%) — top 5 = 81%.

---

## Structural constraints

Convention: for a claimed subset relation `S ⊆ G` the executable violation test is
`yes_bid(S) − yes_ask(G) − fee(S, bid) − fee(G, ask) > 0`, sized at
`min(yes_bid_size(S), yes_ask_size(G))`. Fees are computed per-series from
`fee_multiplier`. Every number below is from the 2026-08-02T20:52Z snapshot.

---

### C0 — Nesting inside a threshold ladder (largest, most mechanical)

**Relation.** Within one event, `{X > a} ⊆ {X > b}` for `a > b`, so
`P(T_a) ≤ P(T_b)`. Inequality: `yes_bid(T_a) ≤ yes_ask(T_b)`.
For "or below" ladders (`KXOPUS48Y`, `KXAAAGASMIN`) the direction reverses.

**Rule basis.** All legs of an event share a rule sentence differing only in the strike:
"…increases by above 0.2%…" vs "…above 0.3%…" — identical underlying, identical
reference period, identical source.

**Coverage.** 212 ladder events, 2,877 legs, **2,665 adjacent nested pairs**.

**Live check — CONSISTENT.** 7 of 2,665 pairs show a raw crossing; **0 survive fees.**
The largest is `KXFEDFUNDSYEAR-31JAN01-T2.50` bid 0.700 vs `-T2.25` ask 0.680
(gross +2.0c, fee 3.01c, **net −1.01c**). All 7 sit in `KXFEDFUNDSYEAR` / `KXUSCPIYEAR`
events 5–11 years out, and all 7 are 1–2c crossings against ≈3c round-trip fees. The
constraint holds economically everywhere.

**Failure modes.** (a) None from settlement logic — this relation is exact by
construction. (b) Parser-level only: a ladder whose strikes are written with word
multipliers (`KXMUSKNW`: "Above \$450 billion" … "Above \$1 trillion";
`KXGOVTSPEND`: "At least \$50 billion" … "At least \$1 trillion") will sort wrong if the
multiplier is dropped, producing 788 phantom violations instead of 7. The shipped
`taxonomy.parse_threshold` has this bug: `_RE_THRESHOLD_ABOVE` only matches single-letter
multipliers `[kmbt]`, not the spelled words, so `$1 trillion` parses as level 1.0.

---

### C1 — `KXAAAGASD-26AUG03` ≡ `KXAAAGASW-26AUG03` (duplicate listing of one fact)

**Relation.** Equality, not implication. The "daily" and "weekly" AAA gas series list the
**same observation date** with overlapping strikes.

**Rule basis.** Identical sentence in both series, differing only in the strike:

> `KXAAAGASW-26AUG03-4.090` — "If average regular gas prices for United States are
> **strictly greater than \$4.090 on Aug 3, 2026 according to AAA**, then the market
> resolves to Yes."
> `KXAAAGASD-26AUG03-4.090` — "If average regular gas prices for United States are
> **strictly greater than \$4.090 on Aug 3, 2026 according to AAA**, then the market
> resolves to Yes."

Both close 2026-08-03T03:59:00Z and expire 2026-08-10T14:00:00Z. Both are
`quadratic`, `fee_multiplier: 1`.

**Inequality.** For every shared strike `k`:
`yes_bid(W_k) ≤ yes_ask(D_k)` **and** `yes_bid(D_k) ≤ yes_ask(W_k)`.

**Live check — VIOLATED at 2 of 7 shared strikes.**

| strike | W bid/ask | D bid/ask | sell W, buy D (net) | size | \$ |
|---|---|---|---|---|---|
| 4.060 | 0.990/1.000 | 0.990/1.000 | −0.0107 | 0 | — |
| 4.070 | 0.990/1.000 | 0.990/1.000 | −0.0107 | 0 | — |
| 4.080 | 0.980/0.990 | 0.980/1.000 | −0.0214 | 0 | — |
| **4.090** | 0.770/0.780 | 0.700/0.740 | **+0.0041** | 2 | \$0.01 |
| **4.100** | 0.070/0.080 | 0.040/0.050 | **+0.0120** | 57.62 | \$0.69 |
| 4.110 | 0.000/0.010 | 0.000/0.010 | −0.0107 | 0 | — |
| 4.120 | 0.000/0.010 | 0.000/0.010 | −0.0107 | 0 | — |

Total realisable at top of book: **\$0.70**. Structurally real, economically negligible.

**Failure modes.** (a) The two series could be re-keyed so `KXAAAGASW` refers to a
week-end rather than a specific date — the identity is asserted by the rule sentence, not
by the ticker, so a scanner must diff `rules_primary` and not the tickers. (b) Strike
precision: W quotes some strikes at 2 decimals (`4.02`) and D at 3 (`4.055`); only
numerically equal strikes are related. (c) A single-day AAA outage triggers different
`early_close_condition` paths.

---

### C2 — Mutex + tiled bucket partition sums to 1

**Relation.** For a mutex event whose legs tile the space of publishable values,
`Σ_i P_i = 1`. Buy-all-YES arb if `Σ yes_ask_i + Σ fee_i < 1`; sell-all-YES arb if
`Σ yes_bid_i − Σ fee_i > 1`.

**Rule basis (and the resolution of the "16 of 18 untiled" result).**
Prior automated profiling reported **16 of 18** Economics mutex bucket partitions as
untiled. That is a **parser artifact, not a settlement gap.** Two distinct defects:

1. **Scale-dependent tolerance.** `taxonomy.partition_is_tiled` accepts a gap up to
   `0.011 * max(1, |hi|)` — a *relative* tolerance. Every one of these ladders is
   quantized at the reporting precision, so consecutive legs are separated by exactly one
   reporting increment. `KXGDPYEAR` legs run "0.1% to 0.5%", "0.6% to 1.0%": gap 0.1,
   scale 0.5, relative gap 0.20 → rejected. `KXLFPRATE` legs run "60.5% to 60.9%",
   "61.0% to 61.4%": *identical structure*, gap 0.1, scale 60.9, relative gap 0.0016 →
   accepted. The verdict is decided by the magnitude of the index, not by the partition.
2. **Unhandled compact comparators.** The three post-count series use `<9` / `>20` rather
   than `Below 9` / `Above 20`; neither `parse_bucket` nor `parse_threshold` matches, so
   `partition_is_tiled` returns `False` on the parse-failure branch without ever
   evaluating a gap.

Replacing the relative tolerance with a **quantum test** — compute all inter-leg gaps,
accept if every gap is 0 or a single constant `q` — and adding `<N`/`>N` gives:

| event(s) | quantum | corrected verdict |
|---|---|---|
| `KXGDPYEAR-26` … `-36` (11) | 0.1 pp | tiled |
| `KXPSAVERT-27JAN` | 0.1 pp | tiled |
| `KXM2GROWTH-27JAN26` | 0.1 pp | tiled |
| `KXLFPRATE-27JAN08` | 0.1 pp | tiled |
| `KXSCFI-26DEC25` | 0.01 index pt | tiled |
| `KXWEFTWEETS` / `KXIMFTWEETS` / `KXFEDTWEETS-26AUG06` | 1 post | tiled |
| `KXWTIW-26AUG0714` (Commodities) | \$0.01 | tiled |

**18 of 18 Economics mutex bucket partitions tile** (19/19 including Commodities), versus
2/19 from the shipped checker. The quantum is confirmed by rule text in each case:

> `KXGDPYEAR` rules_secondary — "All stated bounds are inclusive. For example, '5.6% to
> 6.0%' includes both 5.6% and 6.0%, '6.1% or above' includes 6.1%, and '0.0% or below'
> includes 0.0%." — and the two cap legs' `rules_primary` close the line exactly:
> "is **below 0.1%**" and "is **above 6.0%**". There is no value of a one-decimal BEA
> print that pays nothing.
> `KXPSAVERT` / `KXLFPRATE` — "…as represented by the **one-decimal place value** reported
> by Federal Reserve Economic Data / Trading Economics…"
> `KXM2GROWTH` — "…expressed as a percentage and **rounded to one decimal place**."
> `KXWEFTWEETS` — "**All 'between' ranges are inclusive of their upper and lower bounds.**"
> (post counts are integers)
> `KXSCFI` — legs "1,500 to 1,999.99" / "2,000 to 2,499.99", i.e. a 0.01 index-point
> quantum on the SCFI composite.

**Live check on all 11 `KXGDPYEAR` events (the zero-fee series — total fee cost \$0):**

| event | Σ ask | buy-all edge | min ask depth | Σ bid | sell-all edge |
|---|---|---|---|---|---|
| `KXGDPYEAR-26` | 1.0050 | −0.0050 | 0.05 | 0.8690 | −0.1310 |
| `KXGDPYEAR-27` | 1.4800 | −0.4800 | 115.00 | 0.6100 | −0.3900 |
| `KXGDPYEAR-28` | 1.0300 | −0.0300 | 15.01 | 0.7200 | −0.2800 |
| `KXGDPYEAR-29` | 1.3200 | −0.3200 | 14.00 | 0.7900 | −0.2100 |
| `KXGDPYEAR-30` | 1.1600 | −0.1600 | 18.01 | 0.6400 | −0.3600 |
| `KXGDPYEAR-31` | 1.0700 | −0.0700 | 66.00 | 0.4300 | −0.5700 |
| `KXGDPYEAR-32` | 1.0900 | −0.0900 | 10.00 | 0.5300 | −0.4700 |
| **`KXGDPYEAR-33`** | **0.9200** | **+0.0800** | **0.01** | 0.4600 | −0.5400 |
| `KXGDPYEAR-34` | 1.0800 | −0.0800 | 20.00 | 0.4900 | −0.5100 |
| `KXGDPYEAR-35` | 1.0200 | −0.0200 | 5.00 | 0.8100 | −0.1900 |
| `KXGDPYEAR-36` | 1.5500 | −0.5500 | 15.82 | 0.4700 | −0.5300 |

**One violation: `KXGDPYEAR-33` (US real GDP growth in 2033).** Buying all 14 legs at ask
costs \$0.9200 and pays \$1.0000 with certainty; the series is `fee_multiplier: 0`, so
gross edge = net edge = **+8.00c per basket**. **But the binding leg
`KXGDPYEAR-33-B5.3` ("5.1% to 5.5%") has an ask depth of 0.01 contracts.** Executable
size at top of book is 0.01 baskets = **\$0.0008**. The second-thinnest leg has 15
contracts; if `B5.3`'s next ask level were 4c instead of 3c the sum would still be 0.93
and the edge would survive at 15 baskets ≈ \$1.05, but the snapshot only contains
top-of-book so that cannot be asserted. **Verdict: violated in price, not executable in
size.**

**Failure modes.** (a) An off-quantum print (BEA publishing to two decimals) would open a
real hole in the `KXGDPYEAR` partition; the "one-decimal" rounding clause is present in
`KXPSAVERT`/`KXLFPRATE`/`KXM2GROWTH` but **only implicit in `KXGDPYEAR`** — its
rules_secondary asserts inclusivity of the bounds but never states the rounding. (b) A
non-publication (data source discontinued) resolves nothing and the basket pays 0.
(c) Mid-life leg additions: `KXECONSTATCPIYOY-26JUL` has 26 legs and `-26SEP` has 16, so
the leg set is not stable across events of the same series and a cached basket goes stale.

---

### C3 — Point-mass menu ⊆ threshold ladder (same release)

**Relation.** For a `KXECONSTAT<STAT>-<MONTH>` menu and the matching `KX<STAT>-<MONTH>`
ladder, for any ladder strike `x`:
`Σ_{v > x} P(Exactly v) ≤ P(Above x)`
because `{value ∈ menu, value > x} ⊆ {value > x}`. This is one-sided only: the menu is
**truncated**, so a print above the menu's top pays in the ladder and nothing in the menu.

**Rule basis.** Same source, same reference month, and — decisively — **identical
`close_time` and `expiration_time`**. `KXECONSTATU3-26SEP` and `KXU3-26SEP` both close
2026-10-02T12:29:00Z and expire 2027-01-01T14:00:00Z.

> `KXU3-26SEP-T4.4` — "If the seasonally adjusted unemployment rate (U-3) reported by the
> Bureau of Labor Statistics in the Employment Situation Report is above 4.4% in
> September 2026, then the market resolves to Yes."
> `KXECONSTATU3-26SEP-T4.5` — "If the Unemployment rate is exactly 4.5% in Sep 2026, then
> the market resolves to Yes."

**Executable form.** Sell every menu leg with `v > x` at its bid, buy the ladder leg at
its ask. Payoff ≥ 0 in every state. Net = `Σ bid − ask − fees`.

**Live check — 4 VIOLATIONS out of 23 (statistic, month) pairs examined, all in U-3.**

| pair | strike x | legs sold | Σ bid | ladder ask | gross | fee | **net** | size | \$ |
|---|---|---|---|---|---|---|---|---|---|
| `KXECONSTATU3-26SEP` / `KXU3-26SEP` | 4.4 | 9 | 0.290 | 0.220 | +7.00c | 3.18c | **+3.82c** | 38 | 1.45 |
| " | 4.5 | 8 | 0.220 | 0.180 | +4.00c | 2.55c | **+1.45c** | 100 | 1.45 |
| " | 4.6 | 7 | 0.160 | 0.130 | +3.00c | 1.91c | **+1.09c** | 100 | 1.09 |
| `KXECONSTATU3-26AUG` / `KXU3-26AUG` | 4.5 | 5 | 0.130 | 0.090 | +4.00c | 1.48c | **+2.52c** | 9 | 0.23 |
| `KXECONSTATU3-26NOV` / `KXU3-26NOV` | 4.4 | 8 | 0.430 | 0.380 | +5.00c | 4.49c | +0.51c | 5 | 0.03 |

All CPI pairs (headline/core, MoM/YoY, all five months) are **consistent** — the largest
CPI figure is −0.0107 (i.e. fee-negative by a full cent).

Total realisable across all U-3 violations at top of book: **≈\$4.25**.

**Failure modes.** (a) `KXECONSTATU3`'s `rules_primary` says only "the Unemployment rate",
with no "seasonally adjusted" or "U-3" qualifier and an empty `rules_secondary`; the
ladder is explicit. If the menu were ever settled on U-6 or on NSA data the relation
breaks. The matching `settlement_sources` ("Bureau of Labor Statistics- Employment
Situation") and identical expiry are the only evidence they are the same number.
(b) The `KXECONSTATU3` book is a uniform 100-contract grid at every strike with
open interest 0 on half the legs — it reads as a single automated quoter, so the "bids"
may not be resilient. (c) Truncation direction: the reverse inequality
(`P(Above x) ≤ Σ_{v>x} P(Exactly v)`) is **false** and must never be scanned —
`KXECONSTATU3-26SEP` tops out at "Exactly 5.5%" while `KXU3-26SEP` goes to "Above 5.0%".

---

### C4 — `KXFED` (post-meeting rate) ≡ `KXFEDDECISION` (action taken), next meeting only

**Relation.** With the current target-range upper bound `R = 3.75%` (implied by
`KXFED-26SEP`: T3.50 ≈ 0.985, T3.75 ≈ 0.595, T4.00 ≈ 0.015):

| ladder leg | equivalent decision basket |
|---|---|
| `KXFED-26SEP-T4.00` ("Above 4.00%") | `H26` |
| `KXFED-26SEP-T3.75` | `H25 + H26` |
| `KXFED-26SEP-T3.50` | `H0 + H25 + H26` |
| `KXFED-26SEP-T3.25` | `C25 + H0 + H25 + H26` |

Two-sided: `Σ yes_bid(basket) ≤ yes_ask(ladder)` and
`yes_bid(ladder) ≤ Σ yes_ask(basket)`.

**Rule basis.**

> `KXFED-26SEP-T3.75` — "If the **upper bound of the target federal funds rate** published
> on the Federal Reserve's official website is greater than 3.75% **following the Federal
> Reserve's Sep 16, 2026 meeting**, then the market resolves to Yes."
> `KXFEDDECISION-26SEP-H25` — "If the Federal Reserve does a Hike of 25bps on
> September 16, 2026, then the market resolves to Yes."

Both series are `quadratic_with_maker_fees`; makers pay 0.0175·P(1−P), takers 0.07·P(1−P).

**Live check — CONSISTENT, and fee-dominated.**

| ladder leg | ladder bid/ask | basket bid/ask | buy ladder / sell basket | sell ladder / buy basket |
|---|---|---|---|---|
| T4.00 | 0.010/0.020 | 0.010/0.020 | gross −1.00c, fee 0.21c, net −1.21c | −1.21c |
| T3.75 | 0.590/0.600 | 0.570/0.590 | gross −3.00c, fee 3.49c, net −6.49c | gross **0.00c**, fee 3.56c, net −3.56c |
| T3.50 | 0.980/0.990 | 0.980/1.010 | net −4.57c | net −6.71c |
| T3.25 | 0.990/1.000 | 0.990/1.030 | net −4.57c | net −7.78c |

The T3.75 pair prices to the cent (`yes_bid(ladder) = Σ yes_ask(basket) = 0.590`) yet the
4-leg round trip costs 3.56c in taker fees. **The binding constraint on this relation is
the fee, not the market.**

**Failure modes.** (a) **This identity only holds for the next meeting.** For `26OCT` and
later, the level after the meeting depends on all intervening decisions, so no single
decision menu determines the ladder. (b) An **inter-meeting emergency move** changes the
level without a scheduled-meeting decision, breaking the map in both directions —
`KXFEDMEET-27` ("Will the Fed have an emergency meeting in 2026?") is the market that
prices exactly this risk. (c) A cancelled meeting resolves `H0` to Yes by rule
("if a scheduled FOMC meeting is canceled … the strike for 'Fed maintains rate' will
resolve to Yes") while the ladder resolves on the actual published rate. (d) `KXEFFR` is
the **effective** fed funds rate, not the target upper bound — it is not interchangeable
with `KXFED` at the same strike.

---

### C5 — Adjacent-meeting drift bound

**Relation.** For any strike `x`, `{rate after meeting n > x}` and
`{rate after meeting n−1 > x}` can differ only if meeting `n` changed the rate:
`|P(FED_n > x) − P(FED_{n−1} > x)| ≤ 1 − P(H0 at meeting n)`.

**Rule basis.** `H0` = "Hike of 0bps"; a 0bp move leaves the published upper bound
unchanged, so the two indicators coincide on that event.

**Live check — CONSISTENT at all 5 consecutive pairs.**

| pair | max \|ΔP\| over shared strikes | at strike | 1 − P(hold) range |
|---|---|---|---|
| 26SEP→26OCT | 0.150 | T4.00 | [0.300, 0.340] |
| 26OCT→26DEC | 0.195 | T4.00 | [0.400, 0.410] |
| 26DEC→27JAN | 0.240 | T3.50 | [0.360, 0.370] |
| 27JAN→27MAR | 0.150 | T3.50 | [0.270, 0.320] |
| 27MAR→27APR | 0.160 | T3.00 | [0.280, 0.360] |

Slack is 40–100% in every case; this is a loose but exact bound, useful as a sanity filter
rather than a scanner target.

**Failure modes.** Inter-meeting moves (same as C4b); a skipped meeting in the calendar
between the two events.

---

### C6 — `KXRATECUT` ⊕ `KXRATECUTCOUNT-T0` is a complementary pair

**Relation.** "At least one cut" and "exactly 0 cuts" are complementary:
`P(RATECUT) + P(T0) = 1`. Arb if `yes_bid(RATECUT) + yes_bid(T0) > 1` (sell both — exactly
one pays) or `yes_ask(RATECUT) + yes_ask(T0) < 1` (buy both).

**Rule basis.**
> `KXRATECUT-26DEC31` — "If the Federal Reserve cuts its target federal funds rate range
> at least once **between February 26, 2026 and December 31, 2026**…"
> `KXRATECUTCOUNT-26DEC31-T0` — "If the Fed cuts 0 times **starting Jan 1, 2026 and before
> 2027**…"

**The windows differ** (Feb 26 vs Jan 1). Complementarity is exact only if no cut occurred
between 2026-01-01 and 2026-02-26 — not determinable from metadata.

**Live check — CONSISTENT, and the tightest pair in the category.**
sell both: 0.137 + 0.851 = **0.988** (< 1, no arb).
buy both: 0.140 + 0.863 = **1.003** (> 1, no arb); round-trip fee 1.68c.
The no-arb band is 1.2c wide against a 1.68c fee.

Related, also consistent:
- `{changes = 0} ⊆ {cuts = 0}`: `yes_bid(KXFEDCHGCOUNT-27JAN01-E0) = 0.234` ≤
  `yes_ask(KXRATECUTCOUNT-26DEC31-T0) = 0.863`. (Same window caveat: `KXFEDCHGCOUNT`
  says only "the number of rate changes before 2027" with no start date.)
- `KXLARGECUT-26` ("cut by more than 25 basis points before Dec 31, 2026") vs the `C26`
  legs of the remaining 2026 meetings: `P(LARGECUT) ≥ max_m P(C26_m)` →
  0.052 bid ≥ 0.030 max ask ✓; and `P(LARGECUT) ≤ Σ_m P(C26_m)` → the three remaining
  `C26` legs have **zero bid** (sum 0.000) against a `LARGECUT` ask of 0.053, so the
  upper bound is not testable on this book. Note also `KXLARGECUT-26` covers the whole of
  2026 including meetings already past, so the sum bound is one-sided in practice.

---

### C7 — Combination contract ↔ its marginals

**Relation.** For a mutex combination grid, summing a row (or column) reproduces a
marginal: `Σ_core P(headline = h, core = c) = P(headline = h)`, matched to the
`KXECONSTATCPI` point leg. Equality when the grid is complete in the collapsed dimension.

**Rule basis.**
> `KXCPICOMBO-26JULB-0002` — "If **ALL of the following occur** for before Jul 2026:
> Headline: Exactly 0.0%, Core: Exactly 0.2%…"

The `KXCPICOMBO-26JULB` grid is a complete 5×3 product
(headline ≤−0.1 / 0.0 / 0.1 / 0.2 / ≥0.3 × core ≤0.1 / 0.2 / ≥0.3), so every row sum is
an exact marginal.

**Live check — CONSISTENT (books far too wide to bind).**

| marginal | combo row bid/ask | `KXECONSTATCPI` leg bid/ask | sell row / buy point | buy row / sell point |
|---|---|---|---|---|
| headline = 0.0% | 0.190/0.590 | 0.270/0.330 | −16.75c | −36.44c |
| headline = 0.1% | 0.180/0.450 | 0.330/0.430 | −27.83c | −16.16c |
| headline = 0.2% | 0.080/0.320 | 0.140/0.180 | −11.56c | −20.87c |

`KXFEDCOMBO-26SEPB` vs `KXFEDDECISION-26SEP`, also **CONSISTENT**:

| rate cell | combo bid/ask | decision bid/ask | sell combo / buy decision | buy combo / sell decision |
|---|---|---|---|---|
| no change | 0.420/0.480 | 0.410/0.420 (`H0`) | −3.54c | −10.65c |
| 25bp cut | 0.020/0.080 | 0.010/0.020 (`C25`) | −0.28c | −7.61c |
| 25bp hike | 0.460/0.590 | 0.560/0.570 (`H25`) | −15.16c | −7.59c |

**Failure modes.** `KXFEDCOMBO` covers only 3 of the 5 `KXFEDDECISION` outcomes (no
`>25bp` cells), so the dissent-collapsed direction is a **subset relation, not an
equality**: `Σ_rate P(rate, dissents = 0) ≤ P(FOMCDISSENTCOUNT = 0)` — live 0.200 vs
0.330 ask, consistent with slack. Scanning it as an equality produces false positives.

---

### C8 — Individual dissenters vs the dissent count

**Relation.** `KXFEDDISSENT-26SEP` is **non-mutex** (12 named FOMC participants, each an
independent binary); `KXFOMCDISSENTCOUNT-26SEP` is a mutex 0–4 menu.
- Disjointness: `{count = 0} ∩ {person i dissents} = ∅`, so
  `yes_bid(count0) + yes_bid(person_i) ≤ 1`.
- Expectation: `Σ_i P_i = E[#dissents] ≥ Σ_{k=0..4} k·P(count = k)` (≥ because the count
  menu truncates at 4).

**Rule basis.**
> `KXFEDDISSENT-26SEP-KEVI` — "If Kevin Warsh **formally dissented** at the September 2026
> FOMC meeting, then the market resolves to Yes."
> `KXFOMCDISSENTCOUNT-26SEP-0` — "If there are exactly 0 dissenting votes at the next
> scheduled FOMC meeting (scheduled for Sep 16, 2026)…"

**Live check — CONSISTENT.**
`Σ_i yes_bid = 1.330`, `Σ_i yes_ask = 1.940`. Ask-weighted `Σ k·P_k = 2.080`,
bid-weighted 1.740. The lock (buy all 12 individuals at ask 1.940, sell `k` units of each
count leg at bid for 1.740) is **−0.200 before fees** — consistent.
Disjointness: `yes_bid(count0)` vs largest individual bid 0.230 (Bowman) — sum well
under 1.

**Failure modes.** (a) The individual list must be exactly the voting membership; a
non-voter or an unlisted voter dissenting breaks `Σ_i P_i = E[count]` in the "≤"
direction. (b) "Formally dissented" (individual) vs "dissenting votes" (count) is not
obviously the same predicate for an abstention. (c) `KXFEDDISSENT` has
`collateral_return_type: ''` — no netting — so a 12-leg basket ties up full collateral.

---

### C9 — Deadline-ladder nesting (`KXIPO*`, `KXWTIWHEN`, `KXFEDHIKE`)

**Relation.** `{by t1} ⊆ {by t2}` for `t1 < t2` → `yes_bid(t1) ≤ yes_ask(t2)`.

**Rule basis.**
> `KXWTIWHEN-100-26AUG31` — "…the WTI front-month settle price is above \$100 on any
> market day **between Issuance and Aug 31, 2026**…"
> `KXWTIWHEN-100-26SEP30` — same sentence with "Sep 30, 2026".

**Coverage.** 23 deadline events, **170 nested pairs**.

**Live check — CONSISTENT.** 1 raw crossing:
`KXIPOSTARLINK-27APR01` bid 0.080 vs `-27MAY01` ask 0.070, gross +1.00c against a
0.98c fee → **net +0.02c**, i.e. two hundredths of a cent per contract. Everything else
holds with slack.

Note `KXWTIWHEN-100`'s ask ladder is non-monotone (Before Sep 0.48, Before Oct 0.20,
Before Nov 0.25, Before Dec 0.24, Before 2027 0.29) — non-monotone **asks** are not a
violation; only `bid(earlier) > ask(later)` is.

---

### C10 — Year-end level ⊆ first-touch during the year (WTI)

**Relation.** If WTI settles above \$100 on Dec 31 2026, it was above \$100 on at least
one market day in 2026:
`P(KXWTIDIRY-26DEC31H1430-T100) ≤ P(KXWTIWHEN-100-26DEC31)`.

**Rule basis.**
> `KXWTIDIRY-26DEC31H1430-T100` — "If the settlement price of WTI Crude Oil on
> December 31, 2026 at 02:30 PM EST is above 100 USD/Bbl…"
> `KXWTIWHEN-100-26DEC31` — "If ICE reports that the WTI front-month settle price is above
> \$100 **on any market day between Issuance and Dec 31, 2026**…"

**Live check — CONSISTENT.** `yes_bid(WTIDIRY-T100) = 0.200` vs
`yes_ask(WTIWHEN-100-26DEC31) = 0.290` → −9.0c before fees.

**Failure modes.** (a) "Between **Issuance** and Dec 31" — the first-touch window starts
at series issuance, not Jan 1, so an early-2026 touch before issuance would not count;
that only weakens the superset in the direction that preserves the inequality, but it
means the two are **not** equal at the boundary. (b) `KXWTIDIRY` says "the settlement
price of WTI Crude Oil at 02:30 PM EST" without naming ICE or "front-month"; if Dec 31 is
a shortened session or the front month rolls, the two references can diverge.
(c) Subtitle/rule mismatch: the leg's `yes_sub_title` is "100 or above" while
`rules_primary` says "**above** 100" — the rule governs.

---

### C11 — Running extremum ⊇ any single period

**Relation.** `{U-3 above x in month m} ⊆ {U-3 above x in some month of 2026}` →
`yes_bid(KXU3-26<M>-Tx) ≤ yes_ask(KXU3MAX-27-x)`. Same for
`KXLCPIMAXYOY-27` ("at least X% in any month") vs monthly `KXCPIYOY-26<M>-TX`
(note "above X" ⊂ "at least X", so the implication survives the comparator mismatch),
and `KXAAAGASMAX-26DEC31` vs the daily/weekly gas ladders.

**Rule basis.**
> `KXU3MAX-27-4.5` — "If **any** U.S. seasonally adjusted U-3 unemployment rate for a month
> in 2026 is above 4.5%, the market resolves to Yes."
> `KXU3-26SEP-T4.5` — "…U-3 … is above 4.5% in September 2026…"

**Live check — CONSISTENT.** 23 (superset, subset) pairs with matching strikes,
**0 violations**. Widest margin: `KXU3-26OCT-T4.5` bid 0.230 vs `KXU3MAX-27-4.5` ask 0.440
(−24.0c). Tightest: `KXU3-26NOV-T4.8` bid 0.070 vs `KXU3MAX-27-4.8` ask 0.150 (−9.4c).

**Failure modes.** (a) `KXU3MAX-30`'s window is "from June 2025 to January 2030" — it
spans months already published, so part of its value is already determined; a scanner
must not treat it as forward-looking. (b) `KXAAAGASMAX`/`MIN` strikes (\$3.60–\$4.60
range) barely overlap the daily ladder strikes (\$4.055–\$4.135), so the relation is
mostly untestable in this snapshot. (c) `KXLCPIMAXYOY-27` strikes (4.5–7.0) sit above the
live monthly `KXCPIYOY` strikes (3.0–5.0) for most months; only 4.5 and 5.0 overlap.

---

### Summary of live checks

| constraint | pairs/baskets checked | raw violations | net-positive after fees | max \$ at top-of-book |
|---|---|---|---|---|
| C0 ladder nesting | 2,665 | 7 | **0** | — |
| C1 GASD ≡ GASW | 7 | 2 | **2** | \$0.70 |
| C2 mutex tiled partition | 19 (11 GDPYEAR) | 1 | **1** | \$0.0008 (depth-capped) |
| C3 point menu ⊆ ladder | 23 | 5 | **4** | \$4.25 |
| C4 FED ≡ FEDDECISION | 8 | 0 | 0 | — |
| C5 adjacent-meeting drift | 5 | 0 | 0 | — |
| C6 RATECUT complement | 3 | 0 | 0 | — |
| C7 combo ↔ marginals | 9 | 0 | 0 | — |
| C8 dissenters vs count | 2 | 0 | 0 | — |
| C9 deadline nesting | 170 | 1 | 1 | \$0.0002/contract |
| C10 WTI level ⊆ touch | 1 | 0 | 0 | — |
| C11 extremum ⊇ period | 23 | 0 | 0 | — |

**2,935 settlement-logic relations evaluated; 16 raw price crossings; 8 survive fees; the
total realisable across all of them at top-of-book is under \$5.** The category is
structurally rich and economically closed.

---

## Traps a scanner must encode

1. **`mutually_exclusive` is not completeness.** `KXNBERRECESSQ` is mutex with 6 legs
   (`Q4 2024` … `Q1 2026`, "If the NBER declares the peak of American business activity
   predating a recession to be in Q4 2024…"). Σ ask = 0.745 → a naive buy-all-YES scanner
   reports +22.2c of "arb". There is no leg for "peak after Q1 2026" or "no recession
   declared", so the basket can pay zero. Kalshi's own rule text says "Only one bucket,
   **at maximum**, can resolve to Yes."

2. **`KXECONSTAT*` menus are truncated partitions.** Mutex, `MECNET`, but bounded on both
   sides with no catch-all. `KXECONSTATCPI-26JUL` spans −0.3% to +0.6%; a +0.7% print pays
   nothing. Σ P < 1 is legitimate. Only the `Σ ≤ 1` direction is a constraint. The leg
   range also **changes between events of the same series** (`KXECONSTATCPIYOY-26JUL` has
   26 legs, `-26SEP` has 16) — never cache a basket definition.

3. **The tiling test must be quantized, not tolerance-based.** See C2. A relative
   tolerance makes the verdict depend on the magnitude of the index: `KXGDPYEAR`
   (values ≈ 2) fails and `KXLFPRATE` (values ≈ 61) passes on *identical* structure.
   Detect the quantum from the gap distribution and confirm it against the rounding clause
   in `rules_secondary` ("one-decimal place value", "rounded to one decimal place",
   "All 'between' ranges are inclusive").

4. **Subtitles lie about the strike; `rules_primary` does not.**
   - `KXGDPYEAR-26-T0.1` subtitle "0.0% or Below", rule "is **below 0.1%**".
   - `KXGDPYEAR-26-T6.0` subtitle "6.1% or Above", rule "is **above 6.0%**".
   - `KXWTI-26NOV03` subtitle "\$73 or above", ticker `T72.99`.
   - `KXWTIDIRY-…-T100` subtitle "100 or above", rule "**above** 100 USD/Bbl".
   - `KXLAYOFFSYINFO-26-494000` subtitle "Yes", ticker strike `494000`, rule "more than
     **447,000** layoffs in the information sector in 2026". **The ticker strike is wrong.**

5. **Word multipliers break threshold parsers.** `KXMUSKNW-26AUG31` runs
   "Above \$450 billion" … "Above \$1 trillion"; `KXGOVTSPEND-27` runs "At least \$1
   billion" … "At least \$1 trillion". Dropping the multiplier sorts `$1 trillion` below
   `$450 billion` and fabricates a 79c "arb". The shipped
   `taxonomy._RE_THRESHOLD_ABOVE` only accepts `[kmbt]`, not the spelled words.

6. **Compact comparators `<N` / `>N`.** `KXFEDTWEETS` / `KXIMFTWEETS` / `KXWEFTWEETS` legs
   are `<9`, `9-11`, …, `>20`. Neither `parse_bucket` nor `parse_threshold` matches them,
   so tiling silently fails on the parse branch. Prefer `strike_type` (`less` /
   `greater` / `between` / `greater_or_equal` / `less_or_equal`) as the primary comparator
   signal and the subtitle only for the number.

7. **Finalized legs inside open events.** 78 non-active markets sit in 30 open events:
   `KXWTIWHEN-65` has 5 legs `finalized`/`no` and 6 active; `KXWTIWHEN-100` has one leg
   `closed` with `result: ''`; the 17 `KXIPO*` events each carry expired month legs. A
   basket built from `event.markets` without filtering `status == 'active'` will be
   mis-sized and will read `yes_ask = 0` (not 1) on the dead legs.

8. **Market ticker ≠ `event_ticker` + suffix.** `KXBALANCESHEET-EO26`'s legs are
   `KXBALANCESHEET-EO26-6.2` … except `KXBALANCESHEET-26-7.2`, which drops the `EO`.
   19 markets in the slice are not prefixed by their event ticker. Always key on
   `market.event_ticker`, never on string surgery.

9. **`KXFEDFUNDSYEAR-<YY>JAN01` is the year *before* `YY`.** `-28JAN01` = end of 2027.
   Same for `KXUSCPIYEAR-<YY>FEB01`. `KXGDPYEAR-<YY>` is the year itself. Three sibling
   annual series, three different date conventions.

10. **`liquidity_dollars` and `notional_value_dollars` are dead fields** in this snapshot
    (0 and 1 for every market). Depth must come from `yes_bid_size_fp` /
    `yes_ask_size_fp`, which are **decimal strings** supporting fractional contracts —
    the binding leg of the `KXGDPYEAR-33` basket has an ask depth of `"0.01"`. Parsing
    them as ints silently truncates to 0 and drops real depth; ignoring the fraction turns
    an unexecutable 0.01-contract quote into a phantom fill.

11. **Yes/no cross-listing of the same fact under different series names.**
    `KXAAAGASD-26AUG03` and `KXAAAGASW-26AUG03` (C1) settle on the identical AAA print.
    `KXECONSTATU3-26SEP` and `KXU3-26SEP` share close and expiration timestamps. Detect
    duplicates by `(rules_primary normalized, close_time, expiration_time)`, not by
    series ticker.

12. **`quadratic_with_maker_fees` sits on the most liquid Fed and CPI series.**
    `KXFED`, `KXFEDDECISION`, `KXCPI`, `KXCPIYOY`, `KXU3`, `KXPAYROLLS`, `KXGDP`,
    `KXRATECUTCOUNT`, `KXAAAGASM`, `KXEGGS`. Any basket built as a resting-order structure
    on these pays 0.0175·P(1−P) per leg instead of 0. Multi-leg structures in this
    category are fee-bound, not price-bound: the C4 `KXFED`/`KXFEDDECISION` T3.75 pair
    prices to exactly 0 gross edge against a 3.56c four-leg taker fee.

13. **Category fields disagree.** 20 `Economics`-shard events belong to `Financials`
    series and 3 to `Politics`; the `Commodities` shard contains AI token-price series.
    `KXFLYCANCJFK` (JFK flight cancellations) is the #2 open-interest series in
    `Economics`. Group by series ticker prefix.

14. **Rounding is stated in `rules_secondary`, not `rules_primary`, and not everywhere.**
    `KXPSAVERT` / `KXLFPRATE` / `KXCPIYOY` state the one-decimal basis inline;
    `KXGDPYEAR` never states a rounding rule at all — its partition tiles only under the
    assumption that BEA continues to publish one decimal.

---

## Open questions

1. **Is `KXECONSTATU3` seasonally adjusted U-3?** Its `rules_primary` says only "the
   Unemployment rate" and its `rules_secondary` is empty. The C3 relation to `KXU3` —
   which carries the four live violations in this snapshot — rests on inference from a
   shared `settlement_sources` entry and identical close/expiration timestamps. The
   contract terms PDF (`contract_terms_url`) is not in the census.

2. **What determines the `KXECONSTAT*` leg range?** `KXECONSTATCPIYOY` has 26 legs for
   July and August 2026 but 16 for September and November. Whether legs are added on
   demand (and therefore whether the truncation gap is dynamic) cannot be settled from a
   single snapshot.

3. **`KXFEDCHGCOUNT-27JAN01`'s window start.** "The number of rate changes before 2027"
   has no start date in the rule. If it is not 2026-01-01 the subset relation to
   `KXRATECUTCOUNT-26DEC31` (which does say "starting Jan 1, 2026") is not exact.

4. **`KXRATECUT`'s February 26 start date.** Whether a cut occurred between 2026-01-01 and
   2026-02-26 determines whether C6's complementarity is exact. This is historical fact,
   not metadata.

5. **Does `KXWTIDIRY` use the ICE front-month settle?** Its rule says "the settlement
   price of WTI Crude Oil on December 31, 2026 at 02:30 PM EST" and its
   `settlement_sources` is ICE, but the contract is not named. `KXWTIW`'s
   `custom_strike` carries `{'front_month_contract': 'WBS 26U-ICE', …}` — no equivalent
   field is populated on `KXWTIDIRY` (its `custom_strike` is null). The C10 relation
   assumes they are the same reference.

6. **Why does `KXGDPYEAR` carry `fee_multiplier: 0`?** It is one of only 14 zero-fee
   series exchange-wide and the only multi-leg partition among them in this slice. Whether
   this is a permanent promotional setting or a per-series subsidy that can be revoked
   determines whether the C2 basket structure is durable.

7. **Depth beyond top-of-book.** Every economic conclusion here is capped by top-of-book
   sizes. The `KXGDPYEAR-33` basket has an 8c gross edge and 0.01 contracts of depth on
   one leg; the true size is a full-book question this census cannot answer.

8. **`KXCITRINI`.** `fee_multiplier: 0`, category `Economics`,
   `contract_terms_url` → `POLITICALOUTCOMESINSET.pdf`, settlement source literally named
   "The Source Agencies are" pointing at `kalshi.com`. No live event in the snapshot; its
   template and relation to any other series is unknown.

9. **Media-panel settlement.** 242 Economics markets list an eight-outlet panel (WSJ,
   Reuters, ABC, Bloomberg, CNBC, NYT, BBC, FT) instead of a statistical agency. The
   adjudication rule among disagreeing outlets is not in the census metadata, and no
   settlement-logic constraint can be asserted across markets that use it.
