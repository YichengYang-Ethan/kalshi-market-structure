# Financials + Crypto

Snapshot `2026-08-02T20:52Z`. Shards: `by_category/Financials.jsonl.gz`, `by_category/Crypto.jsonl.gz`.

Conventions used throughout:

* Prices are dollars per $1 contract. **Quote presence is keyed off the size fields, never the price
  fields** — see Traps #1. `yes_ask_dollars` is only a real offer when `yes_ask_size_fp > 0`.
* Only `status == 'active'` legs are counted unless stated otherwise.
* Fees: `taker = fee_multiplier * 0.07 * P * (1-P)` per contract per leg, rounded up to a centicent
  ($0.0001); `maker = 0` unless `fee_type == 'quadratic_with_maker_fees'` (coefficient 0.0175);
  no settlement fee. Every arithmetic result below that is labelled "net" has taker fees on both
  legs subtracted.
* The book is one-sided in the data model: `no_bid = 1 - yes_ask` and `no_ask = 1 - yes_bid` hold
  exactly on all 10,722 active legs (0 exceptions). Selling YES *is* buying NO; there is no second book.

---

## Inventory — events, markets, series count; how much of the exchange this is

|                                   | Financials | Crypto | Slice      | Exchange | Slice share |
| --------------------------------- | ---------: | -----: | ---------: | -------: | ----------: |
| Events                            |        443 |    108 |    **551** |    8,478 |        6.5% |
| Markets (all statuses)            |      8,152 |  2,646 | **10,798** |   73,964 |       14.6% |
| Markets, `status == 'active'`     |      8,093 |  2,629 | **10,722** |        — |           — |
| Distinct series with live events  |        259 |     78 |    **337** |        — |           — |
| Series carrying this `series.category` | 715 |    271 |        986 |   12,370 |        8.0% |

Mean legs per event is **19.6** here versus **8.7** exchange-wide. This is the ladder heartland: a single
series, `KXNASDAQ100U`, carries 2,800 active markets (26% of the slice) across 7 hourly events —
400 strikes per event on a 10-point grid.

**Status mix.** 10,722 active, 73 finalized, 2 inactive, 1 closed. The 76 non-active legs sit inside
**32 still-open events**, and 52 of them settled **YES**. Worst cases: `KXIBOV-26DEC31` 4 active of 14,
`KXKOSPI-26DEC31` 2 of 11, `KXNASDAQ100MAXY-26DEC31H1600` 7 of 11 (four strikes already touched).
Finalized legs carry `yes_bid = 0.0000 / yes_ask = 1.0000` — the same encoding as "no quote".

**Structural key.** `collateral_return_type` partitions the slice cleanly and is far more reliable
than any subtitle heuristic:

| `collateral_return_type` | events | `mutually_exclusive` | leg `strike_type`s | meaning |
|---|---:|---|---|---|
| `DIRECNET` | 367 | always `false` | `greater` (4,647), `greater_or_equal` (3,729) | nested one-sided ladder |
| `MECNET`   |  69 | always `true`  | `between` (1,235), `custom` (217), `greater` (35), `less` (34) | mutually exclusive partition |
| `''`       | 115 | always `false` | `custom` (429), `greater` (184), `less` (121), … | everything else |

`MECNET ⟺ mutually_exclusive == true` with zero exceptions in this slice. `DIRECNET` never contains a
`less` or `between` leg, so a DIRECNET event is always a monotone "≥ X" ladder.

**Category reliability.** Only 6 events have `event.category != series.category`
(`KXWTIMAX`, `KXWTIMIN`, `KXVERARELEASE` → Commodities; `KXUSFUNDHEAD`, `KXUSOPENAIANTH` → Politics;
`KXCOMPANYACTIONANTH` → Science and Technology), but the *content* incoherence is much larger: the
Financials shard also carries 13 FDA drug-approval binaries (`KXVENGLUSTAT`, `KXIVONESCIMAB`,
`KXBBP418`, …), 12 consumer price-increase / product-launch markets (`KXPRICEINCREASECLAUDE`,
`KXNEWXBOX`, `KXIPHONERELEASE`, …) and 2 crude-oil ladders. Of the 986 series labelled
Financials/Crypto in `series.json`, only 331 have a live event here; the slice's other 6 live series
carry a different `series.category`. **The series ticker grammar is the usable grouping key.**

**Frequency mix (events):** `one_off` 312, `monthly` 68, `hourly` 56, `annual` 43, `weekly` 30,
`daily` 17, `custom` 16, `fifteen_min` 9. `frequency` is a scheduling label, not a horizon label —
`KXH200MS` is a *monthly* average priced series filed as `one_off`, and `KXDJI` is hourly but filed
as `one_off`.

**Expiry horizon (active legs, days from snapshot to `close_time`):** min 0.006 d, p10 0.71, median
4.94, p90 271, max 4,899 (`KXNEWROLEJP-35DEC`, Dec 2035). Bucketed: <1 d 4,594 legs (43%), 1–7 d 1,662,
7–31 d 665, 1–6 mo 1,858, 6–12 mo 1,500, >1 y 443.

---

## Series families

`mkts` = active markets. `2-sided` = both sides quoted with non-zero size. `tight&deep` = spread ≤ $0.02
**and** ≥ 100 contracts on both sides — the fraction that is genuinely tradeable in size.

| Family | series | ev | mkts | lifetime vol (contracts) | OI | 2-sided | med spread | tight&deep |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| US index intraday directional | 3 | 21 | 3,670 | 87,313 | 57,671 | 41% | $0.280 | 0.2% |
| hardware / memory spot price (Ornn) | 15 | 134 | 2,015 | 1,260,906 | 517,421 | 89% | $0.060 | 15.1% |
| company KPI ladder | 124 | 165 | 1,444 | 2,086,236 | 841,831 | 95% | $0.050 | 9.8% |
| crypto intraday directional | 8 | 23 | 1,084 | 2,976,862 | 1,324,455 | 10% | $0.030 | 3.0% |
| crypto intraday range partition | 8 | 23 | 1,084 | 259,529 | 192,484 | 8% | $0.050 | 0.4% |
| IPO timing / underwriter | 24 | 26 | 270 | 2,401,006 | 734,188 | 84% | $0.060 | 4.4% |
| US Treasury yield / spread | 13 | 13 | 169 | 92,982 | 54,618 | 82% | $0.070 | 0.0% |
| crypto annual terminal partition | 8 | 8 | 166 | 41,742,269 | 7,302,740 | 49% | $0.010 | 6.6% |
| crypto running extreme — month | 16 | 16 | 123 | 409,721 | 342,523 | 73% | $0.020 | 13.8% |
| US index daily range partition | 2 | 4 | 120 | 13,848 | 12,143 | 58% | $0.020 | 44.2% |
| crypto running extreme — year | 16 | 16 | 106 | 10,966,492 | 3,537,661 | 89% | $0.050 | 17.0% |
| US index annual terminal | 6 | 6 | 93 | 9,844,920 | 7,118,128 | 90% | $0.020 | 36.6% |
| index membership | 5 | 5 | 82 | 59,829 | 28,343 | 54% | $0.050 | 1.2% |
| M&A / corporate action | 17 | 17 | 50 | 3,269,186 | 1,246,123 | 84% | $0.050 | 10.0% |
| crypto milestone / first-cross | 13 | 13 | 49 | 12,891,968 | 4,862,425 | 96% | $0.040 | 22.4% |
| FX | 3 | 3 | 38 | 564,302 | 21,561 | 100% | $0.020 | 5.3% |
| US index annual running extreme | 5 | 5 | 31 | 1,570,486 | 749,848 | 100% | $0.060 | 0.0% |
| foreign index | 6 | 6 | 29 | 17,017 | 6,552 | 93% | $0.060 | 0% |
| commodity (mislabelled: WTI) | 2 | 2 | 22 | 6,695,549 | 2,585,160 | 100% | $0.012 | 13.6% |
| consumer price increase / product | 12 | 12 | 19 | 273,689 | 87,967 | 100% | $0.060 | 0% |
| sentiment index (`KXFEAR`) | 1 | 3 | 15 | 13,556 | 7,358 | 67% | $0.055 | 0% |
| biotech approval binary | 13 | 13 | 13 | 10,277 | 5,834 | 100% | $0.050 | 0% |
| relative performance duel | 5 | 5 | 10 | 66,975 | 30,577 | 100% | $0.080 | 10.0% |
| crypto annual directional (`KXSOLD26`) | 1 | 1 | 9 | 162,815 | 56,052 | 100% | $0.070 | 0% |
| crypto 15-minute target | 9 | 9 | 9 | 872,201 | 313,565 | 100% | $0.040 | 0.0% |
| US index daily up/down | 2 | 2 | 2 | 5,201 | 2,772 | 100% | $0.010 | 50.0% |

### Ticker grammar, family by family

The grammar is what makes relation extraction programmatic. Two universal rules first:

* **Event ticker** = `<SERIES>-<PERIOD>`, and `<PERIOD>` is one of `YYMMM` (month),
  `YYMMMDD` (day), `YYMMMDDHH` (day + close hour ET, no separator), `YYMMMDDHHHHMM`
  (`26AUG03H1600` = Aug 3 2026, `H1600` = close hour), or `YY` (year).
  A few families interpose the asset: `KXBTCMAXMON-BTC-26AUG31`.
* **Market ticker** = `<EVENT>-<STRIKE>`. `T` prefixes a *threshold* strike, `B` a *bucket*
  midpoint label, `N` a negative value (`KXCTCQ-26AUGCOMP-N2.5` = "Above −2.5%"). **`T` is not
  directional**: inside a MECNET partition the bottom `less` leg and the top `greater` leg are both
  `T`-prefixed (`KXBTC-26AUG0717-T51500` = "$51,499.99 or below", `…-T75499.99` = "$75,500 or above").
  Use `strike_type`, never the prefix.

**Crypto intraday pair — `KX<COIN>` (range) + `KX<COIN>D` (directional).**
`KXBTC`/`KXBTCD`, `KXETH`/`KXETHD`, `KXXRP`/`KXXRPD`, `KXHYPE`/`KXHYPED`, `KXBNB`/`KXBNBD`,
`KXDOGE`/`KXDOGED`, `KXSHIBA`/`KXSHIBAD`, and the irregular `KXSOLE`/`KXSOLD`. The two series share the
**identical event suffix, identical `open_time`, `close_time`, `expiration_time` and identical
`rules_primary` reference**. Event key `26AUG0717` = Aug 7 2026, 5 pm ET. Fee mult 1, `quadratic`.
The `D` series is `DIRECNET` (`greater`, `-T<floor>` with floor one tick below the displayed level:
`T51999.99` ↔ "$52,000 or above"); the base series is `MECNET` (`-T<cap>` bottom, `-B<midpoint>`
interior, `-T<floor>` top).

**Crypto 15-minute — `KX<COIN>15M`.** Event `KXBTC15M-26AUG021700`, single leg `-00`. Grammar is
`YYMMMDD` + `HHMM` close. Not a fixed strike: the leg settles YES if the 60-second BRTI mean before
5:00 pm is **at least the 60-second BRTI mean before 4:45 pm**; the `yes_sub_title`
"Target Price: $63,362.99" is the 4:45 reference frozen at snapshot time.

**Crypto annual terminal — `KX<COIN>Y`.** `KXBTCY`, `KXETHY`, `KXXRPY`, `KXBNBY`, `KXDOGEY`,
`KXHYPEY`, `KXNEARY`, `KXZECY`. Event `-27JAN0100`. MECNET, `MECNET` collateral.
Two strike encodings coexist: `KXBTCY`/`KXETHY`/`KXNASDAQ100Y` use plain decimals
(`T20000.00`, `B22500`), while `KXXRPY`/`KXDOGEY`/`KXHYPEY`/`KXNEARY`/`KXZECY` use a **fixed-point
×10⁴ integer**, zero-padded (`KXXRPY-27JAN0100-T05000` = $0.5000; `KXHYPEY-…-B950000` = $95.0000).
`KXBTCY` and `KXETHY` are the exchange's only **`fee_multiplier == 0`** series in this slice.

**Crypto running extremes — `KX<COIN>MAXMON` / `MINMON` / `MAXY` / `MINY`.**
Event `KXBTCMAXMON-BTC-26AUG31`, leg `-26AUG31-6500000` (again ×10⁵ fixed point for BTC:
6500000 = $65,000.00). Not DIRECNET (collateral `''`) despite being nested ladders.

**Crypto milestone / first-cross.** Ad hoc tickers: `KXBTCMAX100-26` (leg suffix = month word `AUG`…`DEC`),
`KXBTCMAX150-25`, `KXDOGEMAX1`, `KXBTC2026200` / `KXBTC2026250` (threshold baked into the series name),
`KXBTCHALF`, `KXSATOSHIBTCYEAR`, `KXBTC50VS100`, `KXCRYPTORETURNY` (entity menu, leg = coin symbol),
`KXTOKENLAUNCH`, `KXFDVOPENSEA`.

**US index intraday directional — `KXNASDAQ100U`, `KXINXU`, `KXDJI`.**
`U` = "underlying, hourly". `KXINXU-26AUG03H1600`, leg `-T7224.9999` ("7,225 or above",
`greater_or_equal`). `KXNASDAQ100U` same grammar, 400 legs at a 10-point step (26,100 → 30,090).
`KXDJI` drops the `H`: `KXDJI-26AUG0316` and legs with a bare decimal `-52425.00`.
Seven hourly events per trading day, `H1000`…`H1600`.

**US index daily range partition — `KXNASDAQ100`, `KXINX`.** `KXINX-26AUG07H1600`, MECNET, 30 legs,
25-point buckets for INX / 100-point for NDX. The `H1600` event of the `U` series and the `H1600`
event of the base series are the **same instant** (identical `close_time` 20:00 Z).

**US index annual terminal — six series on one instant.** `KXNASDAQ100Y-26DEC31H1600` (MECNET,
30 buckets), `KXNDQDIRY-26DEC31H1600` (DIRECNET, 17 thresholds), `KXNASDAQ100POS-26DEC31H1600`
(single leg at the 2025 close, `T25249.85`); and the S&P mirror `KXINXY` / `KXINXDIRY` / `KXINXPOS`.
All four NDX series carry `close_time = 2026-12-31T21:00:00Z` and the same rule phrase.
`KXNASDAQ100Y` and `KXINXY` are `quadratic_with_maker_fees`.

**US index annual running extreme — `KX<INDEX>MAXY` / `MINY`, `KXDJIA`.**
`KXINXMAXY-01JAN2027` (note the inverted `DDMMMYYYY` period — unique in the slice),
`KXNASDAQ100MAXY-26DEC31H1600`, `KXDJIA-26DEC31`.

**US Treasury — `KXUST<N>A` and `KXUST<N>AD`.** `KXUST10A-26AUG07` and `KXUST10AD-26AUG03` have
identical 15-leg strike grids (`T4.55` → "4.56% or above") but different dates: the `A` series is
`frequency = daily`, the `AD` variant is `one_off`. Plus `KX10Y2Y` (touch-any-daily-observation,
strikes `T.7`…`T1.00` in percent), `KX10Y2YDATE` (terminal, strikes `T-30`…`T70` in **bps**),
`KXNOTE10Y` (year-end level).

**Hardware / memory spot — the Ornn family.** `KX<PRODUCT><M|W>S`:
`KXDDR5MS` / `KXDDR5WS` / `KXDDR5EMS` / `KXDDR5EWS` (the `E` = eTT grade),
`KXH100`, `KXH200`, `KXB200`, `KXA100`, `KXRTX5090` × `{MS, WS}`, plus `KXDRAMAY`.
`MS` events key on `YYMMM` and settle on a **monthly arithmetic mean**; `WS` events key on `YYMMMDD`
(a Friday) and settle on a **single 4 pm ET reading**. 15 series, 134 events, 2,015 markets — the
second-largest family here and the best-quoted (15.1% tight&deep).

**Company KPI ladder — `KX<TICKER>` and `KX<TICKER>A`.** The bare ticker is the *quarterly* KPI
(`KXMCD-26NOVREST` = Q3 2026 restaurants), the `A` suffix is the *fiscal-year* KPI
(`KXMCDA-27JANREST` = fiscal 2026). Leg suffix is the raw number (`-46300`) or a signed percent
(`-N2.5`). 124 series, all `Fiscal.ai`-settled, all DIRECNET. `FT` suffix = foot traffic
(`KXWMTFT`, `KXSBUXFT`, `KXDPZFT`).

**IPO / underwriter.** Three shapes under one theme: deadline ladders (`KXDATABRICKS-DATE`, legs
`-26SEP01` … `-28JAN01`), entity menus (`KXIPO-26`, legs `-BEAS`, `-KRAKEN`, …), and MECNET menus
(`KXOPENAIBANKPUBLIC-28JAN01`, `KXOPENAISECTOR-XX`, `KXOPENAILEADLEFT-28JAN01B`). `KXIPO` is
`quadratic_with_maker_fees`.

**Index membership.** `KXSP500ADDQ-26SEP30`, `KXSP500REMOVEQ`, `KXNDXADDQ`, `KXNDXREMOVEQ`,
`KXDJIAREMOVE-27JAN01`; legs are equity symbols (`-SPCX`, `-AFRM`).

**Relative performance duels — `KX<A>VS<B>`.** `KXINXVSBTC`, `KXINXVSGOLD`, `KXINXVSINXEW`,
`KXDXYVSGOLD`, `KXWTIVSBRENT`. Exactly 2 legs, MECNET, legs named after the assets.

### Fee status

| | series |
|---|---|
| `quadratic`, `fee_multiplier = 1` (the default) | 331 of 337 live series |
| `quadratic`, `fee_multiplier = 0` (**free both sides**) | `KXBTCY`, `KXETHY` |
| `quadratic_with_maker_fees` (maker 0.0175 coefficient) | `KXBTCMAX150`, `KXINXY`, `KXIPO`, `KXNASDAQ100Y` |

**Tick size is not uniform.** 74 legs quote at tenth-of-a-cent granularity — `KXBTCY` (28),
`KXETHY` (18), `KXWTIMAX` (10), `KXINXMAXY` (7), `KXINXMINY` (5), `KXBTCHALF` (2),
`KXNASDAQ100POS` (1), `KXNEAR15M` (1). Everything else is on a $0.01 grid. The two zero-fee series
have both zero fee **and** the fine tick, which is why they carry the tightest partition on the
exchange (below).

---

## Contract templates

Five templates cover 100% of the slice. Each one below is anchored by a verbatim `rules_primary`
excerpt from a live leg.

**1. Threshold ladder (DIRECNET, 367 events, 8,376 legs).** One leg per level, all `greater` or
`greater_or_equal`, prices monotonically non-increasing in the level. Legs are *not* mutually
exclusive; each is an independent binary.

> `KXINXU-26AUG03H1600-T7224.9999` — "If the S&P 500 index value on Aug 3, 2026 at 4pm EDT is above
> 7224.9999, then the market resolves to Yes."

**2. Bucket partition (MECNET, 69 events, 1,552 legs).** Bottom leg `less`, interior legs `between`,
top leg `greater`; exactly one settles YES.

> `KXBTC-26AUG0317-T53250` — "If the simple average of the sixty seconds of CF Benchmarks' Bitcoin
> Real-Time Index (BRTI) before 5 PM EDT is below 53250 at 5 PM EDT on Aug 3, 2026, then the market
> resolves to Yes."

**3. Deadline ladder (cumulative, collateral `''`).** "Before `<date>`" legs, nested in time, not
mutually exclusive.

> `KXDATABRICKS-DATE-26SEP01` — "If Databricks confirms an IPO before Sep 1, 2026, then the market
> resolves to Yes." Secondary: "An IPO is confirmed if 1) the SEC declares the company's Form S-1
> effective OR 2) the IPO is priced OR 3) a securities exchange has assigned a ticker to it."

**4. Entity menu.** One leg per named candidate. Sometimes MECNET (at most one wins), sometimes not.

> `KXIPO-26-BEAS` — "If Beast Industries confirms an IPO before Jan 1, 2027, then the market resolves
> to Yes." (`mutually_exclusive = false`: several companies can IPO in the same year.)
>
> `KXOPENAISECTOR-XX-…` — "If OpenAI is assigned to the Communication Services sector, then the
> market resolves to Yes." (`MECNET`, 12 legs = 11 GICS sectors + `Unassigned`, so **exhaustive**.)

**5. Running-extreme / touch ladder (collateral `''`).** "Ever above / ever below X during a window".
Nested in the level, but the window anchor lives only in the prose.

> `KXBTCMAXMON-BTC-26AUG31-6500000` — "If the price of BTC after issuance and through 11:59 PM ET on
> Aug 31, 2026 is ever above $ 65000.00, then the market resolves to Yes."
>
> Secondary (this is the clause that matters): "At each minute throughout the market duration, a
> settlement value is calculated using every minute-by-minute CF BNBUSD_RTI price… the top 20% and
> bottom 20% of the **cumulative dataset** are removed before calculating the average… **The
> measurement period runs from when the market is issued** until the specified end time."

Two sub-templates worth separating because they look like #1 but are not:

* **Period-average ladder** (Ornn `MS` series): the underlying is a mean, not a level.
  > `KXH200MS-27AUG-1.000` — "If the average value of NVIDIA H200 compute per hour is above $1 in
  > August 2027, then the market resolves to Yes." Secondary: "…calculated as the arithmetic mean of
  > hourly values reported by Ornn."
* **Relative-return duel**: two legs, threshold is a comparison, ties resolve both No.
  > `KXINXVSGOLD-26DEC31-INXTR` — "If S&P 500 Total Return Index performs above Gold for the period
  > of 2026 by 0.001% then the market resolves to Yes." Secondary: "Percent return is calculated from
  > the official open price of each asset on January 2, 2026… and the official closing price on
  > December 31, 2026."

---

## Settlement

**Sources** (events citing each; an event may cite several):
`Fiscal.ai` 166 (company KPIs), `Ornn` 133 (compute/memory spot), `CF Benchmarks` 106 (all crypto),
`The Wall Street Journal` 29, `Reuters` 29, `"For example, Google Finance"` 28 (US indices),
`ABC` 27, `CNBC` 26, `Financial Times` 22, `Bloomberg` 19, `New York Times` 17, `BBC` 17,
`AppliedXL` 13, `U.S. Department of the Treasury` 11 (UST yields), `S&P Global` 10 (index membership),
`SEC` 10, `ICE` (FX), `Trading View` (foreign indices), `TrendForce` (`KXDRAMAY`).

Note the index sources are *examples*, not authorities: the settlement_sources entry is literally
named `"For example, Google Finance"`. Every US index series in this slice cites the same URL, which
is why the intraday, daily and annual index series can be treated as one reference value.

Crypto is uniformly CF Benchmarks real-time indices — `BRTI` (BTC), `ETHUSD_RTI`, `SOLUSD_RTI`,
`BNBUSD_RTI` — and the standard terminal formulation is "**the simple average of the sixty seconds
of … before <T>**". This 60-second averaging window is load-bearing for the horizon-nesting analysis
below.

**Early close.** `can_close_early = true` on all 10,722 active legs, but `early_close_condition` is
populated on only 2,205 (20.6%):

| legs | condition |
|---:|---|
| 8,517 | (none) |
| 1,677 | "This market will close and expire early if the event occurs." |
| 198 | "This market will close and expire early if the price criterion is met." |
| 82 | "…if the index administrator announces…" |
| 42 | "…if the IPO underwriting is announced…" |
| 37 | "…if the economic data is released…" |
| 29 | "…if the company makes the specified…" |
| 25 | "If this event occurs, the market will close the following 10am ET." |

The 198 price-criterion legs are the running-extreme families: once the level is touched the market
resolves immediately, which is why `KXNASDAQ100MAXY-26DEC31H1600` already carries four finalized-YES
legs inside an open event.

**Settlement timer** (`settlement_timer_seconds`): 60 s on 5,273 legs, 1,800 s on 5,197, 3,600 s on
215 (`KXUST*`, `KX10Y2Y`, `KXNOTE10Y`, BTC annual/milestone series, `KXWTIMAX/MIN`),
300 s on 28 (`KXIPO`), and **1 s** on the 9 `KX*15M` legs.

**Expiration vs close.** `expiration_time` typically sits one week after `close_time` (crypto
hourly: close `2026-08-03T21:00Z`, expiration `2026-08-10T21:00Z`), while
`expected_expiration_time` is minutes after close. The gap is the data-availability grace period,
e.g. `KXUST10A`: "The market will expire at the sooner of the first 7:00 PM ET following the data
release for Aug 7, 2026, or one week following Aug 7, 2026."

---

## Liquidity

**Quote presence.** `yes_ask_size_fp == 0` ⟺ no offer (2,041 legs) and `yes_bid_size_fp == 0` ⟺ no bid
(2,774 legs), with zero exceptions. When there is no offer the price field is `1.0000` on 1,985 legs
but `0.0000` on **56** legs; when there is no bid it is always `0.0000`.

| | Financials | Crypto | Slice |
|---|---:|---:|---:|
| active legs | 8,093 | 2,629 | 10,722 |
| two-sided | 5,458 (67.4%) | 523 (19.9%) | 5,981 (55.8%) |
| bid only (no offer) | 1,452 | 515 | 1,967 |
| ask only (no bid) | 1,183 | 1,517 | 2,700 |
| neither side | 0 | 74 | 74 |
| spread p10/p25/p50/p75/p90 | .010/.030/.070/.320/.940 | .010/.010/.040/.060/.130 | .010/.020/.060/.300/.940 |
| min(bid,ask) depth p25/p50/p90 (contracts) | 3 / 5 / 177 | 5 / 40 / 1,000 | 4 / 5 / 201 |
| **tight&deep** (≤$0.02 and ≥100 both sides) | 518 (6.4%) | 77 (2.9%) | **595 (5.5%)** |

Crypto looks worse on two-sidedness and better on everything else: the crypto books that exist are
tight and deep, but 58% of crypto legs have no bid at all because the intraday ladders are quoted
one-sided far from the money.

**Depth is fractional.** `*_size_fp` is a fixed-point contract count and takes sub-1 values:
0.4% of non-zero ask sizes and 0.6% of non-zero bid sizes are below one contract
(`KXBTC-26AUG0717` has legs quoted 0.02 ask on **0.01 contracts**). 15.2% of two-sided legs have
≤ 1 contract on the thin side. Any scanner that treats a quote as executable without reading the
size will manufacture phantom edges.

**Open interest and volume.** Total OI 32.0 M contracts; **59.7% of legs have zero OI** and 59.2%
have zero lifetime volume. Lifetime volume 98.6 M contracts, extremely concentrated:

| series | lifetime volume | share |
|---|---:|---:|
| `KXBTCY` | 29,830,983 | 30.2% |
| `KXETHY` | 11,909,105 | 12.1% |
| `KXWTIMAX` | 6,566,676 | 6.7% |
| `KXBTC2026200` | 6,519,516 | 6.6% |
| `KXINXY` | 5,247,729 | 5.3% |
| `KXBTCMAXY` | 4,178,268 | 4.2% |
| `KXNASDAQ100Y` | 3,558,617 | 3.6% |
| `KXBTCMINY` | 3,419,017 | 3.5% |
| `KXBTCD` | 2,666,495 | 2.7% |
| `KXACQANNOUNCEEBAY` | 2,490,829 | 2.5% |
| **top 10** | | **77.5%** |

24-hour volume tells the opposite story — 4.49 M contracts, of which `KXBTCD` 2.34 M (52%),
`KXBTC15M` 684 k, `KXBTCMAXMON` 201 k, `KXETHD` 177 k, `KXBTCY` 140 k. Lifetime volume ranks the
zero-fee annual markets first; current flow is overwhelmingly the intraday BTC ladder.

**The 400-leg ladder.** `KXNASDAQ100U-26AUG03H1600` has 400 active legs; only **128** are two-sided,
167 are bid-only, 105 ask-only, and only 116 have ever traded. Its family median spread is $0.28.
Leg count is not liquidity.

`liquidity_dollars` is `0.0000` on all 10,722 legs in this snapshot — the field is not populated
here and must not be used as a filter.

---

## Structural constraints

Nine relations hold as settlement logic in this slice, plus one that superficially looks like a
constraint and is **rejected** on the rule text. Every live check below uses executable sides
(the specific leg's `yes_bid` against the general leg's `yes_ask`) and per-series fees.

### S1 — MECNET tiled partition sums to one

**Rule basis.** `mutually_exclusive = true` (⟺ `collateral_return_type = MECNET`) plus a structurally
verified tiling. Verified independently of `taxonomy.partition_is_tiled`: intervals taken from
`custom_strike.floor_strike`/`cap_strike` where present and from the `between` subtitle otherwise,
then checked for a `(-inf, …]` left tail, an `[…, inf)` right tail, no overlap and no gap wider than
one tick. **Result: 39 of 39 numeric MECNET partitions tile — 8 Financials, 31 Crypto, 1,457 legs.**
This reproduces the brief's 31/31 and 8/8 exactly. The remaining 30 MECNET events are non-numeric
(13 single-leg biotech binaries, 5 two-way duels, 3 `KXFEAR` ordinal partitions, 9 entity menus) and
are handled in S2/S3.

**Inequalities.** For a tiled partition with legs *i*:

* Buy-all-YES: `Σᵢ yes_askᵢ + Σᵢ fee(yes_askᵢ) ≥ 1`, otherwise a riskless $1 payoff is bought below par.
  Requires an offer on **every** leg.
* Sell-all-YES (= buy all NO): `Σᵢ yes_bidᵢ − Σᵢ fee(1 − yes_bidᵢ) ≤ 1`. This one is
  **subset-valid**: for any subset S of a mutually exclusive event at most one leg wins, so selling
  YES on |S| legs costs `|S| − Σ_S bid` and pays at least `|S| − 1`. Missing quotes on the other legs
  do not matter — the binding statistic is the sum of *all available* bids.

**Live check.** Buy side: 30 of 39 partitions are fully offered. Cost distribution
min 1.0759, p25 1.3454, median 1.5942, p75 10.9112, max 34.8329. **No violation** — the cheapest is
`KXEURUSD-26AUG0310` at 1.0759 and the second cheapest is `KXBTCY-27JAN0100` at **1.0880**.
Sell side: two partitions carry a raw `Σ bid > 1`, and both die on fees.

| partition | fee mult | legs | legs bid | Σ bid | fee | worst-case P&L per basket | thin-side depth |
|---|---:|---:|---:|---:|---:|---:|---:|
| `KXUSDJPY-26AUG0310` | 1 | 15 | 15 | **1.0300** | 0.0469 | **−0.0169** | 5.0 |
| `KXXRPY-27JAN0100` | 1 | 24 | 9 | **1.0300** | 0.0505 | **−0.0205** | 0.2 |
| `KXBTCY-27JAN0100` | **0** | 28 | 28 | 0.9960 | 0.0000 | **−0.0040** | 2.4 |
| `KXETHY-27JAN0100` | **0** | 18 | 18 | 0.9480 | 0.0000 | −0.0520 | 0.2 |

**`KXBTCY` is the tightest structural constraint found in this snapshot.** It is zero-fee, quotes on a
tenth-cent tick, has an offer and a bid on all 28 legs, per-leg spreads of $0.001–$0.008
(median $0.003), and its sum-of-bids sits **0.4 cents** below the no-arbitrage bound with no fee
cushion whatsoever. Its sum-of-asks is 1.0880, so the whole 28-leg partition trades inside a
9.2-cent band — about 0.33 cents of half-spread per leg. `KXETHY` is the same construction one
notch looser (0.9480 / 1.1140).

**How much of the slice this covers, and how much is testable.** Bid coverage is the binding
limitation: the median tiled partition has bids on only **14%** of its legs (ask coverage median
100%). Nine of 39 partitions cannot be tested on the buy side at all.

**Failure modes.** (a) A gap in the tiling voids buy-all-YES — none here, but the check must be
structural, not "it's mutex so it must tile". (b) A finalized leg inside an open MECNET event would
break both sides; none of the 39 tiled partitions contains a non-active leg (all 32 dead-leg-bearing
events are DIRECNET or `''`), but this must be re-checked every snapshot. (c) `KXOPENAISECTOR`'s
secondary rule allows a **fractional** payout: "If OpenAI is assigned to more than one sector by the
GICS, then 'Yes' holders for any attributed sector will receive $1/number of sectors" — the partition
still sums to 1 in expectation but individual legs are not 0/1.

### S2 — Categorical MECNET partitions that the shared parser cannot see

`KXFEAR` (3 events × 5 legs: Extreme Fear / Fear / Neutral / Greed / Extreme Greed) and
`KXOPENAISECTOR` / `KXANTHROPICSECTOR` (12 legs = 11 GICS sectors + `Unassigned`) are **exhaustive**
partitions with non-numeric leg labels. `taxonomy.partition_is_tiled` returns `False` for all five
because the subtitles carry no parseable number, so a scanner keyed on that function silently drops
them. S1's inequalities apply verbatim.

**Live check.** `KXFEAR-26AUG14`: 5/5 bid, 5/5 ask, Σ bid 0.880, buy-all cost 1.1958 — consistent.
`KXFEAR-26AUG07`: Σ bid 0.880, cost 1.2124 — consistent. `KXFEAR-26AUG21`: only 1 leg bid,
cost 1.0327 — consistent. `KXOPENAISECTOR-XX`: Σ bid 0.910, Σ ask 1.420 — consistent.
`KXANTHROPICSECTOR-XX`: Σ bid 0.870, Σ ask 1.120 — consistent.

**Rule basis.** `KXFEAR`: "If the first value update after 4:00 PM ET on Aug 21, 2026 is Extreme
Fear, then the market resolves to Yes" — the CNN classification has exactly these five values.

### S3 — MECNET menus that are exclusive but *not* exhaustive

`KXNEWROLEJP`, `KXNEWROLEGS` (6 named executives each), `KXOPENAILEADLEFT`, `KXANTHROPICLEADLEFT`
(6 banks), `KXACQUANNOUNCEPINS` (6 acquirers), and the five two-leg duels. Only the **≤ 1** half of
S1 applies: `Σ yes_bid − Σ fee ≤ 1` is valid, `Σ yes_ask ≥ 1` is **not** (nothing forces a winner).

> `KXNEWROLEJP-35DEC` — "If Marianne Lake is appointed, elected, named, designated, or succeeded to
> the position as CEO for JP Morgan Chase before Dec 31, 2035, then the market resolves to Yes."
> Nothing in the rule excludes a seventh person.

Duels tie-break to both-No: `KXINXVSGOLD-26DEC31` — "If S&P 500 Total Return Index performs above
Gold for the period of 2026 **by 0.001%**…", so an exact tie pays neither leg (payoff 2 on the
sell-both basket, which only strengthens the ≤ 1 bound).

**Live check.** `KXINXVSGOLD-26DEC31` is a raw violation: bids 0.82 (INXTR, 37 contracts) + 0.19
(GOLD, 105) = **1.0100**. Fees 0.0212 ⇒ **−0.0112** net. Consistent after fees.
All other menus are well inside: `KXNEWROLEJP` Σ bid 0.890, `KXOPENAILEADLEFT` 0.910,
`KXANTHROPICLEADLEFT` 0.910, `KXDEELRIP` 0.930, `KXINXVSBTC` 0.960, `KXWTIVSBRENT` 0.900,
`KXINXVSINXEW` 0.800, `KXDXYVSGOLD` 0.650, `KXACQUANNOUNCEPINS` 0.170.

### S4 — Monotonicity within a one-sided ladder

**Rule basis.** In a DIRECNET (or `''`-collateral one-sided) event all legs read the same underlying
at the same instant with only the level differing, so `YES(≥ L₂) ⊂ YES(≥ L₁)` for `L₁ < L₂` and
therefore `P(L₁) ≥ P(L₂)`.

**Inequality.** `yes_bid(L₂) − yes_ask(L₁) − fee(yes_ask(L₁)) − fee(1 − yes_bid(L₂)) ≤ 0`.
Buying the low strike and selling the high strike has payoff 1 when `L₁ ≤ X < L₂` and 0 otherwise —
never negative.

**Live check.** Applied to every event whose active legs are *all* upward (`greater`/`greater_or_equal`)
or *all* downward (`less`) — **405 events, 90,611 ordered executable pairs**. Three raw one-cent
inversions, **zero** net-positive:

| event | levels | ask(low) | bid(high) | raw | net of fees | depth |
|---|---|---:|---:|---:|---:|---:|
| `KXH200MS-26OCT` | $6.00 → $6.50 | 0.18 | 0.19 | +0.010 | **−0.0112** | 6 |
| `KXBNBMAXMON-BNB-26AUG31` | $630 → $640 | 0.52 | 0.53 | +0.010 | **−0.0250** | 20 |
| `KXB200MS-26OCT` | $5.50 → $6.00 | 0.49 | 0.50 | +0.010 | **−0.0251** | 184 |

Restricting to DIRECNET only gives 361 testable events / 89,874 pairs and the first and third rows.
The `KXBNBMAXMON` inversion is invisible to a DIRECNET-only scan because the running-extreme families
carry `collateral_return_type = ''` — **a scanner must key on leg `strike_type`, not on the collateral
flag**, or it will miss a quarter of the nested ladders.

**Failure modes.** The check is only valid when all legs share one subject and one instant. In this
slice every one-sided event does, but the guard is cheap: reject any event where two legs parse to
the same level, or where `custom_strike` carries different `Index`/`company` values across legs.

### S5 — Crypto directional ladder = tail sum of the paired range partition

**Rule basis.** `KX<COIN>D` and `KX<COIN>` share the event suffix, `open_time`, `close_time`,
`expiration_time` and the identical settlement clause. Verbatim, same event `26AUG0317`:

> `KXBTCD-…-T52999.99`: "If the simple average of the sixty seconds of CF Benchmarks' Bitcoin
> Real-Time Index (BRTI) before 5 PM EDT is **above 52999.99** at 5 PM EDT on Aug 3, 2026, …"
>
> `KXBTC-…-T53250`: "If the simple average of the sixty seconds of CF Benchmarks' Bitcoin Real-Time
> Index (BRTI) before 5 PM EDT is **below 53250** at 5 PM EDT on Aug 3, 2026, …"

Same statistic, same instant. Therefore, whenever a directional floor `f` coincides with a bucket
boundary, `YES_D(f) = ⋃ { buckets with lo ≥ f }` — an **identity**, not an inequality.

**Inequalities.** With `B(f)` the matching bucket set:

* `Σ_{i∈B(f)} yes_bidᵢ − yes_ask_D(f) − fees ≤ 0` (buy the ladder leg, sell the tail)
* `yes_bid_D(f) − Σ_{i∈B(f)} yes_askᵢ − fees ≤ 0` (buy the tail, sell the ladder leg)

**Live check.** 25 event-pairs across 10 series pairs, **1,116 threshold levels matched**
(8 crypto pairs plus the two index pairs of S6). Direction 1 was testable **0 times** — it needs a
bid on every bucket in the tail, and bucket bid coverage is 14%. Direction 2 was testable **479
times**. Best (least negative) net edges: `KXBTCD/KXBTC 26AUG0717` **−0.0977**,
`KXBNBD/KXBNB 26AUG0217` −0.1968, `KXXRPD/KXXRP 26AUG0217` −0.2334. **No violation.**

The identity is structurally exact and economically loose: the bucket-side ask stack accumulates one
half-spread per bucket, so a 40-bucket tail is ~20 cents wide before anything else happens.

**Failure modes.** (a) Grid misalignment: `KXDOGE`/`KXDOGED` and `KXSHIBA`/`KXSHIBAD` matched
31 and 28 levels but had **zero** testable pairs because the range side is entirely unbid and
partially unoffered. (b) Boundary convention: the `D` floor is one tick below the displayed level
(`T51999.99` ↔ "$52,000 or above") while the bucket `lo` is the level itself. Matching on the
subtitle number works; matching on the ticker number does not.

### S6 — Index hourly ladder = daily range partition at the same instant

`KXINXU-26AUG03H1600` and `KXINX-26AUG03H1600` both have `close_time = 2026-08-03T20:00:00Z`,
`expiration_time = 2026-08-10T23:00:00Z` and the same settlement source URL
(`google.com/finance/quote/.INX:INDEXSP`). Same for `KXNASDAQ100U` / `KXNASDAQ100`.

**Caveat on exactness.** The rule *wording* differs and this is not cosmetic:

> `KXINXU-26AUG03H1600-T7224.9999`: "If **the S&P 500 index value on Aug 3, 2026 at 4pm EDT** is
> above 7224.9999…"
>
> `KXINX-26AUG03H1600-T7075`: "If **the end-of-day S&P 500 index value on August 03, 2026** is
> below 7075…"

"the value at 4pm EDT" and "the end-of-day value" are the same number in normal operation but are not
the same *definition*; a closing-auction revision or a delayed final print separates them. Treat this
as an identity with a wording risk, not a hard identity like S5.

**Live check.** `KXNASDAQ100U/KXNASDAQ100`: 29 of 400 ladder levels land on a bucket boundary
(10-point grid vs 100-point buckets); 24 testable; best net **−0.1404**.
`KXINXU/KXINX`: 18 of 90 levels match (5-point vs 25-point); 15 testable; best net **−0.1545**.
**No violation.**

### S7 — Annual index: directional ladder = tail of the terminal partition

`KXNDQDIRY-26DEC31H1600`, `KXNASDAQ100Y-26DEC31H1600`, `KXNASDAQ100POS-26DEC31H1600` all carry
`close_time = 2026-12-31T21:00:00Z`, `expiration_time = 2027-01-08T00:00:00Z`, and the *identical*
rule phrase "the Nasdaq 100 index value on Dec 31, 2026 at 4pm EST". Same for the S&P triple.
This is the cleanest exact identity in the slice — same instant, same source, same wording.

**Live check** (both directions testable because the annual partitions are well bid):

| pair | levels matched | best net, buy-ladder/sell-tail | best net, buy-tail/sell-ladder |
|---|---:|---:|---:|
| `KXNDQDIRY` ↔ `KXNASDAQ100Y` | 8 | −0.1023 (at 33,000) | **−0.0576** (at 31,000) |
| `KXINXDIRY` ↔ `KXINXY` | 8 | **−0.0500** (at 7,600) | −0.1017 (at 8,400) |

**No violation.** −0.0500 is the tightest cross-series slack found anywhere in this slice. Worked
example at NDX 31,000: ladder ask 0.45, five-bucket tail Σ ask 0.35, ladder bid 0.33 —
`0.33 − 0.35 − fee(1−0.33) − Σ fee(askᵢ) = −0.0576`.

### S8 — Bracketing a non-aligned threshold

`KXNASDAQ100POS` settles above **25,249.85** (the 2025 close), which is not a `KXNASDAQ100Y` bucket
boundary; it falls strictly inside `[25,000, 25,499.99]`. So the identity degrades to a two-sided
bracket:

`P(tail ≥ 25,500) ≤ P(POS) ≤ P(tail ≥ 25,000)`

**Live check.** POS quotes 0.671 / 0.679 (tenth-cent tick).
Upper: `bid(POS) − Σ ask(17-leg tail ≥ 25,000) − fees = 0.671 − 0.840 − … = **−0.2398**`.
Lower: `Σ bid(16-leg tail ≥ 25,500) − ask(POS) − fees = 0.630 − 0.679 − … = **−0.1064**`. Consistent.
Same construction for `KXINXPOS-26DEC31H1900` (threshold 6,845.50 inside the `[6,800, 6,999.99]`
bucket of `KXINXY`): **−0.1148** and **−0.2121**. Consistent.

### S9 — Threshold nesting inside the crypto milestone family

`KXBTC2026250` ⊂ `KXBTC2026200`: higher threshold **and** a later window start
("starting 2025-10-18T14:00:00.000Z" vs "starting 2025-10-10"), both ending "before Jan 1, 2027 at
12:00 AM ET". Strict subset both ways.
**Live check:** `bid(250k) − ask(200k) − fees = 0.01 − 0.04 − 0.0334… = **−0.0334**`. Consistent.

`KXDOGEMAX1`: "Before Jan 1, 2027" ⊂ "Before Jun 1, 2027", identical threshold 0.99999999 and
identical rule text. Quotes 0.04/0.05 and 0.08/0.09 ⇒ `0.04 − 0.09 < 0`. Consistent.

`KX10Y2YDATE-26DEC31` ⊂ `KX10Y2Y-26DEC31` at the 0.70% level: the terminal reading is one of the
daily observations the touch ladder scans.

> touch: "…on **any daily observation dated between Issuance and Dec 31, 2026 (inclusive)**, is above .7%"
> terminal: "If the daily 10-Year … minus the 2-year … **for December 31, 2026** is above -30bps"

**Live check:** touch ask 0.76, terminal bid 0.20 ⇒ net **−0.584**. Consistent, with enormous slack
(the touch premium over the terminal is 43–56 cents — economically plausible for a 5-month touch).

### S10 — Terminal-in-running-max, and why it is *not* exact

`KXBTCY-27JAN0100` tail ≥ $100,000 versus `KXBTCMAXY-26DEC31` "Above $99,999.99" looks like a clean
`terminal ⊆ running max`. It is not, for two independent reasons:

1. **Window boundary.** `KXBTCMAXY` closes at `2027-01-01T04:59:00Z` ("before Dec 31, 2026 at
   11:59 PM ET"); `KXBTCY` closes at `2027-01-01T05:00:00Z` and settles on "the simple average of
   the sixty seconds of BRTI **before** 12 AM EST". The terminal averaging window is
   `04:59:00–05:00:00Z` — it begins exactly where the max window ends. The terminal reading is
   outside the max window.
2. **Different statistics.** `KXBTCMAXY`'s secondary rule defines its value as a **trimmed mean over
   the whole measurement period** ("taking all BRTI values for each minute from market issuance until
   the specified time… removing the top 20% and bottom 20%… then averaging the remaining 60%"), with
   a separate spot-touch early-expiry clause. `KXBTCY` is a 60-second simple mean. These are not the
   same random variable.

**Live check anyway** (as a diagnostic, not as an enforceable bound):
tail ≥ 100,000 Σ bid 0.083 vs MAXY ask 0.13 ⇒ **−0.0613**;
tail ≥ 150,000 bid 0.022 vs MAXY ask 0.04 ⇒ **−0.0223**. Prices behave as if the relation holds.
Similarly `KXBTCMAX100-26-DEC` ("cross $100k before Jan 1 2027") bid 0.11 vs `KXBTCMAXY` ask 0.13 ⇒
**−0.0349**. Do not encode these as hard constraints.

### R1 — REJECTED: monthly running extreme nested in annual running extreme

This is the relation the ticker grammar most obviously suggests (`KX<COIN>MAXMON` ⊂ `KX<COIN>MAXY`),
and it is the one that *fails*. On the snapshot it produces six apparent net-positive violations, all
in BNB, up to **+0.1363** with 100 contracts of depth:

| strike | `KXBNBMAXY` ask | `KXBNBMAXMON` bid | net of fees |
|---:|---:|---:|---:|
| 640 | 0.36 (400) | 0.53 (100) | **+0.1363** |
| 650 | 0.18 (400) | 0.31 (100) | +0.1046 |
| 660 | 0.15 (10) | 0.26 (100) | +0.0875 |
| 670 | 0.15 (5) | 0.18 (100) | +0.0106 |
| 540 (MIN) | 0.59 | 0.67 | +0.0475 |
| 550 (MIN) | 0.64 | 0.78 | +0.1117 |

Windows genuinely nest (`KXBNBMAXY` `open_time` 2026-07-22T16:46Z → Dec 31; `KXBNBMAXMON`
2026-08-01T04:10Z → Aug 31), the settlement source is identical (`CF BNBUSD_RTI`), and the primary
rule text is word-for-word the same apart from the date. The relation still does not hold, because of
the secondary rule:

> "At each minute throughout the market duration, a settlement value is calculated using every
> minute-by-minute CF BNBUSD_RTI price… the top 20% and bottom 20% of **the cumulative dataset** are
> removed before calculating the average of the remaining values. If the trimmed mean associated with
> any single minute during the period is above the threshold, the market resolves to Yes.
> **The measurement period runs from when the market is issued** until the specified end time."

Each market's monitored quantity is a **running trimmed mean anchored at its own issuance**, not the
spot price. The monthly market's mean covers August only; the annual market's mean is dragged by
July. In a rising market the August-anchored mean crosses $640 on minutes when the July-anchored mean
does not. The two series do not observe a common path, so no pathwise-max inequality is available —
and the sign of the pricing gap (monthly *above* annual) is exactly what the mechanism predicts.

Other coins are untestable or consistent: DOGE −0.3157, ZEC −0.6665, all MIN pairs negative; BTC and
SOL share no strike between the MON and Y grids.

### Relations that do **not** exist (state them so a scanner does not invent them)

* **Hourly vs daily vs annual index levels.** `KXINXU-26AUG03H1000` (10 am) and
  `KXINX-26AUG03H1600` (4 pm) are different instants. There is no settlement relation between them —
  only correlation. The *only* cross-horizon index identity is same-timestamp (S6, S7).
* **Weekly vs monthly Ornn ladders.** `KXH200WS-26SEP11` reads a single 4 pm ET print; `KXH200MS-26SEP`
  is the arithmetic mean of the month's hourly values. A subinterval reading imposes **no** inequality
  on a mean over the superinterval. Correlation only.
* **Quarterly vs fiscal-year company KPIs.** `KXMCD` (Q3 restaurants, 46,300–46,700) and `KXMCDA`
  (fiscal 2026 restaurants, 46,800–47,600) measure different periods. Correlation only.
* **`KXUST10A` vs `KXUST10AD`.** Identical 15-strike grids but different observation dates
  (Aug 7 vs Aug 3). No nesting.

---

## Traps

1. **Two "no quote" encodings on the ask.** `yes_ask_size_fp == 0` means no offer, and the price is
   `1.0000` on 1,985 legs but **`0.0000` on 56 legs**. A scanner that detects "no ask" by
   `price == 1.0` will read those 56 legs as free YES contracts. Always gate on the size field.
   The bid is consistent (`size == 0 ⟺ price == 0.0000`, 2,774 legs).

2. **Fractional depth.** `*_size_fp` takes values below one contract (`KXBTC-26AUG0717` quotes
   0.02 ask on 0.01 contracts; `KXETHY` has a 0.20-contract bid). 15.2% of two-sided legs have ≤ 1
   contract on the thin side. A dollar-denominated edge computed without size is fiction.

3. **`liquidity_dollars` is 0 on all 10,722 legs.** Not a filter in this snapshot.

4. **Finalized legs inside open events.** 32 open events hold 76 non-active legs, 52 of them
   resolved **YES**. `KXKOSPI-26DEC31` is 2 active of 11; `KXIBOV-26DEC31` is 4 of 14;
   `KXNASDAQ100MAXY-26DEC31H1600` has four already-touched strikes still listed. They carry
   `bid 0.0000 / ask 1.0000`, indistinguishable from an unquoted live leg. Filter on
   `status == 'active'` *before* sizing any basket.

5. **`T` is not a direction marker.** In a MECNET partition the bottom `less` leg and the top
   `greater` leg are both `-T…`. Use `strike_type`.

6. **Two strike encodings in the same family.** `KXBTCY-27JAN0100-T20000.00` is a plain decimal;
   `KXXRPY-27JAN0100-T05000` is a ×10⁴ fixed-point integer meaning $0.5000, and
   `KXBTCMAXMON-BTC-26AUG31-6500000` is ×10² meaning $65,000.00. Parsing the ticker numerically
   without a per-series scale gives errors of 10⁴. Prefer `custom_strike.floor_strike` /
   `cap_strike`, then the subtitle; use the ticker last.

7. **The `H` code in an event ticker is the *close* hour, not the observation hour.**
   `KXINXPOS-26DEC31H1900` closes at `2027-01-01T00:00:00Z` (7 pm ET) but settles on "the S&P 500
   index value on Dec 31, 2026 **at 4pm EST**". Pair series on `close_time` **and** on the rule text,
   never on the ticker suffix alone.

8. **Running-extreme markets do not track spot.** The primary rule says "If the price of BTC …
   is ever above $65,000"; the secondary rule says the monitored quantity is a **running trimmed mean
   anchored at issuance**. Two markets on the same coin with different issuance dates monitor
   different processes (see R1). And the anchor date is only in prose — `open_time` is the closest
   metadata proxy.

9. **Deadline-ladder legs can carry inconsistent windows.** `KXBTCMAX100-26`:
   AUG/OCT/NOV say "starting **Jul 21, 2026**", SEP/DEC say "starting **02/17/2026 04:00 PM**".
   The SEP leg's window is therefore *not* a subset of the OCT leg's window, so the ladder is not
   strictly nested on its own text even though it is priced monotonically (0.02/0.04/0.08/0.11 bids).
   Read every leg's rule, not just the first.

10. **Template placeholders escape into production.** `KXBTCMAX150-25` legs read
    "If the price of Bitcoin is above `|| Count ||` by `|| Date ||` at `|| Time ||`, then the market
    resolves…". Any threshold extraction from that series must fall back to the subtitle.

11. **`KX*15M` has no fixed strike.** The strike is the 60-second mean 15 minutes earlier; the
    `yes_sub_title` "Target Price: $63,362.99" is a snapshot artifact that is meaningless before
    T−15 min. `settlement_timer_seconds = 1`.

12. **`collateral_return_type` is necessary but not sufficient for finding nested ladders.**
    All 16 monthly and 16 annual crypto running-extreme series, plus `KXBTCMAXY`, `KXINXMAXY`,
    `KXNIKKEI` and `KXWTIMAX/MIN`, are perfectly nested ladders with `collateral_return_type = ''`.
    The DIRECNET-only monotonicity scan tests 89,874 pairs; keying on leg `strike_type` instead tests
    90,611 and catches an extra inversion.

13. **The shared taxonomy parser mis-handles four subtitle grammars present here.** Verified against
    the live strings; each is handled locally in this analysis:

    | subtitle | `taxonomy.parse_threshold` returns | correct |
    |---|---|---|
    | `"Above 197 thousand"` (`KXGOOG`) | `197000000000000.0` — the `[kmbt]` group eats the `t` of "thousand" | 197,000 |
    | `"Above -2.5%"` (`KXCTCQ`, `KXCTCA`, `KXWEN`) | `None` — no sign in the digit class | −2.5 |
    | `"Above -30bps"` (`KX10Y2YDATE`) | `None` | −0.30 (percent axis) |
    | `"$2,000,000,000+"` (`KXFDVOPENSEA`) | `('$2,000,000', 0.0, '>=')` — the `N+` regex splits inside the number | 2.0e9 |

    Also `parse_bucket`/`parse_threshold` return `None` for `KXFEAR`'s ordinal labels and for
    `KX*15M`'s "Target Price: …", which makes `partition_is_tiled` report `False` on five genuinely
    exhaustive MECNET partitions (S2). Recommended upstream fixes: add `\.\d+` to the numeric class,
    allow a leading sign, order the unit alternation `bps|thousand|…|b|t` so `bps` wins over `b`, and
    require a digit boundary before the `+` in `_RE_THRESHOLD_PLUS`.

14. **`frequency` and `series.category` are both unreliable.** `KXH200MS` is monthly-average but
    filed `one_off`; `KXDJI` is hourly but filed `one_off`; `KXWTIMAX`/`KXWTIMIN` sit in the
    Financials shard as Commodities series and carry 6.7 M contracts of volume, i.e. they are not a
    rounding error.

15. **Not every MECNET leg is 0/1.** `KXOPENAISECTOR` pays `$1 / number of sectors` on multi-sector
    assignment. Basket P&L bounds built on 0/1 payoffs are wrong for that event.

---

## Open questions

* **`KXBTCMAXY`'s two contradictory settlement clauses.** The secondary rule defines the resolution
  value as a period trimmed mean *and* says "If the BRTI **crosses the threshold at any point** during
  the measurement period (triggering early expiration), the market immediately resolves." Whether
  the operative test is the running trimmed mean or spot touch cannot be settled from metadata; it
  determines whether S10 is a hard bound or not.
* **Issuance anchors.** Every running-extreme series says "after issuance" without a date. I used
  `open_time` as the proxy. Whether `open_time` is the contractual issuance instant is unverified,
  and R1 turns on that question.
* **`KXINX`'s "end-of-day" vs `KXINXU`'s "at 4pm EDT".** Whether these can ever differ (closing
  auction revision, delayed final print) decides whether S6 is an identity or a near-identity.
* **`KXUST<N>A` vs `KXUST<N>AD`.** The two variants have identical grids and rules but different
  dates and different `frequency` values (`daily` vs `one_off`). What distinguishes them
  operationally is not recoverable from metadata.
* **`Ornn` and `Fiscal.ai`** are the two largest settlement sources here (133 and 166 events) and
  neither is a public price feed. Revision policy ("Revisions to the underlying made after…") is
  truncated in `rules_secondary` and the full `contract_terms_url` was not fetched.
* **`collateral_return_type` semantics.** `MECNET`/`DIRECNET` clearly correspond to mutually-exclusive
  and directional collateral netting, so basket margin should differ; the actual margin formula is not
  in this dataset and it determines the real capital cost of every constraint above.
* **`KXSOLD26`** is an annual SOL directional ladder on `27JAN0100` with no paired range partition
  (there is no `KXSOLY`), so S5's identity has no counterpart for SOL at the annual horizon. Whether
  a `KXSOLY` exists off-snapshot is unknown.
