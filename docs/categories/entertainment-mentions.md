# Entertainment & Mentions

Structural profile of the API categories `Entertainment` and `Mentions`, from the
full-exchange census snapshot **2026-08-02T20:52Z**. All prices are dollars per contract
as reported by the trade API; all fee arithmetic uses the schedule effective 2026-07-07
(`taker = fee_multiplier * 0.07 * P * (1-P)` per contract per leg, rounded up to a
centicent; `maker = 0` unless `fee_type == 'quadratic_with_maker_fees'`, then 0.0175).

The two categories are documented together because they share one contract shape — a
non-exclusive menu of propositions about one subject — and because `Mentions` is
structurally a spin-off of the Entertainment/Politics "what will X say" template.

---

## Inventory — events, markets, series count; how much of the exchange this is

| | Entertainment | Mentions | combined |
|---|---:|---:|---:|
| open events | 498 | 58 | 556 |
| open markets | 6,789 | 983 | 7,772 |
| distinct series with an open event | 292 | 57 | 349 |
| series in the catalog with this `series.category` | 2,490 | 398 | 2,888 |
| share of exchange open markets (73,964 total) | 9.2% | 1.3% | **10.5%** |
| share of exchange open events (8,478 total) | 5.9% | 0.7% | **6.6%** |

Entertainment is the exchange's **fourth-largest category by open markets** (after Sports
35,344, Elections 11,476, Financials 8,152) and its **most fragmented**: 6,789 markets are
spread over 292 series, a median of 10 markets per series and a mean of 23.2. The tail is
extreme — 79 series carry exactly one market.

Catalog dormancy is the defining feature. Only **291 of 2,490** Entertainment series
(11.7%) and **57 of 398** Mentions series (14.3%) have an open event. The Entertainment
catalog is a graveyard of one-off celebrity propositions; ticker-prefix mining over
`series.json` will surface thousands of series that cannot be traded.

Category labelling is unusually clean here (unlike Elections/Politics): of 556 events, only
**one** has a `series.category` that disagrees with its `event.category` —
`KXTRUMPAPOLOGY-26` ("Will Donald Trump issue a public apology?") sits in the
`Entertainment` shard while its series is catalogued under `Politics`. Do not read this as
a general licence to group by category; it is a property of this slice, not of the field.

Template mix (via `taxonomy.classify_event`, active legs only):

| template | Entertainment events | Mentions events |
|---|---:|---:|
| `entity_menu` | 220 | **58 (100%)** |
| `threshold` (one-sided ladder) | 133 | 0 |
| `binary` (single leg) | 115 | 0 |
| `deadline` | 15 | 0 |
| `combination` | 15 (**all 15 are misclassifications — see Traps**) | 0 |

`mutually_exclusive` is **True on 131 of 498** Entertainment events and on **0 of 58**
Mentions events. `collateral_return_type` is a perfect machine-readable proxy for the flag
in this slice: `MECNET` on exactly the 131 mutex events, `DIRECNET` on 62 ladder events,
empty on the remaining 305.

---

## Series families

Grouped by what they actually settle on, not by their display titles. Market counts are
open markets in the snapshot. Every series in this slice has `fee_multiplier = 1`; there
are **no zero-fee series** here. Seven series carry maker fees.

### 1. Streaming / consumption threshold ladders (Luminate, YouTube, Netflix) — 1,712 markets

| series | mk | ev | frequency | source | notes |
|---|---:|---:|---|---|---|
| `KXARTISTSTREAMSY` | 1,298 | 60 | annual | Luminate | **largest series in the slice** |
| `KXALBUMEQUIV` | 135 | 12 | weekly | Luminate | album-equivalent units, first week |
| `KXPUREALBUMS` | 119 | 10 | weekly | Luminate | pure (product) sales, first week |
| `KXYTVIEWSHIGH` | 69 | 8 | monthly | YouTube Charts | max daily views in a calendar month |
| `KXYTVIEWSW` | 61 | 7 | weekly | YouTube Charts | max daily views in a Mon–Sun week |
| `KXYTVIEWS` | 7 | 7 | monthly | YouTube Charts | single-strike duplicate of `KXYTVIEWSHIGH` |
| `KXNETFLIXTOPVIEWSTV` / `...MOVIE` | 22 | 2 | one-off | Netflix | "At least N million views" |

Ticker grammar: `KXARTISTSTREAMSY-<ARTISTCODE><YY><MONDD>-<STRIKE>`, e.g.
`KXARTISTSTREAMSY-WEEKND26DEC31-13.5B` = The Weeknd, period ending 2026-12-31, strike
13.5 billion streams. The artist code is a mnemonic, not a slug (`YEEZY` = Kanye West,
`POPKING` = Michael Jackson, `RIRI` = Rihanna) — never derive the artist from it. The
strike suffix is the literal number with a `K`/`M`/`B` multiplier and is the only reliable
machine-readable strike; `custom_strike` carries an opaque `{"musician": "<uuid>"}` (and
sometimes the literal placeholder `{"musician": "XXX"}` in `KXALBUMEQUIV`).

`KXALBUMEQUIV` / `KXPUREALBUMS` share an event key: `KX<SERIES>-<ALBUM3><YY><MON><DD>`
where the date is the **end of the Luminate tracking week** (`FRE26OCT08`,
`WILD26AUG20`). This shared key is what makes the pure-sales ⇒ album-equivalent
implication (below) machine-extractable.

`KXYTVIEWSW-<ART3><YY><MON><DD>` uses the week-end date; `KXYTVIEWSHIGH-<ART3><YY><MON>`
uses the **month after** the measured month (`-26SEP` is the August 2026 market). The
ticker month is a settlement month, not the measurement window.

### 2. Critic-score ladders — 228 markets

`KXRT` (176 mk / 15 films, Rotten Tomatoes) and `KXMC` (52 mk / 4 games, Metacritic).
Grammar `KXRT-<FILM3>-<SCORE>`, e.g. `KXRT-AVE-70` = *Avengers: Doomsday*, Tomatometer
above 70. `KXRT` alone holds **4.51 M contracts of open interest** — 22% of all
Entertainment OI — concentrated in `KXRT-SPI` (*Spider-Man*, 4.02 M OI across 23 strikes, 3.57 M of it on six strikes).
`frequency = custom`; settlement is pinned to "the Monday after wide release at 10:00 AM
ET".

### 3. Billboard chart menus — 549 markets

Five series describe the **same weekly chart** from different angles:

| series | mk | proposition |
|---|---:|---|
| `KXBBCHARTPOSITIONALBUM` | 280 | one event per album; legs are ranks 1–10 (Billboard 200) |
| `KXBBCHARTPOSITIONSONG` | 40 | one event per song; legs are ranks 1–10 (Hot 100) |
| `KXTOPALBUM` / `KXTOPSONG` | 43 / 43 | one event per week; legs are titles; "#1" |
| `KXBILLBOARDRUNNERUPALBUM` / `...SONG` | 44 / 43 | same, "#2" |
| `KXRANKLISTSONGTOP10` | 43 | same, "Top 10" |
| `KXALBUMDEBUT` | 15 | single binary, "debuts at #1" for one album/week |

Grammar: subject-major (`KXBBCHARTPOSITIONALBUM-<YY><MON><DD><ALB3>-<RANK>`) vs
week-major (`KXTOPALBUM-<YY><MON><DD>-<ALB3>`). The date in both is the **chart issue
date**, and the 3-letter subject code is shared across all five series for a given week —
this is the join key for the equivalences in *Structural constraints*.

### 4. Annual chart-depth menus (per artist, 2026) — 434 markets

`KX1SONG` (116), `KX10SONG` (112), `KX20SONG` (96), `KX1ALBUM` (110). One event each for
the whole year; one leg per artist (`-DRA` Drake, `-WEE` The Weeknd, …). Titles: "Who will
have a #1 hit / top 10 song / top 20 song / #1 album this year?". `mutually_exclusive =
False` — many artists can qualify. The three song series form the only genuine
chart-depth nesting lattice in the category (see constraints, and the features caveat).

### 5. Spotify Wrapped year-end rank menus — 214 markets

`KXTOPSONGSPOTIFY` / `...RUNNERUP` / `KXTOPSONGTHIRD`, `KXTOPALBUMSPOTIFY` / `...RUNNERUP`
/ `...THIRD`, `KXTOPARTIST` / `...RUNNERUP` / `...THIRD`, each with a `...USA` twin
(different chart — global vs USA — and therefore **not** interchangeable). All
`mutually_exclusive = True`, all resolve off "Spotify's 2026 Spotify Wrapped Top 10 …
chart on the date that the chart is released for 2026".

### 6. Awards — nominees and winners — 636 markets

**Oscars (99th Academy Awards).** Sixteen `KXOSCARNOM*` nominee series
(`mutually_exclusive = False`, 267 mk) and six `KXOSCAR*` winner series
(`mutually_exclusive = True`, 123 mk). Grammar `KXOSCAR[NOM]<CATEGORY>-27-<SUBJ3>`; the
`<SUBJ3>` suffix is **shared between the nominee and winner series** (`-ODY` = *The
Odyssey* in both `KXOSCARNOMPIC-27` and `KXOSCARPIC-27`), which is the join key. Winner
menus carry an extra `-TIE` leg; nominee menus do not.

**Emmys (78th).** Thirteen `KXEMMY*` winner series (`mutually_exclusive = True`, 156 mk)
plus `KXEMMYCOUNT` (117 mk / 6 shows, "how many Emmys will X win", legs `Exactly N`). No
Emmy nominee series — nominations have already been announced, and the non-nominated legs
inside the winner events are **finalized `no`** while the events remain open.

**Grammys (69th).** Five `KXGRAMMYNOM*` nominee series (`mutually_exclusive = False`) and
`KXGRAMAOTY` / `KXGRAMBNA` winner series. `KXGRAMBNA-69` and `KXGRAMMYNOMNAOTY-69` are a
perfectly aligned 67-leg pair. `KXLGRAM` covers the Latin Grammys.

Also: `KXVFILMFESTIVAL` (191 mk / 6 Venice prizes) and `KXGAMEAWARDS`.

Maker-fee series (`fee_type = quadratic_with_maker_fees`, 0.0175 coefficient) — the only
ones in this slice: `KXSUPERBOWLHEADLINE` (53 mk), `KXEMMYDSERIES` (15), `KXEMMYCSERIES`
(13), `KXEMMYCACTO` (12), `KXEMMYDACTR` (11), `KXEMMYDACTO` (11), `KXEMMYCACTR` (11).
**126 markets total.** Any passive quoting strategy must special-case these seven.

### 7. Appearance / casting / release menus — ~1,400 markets

`KXPERFORMVS` (134), `KXPERFORMSUPERBOWL` (133), `KXROLEATEVENTCOACHELLA` (114),
`KXALBUMRELEASE` (95), `KXSONGRELEASE` (53), `KXMEDIAGUEST*`, `KXPERFORMROLE*`,
`KXACTOR*`, `KXENGAGEMENT*` (17 one-market series), `KXMOVIEDELAY*`, `KXSHOWEND*`. Almost
all are `mutually_exclusive = False` entity menus or single binaries. `KXMEDIARELEASE*`
and `KXALBUMRELEASEDATE*` are deadline ladders (`Before <date>` legs).

### 8. Mentions — 983 markets, 100% `entity_menu`, 100% `mutually_exclusive = False`

Two window grammars, and the distinction is the whole ballgame:

**(a) Event-scoped** — 862 markets in 54 events. The counting window is one named
broadcast.

| family | mk | events | window |
|---|---:|---:|---|
| `KXEARNINGSMENTION<TICKER>` | 711 | 47 | "the next `<Company>` earnings call (including the Q+A)" |
| `KXFEDMENTION` | 45 | 1 | "his Sep 2026 post-FOMC meeting introductory remarks and Q+A" |
| `KXDEBATEMENTION` | 38 | 2 | one named debate |
| `KXHEARINGMENTION` | 15 | 1 | one named Congressional hearing |
| `KXFOXNEWSMENTION` | 15 | 1 | one named TV appearance |
| `KXMRBEASTMENTION` | 13 | 1 | "Next MrBeast Youtube Video" |
| `KXMAMDANIMENTION` | 13 | 1 | "next NYC Mayor's Office announcement" |
| `KXTALARICOMENTION` | 12 | 1 | one named TV appearance |

**(b) Calendar-window** — 121 markets in 4 events, all Trump. `KXTRUMPSAY` (weekly, 32),
`KXTRUMPSAYMONTH` (monthly, 31), `KXTRUMPSAYNICKNAME` (quarterly, 29),
`KXTRUMPSAYCOMPANY` (monthly, 29). Window is a date range, and the admissible surface is
much wider: "public statements, direct quotes published by Source Agencies, or written
public statements on his personal social media accounts (Twitter/Truth Social)".

Ticker grammar: `KX<SUBJECT>MENTION-<YY><MON><DD>[<seq>]-<WORDCODE>` (event-scoped, date =
the broadcast date, `B` suffix disambiguates two same-day events:
`KXDEBATEMENTION-26AUG03` / `-26AUG03B`) and `KXTRUMPSAY*-<YY><MON><DD>-<WORDCODE>` (date =
the **window end**, exclusive). `<WORDCODE>` is the first four alphanumeric characters of
the leg subtitle, upper-cased, truncated or extended on collision: 875 of 983 codes are
4 characters, 70 are 3, 26 are 2, 12 are 5. Twenty-three codes do **not** match the first
four characters of the subtitle, because the code is taken from the *canonical* word in a
slash-list rather than the first (`-GASO` for "Gas / Gasoline / Fuel", `-ARTI` for
"AI / Artificial Intelligence", `-TSLA` for "Tesla / TSLA"). Collision extension is live:
`KXFEDMENTION-26SEP-GOOD` is "Good Afternoon" and `-GOODS` is "Goods inflation". **Parse
the subtitle, never the code.**

---

## Contract templates

### T1 — one-sided threshold ladder (133 Entertainment events, 1,844 `strike_type=greater` markets)

Legs are `Above <L>` (1,795 of 1,848 threshold legs start with "Above"; 46 with "At
least", 7 with "Below"), one per strike, sharing a subject and a measurement window.
`mutually_exclusive = False`. There is no lowest-bucket leg and no top bucket — the ladder
does not tile a line; it is a nested chain.

> `KXARTISTSTREAMSY-WEEKND26DEC31-13.0B`: *"If The Weeknd has Above 11B Worldwide Streams
> during the January 01 - December 31, 2026 period, then the market resolves to Yes."*
> (the rule text always quotes the event's lowest strike; the per-leg strike is in the
> ticker suffix and `yes_sub_title`.)

### T2 — mutually exclusive entity menu over an open universe (131 events)

One leg per candidate subject; `mutually_exclusive = True`; `collateral_return_type =
MECNET`. **Not collectively exhaustive** — the winning subject need not be listed.

> `KXGOOGLESEARCH-TVS27`: *"If His & Hers is the #1 search on Google's Year in Search 2026
> Global - Tv Shows list in 2026, then the market resolves to Yes."* Secondary: *"If
> Google's Year in Search 2026 Global - Tv Shows is not published during 2026, then all
> markets will resolve to NO."*

### T3 — non-exclusive entity menu (220 Entertainment + 58 Mentions events)

One leg per subject, any number may resolve Yes. All of Mentions, plus nominee slates,
performer menus, release menus.

> `KXOSCARNOMPIC-27-ODY`: *"If The Odyssey has been nominated for Best Picture at the 99th
> Academy Awards, then the market resolves to Yes."*

### T4 — count menu ("Exactly N")

`KXEMMYCOUNT` (legs `Exactly 1` … `Exactly N`, **no `Exactly 0` leg**) and
`KXTOP10BBSPOTS` (legs `Exactly 0 songs` … `Exactly 10 songs`). Both
`mutually_exclusive = True`; only the latter is exhaustive.

> `KXEMMYCOUNT-26WID-1`: *"If Widow's Bay has won exactly 1 awards at the 78th Emmy
> Awards, then the market resolves to Yes."*

### T5 — deadline ladder (15 events)

`Before <date>` legs nested by time; `KXMEDIARELEASE*`, `KXALBUMRELEASEDATE*`, `KXESVI`,
`KXGTA6`.

### T6 — mention proposition (983 markets, `strike_type = custom` on all of them)

Two rule shapes. Event-scoped:

> `KXEARNINGSMENTIONNVDA-26AUG26-GAMI`: *"If Gaming is said by any NVIDIA Corporation
> representative (including the operator of the call) during the next NVIDIA Corporation
> earnings call (including the Q+A), then the market resolves to Yes."*

Calendar-window:

> `KXTRUMPSAY-26AUG03-KAMA`: *"If Kamala, or a plural or possessive form of Kamala, is
> stated by Donald Trump after July 27th, 2026 at 8:00am ET and before Aug 3, 2026 at
> 12:00am ET, then the market resolves to Yes."*

Both carry the same payout criterion in `rules_secondary`: *"The exact phrase/word, or a
plural or possessive form of the phrase/word, must be used. Grammatical/tense inflections
are otherwise not included. … For phrases with slashes like "Doge/Dogecoin," either word
satisfies the criterion. If the word must be said a minimum number of times, all instances
must occur after market issuance."*

A count qualifier can be embedded in the leg subtitle — `Trump (3+ times)`,
`Dividend (2+ times)`, `Vega (5+ times)`. There are exactly **7 such legs in 983**, in 6
different events, and in **no case does the same event also list the bare phrase**. So the
count qualifier is a one-off strike, not a ladder: there is **no mention-count ladder and
therefore no count-nesting lattice anywhere in Mentions**.

---

## Settlement

**Sources.** Entertainment leans on chart publishers — Billboard (1,924 markets), Luminate
(1,554), Spotify (725), Netflix, Rotten Tomatoes, Metacritic, Sotheby's — plus a
standard 12-outlet news panel (Reuters 977, AP 939, CNN 912, CBS 901, Variety 847, Fox
News 845, ABC 820, MSNBC 789, Rolling Stone 641, THR 633, NYT 603) for the appearance and
casting menus. Awards resolve off the awarding body itself (Academy of Motion Picture
Arts, Academy of Television Arts, Recording Academy, La Biennale di Venezia). Every awards
series carries a disclaimer clause: *"This market and these products have not been
endorsed by the Oscars."*

Mentions is narrower: Bloomberg on all 832 earnings-call markets (with video primary —
*"Video of the … earnings call will be primarily used to resolve the market; if a
consensus by Kalshi employees cannot be reached using video, transcripts … will be
used"*), the Federal Reserve for `KXFEDMENTION`, MrBeast/NYC Mayor's Office for the
creator/official series, and the 12-outlet news panel for the Trump and debate series.
Resolution is explicitly a **human adjudication over video** with transcripts as fallback.

**Early close.** `can_close_early = True` on **100% of active markets in both categories**
(6,405 + 957). Conditions cluster into five texts; the two that matter:

- *"This market will close and expire early if the event occurs."* (2,008 Entertainment,
  862 Mentions) — a mention leg that comes true stops trading immediately.
- *"This market will close and expire early if the specified word or phrase is stated by
  President Trump."* (95 Mentions markets)
- *"This market will close and expire early if the data for the January 01 – December 31,
  2026 period is released early."* (1,114 Entertainment, the Luminate ladders)
- *"This market will close and expire early if the relevant Billboard chart is
  published…"* (320)

Consequence: in Mentions, **all 26 finalized markets in the snapshot resolved `yes`**
(0 `no`). A Mentions leg that is finalized before its scheduled expiry is a leg that
already happened. Entertainment's 369 finalized legs split 255 `yes` / 114 `no`, because
awards nominations knock out losers as well.

**Settlement timer.** 1,800 s on all 957 Mentions markets and on 4,980 Entertainment
markets; 3,600 s on 974; 300 s on 274; 3,598 s on 176.

**Expiry horizons** (days from snapshot, active markets): Entertainment p10 = 19,
median = 155, p90 = 515, max = 3,073 (`KXSHOWENDSIMPSONS`, "Before 2030" style).
Mentions p10 = 16, median = 150, p90 = 181, max = 240.

**`expiration_time` is a backstop, not the resolution date, for event-scoped Mentions.**
`KXEARNINGSMENTIONNVDA-26AUG26` settles on the 2026-08-26 call but carries
`expiration_time = 2026-12-31T15:00Z`; `KXEARNINGSMENTIONMCD-26AUG04` likewise. The real
date is in the event ticker and `sub_title`. Calendar-window Trump markets are honest
(`KXTRUMPSAYMONTH-26SEP01` expires 2026-09-01).

**`liquidity_dollars` is 0 on all 7,362 active markets in this slice** and cannot be used.

---

## Liquidity

| | Entertainment | Mentions |
|---|---:|---:|
| active markets | 6,405 | 957 |
| two-sided (`0 < yes_bid`, `yes_ask < 1`) | 4,164 = **65.0%** | 948 = **99.1%** |
| no bid at all (`yes_bid = 0`) | 1,819 = 28% | 3 = 0.3% |
| no offer (`yes_ask = 1`) | 425 = 7% | 6 = 0.6% |
| spread on two-sided: p25 / median / p90 | 3¢ / 5¢ / 10¢ | 1¢ / 3¢ / 8¢ |
| fraction of two-sided at ≤ 2¢ | 19% | 47% |
| `min(bid_size, ask_size)` on two-sided: p25 / median / p75 | 5 / 5 / 50 | 6 / 23 / 64 |
| **tradeable** (two-sided, ≤5¢ wide, ≥25 contracts both sides) | 1,132 = **17.7%** | 363 = **37.9%** |
| total open interest (contracts) | 20.26 M | 1.76 M |
| total volume | 37.23 M | 2.48 M |
| median / p90 / p99 OI per active market | 248 / 3,709 / 54,765 | 259 / 1,679 / 20,000 |
| markets with zero OI | 20% | 5% |

**Only ~18% of Entertainment is genuinely tradeable.** The rest is either one-sided or a
5-lot quote. OI is extremely concentrated: the top 10 markets hold **24.4%** of combined
OI, the top 50 hold 46.6%, the top 500 hold 79.8%.

Largest books: `KXRT-SPI-91` (1.05 M OI), `KXRT-SPI-90` (0.89 M), `KXRT-SPI-92` (0.80 M),
`KXMEDIARELEASEST-27JAN01` (0.47 M OI / 2.44 M volume), `KXOSCARPIC-27-ODY` (0.47 M),
`KXRANKLISTGOOGLESEARCH-26DEC-DON` (0.39 M), `KXTRUMPSAY-26AUG03-STUP` (0.32 M),
`KXNETFLIXRANKSHOW-26AUG03-THE` (0.24 M).

Two-sidedness by family (active markets, ≥20 mk):

| series | mk | two-sided | tradeable | OI |
|---|---:|---:|---:|---:|
| `KXPERFORMVS` | 134 | 94% | 71% | 5,776 |
| `KXSUPERBOWLHEADLINE` | 53 | 100% | 58% | 137,951 |
| `KXROLEATEVENTCOACHELLA` | 114 | 100% | 54% | 93,894 |
| `KXYTVIEWSHIGH` | 69 | 97% | 41% | 54,010 |
| `KXALBUMEQUIV` | 135 | 76% | 33% | 207,387 |
| `KXRT` | 176 | 78% | 21% | 4,512,993 |
| `KXARTISTSTREAMSY` | 1,114 | 71% | **15%** | 505,516 |
| `KXMUSICREPORT` | 164 | 10% | 4% | 504,000 |
| `KXPERFORMSUPERBOWL` | 133 | 20% | 2% | 3,077 |
| `KXVFILMFESTIVAL` | 191 | 11% | 0% | 1,945 |
| `KXBBCHARTPOSITIONALBUM` | 280 | **0%** | 0% | **171** |

`KXBBCHARTPOSITIONALBUM` is the clearest **nominal book** in the slice: 280 markets, zero
two-sided quotes, 171 contracts of open interest in total. Its legs quote `0.00 / 0.97`;
across all of Entertainment there are **231 markets quoted exactly `0 / 0.97`**, a
seeded-placeholder signature. For `KXBBCHARTPOSITIONSONG-26AUG15IKN` the ten mutually
exclusive legs sum to `yes_ask = 9.60` and `yes_bid = 0.00` — a "book" carrying no
information at all.

---

## Structural constraints

Every relation below is a settlement-logic constraint (one contract's resolution condition
is a subset of another's, or legs partition an outcome space). Statistical co-movement is
excluded. Each is stated as a price inequality on **executable sides**, with the clause
that makes it exact, the failure modes, and a live check on the snapshot. Fees are the
verified taker formula on both legs; `fee_multiplier = 1` throughout this slice.

### C1 — Threshold-ladder monotonicity (exact)

For two strikes `L_hi > L_lo` in the same ladder event:
`Above L_hi` ⇒ `Above L_lo`, therefore **`P(L_hi) ≤ P(L_lo)`**.

Executable form: violated iff `yes_bid(L_hi) − yes_ask(L_lo) > taker(1−yes_bid(L_hi)) +
taker(yes_ask(L_lo))`; the lock is *buy `L_lo` YES at ask + buy `L_hi` NO at
`1 − yes_bid(L_hi)`*, which pays ≥ $1 in every state.

Basis: identical rule text with only the numeral changed — *"If The Weeknd has Above 11B
Worldwide Streams during the January 01 - December 31, 2026 period…"* vs the same sentence
with 13B. Same subject, same window, same source, same `strike_type = greater`.

Failure modes: (a) mixed comparators inside one event (`greater` vs `greater_or_equal`
vs `less` — 54 and 7 markets respectively in the slice) invert or blunt the relation;
(b) finalized legs sitting inside an open ladder quote `0.00 / 1.00` and must be dropped
(e.g. `KXARTISTSTREAMSY-YEEZY26DEC31-6.75B` and `-7.0B` are finalized inside an otherwise
active 23-leg ladder); (c) `KXYTVIEWSW` and `KXYTVIEWSHIGH` look like the same ladder for
the same artist but measure different windows (below).

**Live check.** 133 ladder events, **1,715 adjacent strike pairs**. One pair is
gross-positive and **zero are net-positive**: `KXRT-AVE` — `Above 50` bid 0.92 (size 1) vs
`Above 45` ask 0.91 (size 1,278), gross **+1.00¢**, fees 0.515¢ + 0.573¢ = 1.089¢, net
**−0.09¢**. The category is internally consistent to within one tick of the fee.

Note on capital: Kalshi sets `collateral_return_type = DIRECNET` on only 61 of the 133
ladder events (`KXRT`, `KXMC`, `KXALBUMEQUIV`, `KXPUREALBUMS`, `KXYTVIEWSHIGH`, `KXART`,
`KXHERMES*`, `KXFRAGRANCE`, `KXNETFLIXTOPVIEWS*`, `KXMACBOOKPRICE`, `KXCREED`,
`KXMOSTEXPENSIVEART`, `KXFOLLOWERCOUNTCLAV`). **`KXARTISTSTREAMSY`, all 60 events and
1,298 markets, gets no netting** — the settlement implication holds but the exchange makes
you post full collateral on both legs of the spread.

### C2 — Winner ⊆ nominee (exact)

For the same award category and the same subject:
`won <award>` ⇒ `nominated for <award>`, therefore **`P(win) ≤ P(nominate)`**.

Executable: violated iff `yes_bid(win) − yes_ask(nom) > taker(1−yes_bid(win)) +
taker(yes_ask(nom))`.

Basis: the paired rule strings differ only in the verb —
*"If The Odyssey **has won** Best Picture at the 99th Academy Awards…"* (`KXOSCARPIC-27-ODY`)
vs *"If The Odyssey **has been nominated for** Best Picture at the 99th Academy Awards…"*
(`KXOSCARNOMPIC-27-ODY`). Both reference the same ceremony ordinal.

Failure modes: (a) **join on the ticker suffix, not the name** — `KXOSCARNOMDIR-27` lists
"Phil Lord" while `KXOSCARDIR-27` lists "Phil Lord & Christopher Miller"; suffix join
gives 13 pairs there, name join only 11, and for Best Actor the nominee board spells
"Jaafar Jackson" against the winner board's "Jafar Jackson"; (b) the two boards are not
co-extensive (Best Picture: 38 winner legs vs 43 nominee legs; Best Actor: 20 vs 29), and
the winner board carries a `-TIE` leg the nominee board does not; (c) the nominee and
winner markets have different resolution dates (`KXGRAMMYNOM*` closes 2027-11-01, the
winner series 2027-12-31), so the spread carries a nomination-announcement gap.

**Live check.** 8 series pairs, **190 suffix-joined legs**, **zero gross-positive**. The
tightest pair is `KXOSCARSUPACTR-27-ZEN` (Zendaya): win bid 0.10 (size 61) vs nominee ask
0.17 (size 5), gross **−7.0¢**, net **−8.6¢**. Consistent everywhere.

### C3 — Chart-depth nesting: #1 ⊆ top 10 ⊆ top 20 (annual, per artist)

`KX1SONG` ⇒ `KX10SONG` ⇒ `KX20SONG` for the same artist and the same year.

Basis for the first link (**exact**): *"If SZA has a **#1 song** on the Billboard Hot 100
(including features), by the Billboard issue for the week of Dec 26, 2026"* vs *"If SZA has
a **top 10 song** on the Billboard Hot 100 (including features), by the Billboard issue for
the week of Dec 26, 2026"*. Identical apart from the depth, both with the features clause,
both anchored to the same final chart issue.

Basis for the second link (**not exact — do not encode as a hard constraint**):
`KX20SONG-26DEC26-SZA` reads *"If SZA has a **top 20 single** on the Billboard Hot 100 by
the Billboard issue for Dec 26, 2026"* — **no "(including features)"**, and
`KX10SONG`'s secondary rules add *"Features are encompassed by the Payout Criterion as long
as they are credited by Billboard"* while `KX20SONG`'s secondary rules say nothing about
features at all. A featured credit that charts top-10 could settle `KX10SONG` Yes and
`KX20SONG` No.

**Live check.**
- `#1 ⇒ top 10`: 103 joined artists, **0 gross-positive**; tightest is Khalid, bid 0.04
  vs ask 0.05, net −1.60¢.
- `#1 ⇒ top 20`: 90 joined artists, **0 gross-positive**; tightest Mariah Carey, bid 0.94
  vs ask 0.98, net −4.53¢.
- `top 10 ⇒ top 20`: 90 joined artists, **2 gross-positive, 1 net-positive** —
  **`KX10SONG-26-SZA` bid 0.55 (size 5) vs `KX20SONG-26DEC26-SZA` ask 0.49 (size 4.8),
  gross +6.00¢, fees 1.73¢ + 1.75¢, net +2.52¢, depth 4 contracts (≈ $0.10 total).**
  Billie Eilish is gross +2.00¢ / net −1.50¢. Given the features-clause asymmetry this is
  most likely a correctly-priced rule difference, not a mispricing — and at 4 contracts it
  is unexecutable either way. Record it as an inequality that **fails on rule text**, not
  as a violation.

### C4 — Cross-series duplicate listing (equivalence, exact)

Two series list the identical proposition, so `P(A) = P(B)` and both directions bind.

**(a) `KXYTVIEWS` ≡ `KXYTVIEWSHIGH`.** Seven single-leg `KXYTVIEWS` markets have a
byte-identical rule to a leg inside the corresponding `KXYTVIEWSHIGH` ladder:
*"If Taylor Swift has above 15M Global daily views on YouTube at any point during August
2026, then the market resolves to Yes."* — `KXYTVIEWS-TAY26SEP-15.0M` and
`KXYTVIEWSHIGH-TAY26SEP-15.0M`. (Two of the ladder legs carry the typo "on YouTube **in**
at any point"; same meaning.)

**Live check.** 7 pairs, both directions, **0 violations**. Tightest:
`KXYTVIEWS-MIC26SEP-28.0M` 0.05/0.07 vs `KXYTVIEWSHIGH-MIC26SEP-28.0M` 0.07/0.08 — selling
the ladder leg at 0.07 against buying the single at 0.07 is gross 0.00¢, net **−0.91¢**
after fees, with 226 × 643 contracts of depth. Nine tenths of a cent from a genuine lock,
and the only relation in this category where real size sits on both sides.

**(b) `KXBBCHARTPOSITION*` rank-1/rank-2 legs ≡ `KXTOPSONG` / `KXTOPALBUM` /
`KXBILLBOARDRUNNERUP*` legs**, same chart, same issue date, same subject:
*"If I Knew It, I Knew You by Taylor Swift is ranked #1 on the Billboard Hot 100 chart for
the Week of Aug 15, 2026"* (`KXBBCHARTPOSITIONSONG-26AUG15IKN-1`) vs *"If I Knew It, I Knew
You is #1 on the Billboard Hot 100 chart for the Week of Aug 15, 2026"*
(`KXTOPSONG-26AUG15-IKN`). **Live check:** 6 song pairs and 14 album pairs, both
directions, **0 violations** — but every one of them is untradeable, because the
`KXBBCHARTPOSITION*` side has no bid and asks at 0.97 (see Liquidity). The equivalence is
real; the arbitrage is not.

### C5 — Rank exclusivity across sibling series (exact)

A subject cannot occupy two distinct ranks on the same chart:
**`Σ_r P(subject at rank r) ≤ 1`** over the sibling series `#1` / `#2` / `#3`.

Executable: sell every leg (buy NO on each at `1 − yes_bid`); the package pays ≥ `n − 1`
because at most one can settle Yes, so it is a lock iff
`Σ yes_bid(leg) − 1 > Σ taker(1 − yes_bid(leg))`.

Basis: the rules differ only in the rank numeral — *"If Golden is the **#1** most streamed
Song on Spotify's 2026 Spotify Wrapped Top 10 Songs Globally chart…"* vs *"… the **#2**
most streamed Song…"* on the same chart and release date.

Failure mode: the global and USA twins (`KXTOPSONGSPOTIFY` vs `KXTOPSONGSPOTIFYUSA`) are
**different charts** and carry no exclusivity between them; the same is true of Netflix
US vs Global.

**Live check.** 14 sibling groups (Spotify song/album/artist global and USA, Billboard 200
and Hot 100 #1/#2 for two chart weeks, Netflix show/movie US and Global, Google Year in
Search person #1/#2). **0 violations.** Highest observed sum is 0.99 (several: `Choosin'
Texas` Hot 100 Aug-08, `A Toxic Love Story` Netflix), which after the sell-side fee is
net **−1.07¢**.

### C6 — Mention leg ⊥ "Event does not qualify" (exact)

In the 6 event-scoped Mentions events that carry an `NQE` leg, a word leg and the NQE leg
cannot both settle Yes: **`P(word_i) + P(NQE) ≤ 1`** for every `i`.

Basis, quoted verbatim from `rules_secondary` on both legs:
> *"If an event is definitively cancelled or the event fails to qualify under the Payout
> Criterion, or any other circumstance prevents normal resolution, then the market for
> "Event does not qualify" resolves to Yes and **all other markets will resolve to No**."*

Executable: buy NO on both legs, cost `no_ask(word) + no_ask(NQE)`, payoff ≥ $1. In this
slice `no_ask ≡ 1 − yes_bid` holds **exactly on all 7,772 markets** (0 exceptions), so the
test is `yes_bid(word) + yes_bid(NQE) > 1 + taker(1−yes_bid(word)) + taker(1−yes_bid(NQE))`.

Note this is only a pairwise exclusion. `NQE = No` does **not** imply any listed word was
said, so there is no sum-to-one over the event.

**Live check.** 6 events with an NQE leg (`KXFEDMENTION-26SEP`, `KXHEARINGMENTION-26AUG04`,
`KXTALARICOMENTION-26AUG03`, `KXDEBATEMENTION-26AUG03` and `-26AUG03B`,
`KXFOXNEWSMENTION-26AUG02`), 119 word legs. **0 violations.** Worst case
`KXFOXNEWSMENTION-26AUG02`: `DEMO` ("Democrat / Democratic Party") bid 0.93 + NQE bid 0.01
= **0.94**. The other 52 Mentions events have no NQE leg at all — 47 of them are
`KXEARNINGSMENTION*`, where a cancelled earnings call has no explicit escape hatch.

### C7 — Mention window containment (exact when it holds; usually it does not)

If phrase `p` appears in two Trump events whose windows nest, `W_a ⊆ W_b` ⇒
**`P(a) ≤ P(b)`**.

Windows, taken from `rules_primary` plus `open_time` (the start bound is only implicit;
`rules_secondary` states it conditionally — *"If the word must be said a minimum number of
times, all instances must occur after market issuance"*):

| event | window |
|---|---|
| `KXTRUMPSAY-26AUG03` | Jul 27 08:00 ET → Aug 3 00:00 ET |
| `KXTRUMPSAYMONTH-26SEP01` | Aug 1 00:00 ET → Sep 1 00:00 ET |
| `KXTRUMPSAYCOMPANY-26SEP01` | Aug 1 00:00 ET → Sep 1 00:00 ET |
| `KXTRUMPSAYNICKNAME-26OCT01` | Jul 1 00:00 ET → Oct 1 00:00 ET |

Only the nickname window contains the others. **The weekly window straddles the month
boundary and is therefore NOT a subset of the monthly window**, despite the 10 shared
phrases (`antifa`, `moon`, `peace in the middle east`, `newscum`, `barack hussein obama`,
`where are you from / who are you with`, `mamdani / zohran`, `uap / ufo`, …). Encoding
"week ⊆ month" would create ten false constraints.

Valid pairs: weekly ⇒ nickname and monthly ⇒ nickname, on the two shared phrases
`barack hussein obama` and `newscum` — **4 candidate implications**.

**Live check: all 4 are currently degenerate.** `KXTRUMPSAYNICKNAME-26OCT01-BARA` and
`-NEWS` are both **finalized with `result = yes`** (the event closed early on 2026-07-27
when the phrases were uttered), so the general leg quotes `0.00 / 1.00` and carries no
constraint. `KXTRUMPSAY-26AUG03-NEWS` is still active at 0.05/0.06 while its superset has
already settled Yes — consistent, and a clean illustration of why finalized legs must be
excluded before any implication is evaluated.

### C8 — Pure album sales ⊆ album-equivalent units (definitional, needs-rule-check)

For the same album and the same Luminate tracking week and the same strike `L`:
`Pure Album Sales > L` ⇒ `Album Equivalent Units > L`, therefore
**`P(KXPUREALBUMS-…-L) ≤ P(KXALBUMEQUIV-…-L)`**.

Basis: Luminate's album-equivalent unit is pure album sales **plus** track-equivalent and
stream-equivalent albums, so AEU ≥ pure sales identically. The contracts state the two
metrics — *"has above 5K **Pure Album Sales (aka Product Sales)** during the … tracking
week"* vs *"has above 5K **Album Equivalent Units** during the … tracking week"* — but
**neither contract states the containment**; it comes from Luminate's definition. Mark it
`needs-rule-check` in any scanner, not `exact`.

Failure modes: the two events must share the album code *and* the week code
(`KXPUREALBUMS-WILD26AUG20` ↔ `KXALBUMEQUIV-WILD26AUG20`; note `KXALBUMEQUIV` has an extra
`-WILD26AUG20B` event with no pure-sales twin); strike ladders only partially overlap.

**Live check.** 9 albums with both events, **52 shared-strike pairs, 0 violations**.
Tightest: `THI26AUG13` at 475K and 500K, pure bid 0.00 vs AEU ask 0.01, net −1.07¢; the
tightest with real size is `THI26AUG13-150K`, pure bid 0.92 (size 22) vs AEU ask 0.96
(size 26), gross −4.00¢, net **−4.78¢**.

### C9 — Mutually exclusive menus: `Σ P ≤ 1`, and *only* `≤`

131 events carry `mutually_exclusive = True` (`collateral_return_type = MECNET`). The
short-side constraint `Σ yes_bid ≤ 1` is sound. The **long-side constraint `Σ yes_ask ≥ 1`
is not available**, because these menus are almost never collectively exhaustive.

Basis for non-exhaustiveness, quoted from `KXGOOGLESEARCH-TVS27` and its siblings:
> *"If Google's Year in Search 2026 Global - Tv Shows is not published during 2026, then
> all markets will resolve to NO."*

and structurally: `KXOSCARPIC-27` lists 38 films for a Best Picture race with no cap on
who may be nominated; `KXNETFLIXRANKSHOWGLOBAL-26AUG03` lists 11 titles against Netflix's
entire catalog.

**Live check.** 129 mutex events with ≥2 active priced legs. **Short side: 0 net-positive**
(only 2 events even reach `Σ yes_bid > 1` — `KXMOSTWINSEMMYS-26B` at 1.030 and
`KXOSCARSUPACTR-27` at 1.010; after 10 and 14 legs of sell-side fees these are −1.41¢ and
−4.14¢, and the minimum bid depth is 0 contracts in both). **Long side: 8 events have
`Σ yes_ask + fees < 1`**, headed by `KXNETFLIXRANKSHOWGLOBAL-26AUG03` (Σ ask **0.150**,
net +**$0.84**, 1,138 contracts of depth) and `KXTOPALBUM-26AUG15` (Σ ask 0.150, net
+$0.84, 4,719 depth). **None of these is a lock** — they are the market correctly pricing
that the winner is probably not on the board. Buying all 11 Netflix legs for 15¢ pays
nothing unless one of those 11 specific titles is #1 globally.

### C10 — Count partitions: one tiled, one holed

`KXTOP10BBSPOTS-26AUG15-ARI` (`Exactly 0 songs` … `Exactly 10 songs`, `mutually_exclusive
= True`) **is** collectively exhaustive — an artist's song count in a ten-slot chart is an
integer in [0, 10] — so both `Σ P = 1` directions bind. **Live check:** Σ ask = 1.350
(buy-all net **−39.5¢**), Σ bid = 0.700 (sell-all net −33.2¢). Consistent.

`KXEMMYCOUNT` is **not**: all six events start at `Exactly 1` (ranges 1–13 through 1–25)
with **no `Exactly 0` leg**. Winning zero Emmys pays nothing, so buy-all-YES is not a lock
even though the flag is `mutually_exclusive = True`. **Live check:** Σ ask ranges 1.070
(`-26PIT`) to 1.500 (`-26HAC`); the closest to a false signal is `KXEMMYCOUNT-26PIT` at
1.070, still above 1.

Derived (weak): `P(show X wins category C) ≤ P(1 ≤ count_X ≤ max)`, so
`yes_bid(win) > Σ yes_ask(count legs)` would be a lock. Live: The Pitt win-bid 0.85 vs
count Σ ask 1.070 (net −29.6¢); Hacks 0.40 vs 1.500; Beef 0.39 vs 1.350. All far from
binding, and the top of the count ladder is not rule-guaranteed, so this stays
`needs-rule-check`.

### C11 — Nominee-slate cardinality (external rule — flag, do not trust)

The Academy nominates exactly 10 for Best Picture and exactly 5 in each acting and
directing category. If that holds, at most `K` of the listed legs can settle Yes, so
selling the entire slate pays ≥ `n − K`: a lock iff
`Σ yes_bid − K > Σ taker(1 − yes_bid)`.

**No clause in `rules_primary` or `rules_secondary` states the slate size.** The
cardinality is external knowledge, and a scanner that encodes it is trusting the Academy's
rulebook, not the contract.

**Live check** (active legs only):

| event | legs | K | Σ yes_bid | fees | net | min bid depth |
|---|---:|---:|---:|---:|---:|---:|
| `KXOSCARNOMDIR-27` | 23 | 5 | 5.580 | 0.183 | **+$0.397** | 1 |
| `KXOSCARNOMACTO-27` | 28 | 5 | 5.430 | 0.181 | **+$0.249** | 1 |
| `KXOSCARNOMPIC-27` | 43 | 10 | 10.300 | 0.326 | −$0.026 | 1 |
| `KXOSCARNOMSUPACTO-27` | 22 | 5 | 5.010 | 0.209 | −$0.199 | 1 |
| `KXOSCARNOMACTR-27` | 22 | 5 | 4.680 | 0.196 | −$0.516 | 5 |

Two slates price above their cardinality by more than fees. Both are capped at **1
contract** of bid depth and require crossing 22–27 books simultaneously, so the realizable
edge is well under a dollar. Report as a structural inconsistency, not a trade.

### Relations that are correlation only — explicitly excluded

`KXRT` (Tomatometer) vs `KXMC` (Metascore) on the same title; `KXARTISTSTREAMSY` vs
`KX1SONG`/`KX10SONG` for the same artist; `KXALBUMEQUIV` vs `KXTOPALBUM` for the same
album; `KXTOP10BBSPOTS` (Ariana Grande song count) vs individual `KXRANKLISTSONGTOP10`
legs (the artist→song mapping is not in metadata). None of these are settlement
constraints and none belong in a scanner.

---

## Traps

1. **`mutually_exclusive = True` almost never means exhaustive here.** 131 mutex events;
   the only genuinely collectively-exhaustive one found is `KXTOP10BBSPOTS-26AUG15-ARI`.
   The rest are open-universe menus with an explicit escape clause (*"then all markets will
   resolve to NO"*). Eight events currently show `Σ yes_ask + fees < 1` and would be
   flagged as buy-all-YES locks by a naive scanner; the best of them,
   `KXNETFLIXRANKSHOWGLOBAL-26AUG03` at `Σ ask = 0.150`, is simply the market saying the
   #1 Netflix show globally is probably none of the 11 listed titles.

2. **`KXEMMYCOUNT` has no `Exactly 0` leg.** Ranges are 1–13 through 1–25. The zero-win
   outcome is unlisted, so the partition has a hole at the bottom and buy-all-YES is not a
   lock. Check the count range structurally, never infer it from `mutually_exclusive`.

3. **Weekly windows straddle month boundaries.** `KXTRUMPSAY-26AUG03` covers
   Jul 27 – Aug 3 and is *not* inside `KXTRUMPSAYMONTH-26SEP01` (Aug 1 – Sep 1), despite
   10 shared phrases. Identically, `KXYTVIEWSW-*26AUG02` measures Jul 27 – Aug 2 while
   `KXYTVIEWSHIGH-*26SEP` measures all of August: same artist, same metric, same "Above X"
   subtitles, **no implication in either direction**. Compare parsed windows, never ticker
   dates.

4. **Ticker dates are not measurement dates.** `KXYTVIEWSHIGH-TAY26SEP` measures August
   2026. `KXEARNINGSMENTIONNVDA-26AUG26` settles on the Aug 26 call but carries
   `expiration_time = 2026-12-31`. Event-scoped Mentions markets all carry a far-future
   backstop expiry; horizon and carry calculations from `expiration_time` will be wrong by
   months.

5. **Finalized legs sit inside open events and are the norm, not the exception.** 369
   Entertainment and 26 Mentions markets. In Emmy winner events, five to nine legs are
   already `finalized / result = no` (the non-nominees) while the event trades on. In
   Mentions, **every finalized market in the snapshot resolved `yes`** — early close fires
   when the phrase is uttered — which is exactly how all four Trump window implications
   became degenerate (`KXTRUMPSAYNICKNAME-26OCT01-BARA` and `-NEWS` settled Yes on
   2026-07-27). A finalized leg quotes `0.00 / 1.00`; feeding that into a spread produces
   a fake 100¢ edge.

6. **Join awards markets on the ticker suffix, not the display name.** `KXOSCARNOMDIR-27`
   says "Phil Lord"; `KXOSCARDIR-27` says "Phil Lord & Christopher Miller". Best Actor has
   "Jaafar Jackson" on one board and "Jafar Jackson" on the other. Across the 8 series
   pairs, suffix join recovers **190** winner/nominee pairs and normalised-name join
   recovers **189** — but not a subset of the same 190: name join loses the two Best
   Director legs whose names disagree while picking up legs the suffix join misses
   (`KXOSCARNOMDIR-27`: 13 by suffix, 11 by name; `KXOSCARSUPACTO-27`: 20 by suffix, 21 by
   name). Join on the suffix, then verify the names rather than the reverse.

7. **Winner boards carry a `-TIE` leg; nominee boards do not.** Any leg-count or
   partition logic that assumes parallel boards will be off by one.

8. **Mentions leg codes are lossy.** The 4-character code is derived from the canonical
   term in a slash-list, not the leading text (`-GASO` = "Gas / Gasoline / Fuel", `-ARTI` =
   "AI / Artificial Intelligence"), and collides-then-extends (`-GOOD` = "Good Afternoon",
   `-GOODS` = "Goods inflation"). 23 of 983 codes do not match the subtitle prefix. Parse
   `yes_sub_title`; split slash-lists into alternatives (*"For phrases with slashes like
   "Doge/Dogecoin," either word satisfies the criterion"*); strip the `(N+ times)`
   qualifier before matching phrases across events.

9. **Rule-text asymmetry can void an apparent nesting.** `KX10SONG` says *"(including
   features)"* and adds *"Features are encompassed by the Payout Criterion as long as they
   are credited by Billboard"*; `KX20SONG` says *"top 20 single"* with no features clause
   at all. The apparent `top 10 ⇒ top 20` implication is the one place in this slice where
   a net-positive number shows up (SZA, +2.52¢), and it is most plausibly the rule
   difference being priced. Diff the rule strings before promoting an implication to
   `exact`.

10. **Chart identity matters more than chart name.** Spotify global vs USA
    (`KXTOPSONGSPOTIFY` vs `KXTOPSONGSPOTIFYUSA`), Netflix US vs Global, Billboard 200 vs
    Hot 100 — same subject codes, same leg labels, different underlying. No exclusivity or
    equivalence crosses these boundaries.

11. **Placeholder books.** 231 Entertainment markets quote exactly `0.00 / 0.97`; the whole
    of `KXBBCHARTPOSITIONALBUM` (280 markets, 171 total OI) is two-sided on 0% of legs. A
    ten-leg mutex event whose asks sum to 9.60 is not a market. Require both a bid and a
    non-placeholder ask before evaluating any constraint.

12. **`taxonomy.classify_event` misfires on 15 Entertainment events.** All 15 return
    `TEMPLATE_COMBINATION` because the `\band\b` test fires on *work titles*, not on
    conjunctions: "Beauty and a Beat" (`KXTOPSONGSPOTIFY-26`, `KXTOPSONGTHIRD-26`,
    `KXTOPSONGSPOTIFYRUNNERUP-26`, `KXMUSICREPORT-TOPSTREAM27DEC31` and three siblings),
    "Sense and Sensibility" (`KXOSCARPIC-27`), "HIT ME HARD AND SOFT", "The Rise and Fall
    of a Midwest Princess", "Star Wars: The Mandalorian and Grogu". **Every one of the 15
    is an `entity_menu`; there are no combination contracts in this slice.** The `and`
    heuristic needs to require the conjunction to join two parsable propositions, or be
    gated on `strike_type`.

13. **`taxonomy.parse_threshold` does not parse count legs.** `Exactly N` (**128 markets**,
    all in `KXEMMYCOUNT` and `KXTOP10BBSPOTS`) and `More than N [weeks]` (**35 markets**,
    in `KXTOPALBUMRECORD`, `KXTOPALBUMRECORDOR`, `KXTOPALBUMRECORDSWAG`, `KXTOPSONGS`)
    return `None`, so
    `partition_is_tiled` returns `False` for **all 498** Entertainment events — including
    the one genuinely tiled partition, `KXTOP10BBSPOTS-26AUG15-ARI`. Count partitions need
    their own parser: `Exactly <n>[ songs]` → `(n, n)`, `More than <n> weeks` → `(n, ∞)`.

14. **`liquidity_dollars` is identically 0** on all 7,362 active markets here. Size must
    come from `yes_bid_size_fp` / `yes_ask_size_fp`.

15. **`no_ask ≡ 1 − yes_bid` holds exactly** on all 7,772 markets in this slice (0
    exceptions), so short-side packages can be priced off `yes_bid` — but that is an
    observation about this snapshot's book construction, not a guarantee; verify before
    relying on it elsewhere.

---

## Open questions

- **Emmy count ceilings.** Is `KXEMMYCOUNT`'s top leg (`Exactly 25` for The Pitt) a
  contractual cap or just where the ladder happened to stop? Without that, the
  `win ⇒ count ≥ 1` relation in C10 cannot be closed, because `count > max` is unpriced.
- **Nominee slate sizes.** Nothing in the contract text fixes 10 Best Picture / 5 acting
  nominees, and the Grammy AOTY field has varied between 8 and 10 across recent years. C11
  is only as good as external rulebook knowledge; the metadata cannot confirm it.
- **Non-qualifying earnings calls.** 47 `KXEARNINGSMENTION*` events have **no** `NQE` leg.
  If a call is cancelled or delayed past `expiration_time`, `rules_primary` ("the next …
  earnings call") does not say whether the markets void, roll to the rescheduled call, or
  settle No. The `KXDEBATEMENTION` postponement clause (*"rescheduled to a time within 14
  calendar days, the markets shall remain open"*) has no analogue in the earnings series.
- **Calendar-window start bounds.** `KXTRUMPSAYMONTH` / `KXTRUMPSAYNICKNAME` /
  `KXTRUMPSAYCOMPANY` state only an end bound in `rules_primary` ("before Sep 1, 2026 at
  12:00am ET"); the start is inferable from `open_time` and from a conditional clause in
  `rules_secondary` that only speaks to multi-count markets. The containment argument in
  C7 survives either reading, but a general window-nesting extractor needs the start bound
  stated, not inferred.
- **Whose "features" count.** `KX1SONG` and `KX10SONG` include features; `KX20SONG` and
  `KX1ALBUM` are silent. Whether the silence means "lead credit only" or "same as the
  others" decides whether C3's second link is a constraint or noise.
- **`KXALBUMDEBUT` vs `KXTOPALBUM`.** `KXALBUMDEBUT-26OCT17-FRE` reads *"If Frequency Of
  Love is the #1 album on the Billboard 200 chart for the week of October 17, 2026"* — the
  word "debut" appears only in the title, not the rule. If a `KXTOPALBUM` event is ever
  listed for the same week, the two are equivalent; in this snapshot the weeks do not
  overlap, so it could not be tested.
- **Entity identity across events.** `KXTOP10BBSPOTS` prices Ariana Grande's song count in
  the Hot 100 top 10 while `KXRANKLISTSONGTOP10` prices individual songs; the artist→song
  mapping exists in neither `custom_strike` (an opaque UUID) nor the subtitles, so the
  obvious cross-constraint cannot be built from metadata.
- **Why `KXARTISTSTREAMSY` is excluded from `DIRECNET`.** 61 of 133 ladders get
  directional collateral netting; the largest ladder family in the category (1,298 markets)
  does not. Whether this is an oversight or a deliberate risk decision changes the capital
  cost of every streams spread by roughly a factor of two.
