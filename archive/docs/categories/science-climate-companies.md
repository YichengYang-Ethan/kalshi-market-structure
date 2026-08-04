# Science & Technology, Climate & Weather, Companies (+ Health, Social, World, Transportation, NULL)

Snapshot: **2026-08-02T20:52Z**. All prices below are from that snapshot and are in dollars per
contract (1.00 = certain YES). "Live check" means the inequality was evaluated on the *executable*
sides of the book (bid of the specific leg vs ask of the general leg) with the per-series taker fee
subtracted, not on midpoints.

This document covers the eight small/long-tail category shards analysed together because they share
one property: none of them is a mass-produced series family like Sports or Elections, and their
structure has to be recovered from series ticker grammar rather than from the `category` field.

---

## Inventory — events, markets, series count; how much of the exchange this is

| shard | events | markets | distinct series | cum. volume (contracts) | open interest | 24 h volume |
|---|---:|---:|---:|---:|---:|---:|
| Climate_and_Weather | 137 | 883 | 83 | 3,683,009 | 2,149,692 | 1,759,917 |
| Science_and_Technology | 119 | 802 | 103 | 48,991,301 | 21,096,538 | 306,857 |
| Companies | 71 | 507 | 60 | 8,978,457 | 2,841,189 | 51,062 |
| Social | 9 | 30 | 9 | 107,695 | 37,032 | 106 |
| World | 7 | 23 | 5 | 449,470 | 186,960 | 8,951 |
| Health | 6 | 12 | 6 | 834,212 | 297,468 | 696 |
| Transportation | 1 | 1 | 1 | 5,611 | 1,344 | 0 |
| NULL (no category) | 1 | 2 | 1 | 11,782 | 5,053 | 38 |
| **slice total** | **351** | **2,260** | **268** | **63,061,536** | **26,615,277** | **2,127,627** |

Exchange totals in the same snapshot: 8,478 events / 73,964 markets across 17 shards.
The slice is **4.1 % of events, 3.1 % of markets, 4.79 % of cumulative volume, 3.49 % of open
interest, but only 1.76 % of 24-hour volume** — i.e. it holds a disproportionate amount of *stale*
open interest (long-dated science questions) and a small share of current flow.

Status mix of the 2,260 markets: `active` 2,144, `finalized` 112, `inactive` 3, `determined` 1.
`market_type` is `binary` for **all 2,260** — there are no scalar/multivariate contracts here.

Series-level metadata for the 268 series in the slice:

- `fee_type`: `quadratic` × 267, `quadratic_with_maker_fees` × 1 (**KXLLM1** only).
- `fee_multiplier`: **1 for all 268**. There is no zero-fee series anywhere in this slice.
  Taker fee = `ceil(0.07·P·(1−P) · 10⁴)/10⁴` per contract per leg:
  0.07¢ at P=0.01, 0.34¢ at P=0.05, 0.63¢ at P=0.10, 1.32¢ at P=0.25, **1.75¢ at P=0.50**.
  Maker fee is 0 everywhere except KXLLM1 (0.0175 coefficient).
- `frequency`: `one_off` 98, `custom` 92, `daily` 41, `annual` 17, `monthly` 10, `weekly` 5, `hourly` 5.
- Every series has a `contract_terms_url` and a non-empty `additional_prohibitions`
  (261/268 are the boilerplate "Persons who are employed by any of the Source Agencies are not
  permitted to trade…"; 3 add `SpaceX`, 3 add `Tesla`, 1 adds the league-personnel clause).

**Category is not a grouping key.** 58 of the 268 series (21.6 %) carry a `series.category` that
disagrees with the shard the event landed in — most commonly `Financials` series appearing in the
`Companies` shard (31 series), `Science and Technology` series appearing in `Health` (5) and
`Politics` series appearing in `Social` (4). Group by ticker grammar, never by category.

### Contract-template census

Running `taxonomy.classify_event()` unmodified gives a badly wrong picture, and the reason is a
parser defect worth fixing rather than working around (see *Traps*, item 1):

| template | `taxonomy.py` as shipped | after degree/unit normalisation |
|---|---:|---:|
| entity_menu | 152 | **63** |
| threshold ladder | 91 | **97** |
| binary | 79 | 79 |
| deadline ladder | 27 | 27 |
| bucket partition | **2** | **85** |

Per shard after normalisation:

| shard | threshold | bucket | binary | entity_menu | deadline |
|---|---:|---:|---:|---:|---:|
| Science_and_Technology | 29 | 0 | 31 | 36 | 23 |
| Climate_and_Weather | 30 | 85 | 13 | 7 | 2 |
| Companies | 35 | 0 | 20 | 14 | 2 |
| Health | 1 | 0 | 5 | 0 | 0 |
| Social | 1 | 0 | 6 | 2 | 0 |
| World | 1 | 0 | 3 | 3 | 0 |
| Transportation | 0 | 0 | 1 | 0 | 0 |
| NULL | 0 | 0 | 0 | 1 | 0 |

The brief's observation that "Climate is mostly entity_menu (96/137), unusual for a numeric domain"
is an artefact of the leg-subtitle grammar, not of the exchange. Climate temperature legs read
`'83° or below'`, `'84° to 85°'`, `'92° or above'` — the shipped `_RE_BUCKET` regex
`^\$?(?P<lo>-?[\d.,]+)\s*(?P<lm>[kmbt])?\s*(?:to|-|–)` cannot skip the `°` glyph between the number
and `to`, so every bucket leg fails to parse and the whole event falls through to the
`entity_menu` default. Normalising `°`, `°C`/`°F` and unit words before parsing turns 80 of those
events into bucket partitions and 5 into threshold ladders; the residual 7 Climate "entity menus"
are genuine (hurricane-name menus, a rain-city menu, a primary-energy-source menu).
**Climate is 85 tiled numeric partitions plus 30 threshold ladders — the most numerically regular
corner of the entire slice.**

### Collateral / mutual exclusivity

`mutually_exclusive` and `collateral_return_type` are perfectly correlated in this slice:

| mutex | collateral_return_type | events |
|---|---|---:|
| True | `MECNET` | 109 |
| False | `DIRECNET` | 80 |
| False | `""` (no netting) | 162 |

`MECNET` = mutually-exclusive netting (at most one leg pays). `DIRECNET` = directional netting,
which Kalshi applies to nested one-sided ladders (a long in a wider leg collateralises a short in a
narrower one). **`DIRECNET` is therefore a reliable machine-readable flag that an event is a nested
ladder** — more reliable than parsing the subtitles. All 85 tiled bucket partitions are MECNET;
all of the "Above $X" corporate-KPI and compute-price ladders are DIRECNET.

---

## Series families

Ticker grammar is the only reliable relation-extraction key. Volumes are cumulative contracts on
active legs; "2-sided" is the share of active legs quoting both a bid > 0 and an ask < 1.00.

| family | series | events | markets | cum. vol | 24 h vol | 2-sided |
|---|---:|---:|---:|---:|---:|---:|
| daily max-temperature ladders | 20 | 40 | 240 | 1,410,838 | 1,333,128 | 61.3 % |
| daily min-temperature ladders | 20 | 40 | 240 | 199,763 | 175,106 | 63.7 % |
| hourly temperature ladders | 5 | 5 | 50 | 130,312 | 122,387 | 20.0 % |
| precipitation (daily menu + monthly ladders) | 11 | 12 | 116 | 135,161 | 104,815 | 70.7 % |
| tropical cyclone (counts, names, category) | 8 | 14 | 146 | 615,128 | 1,994 | 68.3 % |
| climate indices (GISTEMP, RONI, sea ice, Lake Mead, CO₂) | 14 | 19 | 74 | 724,362 | 19,340 | 94.6 % |
| geophysical hazard (quake, volcano, tornado, meteor) | 7 | 9 | 23 | 615,704 | 3,689 | 95.7 % |
| AI leaderboard / benchmark | 13 | 19 | 151 | 9,980,511 | 120,693 | 69.3 % |
| AI model release + AGI declaration | 14 | 17 | 77 | 2,378,561 | 26,944 | 100 % |
| GPU compute price (Ornn) | 15 | 15 | 197 | 92,744 | 13,495 | 93.2 % |
| space launch / mission | 22 | 25 | 115 | 2,298,731 | 44,833 | 90.1 % |
| FDA approval / drug application | 11 | 14 | 63 | 523,004 | 1,309 | 100 % |
| disease case counts / outbreaks | 14 | 15 | 96 | 3,723,794 | 8,382 | 97.8 % |
| corporate KPI (Fiscal.ai) | 21 | 32 | 307 | 684,739 | 9,680 | 96.7 % |
| corporate action (M&A, CEO, layoff, IPO, stake) | 17 | 17 | 109 | 6,250,170 | 10,802 | 84.2 % |
| residual singletons (56 series) | 56 | 58 | 266 | — | — | — |

### 1. Daily temperature ladders — the volume core of Climate

**Two naming generations for the same product, and they are disjoint.**

- `KXHIGH<CITY>` — 7 cities: `NY, CHI, AUS, MIA, DEN, PHIL, LAX`
- `KXHIGHT<CITY>` — 13 cities: `ATL, BOS, DAL, DC, HOU, LV, MIN, NOLA, OKC, PHX, SATX, SEA, SFO`
- `KXLOWT<CITY>` — all 20 cities, and it uses the *long* city code where the high ladder uses the
  short one: `KXLOWTNYC` vs `KXHIGHNY`.

A scanner keying on the literal prefix `KXHIGHT` silently drops 7 of the 20 max-temperature cities,
and a scanner joining high↔low on the city suffix drops NYC unless it aliases `NY → NYC`.

Event ticker: `<SERIES>-<YY><MON><DD>` (`KXHIGHTATL-26AUG03`). Market ticker encodes the strike:

- `-T<n>` with `strike_type = less` → "n−1° or below" (`KXHIGHTATL-26AUG03-T84` = `83° or below`)
- `-B<n.5>` with `strike_type = between` → the 2-degree bucket centred on n.5
  (`KXHIGHTATL-26AUG03-B84.5` = `84° to 85°`)
- `-T<n>` with `strike_type = greater` → "n+1° or above" (`-T91` = `92° or above`)

Note that `-T84` and `-T91` are the *same* suffix grammar with opposite meanings; only
`strike_type` disambiguates. Six legs per event, mutex, MECNET, tiled with no gap.
`frequency = daily`, fee multiplier 1, no maker fee.

### 2. Hourly temperature — `KXTEMP<CITY>H`

5 cities (`NYC, LAX, DC, CHI, AUS`). Event ticker appends a 2-digit hour:
`KXTEMPNYCH-26AUG0217` = 2026-08-02, hour 17 local. Legs are `-T<n>.99` with
`strike_type = greater`, subtitle `'75° or above'` … `'84° or above'` — a **10-leg nested ladder,
`mutually_exclusive = false`, `DIRECNET`**, not a partition. Settlement source is *The Weather
Company*, not NWS (see Settlement).

### 3. Precipitation

- `KXRAIN-<YY><MON><DD>` — one leg per city (20 cities), `mutually_exclusive = false`, no netting.
  This is a genuine entity menu over locations: each leg is an independent "did it rain here" binary.
- `KXRAIN<CITY>M-<YY><MON>` — 8 monthly total-precipitation threshold ladders, `DIRECNET`.
  `KXRAINDENM`, `KXRAINCHIM`, `KXRAINNYCM` are `frequency = monthly`; the other five are `custom`.

### 4. Tropical cyclone

Four distinct grammars, all NOAA/NHC-settled, all `mutually_exclusive = false` except
`KXFIRSTHURRICANE`:

| series | event ticker | shape |
|---|---|---|
| `KXHURCTOT` / `KXHURCTOTMAJ` | `-26DEC01` | Atlantic hurricane / major-hurricane count, "Above N" |
| `KXHURRICANE` | `-26DEC01{EPAC,CPAC}{TOT,MAJ}` | Pacific basins, same shape; basin+severity encoded in the event suffix |
| `KXNAMEDSTORM` | `-26DEC01{EPAC,CPAC}TOT` | named-storm count |
| `KXHURRICANENAMES` | `-26DEC01{ATL,EPAC,CPAC}` | one leg per name on the season list, non-mutex |
| `KXFIRSTHURRICANE` | `-26DEC01ATL` | same name list, **mutex/MECNET** |
| `KXHURCAT` | `-26<STORMNAME>` | per-storm intensity, `Category 3/4/5 or above` nested |

### 5. AI leaderboard / benchmark

The densest cluster in Science & Technology and the one with the most inconsistent grammar.

| series | what it ranks | source | mutex |
|---|---|---|---|
| `KXLLM1-<YYMMMDD>` | "Best AI" — **resolves on the company** | LM Arena (Remove Style Controls) | yes |
| `KXTOPMODEL-<YYMMMDD>` | top-ranked **model string** | LM Arena | yes |
| `KXTECHRANKLISTAICODE-<YYMMMDD>` | #1 on LM Code Arena, **brand** | LMArena Code | yes |
| `KXCODEAI-<YYMMMDD>` | #1 on Datacurve DeepSWE, brand | DeepSWE | yes |
| `KXMATHAI-<YYMMMDD>` | #1 on Text Arena (Math), brand | Arena Math | yes |
| `KXCODINGMODEL-<YYMMM>` | best coding model, **company** | LiveBench.ai "Coding Average" | yes |
| `KXCHINAAI-<YYMMMDD>` | highest-ranked Chinese company | LM Arena | yes |
| `KXMODELHIGH-<YY>-<score>` | first to hit a score, **company** (+`Other`) | LM Arena | yes |
| `KXAISPIKE-<YY>` | any model reaches score X before Jan 1 | LM Arena | no |
| `KXARENASCORE-<MODELCODE>` | one named model's debut score | LM Arena | no, DIRECNET |
| `KXLASTEXAM-<YY>DEC31` | best HLE accuracy by a date | Humanity's Last Exam | no, DIRECNET |
| `KXTOPAI-<YY>` | company had a #1 model at any time in the year | LM Arena | no |

`KXLLM1` is the **only maker-fee series in the whole slice** (`quadratic_with_maker_fees`), and it
is also the largest by open interest after `KXALIENS` (5.04 M contracts across 23 legs).

### 6. GPU compute price — `KX{A100,B200,H100,H200,RTX5090}{MAX,MON,W}`

Five chips × three horizons, all settled on the **Ornn** compute index
(`https://dashboard.ornnai.com/compute`, "USD iteration"):

- `…MON-<YY><MON>31`: 19–20 legs, `Above $x` on a 5¢ grid, resolves on the price **on** the last day.
- `…MAX-<YY>DEC31`: 3–9 active legs on a 15¢/30¢ grid, resolves if the price is above the strike
  **by** Dec 31 — i.e. a running-maximum contract. Crossed strikes are already `finalized`
  (e.g. `KXH100MAX-26DEC31` has 14 finalized legs at $1.13–$3.08 and 6 active at $3.23–$3.98).
- `…W-<YY><MON><DD>`: a single "Price to Beat: 2.76" leg per week, `frequency = weekly`.

`frequency` is unreliable inside this family (`KXA100MON` is tagged `one_off`, `KXRTX5090MON` is
tagged `one_off`, while `KXH100MON`/`KXH200MON`/`KXB200MON` are `monthly`).

### 7. Corporate KPI — the Fiscal.ai family

21 series, 32 events, 307 markets. Ticker grammar
`KX<TICKER>A-<YY><MON><METRIC>-<raw threshold>`:

`KXHOODA-28JANFUNDED-28000000.0` = Robinhood (`HOOD`), report expected Jan 2028, metric
`FUNDED` (funded customers), strike 28,000,000. The month prefix is the **expected reporting
month**, not the measurement period — the measurement period is in the title/rules ("in 2026",
"in fiscal 2026"). Metrics seen: `FUNDED, GOLDSUBS, PROD, DEL, HEAD, PREMSUBS, MAU, GMV, ALBD,
UNITS, RESTS, REST, TXN, USSALES, MTU, FARE, SEATS, RIDES, IMPR, DAP, CIGS, ZYNPCH, COMPTXN,
STORES, PAX, TRIPS, USCOMP, DELIV`. All are `DIRECNET` "Above X" nested ladders.

Note `KXFA` (Ford) breaks the `KX<2-6 letters>A` pattern with a single-letter ticker stem.

### 8. Corporate action

`KXACQANNOUNCEANNUAL-27JAN01` (27 legs, "any company announces an agreement to acquire <target>
before Jan 1, 2027", non-mutex); `KXUSACOMPANYSTAKE-27JAN01` (21 legs, US federal government takes
a stake); `KXCOMPANYLAYOFF-27JAN01` (8 legs); `KXTAKEOVERACQWB-27JUN30` (mutex, 3 legs:
Netflix / Paramount / "None before July 2027"); CEO-succession menus `KXNEWROLEX`, `KXNEWROLEFAZE`,
`KXJPMCEONEW`; single binaries `KXTESLACEOCHANGE`, `KXOPENAICEOCHANGE`, `KXRIPPLINGDEEL`,
`KXTAKEOVERNEE`, `KXCOMPANYSTAKERYANAIR`. `KXIPOANTHROPIC-DATE` and `KXAGICO-COMP` are deadline
ladders.

### 9. The NULL-category event

Exactly one event in the entire exchange snapshot has `category: null`:

```
event_ticker  KXGOLDVSSILVER-26DEC31
series        KXGOLDVSSILVER   (series.category = "Financials", tags ["Match Ups","Markets"])
title         Annual Return: Gold vs. Silver
mutex         true,  collateral_return_type MECNET
legs          -XAU 'Gold'   bid 0.79 / ask 0.86   vol 3,268
              -XAG 'Silver' bid 0.17 / ask 0.24   vol 8,515
settlement    Pyth (https://app.pyth.com/explore)
rules         "If Gold performs above Silver during 2026 by 0.001% rounded to the nearest
               thousandth then the market resolves to Yes."
```

The event-level `category` is missing while the series-level one is present and says `Financials`.
This is a **metadata defect, not a category**: any pipeline that groups by `event.category` will
either drop this event or create a phantom bucket. Group by `series_ticker` → `series.category`.

---

## Contract templates and their leg grammar

**Bucket partition** (85 events, all Climate, all mutex/MECNET, all tiled).
Legs: one `less` leg, k `between` legs, one `greater` leg.
> `KXHIGHTATL-26AUG03-T84`, `'83° or below'` — *"If the maximum temperature recorded at Atlanta for
> Aug 3, 2026, is less than 84° fahrenheit according to the National Weather Service's
> Climatological Report (Daily), then the market resolves to Yes."*

**Threshold ladder** (97 events; 80 of them `DIRECNET`). One-sided, nested, non-mutex.
> `KXHOODA-28JANFUNDED-28000000.0`, `'Above 28 million'` — *"If Robinhood Markets Inc. reports Above
> 28000000.0 funded customers in 2026, then the market resolves to Yes."*

Descending variants exist and must be handled: `KXARCTICICEMIN-26OCT01-T4.8` is `'Below 4.8 million
sq km'` — *"If the National Snow & Ice Data Center records a day between December 19, 2025 and
October 01, 2026 where the extent of arctic sea ice is below 4.8 million square kilometers…"* — so
the nesting runs the other way (lower strike ⊂ higher strike).

**Deadline ladder** (27 events, non-mutex, mostly no netting). Legs differ only by a date, and the
leg's `close_time` equals its deadline — a far more reliable ordering key than the subtitle, which
may be a bare month name (`'Before September'`).
> `KXCLAUDE-MYTH-26SEP01`, `'Before Sep 1, 2026'` — *"If Anthropic releases A model called Mythos
> before Sep 1, 2026, then the market resolves to Yes."*

**Entity menu** (63 events; 24 mutex/MECNET, 39 non-mutex). Non-mutex menus are k independent
binaries sharing an event shell:
> `KXACQANNOUNCEANNUAL-27JAN01-ANYEBAY`, `'eBay'` — *"If any company announces an agreement to
> acquire eBay before Jan 1, 2027, then the market resolves to Yes."*

Mutex menus are winner-take-all but usually **not exhaustive**:
> `KXFIRSTHURRICANE-26DEC01ATL-ART`, `'Arthur'` — *"If a storm named Arthur is the first storm
> categorized as a hurricane in the Atlantic between May 15, 2026 and December 01, 2026…"*
> rules_secondary: *"If there is no storm categorized as a hurricane in the Atlantic between
> May 15, 2026 and December 01, 2026, then all markets resolve to No."*

**Binary** (79 events, single active leg). Mostly long-dated novelty questions
(`KXCOLONIZEMARS`, `KXELONMARS-99` closes **2099-08-01**, `KXMEISSNER`, `KXRIEMANN`).

No `combination` template appears anywhere in this slice.

---

## Settlement

`settlement_sources` is populated on **every** event (0 events with an empty list). The mix is
strongly bimodal: named primary data providers for the numeric families, and a rotating list of
general news outlets for the qualitative ones.

Primary-data settlers used here:

| source | families |
|---|---|
| NWS Climatological Report (Daily), per-station | 20 max-temp + 20 min-temp ladders, 8–10 monthly rain ladders |
| The Weather Company (`https://weather.com/kalshi`) | 5 hourly temperature ladders **and** the daily `KXRAIN` city menu |
| NOAA / National Hurricane Center | all cyclone counts, names, categories |
| NOAA Climate Prediction Center | `KXRONI` (peak RONI value, "final (non-preliminary)" values only) |
| National Snow & Ice Data Center (Sea Ice Index v4) | `KXARCTICICEMIN` |
| U.S. Bureau of Reclamation | `KXMEAD` |
| NASA / NOAA GML | `KXCO2LEVEL`, `KXHMONTHRANGE` (Land-Ocean Temperature Index) |
| Fiscal.ai | all 21 corporate-KPI series |
| Ornn | all 15 GPU compute-price series |
| LM Arena / LiveBench.ai / DeepSWE / Humanity's Last Exam | AI leaderboard family |
| FDA, CDC | drug approval and disease-count families |
| Pyth | `KXGOLDVSSILVER` |
| SEC + wire services | `KXACQANNOUNCEANNUAL` and most corporate actions |

Counts of the most-used news settlers across the slice's 351 events: WSJ 39, NYT 35, AP 26,
Reuters 26+19, ABC 24, Axios 20, CBS 20, Bloomberg 19, The Information 19, Washington Post 19.
Note the **same outlet appears under two entries differing only by a trailing slash in the URL**
(`https://www.reuters.com/` vs `https://www.reuters.com`, CNN, MSNBC, Politico, Fox News, Axios,
Semafor, NYT, WaPo, AP, CBS) — `settlement_sources` must be normalised before it can be used as a
grouping key.

**Station identity.** Each temperature ladder names its station in `settlement_sources`
(`NWS Climatological Report Chicago Midway`, `NWS Climatological Report San Antonio`, …) and
`rules_secondary` gives the CLI product code and WFO URL, e.g. for `KXLOWTNYC`:
*"Data for CLINYC can be found by clicking the following URL:
https://www.weather.gov/wrh/Climate?wfo=okx, navigating to the 'Observed Weather' tab, and choosing
the location 'Central Park NY' with Daily Cl…"*. Seven of the 40 ladders have a degenerate source
name (bare `NWS Climatological Report` for DEN, LAX, NY, PHIL high; DEN, LAX, PHIL, NYC low), so the
station must be read from `rules_secondary`, not from the source name. `KXHIGHTDC` has a trailing
space in its source name (`'NWS Climatological Report DC '`).

**Early close.** `can_close_early = true` for 2,252 of 2,260 markets; the 8 exceptions are all
`KXMEAD-26DEC-A10xx` (Lake Mead end-of-month elevation). Distinct `early_close_condition` texts on
active markets:

| n | condition |
|---:|---|
| 989 | *"This market will close and expire early if the event occurs."* |
| 386 | (none) |
| 396 | *"The Last Trading Time will be 11:59 PM local time on August 0X, 2026 regardless…"* (daily weather) |
| 84 | *"The Last Trading Time will be 11:59 PM ET on August 0X, 2026 regardless…"* |
| 69 | *"If this event occurs, the market will close the following 10am ET."* |
| 38 | *"This market will close and expire early if the weather event occurs."* |
| 24 | *"This market will close and expire early if the acquisition is announced…"* |

The "closes early if the event occurs" family (989 markets, 46.1 % of active) means every deadline ladder
and every running-maximum ladder can lose legs mid-life; a basket built from a cached leg list will
silently shrink.

**Settlement timer** (active markets): 1,800 s dominates (Science 575, Companies 487, Climate 274),
300 s is the daily-weather default (Climate 420), 3,600 s appears in 274 markets, and 25 Climate
markets carry a timer of 0. Two markets carry an anomalous 14 s and four carry 3,599 s.

**Expiry horizon** (days to `close_time` from the snapshot, active legs):

| shard | n | median | ≤ 2 days | > 365 days |
|---|---:|---:|---:|---:|
| Climate_and_Weather | 879 | 1.4 d | 64.8 % | 3.4 % |
| Science_and_Technology | 702 | 151.3 d | 4.4 % | 10.8 % |
| Companies | 495 | 296.3 d | 0.0 % | 49.1 % |
| World | 23 | 128.7 d | 0.0 % | 30.4 % |
| Social | 30 | 881.3 d | 0.0 % | 63.3 % |
| Health | 12 | 882.8 d | 0.0 % | 83.3 % |
| Transportation | 1 | 1247.3 d | 0.0 % | 100 % |

Slice-wide: min 0.01 d, p25 1.4 d, median 120.8 d, p90 606 d, max **26,661 d** (`KXELONMARS-99`,
closing 2099-08-01). The distribution is bimodal — a daily weather book and a multi-year science
book with almost nothing in between.

---

## Liquidity

Across 2,144 active markets:

| measure | value |
|---|---|
| has a bid > 0 | 1,788 (83.4 %) — and every one of those has bid size > 0 |
| has an ask < 1.00 | 2,089 (97.4 %) — likewise all with size > 0 |
| **two-sided book** | **1,733 (80.8 %)** |
| two-sided **and** spread ≤ 2¢ | 448 (20.9 %) |
| traded in the last 24 h | 1,170 (54.6 %) |

Spread on the two-sided subset: p25 = 2¢, **median 5¢**, p75 = 7¢, p95 = 18¢, max 97¢.
Since the fee at P = 0.50 is 1.75¢ per leg, a 5¢ round-trip plus 3.5¢ of fees means the **median
two-sided market in this slice costs ~8.5¢ to cross and unwind** — an order of magnitude above the
structural mispricings measured below.

Depth is the real constraint. Min-side touch depth (`min(bid_size × bid, ask_size × (1−ask))`, i.e.
capital that can actually be committed at the touch) over the 1,733 two-sided markets:
**p25 = $0.60, median = $2.10, p75 = $5.00, max $1,640.** Sizes are *fractional*: 920 of 2,144
active markets quote a non-integer size (e.g. `yes_ask_size_fp = 1.41`, `0.18`, `0.72`), so any
scanner that casts sizes to `int` will overstate or zero out capacity.

Open interest per active leg: 127 legs at zero, p25 = 100, median = 505, p75 = 2,139, p95 = 20,210,
max 9,431,548 (`KXALIENS-27`). Volume per leg: 124 at zero, median 821, p95 46,088, max 26,416,393
(also `KXALIENS-27`). `liquidity_dollars` is **`0.0000` for all 2,144 active markets** in this
slice — the field is not populated here and must not be used as a liquidity filter.
`notional_value_dollars` is `1.0000` for all of them.

Where the flow actually is:

| shard | 2-sided | zero 24 h volume |
|---|---:|---:|
| Companies | 94.5 % | 73.5 % |
| Science_and_Technology | 90.2 % | 50.9 % |
| Climate_and_Weather | 65.4 % | **23.2 %** |

Climate looks the *worst* on quote coverage and the *best* on actual trading: it supplies 1.76 M of
the slice's 2.13 M 24-hour contracts (83 %) off only 3.7 M cumulative volume, because the daily
ladders re-list every day. Science & Technology has 48.99 M cumulative volume but half its legs did
not trade at all in 24 hours — that is parked open interest on multi-year questions
(`KXALIENS-27` alone is 29.6 M cumulative volume / 11.3 M OI, 47 % of the slice's total volume).

Top ten active markets by cumulative volume: `KXALIENS-27` (26.4 M), `KXALIENS-27-26SEP` (1.98 M),
`KXLLM1-26DEC31-A` (1.83 M), `KXTAKEOVERACQWB-27JUN30-PSKY` (1.69 M), `KXNEWOUTBREAKHANTA-26`
(1.64 M), `KXTAKEOVERACQWB-27JUN30-NFLX` (1.50 M), `KXLLM1-26DEC31-OAI` (1.50 M),
`KXLLM1-26DEC31-GOOG` (1.27 M), `KXLLM1-26DEC31-XAI` (1.05 M), `KXTAKEOVERACQWB-27JUN30-NONE`
(0.90 M).

**Nominal vs tradeable, by family.** Genuinely tradeable (two-sided, traded today, non-trivial
depth): the 40 daily temperature ladders, the 5 hourly ladders, `KXLLM1`/`KXTOPAI`/`KXAISPIKE`,
`KXALIENS`, `KXTAKEOVERACQWB`, `KXIPHONERELEASE`, `KXCLAUDE`/`KXGROK`/`KXGEMINI`,
`KXSPACEXCOUNT`. Effectively nominal: the entire GPU compute family (197 markets, 92 k cumulative
volume, 13 k in 24 h — 93 % two-sided but at sizes of 1–10 contracts), the 21-series Fiscal.ai KPI
family (307 markets, 9.7 k contracts in 24 h across all of them), the tropical-cyclone counts
(146 markets, **1,994 contracts in 24 h**), and 79 single-leg binaries of which 51 traded at all
today. Health, Social, World, Transportation and NULL together are 68 markets and 9,791 contracts
of 24-hour volume — listing surface, not a market.

---

## Structural constraints

Notation: `bid(X)` is the price at which YES on leg X can be **sold**, `ask(X)` the price at which
it can be **bought**. Fees are the taker fee at the executed price, one per leg. All series in this
slice have `fee_multiplier = 1` and only `KXLLM1` charges makers.

### S1 — Tiled bucket partition sums to exactly 1 (85 events)

**Inequality.** For a mutually-exclusive event whose legs tile the line with no gap and no overlap:
`Σᵢ ask(i) ≥ 1` and `Σᵢ bid(i) ≤ 1`, net of fees.
**Rule basis.** The legs are `less` / `between` / `greater` on the same underlying with contiguous
strikes and `mutually_exclusive = true` + `MECNET`; e.g. `KXHIGHTATL-26AUG03` covers
`≤83`, `84–85`, `86–87`, `88–89`, `90–91`, `≥92` — exhaustive over ℝ.
**Verified structurally**: all 85 tiled events pass `partition_is_tiled` after unit normalisation;
none has a gap, and none contains a non-active leg.

**Live check.** 79 of the 85 have a complete ask side. `Σ ask`: min 0.9700, median 1.0600,
max 2.4200. The single sub-1 basket is
`KXHIGHTBOS-26AUG03`: `Σ ask = 0.9700` → gross +3.00¢, fees 5.34¢ → **net −2.34¢**, and the
binding leg (`-T77`, ask 0.13) has size 0.18 contracts. 22 have a complete bid side;
`Σ bid`: min 0.4300, median 0.9450, max 1.0400. Two exceed 1:
`KXHIGHMIA-26AUG03` `Σ bid = 1.0400` → gross +4.00¢, fees 4.58¢ → **net −0.58¢** (min bid size 3);
`KXLOWTNYC-26AUG03` `Σ bid = 1.0100` → gross +1.00¢, fees 4.91¢ → **net −3.91¢**.
**Verdict: structurally consistent; two events are gross-violated but fee-dominated.**
**Failure modes.** (a) A leg going `finalized` mid-life breaks exhaustiveness — no tiled event in
this snapshot has one, but `early_close_condition` allows it. (b) The `less`/`greater` legs are
open-ended, so tiling is only verifiable through `strike_type`, not through the subtitles alone.

### S2 — Mutually-exclusive-but-not-exhaustive menus: only `Σ bid ≤ 1` is safe (24 events)

**Inequality.** For any `mutually_exclusive = true` event, at most one leg pays, so for **any
subset S of legs**, `Σ_{i∈S} bid(i) ≤ 1` net of fees. The reverse (`Σ ask ≥ 1`) requires
exhaustiveness and **does not hold here**.
**Rule basis.** `KXFIRSTHURRICANE-26DEC01ATL` rules_secondary: *"If there is no storm categorized as
a hurricane in the Atlantic between May 15, 2026 and December 01, 2026, then all markets resolve to
No."* `KXTAKEOVERACQWB` includes an explicit `None before July 2027` leg, but `KXNEWROLEX-27JAN`
(8 named candidates for CEO of X) and `KXMODELHIGH-27-1550` do not cover the residual.
**Live check.** `Σ ask` for `KXNEWROLEX-27JAN` = **0.4300** and for `KXMODELHIGH-27-1550` = 0.4800;
`KXFIRSTHURRICANE-26DEC01ATL` = 1.37 across 21 legs with `Σ bid = 0.98`. None of these is an
arbitrage. Best sell-side basket: `KXCBDECISIONCANADA-26OCT`, 3 of 5 legs with live bids,
`Σ bid = 1.0200` → gross +2.00¢, fees 2.62¢ → **net −0.62¢**; `KXTAKEOVERACQWB-27JUN30`,
`Σ bid = 1.0200` → **net −1.01¢**. All 109 mutex events have at least one sellable leg; 8 have
`Σ bid > 1` gross; **0 are net-positive after fees.**
**Failure mode.** Treating `Σ ask < 1` as an arbitrage on a non-tiled mutex menu is the single most
dangerous error in this slice — `KXNEWROLEX` would look like a 57¢ edge.

### S3 — Nested one-sided ladders are monotone (97 threshold + 39 deadline = 136 ladders)

**Inequality.** For a `>=`-direction ladder with strikes x₁ < x₂, `{V > x₂} ⊂ {V > x₁}`, hence
`bid(x₂) ≤ ask(x₁)` net of fees. For a deadline ladder with deadlines t₁ < t₂,
`{event before t₁} ⊂ {event before t₂}`, hence `bid(t₁) ≤ ask(t₂)`.
**Rule basis.** The rule strings are identical modulo the numeral/date, e.g.
`KXLASTEXAM-27DEC31-T60`: *"If any language model achieves an accuracy of at least 60% on
Humanity's Last Exam before Dec 31, 2027, then the market resolves to Yes."* For deadline ladders
the leg's `close_time` is exactly the deadline, which is the correct ordering key (leg subtitles are
sometimes bare month names with no year).
**Live check.** 4,395 ordered pairs, 3,716 with both sides executable, **2 raw violations, 1
net-positive**:

- `KXAISPIKE-27`: sell `-1750` (`'At least 1750 score'`) at 0.0400 (size 50), buy `-1650` at 0.0300
  (size **0.72**) → gross +1.00¢, fees 0.48¢ → **net +0.52¢, capacity 0.72 contracts ≈ $0.004.**
- `KXHOODA-28JANFUNDED`: sell `-30200000.0` at 0.5400 (size 137), buy `-30000000.0` at 0.5300
  (size 49) → gross +1.00¢, fees 3.49¢ → **net −2.49¢.**

All 39 deadline ladders (145 adjacent pairs, all pairs checked) are consistent.
**Failure modes.** (a) Descending ladders (`Below X`, `X or below`) invert the nesting; the same
event may mix `less` and `greater` `strike_type`s. (b) A ladder whose legs carry different
*subjects* is not nested — `parse_threshold`'s `subject` field exists for this reason. (c) `MAX`-style
ladders ("above X **by** date") and `MON`-style ladders ("above X **on** date") look identical in the
subtitle and are not the same proposition.

### S4 — `KXSTARSHIPSPACE-26` and `-26B` are two listings of the same random variable

**Identity.** `KXSTARSHIPSPACE-26` is a mutex/MECNET *bucket* partition of the 2026 Starship
"reached space" launch count (`1 or below`, `2`, …, `9`, `10 or above`);
`KXSTARSHIPSPACE-26B` is a `DIRECNET` *threshold* ladder on the same count (`Above 3` … `Above 12`).
Therefore for every N where the tail is expressible:
`P(26B: Above N) = Σ_{k>N} P(26: k)`, hence
`bid(26B-N) ≤ Σ_{k>N} ask(26-k)` and `ask(26B-N) ≥ Σ_{k>N} bid(26-k)`.
**Rule basis.** Identical underlying and identical qualification clause.
`KXSTARSHIPSPACE-26-3.0`: *"If exactly 3 Starship launches reach Space in 2026…"*;
`KXSTARSHIPSPACE-26B-3`: *"If above 3 Starship launches reach Space in 2026…"*; both
rules_secondary: *"A Starship will be considered to have reached space if its maximum altitude is at
least 62 miles above sea level at any point during its flight."*
**Live check — this is the one genuinely violated, executable constraint in the slice:**

| N | sell `26B-N` | buy tail buckets | gross | fees | **net** | capacity |
|---:|---|---|---:|---:|---:|---:|
| 5 | 0.3600 (sz 5) | 6,7,8,9,10+ = 0.2600 | +10.00¢ | 3.29¢ | **+6.71¢** | 1.41 |
| 6 | 0.1700 (sz 5) | 7,8,9,10+ = 0.1200 | +5.00¢ | 1.81¢ | **+3.19¢** | 5 |
| 7 | 0.0900 (sz 5) | 8,9,10+ = 0.0600 | +3.00¢ | 1.00¢ | **+2.00¢** | 5 |
| 8 | 0.0700 (sz 5) | 9,10+ = 0.0500 | +2.00¢ | 0.81¢ | **+1.19¢** | 5 |
| 9 | 0.0400 (sz 250) | 10+ = 0.0300 | +1.00¢ | 0.48¢ | **+0.52¢** | 61 |

Total extractable profit if all five are lifted (legs are shared, so this is an upper bound):
**≈ $0.72.** The constraint is violated and executable; the capacity is negligible.
**Failure mode / limit.** N ≥ 10 is *not* comparable: the bucket ladder's top leg is
`10 or above`, which includes exactly 10, so `{count > 10}` cannot be assembled from it.
Also note the reverse direction is not violated (`ask(26B-3) = 0.95` vs `Σ bid(tail) = 0.87`).

### S5 — "First hurricane named X" ⊂ "X is a hurricane"

**Inequality.** `bid(KXFIRSTHURRICANE-26DEC01ATL-<NAME>) ≤ ask(KXHURRICANENAMES-26DEC01ATL-<NAME>)`.
**Rule basis.** *"If a storm named Arthur is **the first** storm categorized as a hurricane in the
Atlantic between May 15, 2026 and December 01, 2026…"* vs *"If a storm named Arthur is a storm
categorized as a hurricane in the Atlantic between May 15, 2026 and December 01, 2026…"* — identical
basin, identical window, identical name list (21 shared names), both NOAA/NWS-settled.
**Live check.** 21 name pairs, 6 with both sides executable, **0 violations**. Tightest:
`Cristobal` — `bid(FIRST) = 0.49` vs `ask(NAMES) = 0.50`, slack **1.00¢** (fees on that trade would
be ≈ 3.5¢). Note the NAMES leg for Cristobal has **no bid at all** (0.00/0.50) while the FIRST leg
bids 0.49; the ordering is respected only because the NAMES ask happens to sit 1¢ above.
Widest slack: 98¢ on the late-alphabet names, where the NAMES legs are quoted 0.00/0.98.
**Failure mode.** Name lists differ by basin; `KXHURRICANENAMES` also lists EPAC and CPAC events
with completely different names, and there is no `KXFIRSTHURRICANE` for those basins.

### S6 — Same population, nested windows: Ebola country menu

**Inequality.** `bid(KXEBOLACOUNTRY-OCT26-<C>) ≤ ask(KXEBOLACOUNTRY-27-<C>)`.
**Rule basis.** Both: *"If a confirmed human case of Ebola disease in <country> is officially
reported after Issuance and before <Oct 1, 2026 | Jan 1, 2027>, then the market resolves to Yes."*
Same 16-country leg set, same issuance anchor.
**Live check.** 16 pairs, all 16 executable on both sides, **0 violations, minimum slack 8.00¢.**

### S7 — Same benchmark, nested windows: Humanity's Last Exam

**Inequality.** `bid(KXLASTEXAM-26DEC31-T<X>) ≤ ask(KXLASTEXAM-27DEC31-T<X>)` for the 7 shared
strikes (60, 65, 70, 75, 80, 85, 90 %).
**Rule basis.** *"If any language model achieves an accuracy of at least X% on Humanity's Last Exam
before Dec 31, 20YY…"* — the 2026 window is contained in the 2027 window.
**Live check.** 7 pairs, all executable, **0 violations, minimum slack 24.00¢.**

### S8 — Severity containment in cyclone counts

**Inequality.** Every category-3+ hurricane is a hurricane and every hurricane is a named storm, so
at the same threshold N and the same basin/window:
`bid(MAJ > N) ≤ ask(TOT > N)` and `bid(HURRICANE > N) ≤ ask(NAMEDSTORM > N)`.
**Rule basis.** Atlantic: *"If the NOAA's National Hurricane Center records more than N hurricanes of
hurricane category **3 or above** between January 1, 2026 and December 01, 2026…"* vs *"…category
**1 or above** between January 1, 2026 and December 01, 2026…"* — windows verified identical
(both `close_time` 2026-12-02T04:59Z). Pacific pairs both use *"between May 15, 2026 and
December 01, 2026"* (`close_time` 2026-12-01T15:00Z). **The Atlantic window (Jan 1) and the Pacific
window (May 15) are different — do not cross-pair basins.**
**Live check.** Atlantic MAJ⊂TOT: 4 shared strikes (4,5,6,7), min slack **17.00¢**.
E. Pacific MAJ⊂TOT: 4 shared strikes (5,6,7,8), min slack 47.00¢.
C. Pacific MAJ⊂TOT: 3 shared strikes, min slack 37.00¢.
C. Pacific HURRICANE⊂NAMEDSTORM: 4 shared strikes (2,3,4,5), min slack 30.00¢.
E. Pacific HURRICANE⊂NAMEDSTORM: **no shared strikes** (hurricane ladder 5–13, named-storm ladder
16–26) — the relation exists but is not testable. **0 violations.**

### S9 — Point-in-time #1 ⊂ #1 at any time during the year (AI leaderboard)

**Inequality.** `bid(KXLLM1-26DEC31-<company>) ≤ ask(KXTOPAI-27-<company>)`.
**Rule basis.** `KXLLM1-26DEC31-31-OAI`: *"If **OpenAI** has the top-ranked LLM **on Dec 31, 2026**…"*
vs `KXTOPAI-27-JAN01-OPEN`: *"If OpenAI has a #1 ranked AI model **before Jan 1, 2027**…"* — Dec 31,
2026 is inside the window, and both settle on *LM Arena Leaderboard (Remove Style Controls)*.
**The join key must be extracted from `rules_primary`, not from `yes_sub_title`** — the `KXLLM1`
legs are labelled `Ernie`, `Gemini`, `ChatGPT`, `Claude`, `Grok`, `Muse Spark`, `Qwen`, `Kimi` while
resolving on Baidu, Google, OpenAI, Anthropic, xAI, Meta, Alibaba, Moonshot.
**Live check.** 6 of the 8 `KXLLM1` companies have a `KXTOPAI` counterpart (Google and Anthropic are
**absent** from `KXTOPAI-27`). All 6 consistent:

| company | `KXLLM1` bid | `KXTOPAI` ask | slack |
|---|---:|---:|---:|
| Alibaba | 0.0070 | 0.0700 | 6.3¢ |
| Baidu | 0.0030 | 0.1000 | 9.7¢ |
| Moonshot | 0.0200 | 0.1400 | 12.0¢ |
| Meta | 0.0290 | 0.1500 | 12.1¢ |
| xAI | 0.0600 | 0.2000 | 14.0¢ |
| OpenAI | 0.1430 | 0.3800 | 23.7¢ |

**Failure mode.** `KXTOPAI` says "a #1 ranked AI model" without naming the leaderboard variant in
the rule text; the source list says *" LM Arena Leaderboard (Remove Style Controls)"* (note the
leading space) while `KXLLM1` says *"LM Arena Leaderboard (Remove Style Controls)"* — same board,
different string. A different leaderboard tab would break the containment.

### S10 — OpenAI AGI ⊂ any-company AGI

**Inequality.** `bid(OAIAGI-<yy>) ≤ ask(KXAGICO-COMP-<yy>Q4)`.
**Rule basis.** *"If OpenAI announces that they have attained AGI by Dec 31, 2026…"* ⊂ *"If **any
company** (public or private) officially announces that it has achieved Artificial General
Intelligence (AGI) after market issuance and before Jan 1, 2027…"*
**Live check.** 3 comparable date pairs, **0 violations**: 0.0500 vs 0.1000 (slack 5.0¢);
0.1650 vs 0.4800 (31.5¢); 0.3900 vs 0.7600 (37.0¢).
**Failure mode.** `KXAGICO` carries an *"after market issuance"* qualifier that `KXOAIAGI` does not;
an announcement predating `KXAGICO`'s issuance would resolve the subset YES and the superset NO.
Also `KXAGICO` lives in the `Companies` shard while `KXOAIAGI` lives in `Science_and_Technology` —
a category-scoped scanner would never see this pair.

### S11 — "First company to score 1550" basket = "any model scores 1550" (conditional)

**Identity.** `Σ_i P(KXMODELHIGH-27-1550-i) = P(KXAISPIKE-27-1550)` **if and only if** the `Other`
leg genuinely covers the residual company set.
**Rule basis.** `KXMODELHIGH-27-1550-CLAU`: *"If a model by Anthropic is the first to hit 1550 on
Text Arena before Jan 1, 2027…"*; `KXAISPIKE-27-1550`: *"If an AI model has a score of at least 1550
before Jan 1, 2027 on the LMSYS leaderboard…"*. Same source
(`LM Arena Leaderboard (Remove Style Control)`).
**Live check.** `Σ ask(MODELHIGH) = 0.4800`, `Σ bid = 0.2400`; `KXAISPIKE-27-1550` = 0.2100 / 0.2800.
Both directions consistent: buying the basket and selling AISPIKE is −27.0¢; buying AISPIKE and
selling the basket is −4.0¢. **Consistent.**
**Failure mode — do not treat this as exact.** The `Other` leg's rule text is the degenerate
template fill *"If a model by **Other** is the first to hit 1550 on Text Arena before Jan 1, 2027,
then the market resolves to Yes."* There is no clause telling us what "Other" resolves against, and
if **no** model reaches 1550 the whole `KXMODELHIGH` event pays nothing while `KXAISPIKE-27-1550`
also pays nothing — so the identity survives that case but only by luck of both being NO.

### S12 — Daily minimum ≤ daily maximum (exists, but structurally untestable)

**Inequality.** For a city/date, `min ≤ max` from the *same* NWS CLI daily product, so
`P(min > x) ≤ P(max > x)` for every x.
**Rule basis.** `KXLOWTNYC-26AUG03-T68`: *"If the **minimum** temperature recorded at New York City
for Aug 3, 2026, is less than 68° fahrenheit according to the National Weather Service's
Climatological Report (Daily)…"*; `KXHIGHNY-26AUG03-T80` is the same sentence with **maximum**.
Both list station `CLINYC` / Central Park.
**Live check.** All 20 cities × 2 dates = 40 matched (city, date) pairs. In **0 of 40** does the low
ladder's strike range reach into the high ladder's strike range: the gap between the top of the low
ladder and the bottom of the high ladder is min 2 °F, **median 13 °F**, max 27 °F (e.g. Austin
2026-08-03: low ladder `≤66 … 67–74 … >75`, high ladder `≤99 … 100–107 … >108`). The constraint is
real but Kalshi centres the two ladders on disjoint supports, so it produces **no testable pair**.
A scanner should record this as "relation exists, 0 comparable strikes" rather than "consistent".

### S13 — Hourly temperature ≤ daily maximum (NOT exact — different source)

`KXTEMPNYCH-26AUG0217` (`'75° or above'` … `'84° or above'`) is the temperature at 17:00 local; the
daily max must be ≥ it. But `KXTEMPNYCH` settles on **The Weather Company** (*"the temperature
recorded at Central Park, New York City for Aug 2, 2026 5 PM EDT as reported by The Weather Company
(for coordinates KNYC)"*, and rules_secondary explicitly says *"The official, final value for this
market is the temperature reported by the The Weather Company, not any other weather service. NWS
Climatological Reports, Google Weather, etc. may be useful references…"*) while `KXHIGHNY` settles
on the **NWS Climatological Report**. Two different observation products for the same station can
and do differ by a degree. **Treat this as an approximate relation, not a settlement constraint.**
It is in any case untestable here: the hourly ladders exist for 5 cities on the current day, and
their strike ranges (NYC 75–84, LAX 73–82, DC 74–83, CHI 68–77, AUS 93–102) sit below the
corresponding daily-max ladder ranges.

### S14 — `MON` ⊂ `MAX` in the GPU compute family (no shared strikes)

Price **on** Aug 31 above X implies price **above X by** Dec 31, so
`bid(KX<chip>MON-26AUG31-<X>) ≤ ask(KX<chip>MAX-26DEC31-<X>)`. Checked all five chips:
**zero shared strikes in every case** (H100: MON 2.26–3.21, MAX active 3.23–3.98; A100: MON
0.53–1.48, MAX 1.39–2.59 — the MAX ladder's crossed strikes are already `finalized`). The relation
is structurally sound and empirically vacuous on this snapshot.

### S15 — Hurricane intensity ladder (`KXHURCAT`)

`Category 5 or above` ⊂ `Category 4 or above` ⊂ `Category 3 or above` — rules give the wind
thresholds explicitly (*"maximum sustained winds of greater than or equal to 111 mph"* for cat 3).
`KXHURCAT-26FAUSTO`: 2 adjacent pairs, **0 with both sides executable** (the cat-4/cat-5 legs have
no bid). Relation present, no live test.

### Summary of the live scan

| constraint class | relations checked | executable pairs | raw violations | net-positive after fees |
|---|---:|---:|---:|---:|
| tiled partition Σ = 1 | 85 events | 79 ask / 22 bid | 3 | **0** |
| mutex Σ ≤ 1 | 109 events | 109 with ≥1 sellable leg | 8 with Σ bid > 1 | **0** |
| nested ladders (threshold + deadline) | 136 ladders / 4,395 pairs | 3,716 | 2 | **1** (+0.52¢, 0.72 contracts) |
| cross-listing identity (Starship) | 10 strikes | 8 | 5 | **5** (+0.52 … +6.71¢, ≈ $0.72 total) |
| cross-event/-series subset (S5–S10) | 68 pairs | 53 | 0 | 0 |

---

## Traps

1. **`taxonomy.classify_event()` mis-reads every degree-symbol leg.** `parse_bucket` and
   `parse_threshold` fail on `'84° to 85°'`, `'83° or below'`, `'1.5°C to 1.9°C'`,
   `'Category 3 or above'`, `'Above 1 inches'`. In this slice that misclassifies 85 events
   (80 bucket + 5 threshold) as `entity_menu` and drops `partition_is_tiled` from 85 true to 2.
   Fix in `taxonomy.py`: strip `°`, `°C`/`°F`, unit words (`inches`, `ft`, `mph`, `%`) and a leading
   `Category ` before matching. Until that lands, this document's counts use a local normaliser.
2. **`mutually_exclusive` is the only gate for sum-to-one.** `KXTOPAI-27` has 12 company legs and
   `mutually_exclusive = false`; `KXACQANNOUNCEANNUAL-27JAN01` has 24 active legs and is also
   non-mutex. Conversely `KXGOLDVSSILVER-26DEC31` has 2 legs and *is* mutex. Shape proves nothing.
   In this slice `mutually_exclusive == (collateral_return_type == "MECNET")` holds for all 351
   events, so either field works, but nothing else does.
3. **Mutex ≠ exhaustive.** 24 of the 109 mutex events are non-tiled menus, and most have no residual
   leg. `KXNEWROLEX-27JAN` (`Σ ask = 0.43`), `KXMODELHIGH-27-1550` (`Σ ask = 0.48`) and
   `KXFIRSTHURRICANE-26DEC01ATL` (explicit "all markets resolve to No" clause) look like enormous
   buy-all edges and are not. Only `Σ bid ≤ 1` is safe on a mutex event; `Σ ask ≥ 1` needs a proof
   of exhaustiveness (tiling, or a `None`/`Other` leg whose rule actually covers the residual).
4. **Leg labels are brands; rules resolve on companies.** Every `KXLLM1` leg displays a model name
   (`Ernie`, `Muse Spark`, `Kimi`) and resolves on the vendor (`Baidu`, `Meta`, `Moonshot`).
   `KXMODELHIGH-27-1550-QWEN` displays `Qwen` and reads *"If a model by Alibaba is the first…"*.
   Sibling series do the opposite: `KXTECHRANKLISTAICODE` legs display `Claude` and resolve on
   `Claude` the model brand. Never join AI markets on `yes_sub_title`.
5. **Ticker suffixes are not stable entity keys, even inside one series.** OpenAI is `-OAI` in
   `KXLLM1-26DEC31` and `-OPEN` in `KXLLM1-26AUG03`; Anthropic is `-A` then `-ANTH`; Alibaba is
   `-ALI` then `-ALIB`. Meta's display name is `Muse Spark` / `Muse` / `MUSE` across three events of
   the same series.
6. **Market tickers are not always prefixed by their event ticker.** 17 markets break the rule:
   `KXAISPIKE-27` contains `KXAISPIKE-27B-1520/1530/1540` alongside `KXAISPIKE-27-1550/…/-1750`;
   `KXRKLBCOUNT-27JAN01` contains `KXRKLBCOUNT-27JAN-5…-13`; `KXALIENS-27` contains
   `KXALIENS-26AUG/26OCT/26NOV/26DEC`. Resolve legs through `event.markets[]`, never by string prefix.
7. **Numeric ticker suffixes can collide with different meanings.** In `KXSTARSHIPSPACE-26`,
   `-2` is `'1 or below'` (a `less` strike at 2) while `-2.0` is `'2'` (a `between`/equality leg),
   and `-9` is `'10 or above'` while `-9.0` is `'9'`. The trailing `.0` is load-bearing.
8. **Two naming generations for the same weather product.** `KXHIGH<CITY>` (7 cities) and
   `KXHIGHT<CITY>` (13 cities) are the same contract; `KXLOWT<CITY>` covers all 20 but uses
   `NYC` where the high ladder uses `NY`. A prefix match on `KXHIGHT` loses NY, CHI, AUS, MIA, DEN,
   PHIL, LAX.
9. **Deadline-ladder tops rarely reach the referenced event's horizon.** `KXGROK-GROK46` ends at
   `Before Aug 10, 2026` while `KXARENASCORE-GROK46` runs *"Before Sep 30, 2026"*; `KXGEMINI-GEMI35P`
   ends at `Before Aug 31, 2026` while `KXARENASCORE-GEMI35P` runs *"Before Jan 1, 2027"*. "Model
   scores above X" implies "model was released", but the release ladder cannot close the implication.
10. **Finalized legs sit inside open events.** 32 events mix `active` with `finalized`/`determined`/
    `inactive` legs (116 non-active legs in total): `KXGEMINI-GEMI35P` is 5 finalized + 1 determined
    + 4 active; `KXRTX5090MAX-26DEC31` is 9 finalized + 6 active; `KXTOPAI-27` carries an `inactive`
    `Zhipu AI` leg. Baskets must be rebuilt from `status == 'active'` on every pass, and 46.1 % of
    active markets carry *"This market will close and expire early if the event occurs"*.
11. **`liquidity_dollars` is identically 0.0000** on all 2,144 active markets here, and
    `notional_value_dollars` is identically 1.0000. Size fields are decimal strings and **fractional**
    (920 markets quote non-integer sizes such as `0.18`, `0.72`, `1.41`); casting to `int` destroys
    capacity estimates. `yes_bid == 1 − no_ask` and `yes_ask == 1 − no_bid` hold exactly for all
    2,144 markets, so the YES book is sufficient.
12. **`series.category` and `event.category` disagree for 21.6 % of series**, and one event
    (`KXGOLDVSSILVER-26DEC31`) has `category: null` outright. Cross-category relations are common
    here (`KXOAIAGI` in Science ⊂ `KXAGICO` in Companies), so a category-scoped scanner misses them.
13. **`settlement_sources` needs URL normalisation** — Reuters, CNN, MSNBC, Politico, Fox News,
    Axios, Semafor, NYT, WaPo, AP and CBS each appear twice, differing only by a trailing slash.
14. **`frequency` is not trustworthy** inside a family: `KXA100MON` and `KXRTX5090MON` are tagged
    `one_off` while their siblings are `monthly`; `KXH100MAX` is `annual` and `KXRTX5090MON` is
    `one_off` despite identical construction.
15. **Unit bugs in rule text.** `KXSUBWAY-27-4.19` reads *"If NYC subway ridership reaches a
    seven-day average of at least 4.19 riders before Jan 1, 2027"* while the leg subtitle says
    `'4.19 million'`. Read the subtitle *and* the rule; where they conflict, neither is safe to
    machine-parse.
16. **`can_close_early` is `true` for 2,252 of 2,260 markets.** The 8 exceptions are the Lake Mead
    ladder. Any "hold to expiry" assumption must be checked per leg.

---

## Open questions

1. **Is `KXSTARSHIPSPACE-26` / `-26B` a deliberate dual listing or a duplication?** The two events
   have different `collateral_return_type` (MECNET vs DIRECNET) and very different open interest
   (20,269 vs 2,706 contracts on active legs), and the exchange does not net them. Nothing in the metadata says
   whether Kalshi treats them as one product. The same question applies to `KXSPACEXCOUNT-26B`
   (annual) vs `-26AUG` (monthly), which have no shared strikes.
2. **What does `Other` resolve against in `KXMODELHIGH-27-1550`?** The rule text is the unfilled
   template *"If a model by Other is the first to hit 1550…"*. Without the contract-terms PDF
   (`contract_terms_url` is present for all 268 series but not fetched here) the exhaustiveness of
   the menu cannot be established, which blocks the S11 identity from being exact.
3. **Do the `MAX` compute ladders resolve on a running maximum or on a terminal reading?**
   The rule says *"is above $3.23 **by** Dec 31, 2026"* and the early-close condition plus the
   finalized low strikes strongly imply running-maximum semantics, but the word "maximum" never
   appears in `rules_primary` or `rules_secondary`.
4. **Which NWS station backs the seven ladders whose `settlement_sources.name` is the bare string
   `"NWS Climatological Report"`?** (`KXHIGHDEN`, `KXHIGHLAX`, `KXHIGHNY`, `KXHIGHPHIL`,
   `KXLOWTDEN`, `KXLOWTLAX`, `KXLOWTPHIL`.) The station is recoverable from `rules_secondary` for
   the ones that carry it, but a metadata-only join is impossible. Related: does
   `KXHIGHCHI`/`KXLOWTCHI` (Chicago **Midway**) share a station with the `KXTEMPCHIH` hourly ladder
   (The Weather Company, coordinates code not shown in the truncated rule)?
5. **Are the daily `KXRAIN` city legs and the monthly `KXRAIN<CITY>M` ladders on the same gauge?**
   `KXRAIN` rules name `CLINYC` but the settlement source is The Weather Company and
   rules_secondary points at `weather.com/kalshi`, while `KXRAINNYCM` names *"Central Park, New
   York City"* with the NWS Climatological Report. If they are the same gauge, a monthly-total
   constraint against the sum of daily legs would exist — but the monthly ladder's lowest strike is
   `Above 1 inch` while the daily legs are `> 0 inches`, so no strike pair is comparable today.
6. **Does `KXTOPAI-27`'s "#1 ranked AI model" use the same LM Arena tab as `KXLLM1`?** The source
   strings match up to a leading space, but the rule text names no leaderboard. If `KXTOPAI` were
   scored on a different Arena tab, S9 would not be a settlement constraint.
7. **Why do `KXTOPAI-27` and `KXCODINGMODEL-26DEC` omit Google and Anthropic** when both are
   `KXLLM1` legs and both currently hold top ranks? This may be a deliberate scoping decision in the
   contract terms or a listing gap; it is not resolvable from the API metadata.
8. **What determines the 25 Climate markets with `settlement_timer_seconds = 0`, the two markets
   with 14 s, and the four with 3,599 s?** No series-level field explains the variation.
