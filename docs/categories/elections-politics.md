# Elections & Politics

Snapshot **2026-08-02T20:52Z**. Shards: `by_category/Elections.jsonl.gz`, `by_category/Politics.jsonl.gz`.

Fee model used throughout: taker = `fee_multiplier * 0.07 * P * (1-P)` per contract per leg, rounded **up** to
a centicent ($0.0001); maker = 0 (no series in this slice is `quadratic_with_maker_fees`); no settlement fee.

Every price below is an **executable side**: to sell a leg you hit its `yes_bid_dollars`, to buy you lift its
`yes_ask_dollars`. Sizes are `yes_bid_size_fp` / `yes_ask_size_fp` at the touch only. Every "net" figure is
after both legs' taker fees.

---

## Inventory — how much of the exchange this is

| | Elections | Politics | slice | exchange | share |
|---|---|---|---|---|---|
| events | 2,226 | 493 | **2,719** | 8,478 | **32.1%** |
| markets | 11,476 | 2,170 | **13,646** | 73,964 | **18.4%** |

- Active markets **13,351** (97.8%). Non-active: 274 `finalized`, 20 `inactive`, 1 `closed`.
  **134 open events carry at least one dead leg** (295 dead legs total).
- **1,078 distinct series** — the most series-fragmented slice in this snapshot — but extremely concentrated:
  the top 5 series hold **56.6%** of the markets, the top 20 hold 61.9%. **1,014 of 1,078 series (94%) have
  exactly one event**; 770 have ≤5 markets.
- Every market is `market_type = binary`, `notional_value_dollars = 1.0000`.
- `liquidity_dollars` is **0.0000 on all 13,351 active markets**. The field is unusable here; depth must come
  from `yes_bid_size_fp` / `yes_ask_size_fp`.

Structural composition (by markets):

| bucket | events | markets | share |
|---|---|---|---|
| A. midterm margin ladders (`KXMIDTERMMOV`) | 522 | 3,939 | 28.9% |
| B. midterm turnout ladders (`KXMIDTERMVOTETURN`) | 502 | 2,756 | 20.2% |
| C. party-winner books (`KXHOUSERACE`, `HOUSE{ST}{N}`, `SENATE{ST}`, `GOVPARTY{ST}`) | 542 | 1,095 | 8.0% |
| D. chamber control / seat counts / 2×2 combos | 26 | 145 | 1.1% |
| E. primaries & nominations | 177 | 821 | 6.0% |
| F. presidential 2028 & Trump-personal | 57 | 739 | 5.4% |
| G. long tail (foreign elections, legislation, appointments, geopolitics) | 893 | 4,151 | 30.4% |

Category labels are unreliable: **51 events** sit in a series whose `series.category` disagrees with
`event.category` (22 Politics-series events labelled Elections, 14 the reverse, plus leakage from Economics,
Science and Technology, Entertainment, World, Financials). Group by **series ticker grammar**, never by
category.

---

## Series families

### A. `KXMIDTERMMOV` — margin-of-victory ladders (522 events / 3,939 markets, 28.9%)

Nested one-sided ladders on the 2026 midterm margin, one event per (race × party).

- **Ticker grammar** `KXMIDTERMMOV-{ST}{OFFICE}{PARTY}-P{LEVEL}`. `{ST}` = 2-letter state;
  `{OFFICE}` ∈ {`SEN`, `GOV`, `AL` (at-large CD), `NN` (zero-padded district)}; `{PARTY}` ∈ {`R`,`D`};
  `P{LEVEL}` = integer percentage points. **All 522 event tickers parse with
  `^KXMIDTERMMOV-([A-Z]{2})(AL|\d{2}|SEN|GOV)([RD])$` — zero exceptions.**
  Office mix: 432 districts, 43 GOV, 42 SEN, 5 at-large. Party mix: 264 R / 258 D. 372 distinct House seats.
- **Leg grammar** `yes_sub_title = "{Party}, {N}+ pts"`, `strike_type = greater_or_equal`. Modal 9 legs/event
  (317 events). Rung spacing 3 pts (3,108 adjacent pairs) or 2 pts (309).
- **No ladder has a 0-pt rung.** Lowest-rung distribution: 3 pts (80 events), 2 pts (77), 1 pt (75), tail to
  46 pts. Even the bottom rung is a *strict* subset of "party wins the seat".
- Fee `quadratic` ×1, frequency `one_off`. Settlement source is the unfilled template
  *"official election authority responsible for certifying results in "*.

### B. `KXMIDTERMVOTETURN` — turnout ladders (502 events / 2,756 markets, 20.2%)

- **Ticker grammar** `KXMIDTERMVOTETURN-{ST}{OFFICE}-{RAWVOTES}` — the strike suffix is the literal vote
  count (`KXMIDTERMVOTETURN-WYSEN-220000`).
- **Leg grammar** `"Above {N}K"`, `strike_type = greater` (**strict**, unlike `KXMIDTERMMOV`).
  Modal 5 legs (420 events), then 8 (78). `mutually_exclusive = false` on all 502 — correct for a ladder.
- Fee `quadratic` ×1, `one_off`.

### C. Party-winner books — four parallel families over one map

| family | series | events | markets | leg suffixes |
|---|---|---|---|---|
| `KXHOUSERACE` (one series, one event per seat) | 1 | 350 | 704 | `-D`, `-R` (+4 independents) |
| `HOUSE{ST}{N}` / `KXHOUSE{ST}{N}` (one series per seat) | 75 | 75 | 150 | `-D`,`-R`; **`KXHOUSENC11-26` uses `-DEM`/`-GOP`** |
| `SENATE{ST}` / `KXSENATE{ST}` / `SENATE{ST}S` | 50 | 66 | 136 | `-D`,`-R` (+4 independents) |
| `GOVPARTY{ST}` / `KXGOVPARTY{ST}` | 48 | 49 | 101 | `-D`,`-R` (+3 independents) |

- **The two House families are disjoint.** `KXHOUSERACE-{ST}{NN}-26` covers 350 districts;
  `HOUSE{ST}{N}-26` / `KXHOUSE{ST}{N}-26` covers a **different** 75. Intersection is empty; union is 425 of
  435 seats. The per-seat family holds the competitive districts (AZ-01/02/06, CA-13/21/22/27/41/45, NC-11,
  NH-01, TX-28/34/35, …). A scanner keyed only on `KXHOUSERACE` drops 63 of the 372 seats that have a margin
  ladder.
- **Zero-padding is inconsistent**: `KXHOUSERACE-AZ05-26` pads, `HOUSEAZ1-26` and `KXHOUSEMO5-26` do not,
  `KXHOUSEUT03-26` does. Normalise through `int()`.
- **Ticker year ≠ election year.** `GOVPARTYKS-27` (`sub_title` "In 2027") and `GOVPARTYNH-28`
  (`sub_title` "In 2026") both settle *"pursuant to the **2026** election"*. `SENATE{ST}-26` means the term
  beginning **2027**. The year token is not a reliable key.
- **The state token can name the wrong state.** `SENATELA-26` is titled *"Kentucky Senate winner?"* and
  resolves *"…sworn in as a Senator of **Kentucky** for the term beginning in 2027"*, legs Andy Barr /
  Charles Booker. Louisiana 2026 is `KXSENATELA-26NOV`; `SENATELA-28` really is Louisiana. Senate specials
  append `S` (`SENATEOHS-26`, the only Ohio 2026 Senate book).
- Settlement sources differ by family: `KXHOUSERACE` and `HOUSE{ST}{N}` → *Library of Congress*;
  `SENATE{ST}` → *United States Congress*; `GOVPARTY{ST}` → *US State Governments*.
- All `quadratic` ×1.

### D. Control / seat-count / combination books (26 events / 145 markets — 1.1% of markets, the deepest books)

- `CONTROLH-{YYYY}`, `CONTROLS-{YYYY}` — 2-leg D/R chamber control, 2026 and 2028. `CONTROLH-2026-R` alone
  carries **7,219,321 contracts of open interest**, the largest single book in the slice.
- `KXBALANCEPOWERCOMBO-27FEB` — 2×2, legs `-DD`,`-DR`,`-RD`,`-RR` (House first, Senate second).
- `KXDHOUSESEATS-27` / `KXRHOUSESEATS-27` — mutex bucket partitions of the post-midterm seat count; the leg
  suffix is the bucket's upper edge except the open tails (`210` = "Below 210", `249` = "Above 249").
- `KXDHOUSESEATSDIR-27` — a *nested* `"Above N"` ladder over the same variable, `mutually_exclusive = false`.
- `KXDSENATESEATS-27` (`BELOW45`,`45`…`52`,`ABOVE52`) and `KXDSENATESEATSH-27`
  (`B53`,`E53`…`E57`,`A57`) — **two different partitions of the same variable on the same date**; plus
  `KXDSENATESEATS-29` for 2028 (`B45`,`E45`…`E56`,`A56`).
- `KXHOUSEWINSTATE-{ST}D` — per-state count of D House seats (`E0`,`E1`,`E2`,`A2`; Florida uses
  `B4`,`4`…`10`,`A10`).
- `KX{ST}SENGOVCOMBO-26NOV` — 9 states (AK, GA, IA, KS, ME, MI, MN, NH, OH), legs `-DEMDEM`, `-DEMREP`,
  `-REPDEM`, `-REPREP` (governor first, senator second).
- Cross-state "sweep" conjunctions: `KXDEMCOREFOURSENATESWEEP-26NOV03`, `KXDEMSWINGSTATEGOVSWEEP-26NOV03`,
  `KXPROGSWEEP-26NOV03`, `KXDEMPROGRESSIVESENATESWEEP-26NOV03`, `KXDEMSENATEPRIMARYCOMBO-26NOV03`
  (this last one is an "at least 5 of 6" market, not a conjunction).

### E. Primaries & nominations (177 events / 821 markets)

- **State primary books** `KX{ST}PRIMARY-{NN}{PARTY}{YY}` (`KXFLPRIMARY-06R26`, `KXLAPRIMARY-01D26`) —
  19 series, 155 events, 647 markets; `KXFLPRIMARY` alone is 44 events / 221 markets. Legs are per-candidate
  (`-SSCA` = Steve Scalise). Settlement sources are the party organisations.
- **Derivative series that embed their parent event in the ticker**:
  - `KXPRIMARYMOV-{PARENT}` — **two incompatible leg grammars in one series**: a nested
    `"{Candidate}, ≥N%"` ladder with `greater_or_equal` and `mutually_exclusive=false`
    (`KXPRIMARYMOV-SENATENHR26`), *and* a 2-D candidate × margin-bucket partition `"{Candidate}, a-b%"`
    with `strike_type=custom` and `mutually_exclusive=true` (`KXPRIMARYMOV-SENATEMAD26` = 6 buckets ×
    2 candidates = 12 legs, where **the strike suffix repeats across candidates** — `-P2` appears twice in
    the same event).
  - `KXPRIMARYPLACE-{PARENT}-{K}` — K-th place finisher. K is written `-1`, `-2`, `-4`, `-3RD`.
  - `KXVOTEPRIMARY-{PARENT}{CAND}` — a candidate's vote share as a nested `"At least N%"` ladder. The
    candidate code is sometimes **doubled** (`…BDONBDON`, `…DJSULDJSUL`), sometimes not (`…JFIS`).

### F. Presidential 2028 & Trump-personal (57 events / 739 markets)

`KXPRESNOMD-28` (46 legs, 113 M OI), `KXPRESNOMR-28` (38), `KXPRESPERSON-28` (30),
`KXVPRESNOMD/R-28`, `KXDTICKET`/`KXRTICKET-28NOV07` (25 each), `KXPRESMATCHUP-28NOV07`,
`KX2028DRUN`/`KX2028RRUN`, `KXDECLAREPRESFIRSTD`, and 42 `KXTRUMP*` series (`KXTRUMPRESIGN`,
`KXTRUMPREMOVE`, `KXTRUMPOUT27`, `KXTRUMPPARDON(S)`, `KXTRUMPADMINLEAVE`, …).

### G. Long tail (893 events / 4,151 markets)

Foreign elections (`KXFRENCHPRES`, `KXNEXTROMANIAPM`, `KXISRAELPM`, `KXBRPRES*`, `KXUKCOALITION`,
`KXTHEGAMBIAPRES`, `KXMONGOLIAPRES`, `KXPRESTURKEYR1`, …), legislation (`KXBILLS`, `KXSAVEACT`,
`KXGAMBLINGREPEAL`), appointments and courts (`KXNEXTAG`, `KXNEXTDEF`, `KXNEXTLABORSEC`, `KXFEDGOVNOM`,
`KXSCOTUSCASE`, `KXSCOURT`), geopolitics (`KXHORMUZ*`, `KXGREENLAND*`, `KXGREENTERRITORY`,
`KXUSAEXPANDTERRITORY`, `KXCANTERRITORY`, `KXSTATE51`), and oddities (`KXNEWPOPE`, `KXNOBELPEACE`,
`KXCITRINI`).

### Fees

| fee_type | multiplier | markets |
|---|---|---|
| `quadratic` | 1 | 13,635 |
| `quadratic` | **0** (free both sides) | 11 |

Zero-fee series in this slice: `KXGREENLAND` (3 markets), `KXELECTIRAN` (2), `KXGAMBLINGREPEAL` (2),
`KXCITRINI` (1), `KXDOED` (1), `KXIRANDEMOCRACY` (1), `KXPAHLAVIHEAD` (1). `KXGREENLAND` being free matters:
it sits at one end of the territory implication chain (§C6), so that leg costs nothing to trade while the
structurally adjacent `KXGREENTERRITORY` and `KXUSAEXPANDTERRITORY` are full-fee. **No series in this slice
charges maker fees.**

Series frequency: `one_off` 757, `custom` 281, `annual` 27, `monthly` 7, `weekly` 6.

---

## Contract templates

`classify_event()` over the 2,719 events: `entity_menu` 1,173 · `threshold` 1,077 · `binary` 322 ·
`deadline` 122 · `combination` 17 · `bucket` 8.

**1. Threshold ladder (nested, `mutually_exclusive=false`)** — 1,077 events, dominated by `KXMIDTERMMOV`
(522) and `KXMIDTERMVOTETURN` (502).

> `KXMIDTERMMOV-WYSENR-P26`: *"If the Republican Party wins the 2026 U.S. Senate election in Wyoming by 26
> percentage points or more, then the market resolves to Yes."*
> `rules_secondary`: *"…the vote percentage received by the Democratic Party minus the vote percentage
> received by the candidate/party/option that finishes immediately behind … Each margin range is inclusive
> of its lower bound and exclusive of its upper bound. **No rounding shall be applied to the calculated
> margin.**"*

**2. Entity menu (`mutually_exclusive=true`, rarely exhaustive)** — 1,173 events.

> `KXHOUSERACE-WYAL-26-D`: *"If the House member **sworn in** for WY-AL for the term beginning in 2027 is a
> member of the Democratic Party, then the market resolves to Yes."*
> `SENATEAK-28-D`: *"If a representative of the Democratic party is **sworn in** as a Senator of Alaska for
> the term beginning in 2029…"*
> `GOVPARTYAZ-26-D`: *"If a representative of the Democratic party is **inaugurated** as the governor of
> Arizona pursuant to the 2026 election…"*

**3. Combination (conjunction, `mutually_exclusive=true`)** — 17 events.

> `KXOHSENGOVCOMBO-26NOV-DEMDEM`: *"If ALL of the following occur: Ohio Governor winner: Democratic party,
> Ohio Senate winner: Democratic party, then the market resolves to Yes."*
> `rules_secondary`: *"This is a combination market requiring ALL specified outcomes to occur … If ANY single
> component resolves to No or becomes impossible, the entire contract immediately resolves to No. Each
> component is resolved according to its corresponding Kalshi ruleset: **Ohio Governor winner (GOVPARTY),
> Ohio Senate winner (SENATEPARTY)**."* — note it names *families*, not tickers.

**4. Bucket partition (`mutually_exclusive=true`)** — seat-count books and `KXGREENLANDPRICE`.

> `KXDHOUSESEATS-27-210`: *"If the Democratic party has below 210 House seats on Feb 1, 2027, then the market
> resolves to Yes."*

**5. Deadline ladder (nested, `mutually_exclusive=false`)** — 122 events.

> `KXTRUMPOUT27-27-JAN2029`: *"If Donald Trump leaves office before January 20, 2029…"*
> `KXGREENTERRITORY-29`: *"If the United States acquires any part of Greenland before Jan 21, 2029…"*

**6. Binary** — 322 single-leg events (`KXTRUMPRESIGN`, `KXTRUMPREMOVE`, `KXGREENIND-27`, `KXCITRINI`, …).

`strike_type` over active markets: `greater_or_equal` 4,176 · `custom` 3,963 · `greater` 3,092 ·
`structured` 1,208 · null 630 · `between` 259 · `less` 22 · `less_or_equal` 1.

---

## Settlement

**Sources.** All 2,719 events carry at least one entry. Top by market count:

| source | markets |
|---|---|
| *"official election authority responsible for certifying results in "* (**unfilled template**) | 3,939 |
| *"the relevant election commission of the country in which  takes place"* (**unfilled template**) | 2,756 |
| WSJ / Washington Post / Politico / Reuters / NYT / CNN / Fox / AP / MSNBC (media panel) | ~1,080–1,230 each |
| Library of Congress | 1,200 |
| Democratic Party / Republican Party (nomination books) | 817 / 761 |

Two of the three largest sources are unfilled templates covering **6,695 markets (49% of the slice)**.
`settlement_sources` cannot be used as a grouping key here.

**Settlement timer.** `settlement_timer_seconds`: 1,800 s on 12,475 markets (93%), **14 s** on 397,
300 s on 395, 3,600 s on 74 (the `CONTROL*` books), plus a handful at 50,400 / 90,000 s. The 14-second timer
is concentrated in `HOUSE{ST}{N}` (150) and `GOVPARTY{ST}` (101).

**Early close — the House/Senate asymmetry (re-verified on this snapshot).**
`can_close_early = true` on 13,343 / 13,351 active markets; `early_close_condition` populated on 11,927 (89%).

| family | `early_close_condition` | media-consensus clause in `rules_secondary` | timer |
|---|---|---|---|
| `KXHOUSERACE` (704 legs) | **none — 0/704** | **704/704 (100%)** | 1,800 s |
| `HOUSE{ST}{N}` (150) | *"will close following the swearing in of the Representative for the seat in question"* — 150/150 | 98/150 (65%) | **14 s** |
| `SENATE{ST}` (136) | *"will close early following the swearing in of the Senator for the seat in question."* — 136/136 | **15/136 (11%)** | 1,800 s |
| `GOVPARTY{ST}` (101) | *"will close early following the first person to be sworn in as governor pursuant to the 2026 gubernatorial election"* — 101/101 | 11/101 (11%) | **14 s** |
| `KXMIDTERMMOV` (3,939) | *"will close and expire early if certified election results are published."* | n/a | 1,800 s |
| `KXMIDTERMVOTETURN` (2,756) | *"will close and expire early if the official vote count is certified."* | n/a | 1,800 s |
| `CONTROLH`/`CONTROLS` (8) | none | 8/8, *"may be determined early based on a consensus of media calls projecting control"* | 3,600 s |

So accelerated determination and swearing-in early close are **two independent switches**. `KXHOUSERACE`
carries media acceleration and no swearing-in close; `SENATE{ST}` carries the swearing-in close and almost
never carries media acceleration (11%), and the clause is inconsistent *within* an event (`GOVPARTYME-26`
has it on 1 of 3 legs). 1,190 active legs in the slice carry the *"eligible for accelerated determination
after a consensus of media organizations project the winner"* clause.

Consequence for any cross-family hedge: a `KXHOUSERACE` leg can settle election night on a media call, an
`HOUSE{ST}{N}` / `SENATE{ST}` leg waits for the swearing in (2027-01-03), and the `KXMIDTERMMOV` leg waits
for state certification (Nov–Dec 2026). A structurally riskless pair unwinds in three different weeks.

**Expiry horizon.** Days-to-close from the snapshot: p10 = 151, p25 = p50 = p75 = **457** (2027-11-03),
p90 = 729, max 26,456. Close years: 2027 (10,725 markets), 2026 (982), 2028 (749), 2029 (666), stragglers to
2099. Top close dates: **2027-11-03 (8,813)** — a one-year buffer past the 2026 midterm shared by
`KXMIDTERMMOV`, `KXMIDTERMVOTETURN` and all four party-winner families — then 2027-01-01 (804),
2026-11-03 (343), 2028-11-07 (295), 2029-01-20 (217). Only **363 markets close within 30 days**. `close_time`
is a backstop; the realised date is governed by `early_close_condition`.

`collateral_return_type`: `DIRECNET` 1,104 events, `MECNET` 1,103, empty 512. `strike_period` is empty on
2,715 of 2,719.

---

## Liquidity

Over 13,351 active markets:

| metric | p10 | p25 | p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|---|
| open interest | 0 | 0 | 85 | 1,283 | 6,212 | 19,642 | 553,860 | 7,219,321 |
| lifetime volume | 0 | 0 | 146 | 2,758 | 13,656 | 42,221 | 1,028,468 | 25,883,076 |
| 24 h volume | 0 | 0 | **0** | **0** | 20 | 303 | 3,977 | 480,243 |

- Total OI **325.5 M** contracts, lifetime volume **589.5 M**. But 24 h volume totals only **4.90 M** and is
  non-zero on just **1,867 of 13,351 markets (14%)**. Most of this slice does not print on a given day.
- **Two-sided** (`yes_bid > 0` and `yes_ask < 1`): **12,405 / 13,351 = 92.9%**.
- Spread on two-sided markets: p10 1.0¢, p25 2.2¢, **median 5.0¢**, p75 7.0¢, p95 8.0¢, max 94.8¢.
  1,748 markets quote ≤1¢, 3,028 ≤2¢, 7,449 ≤5¢.
- Min-side depth at the touch: p25 = 5, median 100, p90 = 250, p95 = 500. 7,080 markets show ≥100 contracts
  on both sides; only **272 show ≥1,000**.
- **Genuinely tradeable** (two-sided **and** spread ≤5¢ **and** ≥25 contracts on the thinner side):
  **4,759 / 13,351 = 35.6%**. The other ~64% is nominal — quoted but wide, one-tick deep, or one-sided.

Concentration by open interest:

| series | OI | share |
|---|---|---|
| `KXPRESNOMD` | 113,332,591 | 34.8% |
| `KXPRESPERSON` | 40,173,631 | 12.3% |
| `KXPRESNOMR` | 37,284,920 | 11.5% |
| `CONTROLH` | 12,082,400 | 3.7% |
| `KXGOVFLNOMR` | 9,328,422 | 2.9% |
| `KXMAYORLA` | 8,145,168 | 2.5% |
| `KXBALANCEPOWERCOMBO` | 5,583,972 | 1.7% |
| remaining 1,071 series | — | 30.6% |

Three 2028 presidential series hold **58.6% of all open interest** across 114 of 13,351 markets. Conversely
the two ladder families that dominate market *count* (`KXMIDTERMMOV` + `KXMIDTERMVOTETURN` = 6,695 markets,
49% of the slice) appear nowhere in the OI top 15 — they are wide 100-lot books. **Every constraint below
that involves a ladder leg is capacity-limited to roughly 100 contracts**, regardless of how large the
headline OI is.

---

## Structural constraints

Ten relations. For each: the price inequality, the rule clause that makes it exact, the failure modes, and a
live check on this snapshot.

---

### C1. Margin ladder ⊆ party winner — **VIOLATED**

**Relation.** For every `KXMIDTERMMOV-{ST}{OFF}{P}-P{N}` leg and the matching party-winner leg,

```
P(margin ≥ N pts for party P)  ≤  P(party P holds the seat)
```

executable form (sell the specific leg at its bid, buy the general leg at its ask):

```
yes_bid(KXMIDTERMMOV-…-P{N}) − yes_ask(<party-winner>-{P})
    − fee(yes_bid) − fee(yes_ask)   ≤  0
```

**Rule basis.** `KXMIDTERMMOV-WYSENR-P26`: *"If the Republican Party **wins** the 2026 U.S. Senate election in
Wyoming **by 26 percentage points or more**…"* vs `KXHOUSERACE-WYAL-26-R`: *"If the House member **sworn in**
for WY-AL for the term beginning in 2027 is a member of the [Republican] Party…"*. Winning by ≥N>0 points
entails winning; winning entails being sworn in, modulo the gaps below.

**Mapping.** The join must be made on `rules_primary`, not on the ticker (see Trap 3 — `SENATELA-26` is
Kentucky). Parsing the state and district out of the rules text resolves **520 of 522 ladders with zero
failures** (3,900 leg pairs). Target mix: `KXHOUSERACE` 2,740 pairs, `HOUSE{ST}{N}` 540, `SENATE{ST}` 316,
`GOVPARTY{ST}` 256. Ticker-based joins leave 5–11 ladders unmapped and silently mis-map LA/KY.

**Excluded: 2 ladders where the implication is invalid.** `KXMIDTERMMOV-GASENR` and `-GASEND` read
*"wins the **first round** of the 2026 U.S. Senate election in Georgia by N percentage points or more"* —
Georgia holds a runoff, so winning round one by 2 pts does **not** entail holding the seat. `SENATEGA-26`
exists (0.0900/0.0940 R, 0.9100/0.9120 D) and a naive scanner will pair them. Grep `rules_primary` for
`"first round"` before asserting any margin→winner implication: **139 markets in this slice contain it**.

**Failure modes.**
1. **Swearing-in gap.** The ladder settles on the certified *election margin*; the party market on who is
   *sworn in / inaugurated*. Winner dies, is disqualified, defects, or the seat is vacant on the swearing-in
   date → ladder Yes, party leg No. Exact *modulo swearing in*, not exact.
2. **Third-party winner.** 11 party-winner events carry an explicit independent leg. The ladder has only R
   and D ladders, so an independent win makes the implication vacuous and kills any inverse.
3. **Sub-1-point win.** No 0-pt rung exists anywhere, and *"No rounding shall be applied to the calculated
   margin."* A party winning by 0.7 pts leaves every ladder leg No while the party leg pays. This only
   strengthens ⊆.
4. **Timing.** Three different settlement triggers across the three families (see the early-close table).

**Live check — VIOLATED.** Gap (`spec_bid − gen_ask`) over 3,900 pairs: p50 = −0.44, p95 = −0.067,
p99 = −0.016, **max +0.070**. **14 pairs violate gross; 9 survive fees.**

| specific leg | bid | general leg | ask | gross | net | min size | $ at touch |
|---|---|---|---|---|---|---|---|
| `KXMIDTERMMOV-TX34R-P2` | 0.3000 | `HOUSETX34-26-R` | 0.2300 | +0.0700 | **+0.0429** | 100 | **+4.29** |
| `KXMIDTERMMOV-NY02D-P2` | 0.1600 | `KXHOUSERACE-NY02-26-D` | 0.1200 | +0.0400 | **+0.0231** | 100 | **+2.31** |
| `KXMIDTERMMOV-TX28R-P1` | 0.2100 | `HOUSETX28-26-R` | 0.1700 | +0.0400 | **+0.0184** | 25 | +0.46 |
| `KXMIDTERMMOV-NYGOVD-P4` | 0.9550 | `GOVPARTYNY-26-D` | 0.9300 | +0.0250 | **+0.0173** | 500 | **+8.65** |
| `KXMIDTERMMOV-TX35R-P1` | 0.5700 | `KXHOUSETX35-26-R` | 0.5300 | +0.0400 | +0.0053 | 100 | +0.53 |
| `KXMIDTERMMOV-MO05D-P3` | 0.1600 | `KXHOUSEMO5-26-D` | 0.1400 | +0.0200 | +0.0020 | 8 | +0.02 |
| `KXMIDTERMMOV-NH01D-P1` | 0.9140 | `HOUSENH1-26-D` | 0.9020 | +0.0120 | +0.0002 | 250 | +0.05 |
| `KXMIDTERMMOV-VA06D-P3` | 0.0990 | `KXHOUSERACE-VA06-26-D` | 0.0870 | +0.0120 | +0.0001 | 15 | +0.00 |
| `KXMIDTERMMOV-OH01R-P1` | 0.1800 | `HOUSEOH1-26-R` | 0.1600 | +0.0200 | +0.0001 | 100 | +0.01 |
| `KXMIDTERMMOV-MN02D-P1` | 0.9560 | `HOUSEMN2-26-D` | 0.9530 | +0.0030 | −0.0032 | 249 | −0.80 |
| `KXMIDTERMMOV-FL15D-P2` | 0.1300 | `KXHOUSERACE-FL15-26-D` | 0.1200 | +0.0100 | −0.0054 | 100 | −0.54 |
| `KXMIDTERMMOV-OH10D-P3` | 0.1400 | `KXHOUSERACE-OH10-26-D` | 0.1300 | +0.0100 | −0.0065 | 5 | −0.03 |
| `KXMIDTERMMOV-NYGOVD-P7` | 0.9310 | `GOVPARTYNY-26-D` | 0.9300 | +0.0010 | −0.0081 | 5 | −0.04 |
| `KXMIDTERMMOV-NJ02D-P3` | 0.1600 | `KXHOUSERACE-NJ02-26-D` | 0.1500 | +0.0100 | −0.0085 | 100 | −0.85 |

Total net-positive value at the touch: **$16.32** across 9 pairs in 13 distinct races. **12 of the 14
violations sit on the ladder's lowest rung (P1–P4)** — exactly where the two contracts are economically
closest and the fee wedge is thinnest relative to the gap. The prior finding of persistent violations in this
family is **confirmed on this snapshot**; the capacity is two orders of magnitude smaller than the headline
OI suggests because `KXMIDTERMMOV` quotes 100-lot.

### C2. Margin-ladder monotonicity (within `KXMIDTERMMOV`) — **CONSISTENT**

`yes_bid(P_{k+1}) ≤ yes_ask(P_k) + fees` for adjacent rungs. Both legs are *"…wins … by N percentage points
or more"* on the same race/party with `greater_or_equal` and a shared margin definition, so the nesting is
exact with no wording gap and no structural failure mode.
**Live: 3,417 adjacent pairs, 0 gross violations.**

### C3. Turnout-ladder monotonicity (within `KXMIDTERMVOTETURN`) — **CONSISTENT**

`yes_bid(Above N₂) ≤ yes_ask(Above N₁) + fees` for N₂ > N₁. *"If the total vote count for all participants in
{race} is above {N}…"*, `strike_type = greater` uniformly, so the nesting is exact.
**Live: 2,254 adjacent pairs, 0 gross violations.**

### C4. Cross-party margin exclusivity — **CONSISTENT**

`yes_bid(R, k+ pts) + yes_bid(D, j+ pts) ≤ 1 + fees` for k, j ≥ 1: both parties cannot each win the same
election by ≥1 point. Fails only at a 0-pt rung, which does not exist.
**Live: 1,266 cross-party pairs, 0 gross violations.**

---

### C5. Gov–Senate 2×2 combo marginals — **CONSISTENT except one $0.35 exception**

**Relation.** For each `KX{ST}SENGOVCOMBO-26NOV`:
```
P(GOV=D) = P(DEMDEM)+P(DEMREP)     P(SEN=D) = P(DEMDEM)+P(REPDEM)
P(GOV=R) = P(REPDEM)+P(REPREP)     P(SEN=R) = P(DEMREP)+P(REPREP)
```
plus the single-cell subset bound `P(cell) ≤ min(P(its GOV marginal), P(its SEN marginal))`.

**Rule basis.** *"If ALL of the following occur: Ohio Governor winner: Democratic party, Ohio Senate winner:
Democratic party…"*, with *"Each component is resolved according to its corresponding Kalshi ruleset:
Ohio Governor winner (GOVPARTY), Ohio Senate winner (SENATEPARTY)."*

**Resolving the marginals is a search, not a lookup.** `rules_secondary` names the *family*; the actual
tickers are off-pattern for a third of the states:

| combo | governor book | senate book |
|---|---|---|
| `KXOHSENGOVCOMBO-26NOV` | `GOVPARTYOH-26` | **`SENATEOHS-26`** (special) |
| `KXNHSENGOVCOMBO-26NOV` | **`GOVPARTYNH-28`** (sub_title "In 2026") | `SENATENH-26` |
| `KXKSSENGOVCOMBO-26NOV` | **`GOVPARTYKS-27`** (sub_title "In 2027") | `SENATEKS-26` |
| `KXAKSENGOVCOMBO-26NOV` | **`KXGOVPARTYAK-26`** (KX-prefixed) | `SENATEAK-26` |
| MN, MI, ME, IA, GA | `GOVPARTY{ST}-26` | `SENATE{ST}-26` |

Joining on `rules_primary` recovers all 9 pairs; joining on the ticker year recovers 6.

**Failure modes.**
1. **Not exhaustive.** The 2×2 covers only D and R in both offices. An independent governor or senator
   (live in AK and ME) makes all four legs No. `mutually_exclusive=true` guarantees ≤1 pays, not =1.
2. **Settlement-basis mismatch.** The combo's sources are state Secretaries of State and it says *"winner"*;
   `GOVPARTY{ST}` settles on *inauguration* and `SENATE{ST}` on *swearing in*. Exact on the election outcome,
   near-exact on the payout.
3. **Party-name variants.** `SENATEMN-26-D` reads *"Democratic **(DFL)** party"* in both subtitle and rules.

**Live check.** 36 two-leg marginal identities × 2 directions + 72 single-cell subset pairs.
**2 marginal directions and 1 subset pair clear fees, all in Minnesota, all trivial:**

| relation | executable | net | size | $ |
|---|---|---|---|---|
| `KXMNSENGOVCOMBO-26NOV-DEMDEM` ⊆ `SENATEMN-26-D` | sell cell 0.9400 / buy single 0.9300 | **+0.0014** | 250 | **+0.35** |
| MN `SEN=D` marginal | sell pair 0.9400 / buy `SENATEMN-26-D` 0.9300 | +0.0014 | — | — |
| MN `SEN=R` marginal | buy pair 0.0600 / sell `SENATEMN-26-R` 0.0720 | +0.0031 | — | — |

Everything else is fee-negative; the median two-leg identity is **−0.05 net** in both directions, because a
two-leg basket pays two taker fees against one. Combo internal sums run `ask_sum` 1.04–1.10 →
1.068–1.138 with fees, and `bid_sum` 0.94–1.01 → 0.893–0.975 net. `KXMESENGOVCOMBO` is the only one whose
**gross** bid sum exceeds $1 (1.0100), and it nets to 0.9748 — no arb.

---

### C6. Territory implication chain — **VIOLATED at the outer link**

**Relation.**
```
KXGREENLAND-29  ⊆  KXGREENTERRITORY-29  ⊆  KXUSAEXPANDTERRITORY-29JAN21
```

**Rule basis.**
- `KXGREENLAND-29`: *"If the United States **purchases** at least part of Greenland from Denmark before
  January 20, 2029…"* (`rules_secondary` empty).
- `KXGREENTERRITORY-29`: *"If the United States **acquires any part of Greenland** before Jan 21, 2029…"*,
  plus *"An announcement by the United States and the entity that controls any part of Greenland that it will
  happen is also encompassed by the Payout Criterion."*
- `KXUSAEXPANDTERRITORY-29JAN21`: *"If the United States gains control of **any territory outside its
  sovereignty as of Issuance** before Jan 21, 2029…"*, same announcement clause.

A purchase is an acquisition; Greenland is territory outside US sovereignty as of issuance.
**Deadlines: `KXGREENTERRITORY-29` and `KXUSAEXPANDTERRITORY-29JAN21` both close and expire at
2029-01-21T15:00:00Z — exactly matched.** `KXGREENLAND-29` closes one day earlier (2029-01-20T15:00:00Z),
which only strengthens the subset direction.

**Failure modes.** The announcement clause exists in the two outer contracts but not in `KXGREENLAND`, so the
outer legs can trigger on an announcement the inner one ignores — again only strengthening ⊆. The residual
risk is interpretive: whether the Outcome Review Committee reads "any part of Greenland" identically inside
both rulesets, and whether a lease or base agreement is "gains control".

**Live check.**

| specific | bid | ⊆ general | ask | gross | net | fee mult | size |
|---|---|---|---|---|---|---|---|
| **`KXGREENTERRITORY-29`** | **0.2500** | **`KXUSAEXPANDTERRITORY-29JAN21`** | **0.2200** | **+0.0300** | **+0.0047** | 1 / 1 | **888 → +$4.17** |
| `KXGREENTERRITORY-29-27` | 0.0530 | `KXUSAEXPANDTERRITORY-27JAN01` | 0.0550 | −0.0020 | −0.0093 | 1 / 1 | 4 |
| `KXGREENLAND-29` | 0.1500 | `KXGREENTERRITORY-29` | 0.2700 | −0.1200 | −0.1338 | **0** / 1 | 28 |
| `KXGREENLAND-29-27` | 0.0440 | `KXGREENTERRITORY-29-27` | 0.0550 | −0.0110 | −0.0147 | **0** / 1 | 2 |
| `KXGREENLAND-29` | 0.1500 | `KXUSAEXPANDTERRITORY-29JAN21` | 0.2200 | −0.0700 | −0.0821 | **0** / 1 | 888 |
| `KXCANTERRITORY-29` | 0.0900 | `KXUSAEXPANDTERRITORY-29JAN21` | 0.2200 | −0.1300 | −0.1479 | 1 / 1 | 32 |

The Greenland-specific contract (`KXGREENTERRITORY-29`: 397,975 OI, 2.81 M lifetime volume) trades **3 points
above** the strictly broader all-territory contract (`KXUSAEXPANDTERRITORY-29JAN21`: 27,758 OI, 86 k volume)
at a matched deadline. Net of both taker fees the gap is **+0.47¢ with 888 contracts on the thin side**. The
2027-deadline pair sits within 0.2¢ of violating in the same direction. This is the attention-asymmetry
signature: the named, heavily-traded book carries a premium over the generic superset nobody watches.

---

### C7. Trump departure lattice — **VIOLATED, largest in the slice**

**Relation.** `KXTRUMPRESIGN` and `KXTRUMPREMOVE` are each a subset of `KXTRUMPOUT27-27-JAN2029`,
**and they are mutually exclusive**, so:

```
yes_bid(KXTRUMPRESIGN) + yes_bid(KXTRUMPREMOVE)
    ≤  yes_ask(KXTRUMPOUT27-27-JAN2029) + fee(three legs)
```

**Rule basis.**
- `KXTRUMPRESIGN`: *"If the President of the United States elected for the 2025-2029 term **resigns** the
  office, then the market resolves to Yes."*
- `KXTRUMPREMOVE`: *"If the President of the United States has been **impeached and convicted by the U.S.
  Senate** before Jan 20, 2029…"*, `rules_secondary`: ***"The President must be the sitting President as of
  the day. the Senate votes on conviction to be included in this market."***
- `KXTRUMPOUT27-27-JAN2029`: *"If Donald Trump **leaves office** before January 20, 2029…"*

**This corrects the prior brief.** The sitting-president clause means a **post-resignation Senate conviction
does not count**. Resignation and conviction are therefore mutually exclusive *under the rulesets as
written*: resign first → `KXTRUMPREMOVE` resolves No; convicted and removed → he cannot subsequently resign.
So `P(resign) + P(remove) ≤ P(leaves office)` is an exact settlement relation, and a NO/NO basket on the two
departure contracts has **no** double-loss state. The prior "a post-departure trial is possible" note is the
right physical intuition but the ruleset explicitly excludes it. (The NO/NO constraint itself is weak in
practice — it only binds when both legs exceed 0.5; live it is `no_ask` 0.83 + 0.84 = 1.67 against a
guaranteed ≥$1 payout, i.e. nowhere near.)

**Failure modes.**
1. **Death — the material hole.** `KXTRUMPOUT27` `rules_secondary`: *"If Donald Trump leaves solely because
   they have died, the associated market will resolve and the Exchange will determine the payouts … based
   upon the last traded price (prior to the death) … the Outcome Review Committee will be responsible for
   making a binding determination of fair allocation."* Death is the one departure path where the long-`OUT`
   leg does **not** pay $1 — it pays an administratively determined number that could be below the entry
   price. The basket's payoff in that state is undefined from metadata.
2. **25th Amendment / incapacity.** Covered by `OUT` but by neither short leg — a free win for the basket,
   not a risk.
3. **Deadline edge.** `KXTRUMPRESIGN` closes 2029-01-21; `KXTRUMPREMOVE` and `OUT-JAN2029` close
   2029-01-20. A resignation in the final hours is inside `RESIGN` and outside `OUT`.

**Live check — VIOLATED.**

| leg | bid | ask | bid size | ask size |
|---|---|---|---|---|
| `KXTRUMPRESIGN` | 0.1700 | 0.1800 | 2,050 | 2,155 |
| `KXTRUMPREMOVE` | 0.1600 | 0.1800 | 6,844 | 97 |
| `KXTRUMPOUT27-27-JAN2029` | 0.2600 | 0.2700 | 1,353 | 952 |

Sell `RESIGN` @ 0.1700 + sell `REMOVE` @ 0.1600 + buy `OUT-JAN2029` @ 0.2700:
**gross +0.0600, fees 0.0332, net +0.0268/contract**, min touch size 952 → **+$25.52** — the largest
fee-surviving violation in the category. Each single-leg subset is fine on its own (`RESIGN` bid 0.17 vs
`OUT` ask 0.27 = −0.10; `REMOVE` bid 0.16 vs 0.27 = −0.11); the inconsistency lives entirely in the sum.
The `OUT` deadline ladder is internally monotone: `DJT` (before 2027) 0.0560/0.0570, `28` (before 2028)
0.1600/0.1700, `JAN2029` 0.2600/0.2700.

---

### C8. Chamber control ⟺ seat-count tail, and the balance-of-power 2×2

**C8a — seat-count tail vs control.**
```
CONTROLH-2026-D ⟺ KXDHOUSESEATS-27 ∈ {218-221 … Above 249}   (9 legs)
CONTROLH-2026-R ⟺ KXRHOUSESEATS-27 ∈ {218-222 … Above 237}   (5 legs)
CONTROLS-2026-D ⟺ KXDSENATESEATS-27 ∈ {51, 52, Above 52}     (3 legs)
CONTROLS-2026-R ⟺ KXDSENATESEATS-27 ∈ {Below 45 … 50}        (7 legs)
```
**Rule basis.** `KXDHOUSESEATS-27-220`: *"If the Democratic party has [218-221] House seats **on Feb 1,
2027**…"*. `CONTROLH-2026-D` `rules_secondary`: *"…victory will be determined by the party identification of
the **Speaker of the House on February 1, 2027**"* (Senate: *"the party identification of the **President pro
tempore**"*). Same date, same chamber; 218 and 51 are exact bucket lower edges, so the tails are exactly
replicable.
**Failure modes.** (i) vacancies — a 434-seat House makes 217 a majority, breaking the 218 cut;
(ii) defection between the seat count and the Speaker vote; (iii) the Senate cut assumes a Republican Vice
President breaks a 50-50 tie so D control needs ≥51 — the rule text never states this, it only names the
President pro tempore; (iv) `CONTROL*` can be media-determined early while the seat books settle on Feb 1.

**Live check — one gross inconsistency, none tradeable.**

| relation | basket bid | basket ask | single bid/ask | best net | min size |
|---|---|---|---|---|---|
| D House ≥218 (9 legs) vs `CONTROLH-2026-D` | 0.8270 | 0.8790 | 0.8300 / 0.8400 | −0.0751 | 4 |
| **R House ≥218 (5 legs) vs `CONTROLH-2026-R`** | **0.1900** | 0.2130 | **0.1600 / 0.1700** | −0.0029 | **2** |
| D Senate ≥51 (3 legs) vs `CONTROLS-2026-D` | 0.4600 | 0.4900 | 0.4600 / 0.4700 | −0.0547 | 3,061 |
| D Senate ≤50 (7 legs) vs `CONTROLS-2026-R` | 0.5730 | 0.6140 | 0.5300 / 0.5400 | −0.0205 | 4 |

The R-House row is a **gross violation**: the seat-count book implies P(R ≥ 218) ∈ [0.190, 0.213] while
`CONTROLH-2026-R` quotes 0.16/0.17 — a 2–4 point gap. It is killed by five taker fees (net −0.29¢) and by
**2 contracts** of depth on the thin side. The `KXRHOUSESEATS` tail legs are the least-quoted part of the book.

**C8b — the two Senate seat-count partitions are complements.**
`KXDSENATESEATSH-27-B53` (*"below 53"*) ⟺ NOT `KXDSENATESEATS-27-ABOVE52`, same date, same variable, so
`P(A)+P(B) = 1` exactly. Live: B53 0.8200/0.8400 (bid size **2**), ABOVE52 0.1900/0.2000 (bid size 4,868).
Selling both YES collects **1.0100 gross** for a certain $1 payout — but **net −0.0112** after 2.12¢ of fees,
on 2 contracts. Consistent after costs.

**C8c — balance-of-power 2×2 marginals.**
`KXBALANCEPOWERCOMBO-27FEB` (`-DD`,`-DR`,`-RD`,`-RR`, House first) against `CONTROLH-2026`/`CONTROLS-2026`:
```
P(DD)+P(DR)=P(House D)   P(RD)+P(RR)=P(House R)
P(DD)+P(RD)=P(Senate D)  P(DR)+P(RR)=P(Senate R)
```
Rule: *"If ALL of the following occur on Feb 1, 2027: House Control: Democratic, Senate Control:
Democratic…"* — the components are the same `CONTROL*` rulesets, so this identity is **exact**, and unlike C5
there is no third-party leakage (the Speaker and President pro tempore are always D or R).
**Live check — CONSISTENT.** All four identities are fee-negative in both directions (best −0.0278, worst
−0.0742). The 4-leg sum is bid 1.0020 / ask 1.0340; selling all four collects 1.0020 gross for a certain $1
but nets **0.9580** after 4.40¢ of fees. This is the deepest constraint set in the slice (15 k–106 k
contracts at the touch) and it is priced tight, as expected.

---

### C9. Per-state seat counts vs district books — **CONSISTENT**

**Relations.** For a state with `KXHOUSEWINSTATE-{ST}D` and all its district party books:
```
max_d P(D wins district d)  ≤  P(D wins ≥1 seat)  ≤  Σ_d P(D wins district d)     (Boole/Bonferroni)
Σ_k k·P(N = k)              =  Σ_d P(D wins district d)                           (E[N] identity)
```
where `P(D wins ≥1) = 1 − P(E0)`. Both are settlement-logic consequences (the same random variable N counted
two ways), not correlations.
**Rule basis.** `KXHOUSEWINSTATE-LAD-E0`: *"If Democrats win 0 seats in the 2026 U.S. House of
Representatives elections in Louisiana…"*; district legs: *"If the House member sworn in for LA-02 … is a
member of the Democratic Party…"*.
**Failure modes.** (i) the open top leg (`A2`, `A10`) has no upper bound, so the E[N] upper bound needs the
state's seat count as a cap; (ii) an independent winning a district is neither D nor R in the district book
but *is* "not a D seat" in the count book; (iii) `KXHOUSEWINSTATE-SCD` is dated *"On May 13, 2026"* while its
siblings are *"On Nov 3, 2026"*.

**Live check — CONSISTENT in all five states with both books.**

| state | districts | Σ P(D) [bid, ask] | E[N] implied by `KXHOUSEWINSTATE` | overlap |
|---|---|---|---|---|
| LA | 6/6 | [1.101, 1.290] | [0.970, 1.300] | yes |
| AL | 7/7 | [1.283, 1.483] | [1.050, 1.610] | yes |
| SC | 7/7 | [1.468, 1.612] | [1.170, 1.910] | yes |
| UT | 4/4 | [1.094, 1.245] | [0.920, 1.310] | yes |
| TN | 9/9 | [0.575, 0.830] | [0.340, 0.800] | yes (tight: [0.575, 0.800]) |

No Boole bound is breached: e.g. LA `E0` quotes 0.0100/0.0600 → P(≥1) ∈ [0.940, 0.990], against
max district P(D) = 0.961 (`KXHOUSERACE-LA02-26-D`) and Σ = 1.29. Florida has 28 district books but its
`KXHOUSEWINSTATE-FLD` starts at "Below 4" with no `E0` leg, so the ≥1 bound is not expressible there.

---

### C10. Primary derivatives embed their parent event in the ticker

**Relations.**
```
P(KXPRIMARYPLACE-{parent}-1-{CAND})    =  P({parent}-{CAND})      (1st place = nomination, non-runoff only)
P(KXPRIMARYMOV-{parent}-P{N} for CAND) ≤  P({parent}-{CAND})      (win by ≥N ⊆ win)
```
**Rule basis.** `KXPRIMARYPLACE-KXGOVFLNOMR-4-JCOL`: *"If Jay Collins finishes in 4th place in the 2026
Florida Republican gubernatorial primary according to the certified results…"*.
`KXPRIMARYMOV-SENATENHR26-P52`: *"If the margin of victory for John Sununu in the 2026 New Hampshire
Republican Senate primary falls within 5% to 100%, inclusive of its lower bound and exclusive of its upper
bound…"*. `KXVOTEPRIMARY-GOVFLNOMR26BDONBDON-75`: *"If the certified percentage of the popular vote received
by Byron Donalds … is 50% to 100%, inclusive of both endpoints…"*.

**Parser gap — reported, not silently worked around.** `taxonomy.derivative_parent()` resolves **12 of 22**
derivative events in this slice. A prefix-normalised matcher (strip `-`, strip leading `KX`, longest-prefix
match against known event tickers, accepting a match in **either** direction when the leftover is all digits)
reaches **19/22**. The library's three systematic failures:

| ticker | true parent | why `derivative_parent` misses it |
|---|---|---|
| `KXPRIMARYPLACE-KXGOVFLNOMR-{2,3RD,4}` | `KXGOVFLNOMR-26` | after stripping the place suffix the remainder has **no year**, and no candidate appends one |
| `KXPRIMARYPLACE-WAPRIMARY0326-1` | `KXWAPRIMARY-0326` | the embedded parent drops the `KX` prefix; the `k.replace("-","") == rest` fallback compares `KXWAPRIMARY0326` to `WAPRIMARY0326` |
| `KXVOTEPRIMARY-KXAKSENADVANCE-26AUG18-DJSULDJSUL` | `KXAKSENADVANCE-26AUG18` | the candidate code is **doubled** and the parent itself contains a `-` |

Three are **genuinely orphaned** even under the bidirectional matcher: `KXPRIMARYMOV-GOVAZNOMR26`,
`-AZ5R26`, `-GOVSDNOMRLRHO` — there is no `KXGOVAZNOMR-*`, no `KXAZPRIMARY-*` and no South Dakota governor
nomination event in this snapshot. (`KXPRIMARYMOV-FLPRIMARY06R` → `KXFLPRIMARY-06R26` recovers only once
the matcher accepts a digits-only leftover.)

**Failure modes.** (i) **Runoffs and top-N advances** — `KXAKSENADVANCE`, `KXSCRSENS` and the SD runoff
measure a round, not a nomination, so 1st place ≠ nominee; (ii) the same person carries different codes
across books (`KXSCRSENS-26-DNOR` "Darline Graham" vs `-DGRA` in its derivative); (iii) `KXPRIMARYMOV`'s
bucket variant repeats strike suffixes across candidates, so `(event, strike)` is not a key.
**Live check.** Not priced as a basket: the resolvable parents' `KXPRIMARYPLACE` events carry 3–6 legs with
near-zero 24 h volume. Documented as an extraction relation, not a live inequality.

---

### C11. Mutex sum-to-one — and why it almost never applies

`Σ yes_ask + Σ fee ≥ 1` and `Σ yes_bid − Σ fee ≤ 1` hold only for events that are mutex **and exhaustive
and tiled**.

**Live check on 1,097 mutex events with ≥2 active legs.** `Σ bid − fees > 1`: **0 events**.
`Σ ask + fees < 1`: **31 events — none of them an arbitrage.** Every one fails exhaustiveness:

| event | legs | ask sum + fee | why not exhaustive |
|---|---|---|---|
| `KXFLPRIMARY-10R26` | 3 | 0.0749 | candidate menu, no "another candidate" leg |
| `KXLAPRIMARY-01R26` | 2 | 0.1057 | only Scalise and Arrington listed |
| `KXSTATE51-29` | 8 | 0.1735 | 8 named territories; any other pays nothing |
| `KXNEWPOPE-70` | 7 | 0.3066 | 7 named cardinals |
| `KXPRESNOMG-28` | 6 | 0.7908 | 6 named Green candidates |
| `KXVPRESNOMR-28` | 21 | 0.8350 | 21 named |
| `KXHOUSERACE-ME01-26` | 2 | **0.9896** | **D/R only — an independent wins → both legs No** |
| `KXHOUSERACE-VA08-26` | 2 | 0.9972 | same |
| `SENATERI-26` | 2 | 0.9978 | same |
| `GOVPARTYOK-26` | 2 | 0.9993 | same |

The last four are the dangerous ones: they *look* like complete partitions (two legs, D and R, summing to
0.99) and a naive scanner flags them as free money. They are not — **11 party-winner events in this slice
already carry an explicit independent leg**, proving the exchange treats a non-major-party win as live.

`KXGREENLANDPRICE-29JAN21` is the textbook untiled partition: `partition_is_tiled()` returns **False**.
Legs are `$0 / No Acquisition`, `$1B–$9B`, `$10B–$99B`, `$100B–$299B`, `$300B–$599B`, `$600B–$899B`,
`$900B–$1199B`, `$1.2T or more`. An acquisition for $500 M, $9.5 B, $99.5 B, $299.5 B, $599.5 B, $899.5 B or
$1,199.5 B pays **nothing**. Live ask sum 1.0770 (1.1039 with fees), bid sum 0.9590. The `NOACQ` leg also
conflates "acquired for exactly $0" with "no acquisition", so it is **not** the complement of
`KXGREENTERRITORY-29`.

---

## Live settlement-ambiguity case study: `KXMESENOUTCOME-27JAN` (Maine Senate)

**Not a trade recommendation.** Documented as a settlement-text hazard a scanner must detect and route to
manual review.

`KXMESENOUTCOME-27JAN` is a combination event pairing a *named Democratic nominee* with a *general-election
party outcome*:

| leg | `yes_sub_title` | `rules_primary` | status | bid / ask | OI |
|---|---|---|---|---|---|
| `-GPD` | "Democratic party wins " | *"…**Dem Nominee: Graham Platner**, General Election Winner: Democrat"* | active | 0.6300 / 0.6400 | 116,400 |
| `-GPR` | "Republican party wins" | *"…**Dem Nominee: Graham Platner**, General Election Winner: Republican"* | active | 0.3600 / 0.3700 | 40,262 |
| `-JMD` | "First Dem Nominee: Janet Mills, …" | *"…Dem Nominee: Janet Mills, General Election Winner: Democrat"* | **finalized, `result = no`**, closed **2026-06-10T14:43:22Z** | — | 46,624 |
| `-JMR` | "First Dem Nominee: Janet Mills, …" | *"…Dem Nominee: Janet Mills, General Election Winner: Republican"* | **finalized, `result = no`**, closed **2026-06-10T14:43:30Z** | — | 26,935 |

`rules_secondary`: *"…If ANY single component resolves to No or becomes impossible, the entire contract
immediately resolves to No. Each component is resolved according to its corresponding Kalshi ruleset:
**Dem Nominee (SENATEPARTYNOM)**, General Election Winner (SENATEPARTY). All conditions must be satisfied
before Jan 2027."*

Graham Platner withdrew in July 2026; **Troy Jackson was nominated at the Maine Democratic convention on
2026-07-25**. Kalshi has already updated `SENATEME-26-D`'s display name from Platner to "Troy Jackson", and
`KXMESENATEPERSON-26` prices the change: `-GPLA` (Platner) **0.0000 / 0.0010**, `-TJAC` (Jackson)
**0.6200 / 0.6300**.

**Evidence for the literal reading (the legs should die).**
- The nominee condition has been enforced before: `-JMD` / `-JMR` were finalized to `no` on **2026-06-10**,
  when Mills' candidacy became impossible, exactly as `rules_secondary` prescribes.
- Kalshi's remediation pattern elsewhere is to **add** re-pointed legs rather than re-point stale ones.
  `KXMETXCOMBO-26NOV` carries *both* generations inside one event: `-26NOV-TAL-PLA` and `-26NOV-PAX-PLA`
  (Platner) at **0.0000 / 0.0100**, alongside newly issued `-26NOVB-TAL-JAC` (0.4000/0.4100) and
  `-26NOVB-PAX-JAC` (0.2200/0.2400). The stale Platner legs went to zero and stayed listed.
- **9 of the 11 active legs in this slice whose `rules_primary` names Graham Platner trade at ≈0**
  (`KXPRESNOMD-28-GPLA` 0.0000/0.0010, `KXVPRESNOMD-28-GPLA` 0.0000/0.0100,
  `KXMESENATEPERSON-26-GPLA` 0.0000/0.0010, `KXPLATNERCOLLINSDEBATE-26` 0.0000/0.0200,
  `KXDEMSENATEPRIMARYCOMBO-26NOV03` 0.0030/0.0290, both `KXMETXCOMBO` Platner legs, …).
  The **only** two exceptions are `-GPD` and `-GPR`.

**Evidence for the party reading (the legs are stale labels).**
- `-GPD` quotes **0.6300 / 0.6400** and `-GPR` **0.3600 / 0.3700** — *tick for tick identical* to
  `SENATEME-26-D` (0.6300/0.6400) and `SENATEME-26-R` (0.3600/0.3700), which settle purely on party.
- The `yes_sub_title` on the two live legs has already been **rewritten** to the party form
  ("Democratic party wins ", "Republican party wins") while the dead Mills legs kept the person form
  ("First Dem Nominee: Janet Mills, …"). The display layer has been re-pointed; `rules_primary` has not.
- The Mills legs say "**First** Dem Nominee". If "first nominee" means the primary winner rather than the
  convention nominee, Platner may satisfy the `SENATEPARTYNOM` component and the legs legitimately reduce to
  party markets. `KXDEMPROGRESSIVESENATESWEEP-26NOV03`, which requires Platner to *win his 2026 Senate
  primary* (a different condition), trades **0.7800 / 0.7900** with 21,753 OI — consistent with Platner
  having won the primary and withdrawn afterwards.

**Neither reading can be settled from metadata.** The two readings differ by ~63 cents on 156,662 contracts
of open interest. The correct scanner behaviour is to flag any combination event whose `rules_primary` names
a person as a *component precondition* while a sibling leg with the same precondition structure is already
`finalized`, and route it out of the automated path. Note `KXMESENGOVCOMBO-26NOV` (the Maine Gov–Senate 2×2)
is worded on *party* and is unaffected.

---

## Traps a scanner must encode

1. **`mutually_exclusive` gates all sum logic, and event shape is no evidence.** All 522 `KXMIDTERMMOV`
   events are `mutex=false` (correct for nested ladders); `KXPRIMARYMOV-SENATEMAD26` is `mutex=true` with
   12 legs while `KXPRIMARYMOV-SENATENHR26` is `mutex=false` with 6 — **same series, opposite flags**.
2. **Mutex ≠ exhaustive.** 31 mutex events price below $1 net on the ask side; **none** is an arb. The four
   most dangerous are 2-leg D/R party books (`KXHOUSERACE-ME01-26` 0.9896, `KXHOUSERACE-VA08-26` 0.9972,
   `SENATERI-26` 0.9978, `GOVPARTYOK-26` 0.9993) where an independent winner makes both legs pay zero.
3. **The state token can be the wrong state.** `SENATELA-26` is **Kentucky** (title *"Kentucky Senate
   winner?"*, rules *"Senator of Kentucky"*, legs Andy Barr / Charles Booker). Louisiana 2026 is
   `KXSENATELA-26NOV`; `SENATELA-28` is Louisiana. **Join on `rules_primary`, not on the ticker.** Doing so
   raises `KXMIDTERMMOV` → party-winner coverage from 511/522 to 520/520 (excluding the 2 Georgia
   first-round ladders) and removes a silent wrong-entity match.
4. **Ticker year ≠ election year.** `GOVPARTYKS-27` ("In 2027") and `GOVPARTYNH-28` ("In 2026") both settle
   *"pursuant to the 2026 election"*. `SENATE{ST}-26` means the term beginning 2027. Parse the year out of
   `rules_primary`.
5. **Untiled bucket partitions.** `KXGREENLANDPRICE-29JAN21` has six interior holes plus a sub-$1B hole;
   `partition_is_tiled()` returns `False`. Always call it before any buy-all-YES.
6. **First-round qualifiers.** `KXMIDTERMMOV-GASENR` / `-GASEND` settle on *"the **first round** of the 2026
   U.S. Senate election in Georgia"*, so the margin→winner implication to `SENATEGA-26` is **invalid**
   (Georgia has a runoff). 139 markets in the slice contain "first round" in `rules_primary`; the sibling
   `KXMIDTERMMOV-GAGOVR/D` does **not**, despite Georgia also providing for a gubernatorial runoff.
7. **Leg display names lie about the settlement subject, in both directions.**
   `KXHOUSERACE-WV02-26-D` displays *"Ace Parsi"* and settles on party. `GOVPARTYME-26-D` displays
   *"Hannah Pingree"* and settles on party. The template also produces nonsense when a person is inserted
   into the party slot: `GOVPARTYME-26-RBEN` reads *"a representative of the **Rick Bennett** party"*,
   `GOVPARTYMI-26-MD` *"the **Mike Duggan (Independent)** party"*. Conversely `KXMESENOUTCOME-27JAN-GPD`
   displays *"Democratic party wins"* and settles (per `rules_primary`) on **Graham Platner** being the
   nominee. Read the rules text.
8. **Party-name variants break regex joins.** `SENATEMN-26-D` reads *"Democratic **(DFL)** party"* in both
   subtitle and rules.
9. **Finalized legs sit inside open events.** 134 open events carry ≥1 dead leg (295 total):
   `KXMESENOUTCOME-27JAN` 2 of 4, `KXTRUMPOUT27-27` 1 of 4, `KXUSAEXPANDTERRITORY` 1 of 4,
   `KXGREENLAND-29` 1 of 3. They quote 0.0000 / 1.0000 and poison any basket sum. Filter on
   `status == "active"` and shrink the basket.
10. **The two House families are disjoint and one of them is the competitive half.** Resolving a
    `KXMIDTERMMOV` House ladder requires trying `KXHOUSERACE-{ST}{NN}-26`, `HOUSE{ST}{N}-26` **and**
    `KXHOUSE{ST}{N}-26`, with the district zero-padded in some and not others. 63 of 372 seats live only in
    the per-seat family.
11. **Leg-suffix exceptions.** `KXHOUSENC11-26` uses `-DEM`/`-GOP` instead of `-D`/`-R`; Senate specials add
    `S` to the state code (`SENATEOHS-26`); 11 party-winner events carry a third leg with a
    candidate-initials suffix (`-KSAW`, `-JFET`, `-RBEN`, `-IND`, …).
12. **Same name, different entity, same event.** `KXMESENATEPERSON-26` carries both `-AKIN` "Angus King" and
    `-AKIN3` "Angus King III". Candidate codes are not stable across books either
    (`KXSCRSENS-26-DNOR` vs `-DGRA` for the same person).
13. **Combination `rules_secondary` names families, not tickers.** *"…its corresponding Kalshi ruleset:
    Ohio Governor winner (GOVPARTY), Ohio Senate winner (SENATEPARTY)"* — but the Ohio Senate marginal is
    `SENATEOHS-26`, Alaska's governor marginal is `KXGOVPARTYAK-26`, New Hampshire's is `GOVPARTYNH-28` and
    Kansas's is `GOVPARTYKS-27`. Resolving a combo to its marginals is a search.
14. **`greater` vs `greater_or_equal`.** `KXMIDTERMVOTETURN` legs are `greater` (strict);
    `KXMIDTERMMOV` legs are `greater_or_equal`. `taxonomy.parse_threshold()` returns `">="` for both —
    harmless for monotonicity, wrong at the boundary.
15. **`liquidity_dollars` is 0.0000 on every active market here** and `notional_value_dollars` is 1.0000 on
    every one. Use `yes_bid_size_fp` / `yes_ask_size_fp` for depth.
16. **`settlement_sources` is an unfilled template on 6,695 markets (49%)** — e.g. *"official election
    authority responsible for certifying results in "*. Do not parse or group on it.
17. **`close_time` is a nominal backstop.** 8,813 markets nominally close 2027-11-03, a year after the
    election they reference. The real date comes from `early_close_condition`, which differs across the four
    party-winner families (see Settlement).
18. **Ladder capacity is ~100 contracts.** `KXMIDTERMMOV` quotes 100-lot on both sides in nearly every case;
    a 4¢ net edge is worth ~$4, not $4,000. Rank by `net × min(bid_size, ask_size)`.
19. **A two-leg basket pays two taker fees.** At P ≈ 0.5 each leg costs 1.75¢, so a 2-leg-vs-1-leg identity
    needs a >5¢ gross gap to clear. This is why all 36 `SENGOVCOMBO` marginal identities and all four
    `KXBALANCEPOWERCOMBO` identities are fee-negative despite deep books, and why the single-cell subset
    form (1 leg vs 1 leg) is the only one that ever clears.
20. **`derivative_parent()` resolves 12/22 here.** Extend it before relying on it (see C10), and expect three
    derivatives with no live parent at all.

---

## Open questions

1. **Which text governs `KXMESENOUTCOME-27JAN-GPD`/`-GPR`** — the person-conditioned `rules_primary` or the
   already-rewritten party-worded `yes_sub_title`? The `-JMD`/`-JMR` precedent and the `KXMETXCOMBO`
   re-issue pattern point one way; the subtitle rewrite and the live book point the other. Requires the full
   contract terms document (`series.contract_terms_url`) or an exchange notice. Whether "First Dem Nominee"
   means the primary winner or the convention nominee is the crux.
2. **Does `KXUSAEXPANDTERRITORY`'s *"any territory outside its sovereignty as of Issuance"* strictly contain
   `KXGREENTERRITORY`'s *"any part of Greenland"*?** The C6 violation is only real if the Outcome Review
   Committee reads them that way. The shared settlement source (*The New York Times*) supports it; nothing in
   the metadata makes it binding.
3. **Death handling in `KXTRUMPOUT27`.** The rule delegates to "last traded price" and then to the Outcome
   Review Committee. The C7 basket's payoff in that state is undefined from metadata, and no field gives a
   reference-price rule.
4. **Do `KXMIDTERMMOV-GAGOVR/D` settle on the first round?** The Georgia *Senate* ladders say so explicitly;
   the gubernatorial ladders do not, although Georgia law provides for a gubernatorial runoff. If the
   omission is a template bug, C1 does not hold for those two ladders either.
5. **What determines whether a race gets `KXHOUSERACE` or a per-seat `HOUSE{ST}{N}` series?** The split is
   clean (0 overlap, 425 of 435 seats) and correlates with competitiveness, but no metadata field encodes it —
   and 10 districts have neither.
6. **Why do `KXDSENATESEATS-27` and `KXDSENATESEATSH-27` both exist**, partitioning the same variable on the
   same date at different granularity? Does the `H` suffix carry a documented meaning? Same question for
   `KXDHOUSESEATS-27` (bucket) vs `KXDHOUSESEATSDIR-27` (nested ladder).
7. **`CONTROLS` at 50-50.** *"party identification of the President pro tempore of the Senate on February 1,
   2027"* — organizational control is broken by the Vice President, which C8a assumes. The rule text never
   says so.
8. **Which books get the accelerated-determination clause, and why?** 704/704 `KXHOUSERACE` legs carry it but
   only 15/136 `SENATE{ST}` and 11/101 `GOVPARTY{ST}` — and it is inconsistent *within* an event
   (`GOVPARTYME-26` has it on 1 of 3 legs). If this is a live rule rather than a metadata artefact, the
   affected books close months before their siblings.
9. **Orphaned derivatives.** `KXPRIMARYMOV-GOVAZNOMR26`, `-AZ5R26`, `-GOVSDNOMRLRHO` reference parents
   absent from this snapshot. Settled-and-purged, listed in another category shard, or listed before their
   parent?
10. **Fee-multiplier assignment.** Seven series here are zero-fee, including `KXGREENLAND` — one end of the
    territory chain — while the structurally adjacent `KXGREENTERRITORY` and `KXUSAEXPANDTERRITORY` are
    full-fee. Nothing in `series.json` explains the assignment, and it decides which links in a chain are
    tradeable.
11. **Are `open_interest_fp` / `volume_fp` in contracts or a fixed-point scale?** Values are consistent with
    contracts (`yes_bid_size_fp` prints 100.00, 250.00) but the `_fp` suffix has misled prior work in other
    families. All figures here are reported as-returned.
