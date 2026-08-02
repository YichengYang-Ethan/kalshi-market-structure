# Sports

Snapshot: `2026-08-02T20:52Z`. Source shard: `by_category/Sports.jsonl.gz`, plus `series.json`
for fee and frequency metadata. All prices below are the snapshot's `*_dollars` fields; all
sizes are the `*_size_fp` decimal-contract fields.

---

## Inventory — events, markets, series count; how much of the exchange this is

| quantity | Sports | exchange | share |
|---|---|---|---|
| events | 3,920 | 8,478 | 46.2% |
| markets | 35,344 | 73,964 | 47.8% |
| series with live events | 799 | — | — |
| series carrying `category == "Sports"` in `series.json` | 3,065 | 12,370 | 24.8% |

Sports is the largest category on the exchange by both events and markets — nearly half of
every live contract. It is also the most *dormant-heavy*: only 799 of the 3,065 sports series
have any live event in this snapshot (26%), because the bulk of the series catalogue is
per-league game templates that instantiate only on match days.

Market status inside the shard:

| status | markets |
|---|---|
| `active` | 34,756 |
| `finalized` | 518 |
| `inactive` | 70 |

The 518 finalized markets are **not** in dead events — they sit inside events whose other legs
are still active (finished sets in a live tennis match, a completed map in an ongoing esports
series, an already-decided leg of a season ladder). Every basket computed below must drop them
and shrink the leg count accordingly.

Event-level flags:

| field | values |
|---|---|
| `mutually_exclusive` | `True` 1,946 / `False` 1,974 |
| `collateral_return_type` | `MECNET` 1,946 / `""` 1,944 / `DIRECNET` 30 |
| `strike_period` | empty for all 3,920 events |
| `event.category` | `Sports` for all 3,920 (no internal disagreement in this shard) |

`MECNET` tracks `mutually_exclusive == True` exactly. `DIRECNET` appears on 30 events only.

### Fee status — first-class here

Every one of the 799 sports series has `fee_multiplier == 1`. **There are no free sports
markets** (the exchange's 14 zero-multiplier series are all outside Sports).

56 of the 799 series are `fee_type == "quadratic_with_maker_fees"` — 56 of the 78 live
maker-fee series exchange-wide. (`series.json` lists 107 Sports series with that fee type; the
other 51 are dormant.) Their economic weight is wildly out of proportion to their count:

| | maker-fee series | rest of Sports |
|---|---|---|
| active markets | 1,480 (4.3%) | 33,276 (95.7%) |
| share of open interest | **78.2%** | 21.8% |
| share of lifetime volume | **75.3%** | 24.7% |
| two-sided at the touch | 68.4% | 47.8% |

So the liquid core of sports — every league championship outright, every NFL/MLB/UCL/tennis
moneyline, PGA Tour, March Madness, the award markets — charges makers. The illiquid tail
(player props, correct score, seed grids, next-team menus) does not.

Cost model, per contract per leg, at the verified schedule:

```
taker = ceil_to_centicent( 1 * 0.07   * P * (1-P) )
maker = ceil_to_centicent( 1 * 0.0175 * P * (1-P) )   # only on the 56 series; 0 elsewhere
settlement fee = 0
```

At P = 0.50 that is 1.75c taker, 0.44c maker. A taker-in/taker-out round trip at the money
costs 3.5c against a median two-sided spread of 6c — i.e. fees are roughly 60% of the quoted
spread, and every constraint check below has to net them out before it means anything.

---

## Series families — what they actually do, and the ticker grammar

Functional grouping of the 799 live series (assignment by ticker suffix / stem, not by
`series.category`, which is useless as a join key):

| group | series | events | markets | of which maker-fee |
|---|---|---|---|---|
| tournament progress (seeds, rounds, qualifiers, elimination stage) | 106 | 286 | 6,789 | 15 |
| in-game microstructure (score, total, spread, halves, sets, maps) | 143 | 1,236 | 6,372 | 2 |
| championship / outright | 336 | 805 | 6,224 | 21 |
| player & team stat lines | 33 | 143 | 5,407 | 1 |
| transactions / roster (next team, trades, coaches, starters) | 28 | 172 | 3,370 | 0 |
| awards & season leaders | 71 | 119 | 3,109 | 10 |
| game moneyline | 65 | 953 | 2,191 | 7 |
| season win totals | 17 | 206 | 1,882 | 0 |

Markets by league token: MLB 6,777 · NFL 4,195 · NCAAF 2,453 · NBA 1,595 · Leagues Cup 1,488 ·
March Madness 1,148 · WNBA 1,105 · Brasileirão 1,048 · NCAA men's basketball 1,045 ·
Europa League 870 · PGA 810 · ATP 671 · LoL 417 · UCL-W 352 · CS2 304 · WTA 271 · UCL 259.

### The ticker grammar (this is what makes relation extraction possible)

**1. Per-game families — `KX<LEAGUE><MARKETTYPE>-<GAMEKEY>[-<PERIOD>]`**

The single most useful structural fact in this category: for a given league, *all* per-game
series share one `<GAMEKEY>`, and the market type is a pure suffix on the series stem.

```
KXLEAGUESCUP      GAME | SCORE | TOTAL | TEAMTOTAL | SPREAD | FTTS | 1H | 1HTOTAL | 1HSPREAD
KXMLB             GAME | TOTAL | TEAMTOTAL | SPREAD | F5 | F5TOTAL | F5SPREAD | F7 | HIT | HR | HRR | TB | RBI | KS | SB
KXUEL             GAME | SCORE | TOTAL | TEAMTOTAL | SPREAD | FTTS | 1H | 1HTOTAL | 1HSPREAD | ADVANCE
KXATP             MATCH | EXACTMATCH | SETWINNER | GTOTAL | GSPREAD
KXLOL / KXCS2 / KXVALORANT   GAME | MAP | TOTALMAPS
```

40 stems carry ≥3 members of this suffix vocabulary. `<GAMEKEY>` is
`<YY><MON><DD>[<HHMM>]<AWAY><HOME>`:

```
KXLEAGUESCUPGAME-26AUG08ORLLEO          soccer: no clock component
KXMLBGAME-26AUG051510TBCOL              baseball: HHMM present (doubleheaders)
KXLOLMAP-26AUG051700WUBLUE-2            esports: HHMM present, -2 = map index
KXATPSETWINNER-26AUG01ATMDRA-1          tennis:  -1 = set index
```

Join rate on this key is essentially perfect: Leagues Cup 24/24 across all 9 suffixes, MLB
18/18 (game-level) and 11/11 (prop-level) against `KXMLBGAME`, WTA 31/31, ATP 31/31 for
`GTOTAL`/`GSPREAD`. **The one exception**: `KXATPEXACTMATCH-26AUG03WALJBRO` and
`KXATPSETWINNER-26AUG03WALJBRO-*` use a 4-letter second-player code where
`KXATPMATCH-26AUG03WALBRO` uses 3 — 1 mismatch out of 33 ATP matches. Any ATP scanner needs a
name-based fallback (joining on the date prefix plus the set of `yes_sub_title` player names
recovers 33/33).

**2. Leg grammar inside a per-game event**

| pattern | example | meaning |
|---|---|---|
| `-<TEAMCODE>` | `KXNFLGAME-26SEP14DENKC-KC` | that team wins |
| `-<TEAMCODE><K>` | `KXNFLSPREAD-26AUG06CARARI-CAR17` | team wins by ≥ K (subtitle says "over K−0.5") |
| `-<K>` | `KXNFLTOTAL-26AUG06CARARI-16` | combined total ≥ K |
| `-<TEAM><PLAYER><JERSEY>-<K>` | `KXMLBHIT-26AUG021920BOSLAD-LADFFREEMAN5-2` | that player records ≥ K |
| `-<HOME><h><AWAY><a>` | `KXLEAGUESCUPSCORE-26AUG08ORLLEO-ORL1LEO2` | exact score h–a |
| `-<PLAYER><s1><s2>` | `KXATPEXACTMATCH-26AUG03WALJBRO-WAL21` | that player wins 2–1 in sets |

**The trailing integer in the ticker is the canonical strike, and it is monotone.** Subtitle
text is not: "Over 0.5 1H goals scored", "Arizona -2.5 first 5 innings" and "6+ wins" all
defeat naive numeric extraction (see Traps). Correct-score legs additionally carry the strike
in `custom_strike` as `{home_score, away_score, home_team_id, away_team_id}` with UUIDs that
match the moneyline legs' `custom_strike.soccer_team` — that is the reliable join.

**3. Season-level families — `KX<LEAGUE><CONCEPT>-<YY><SUBJECT>`**

```
KXNFLWINS-27WAS-8            team ladder:   -<TEAM>, legs = -<K>
KXNBAWINS-27WAS-25           same, K in steps of 5
KXNCAAFWINS-26WVU-6          <YY> = calendar year, not season-end year
KXNFLSTAGEOFELIM-27CLE-FW    per-team 6-leg partition; legs REG WC DIV CONF FL FW
KXNCAAFSEED-27S9-OSU         -<YY>S<seed>, legs = team codes (12 seed events x 50 teams)
KXMARMADROUND-27F4-CONN      -<YY><ROUND>, ROUND in {R32,R16,R8,F4,T2}
KXMARMADSEED-27T5-CONN       -<YY>T<n> = "top-n seed", NOT "seed #n"
KXNFLDIVISIONORDER-27NFCWEST-SEASFARILAR   leg = concatenated finish order
```

**4. Outrights — `KX<COMP>-<YY>`** with team/player leg codes:
`KXSB-27`, `KXNCAAF-27`, `KXMARMAD-27`, `KXNBA-27`, `KXNHL-27`, `KXMLB-26`, `KXWC-30`,
`KXNFLAFCCHAMP-27`, `KXNFLAFCEAST-27`, `KXMLBAL-26`.

Note the year field is **not** consistent across a lattice: `KXNCAAFPLAYOFF-26` sits in the
same 2026-27 CFP lattice as `KXNCAAFQF-27`, `KXNCAAFSF-27`, `KXNCAAFFINALIST-27`, `KXNCAAF-27`.
Likewise `KXNCAAFSEC-26` vs `KXNCAAF-27`. Never assume the year token matches across series.

### Largest individual series

| series | events | markets | fee | template |
|---|---|---|---|---|
| `KXMLBHRR` | 11 | 981 | quadratic | player H+R+RBI ladder |
| `KXNEXTTEAMNBA` | 27 | 823 | quadratic | mutex team menu |
| `KXMLBTB` | 11 | 795 | quadratic | player total-bases ladder |
| `KXLEAGUESCUPSCORE` | 24 | 720 | quadratic | 30-cell correct-score grid |
| `KXMLBHIT` | 11 | 646 | quadratic | player hits ladder |
| `KXNCAAFSEED` | 12 | 600 | quadratic | seed × team menu |
| `KXNCAAFWINS` | 69 | 583 | quadratic | season win ladder |
| `KXMARMADROUND` | 5 | 560 | quadratic | reach-round menu |
| `KXNFLWINS` | 32 | 544 | quadratic | season win ladder |
| `KXNFLMATCHUP` | 3 | 496 | quadratic | pairwise matchup menu |
| `KXPGATOUR` | 1 | 151 | **maker** | tournament winner menu |
| `KXSB` | 1 | 32 | **maker** | champion menu |

---

## Contract templates and their leg grammar

`classify_event()` over the 3,920 events:

| template | events | mutex True |
|---|---|---|
| `entity_menu` | 2,909 | 1,925 |
| `binary` | 518 | 1 |
| `threshold` | 453 | 0 |
| `deadline` | 20 | 0 |
| `combination` | 19 | 19 |
| `bucket` | 1 | 1 |

These labels undercount the real structure — `entity_menu` absorbs both true one-of-N menus
*and* every ladder whose subtitle carries a trailing noun (see Traps). Counting by
`strike_type` instead: **8,619 active markets across 178 series are one-sided ladders**
(`greater` 6,534 + `greater_or_equal` 2,085), forming 1,895 distinct ladder groups.

### Template 1 — moneyline / 1X2 (mutex, exhaustive)

2-leg (US/esports/tennis) or 3-leg with an explicit draw leg (soccer, `KXMLBF7`).

> `KXNFLGAME-26SEP14DENKC-KC` — *"If Kansas City wins the Denver vs Kansas City professional
> football game originally scheduled for Sep 14, 2026, then the market resolves to Yes."*
> Secondary: *"If the game ends in a tie, the market will resolve to $0.50 for each team."*

The tie clause is what makes the 2-leg NFL basket sum to exactly $1 in every state.

### Template 2 — one-sided threshold ladder (non-mutex, nested)

Totals, team totals, spreads, season win totals, player props, team points.

> `KXNBAWINS-27WAS-25` — *"If the Washington Pro Basketball team wins at least 25 games…"*
> `KXNFLTOTAL-26AUG06CARARI-16` — *"Over 15.5 points scored"*, `strike_type: greater`
> `KXLEAGUESCUPSPREAD-26AUG08ORLLEO-ORL3` — *"If Orlando wins by more than 2.5 goals in the
> Orlando vs Leon professional Leagues Cup soccer game … after 90 minutes plus stoppage time
> (does not include extra time or penalties), then the market resolves to Yes."*

Two ladders often share one event (both teams on a spread; every player in a prop event).
The subject key is the ticker prefix before the trailing integer.

### Template 3 — correct-score / exact-score grid (mutex, **not** exhaustive)

> `KXLEAGUESCUPSCORE-26AUG08ORLLEO` — 30 legs: `Draw 0-0` … `Orlando City SC wins 5-2`.
> *"If the result is a 0-0 draw … after 90 minutes plus stoppage time (does not include extra
> time or penalties), then the market resolves to Yes."*

The grid covers only part of the score space (no 4-4, 5-3, 5-4, 5-5, nothing above 5). Sum of
the 30 asks in this snapshot has median 13.09 and minimum 7.42 — the grid is quoted, but the
partition has holes, so it supports only ≤ relations, never a sum-to-one.

Tennis is the exhaustive version of the same template: `KXATPEXACTMATCH` has exactly 4 legs
(`WAL20, WAL21, JBRO21, JBRO20`) which do tile the best-of-3 outcome space.

### Template 4 — stage-of-elimination partition (mutex, exhaustive)

> `KXNFLSTAGEOFELIM-27CLE` legs `REG WC DIV CONF FL FW`:
> *"Regular Season: This market resolves Yes if the Cleveland Pro Football team fails to qualify
> for the playoffs. … Runner-Up: … loses in the Pro Football Championship game. Championship
> Winner: … wins the Pro Football Championship game."*

Six legs covering every possible season end-state for one team. This is the cleanest partition
in the category and the anchor for several cross-series identities.

### Template 5 — nested qualification menus (non-mutex)

`KXNCAAFPLAYOFF` ⊃ `KXNCAAFQF` ⊃ `KXNCAAFSF` ⊃ `KXNCAAFFINALIST` ⊃ `KXNCAAF`;
`KXMARMADROUND-27{R32,R16,R8,F4,T2}` ⊃ `KXMARMAD`.

> `KXNCAAFFINALIST-27-SCAR` — *"If South Carolina is one of the teams to reach the College
> Football Playoff National Championship Game, then the market resolves to Yes."*
> `KXNCAAFSF-27-SCAR` — *"If South Carolina qualifies for the College Football Playoff
> Semifinals in the 2026-27 season, then the market resolves to Yes."*

### Template 6 — pairwise matchup menu (mutex)

> `KXNFLMATCHUP-27SB-BALARI` — *"If Baltimore and Arizona is confirmed to be the matchup in the
> Championship Game in the 2026-27 Pro Football season, then the market resolves to Yes."*
> Secondary: *"The market resolves to Yes when the teams secure the right to participate…"*

256 legs = 16 AFC × 16 NFC. `KXNFLMATCHUP-27AFC`/`-27NFC` are C(16,2) = 120 legs each.
`KXTEAMSINWS-26` is the MLB analogue (225 = 15 × 15).

### Template 7 — player-prop ladder with a void clause

> `KXMLBHIT-26AUG021920BOSLAD-LADFFREEMAN5-2` — *"If Freddie Freeman records 2+ hits in the
> Boston vs Los Angeles D professional baseball game originally scheduled for Aug 2, 2026 at
> 7:20 PM EDT, then the market resolves to Yes."*
> Secondary: *"If Freddie Freeman is scratched or not included in the starting lineup, the
> market will resolve to the fair market price. If Freddie Freeman starts the game but does not
> record a plate appearance, the market will resolve to the fair market price. If Freddie
> Freeman is not in the starting lineup but later enters the game, the market will resolve to
> the fair market price, pinch hit at bats will not count towards the market."*

### Template 8 — deadline ladder

Only 20 events, mostly `KXMLBDEBUT` (`KXMLBDEBUT-GEMERSON` legs `29NOV01, 30MAY01, 30AUG01,
30NOV01`) and `KXNFLENDSTREAK` (mutex, legs `2026-27 season` … `2030-31 season`). The
`KXNFLENDSTREAK` partition is truncated — the drought can persist past 2030-31, so no leg pays.

---

## Settlement

**Sources** (weighted by markets):

| sources | markets |
|---|---|
| ESPN + "the Governing League" | 7,800 |
| ESPN + Fox Sports + "the Governing League" | 6,013 |
| ESPN + Fox Sports | 3,737 |
| ESPN + "Kalshi using information originating from the NCAA" | 3,650 |
| "the Governing League" only | 2,709 |
| ESPN only | 2,706 |
| FIFA | 756 |
| ATP | 443 |
| Gamers World + Sofascore (esports) | 417 |
| AP College Football Rankings | 360 |

Top URLs by market count: espn.com (18,000 + 7,882 + 2,170 across three URL spellings),
foxsports.com (9,362 + 2,800), mlb.com (7,406), nfl.com (5,011), nba.com (2,451),
ncaa.com (3,592 across two paths). "the Governing League" is a trademark-avoidance alias whose
URL identifies the actual league. Every sports market also carries the boilerplate
*"Kalshi is not affiliated, associated, authorized, endorsed by, or in any way officially
connected with the Governing League."*

**Early close**: `can_close_early == True` for **all 34,756** active markets. Conditions:

| `early_close_condition` | markets |
|---|---|
| "This market will close and expire early if the event occurs." | 14,628 |
| "This market will close and expire after the event occurs." | 6,537 |
| "This market will close and expire after a winner is declared." | 5,232 |
| "This market will close and expire after a title holder is declared." | 1,303 |
| "…after the event occurs or the regula[r season ends]" | 1,193 |
| "…early if the season ends earlier tha[n scheduled]" | 1,023 |
| (none) | 802 |
| "…after the matchup is confirmed fo[r …]" | 721 |

The asymmetry matters: "*close early **if** the event occurs*" markets (over-thresholds, first
scorer) settle the moment the threshold is crossed, while "*after a winner is declared*"
markets run to the end of the contest. Two legs of the same logical relation can therefore stop
trading at very different times.

**Settlement timer**: 300s (24,561 markets), 30s (3,111), 1800s (2,494), 120s (1,341), 60s
(1,038), 119s (741), 500s (669), 180s (385). Inside a single soccer game the timers differ by
leg type — moneyline/spread/1H at 30s, correct-score/team-total/first-scorer at 300s — so the
legs of a hedge do not become final simultaneously.

**Horizon** (days from snapshot to `close_time`, active markets):

| p0 | p10 | p25 | p50 | p75 | p90 | p99 | max |
|---|---|---|---|---|---|---|---|
| 0.3 | 2.9 | 5.3 | **80.7** | 188.8 | 272.7 | 1,254.8 | 6,203.7 |

131 markets close within 24h, 10,514 within a week, 14,097 within a month, 10,300 beyond six
months. The 17-year tail is `KXGOLFMAJOR-30`-style "will golfer win a major by 2030" contracts.
`close_time != expiration_time` for 3,835 of 34,756 markets; `expected_expiration_time` is set
on all of them.

---

## Liquidity

Over the 34,756 active markets:

| measure | count | share |
|---|---|---|
| two-sided at the touch (bid > 0 and ask < $1) | 16,919 | **48.7%** |
| ask only (no bid) | 17,025 | 49.0% |
| bid only | 805 | 2.3% |
| no quote at all | 7 | 0.0% |
| open interest > 0 | 16,392 | 47.2% |
| traded in the last 24h | 8,191 | 23.6% |

Spread distribution among the two-sided half:

| p0 | p5 | p25 | p50 | p75 | p90 | p99 |
|---|---|---|---|---|---|---|
| $0.001 | $0.01 | $0.02 | **$0.06** | $0.34 | $0.85 | $0.97 |

Tightening for tradeability (fraction of *all* active markets):

| filter | markets | share |
|---|---|---|
| two-sided | 16,919 | 48.7% |
| two-sided, spread ≤ 2c | 4,527 | 13.0% |
| two-sided, spread ≤ 5c | 7,796 | 22.4% |
| two-sided, spread ≤ 5c, ≥100 contracts on both sides | 3,802 | 10.9% |
| two-sided, spread ≤ 3c, ≥500 both sides | 1,799 | 5.2% |
| two-sided, spread ≤ 2c, ≥1,000 both sides | 1,041 | **3.0%** |

**Roughly 3% of sports markets are genuinely institutional-tradeable; ~11% are retail-tradeable;
the other ~89% are display inventory.** Open interest is even more concentrated: the top 200
markets hold 67.2% of category OI and the top 1,000 hold 90.6%.

Highest-volume series (lifetime volume in contracts, active legs only):

| series | active legs | two-sided | median spread | open interest | volume |
|---|---|---|---|---|---|
| `KXPGATOUR` | 73 | 8.2% | $0.009 | 98.95M | 133.72M |
| `KXSB` | 32 | 71.9% | $0.010 | 45.20M | 52.36M |
| `KXMLB` | 30 | 76.7% | $0.001 | 31.57M | 42.26M |
| `KXMLBGAME` | 76 | 97.4% | $0.010 | 16.81M | 25.02M |
| `KXNBA` | 30 | 50.0% | $0.010 | 15.41M | 19.48M |
| `KXNCAAF` | 50 | 36.0% | $0.010 | 8.42M | 9.37M |
| `KXWTAMATCH` | 62 | 96.8% | $0.010 | 5.17M | 8.04M |
| `KXMLBTOTAL` | 201 | 85.6% | $0.020 | 4.82M | 7.66M |
| `KXNEXTTEAMNBA` | 823 | 11.4% | $0.020 | 5.20M | 7.48M |
| `KXATPMATCH` | 66 | 100.0% | $0.010 | 2.98M | 5.84M |

The top 35 series hold 86.1% of category volume. Note the pattern: the moneyline series
(`KXMLBGAME`, `KXATPMATCH`, `KXWTAMATCH`) are ~100% two-sided at a 1c spread, while the
wide-menu series (`KXNEXTTEAMNBA` 823 legs, `KXPGATOUR` 151 legs) are ~10% two-sided — a few
favourites carry all the flow.

**Nominal quotes.** 11,160 active markets carry an ask with no bid and zero open interest.
The ask on those is often a placeholder rather than a price: 2,004 sit at $0.99, and **650 sit
at exactly $0.44** — 401 of them in `KXNFLMATCHUP` and 228 in `KXBRASILEIROSCORE`. Example:
of the 16 `Seattle vs <AFC team>` Super Bowl matchup legs, 11 quote `bid $0.00 / ask $0.4400`
with zero OI while `KXNFLNFCCHAMP-27-SEA` bids $0.12. Any basket-sum scanner that consumes
`yes_ask_dollars` naively will read those 16 legs as costing $5.82 to cover a $0.12 claim.

`liquidity_dollars` is `0.0000` on **every** market in this snapshot and must not be used;
`notional_value_dollars` is `1.0000` everywhere.

---

## Structural constraints

Convention throughout. For an implication *S ⟹ G* the executable test is

```
buy YES(G) at ask_G  +  buy NO(S) at (1 - bid_S)      -> min payoff $1
violated (net of fees) iff   bid_S - ask_G - f(bid_S) - f(ask_G) > 0
```

For an identity Σᵢ P(Aᵢ) = P(B) both directions are testable:

```
buy legs / sell aggregate:  bid_B - f(bid_B) - Σ (ask_i + f(ask_i)) > 0
sell legs / buy aggregate:  Σ (bid_i - f(bid_i)) - ask_B - f(ask_B) > 0
```

with `f(p) = ceil_to_centicent(0.07·p·(1−p))` (taker; `fee_multiplier = 1` for every sports
series). Maker fees never enter a taker-side violation check but do gate any attempt to *rest*
the passive side of these relations on the 56 maker-fee series.

**19,530 executable checks were run on this snapshot. 3 gross violations exist; 2 survive fees.
Both surviving ones are worth under $0.50 of total notional.**

### C1 — Threshold-ladder monotonicity (all one-sided ladders)

- **Inequality**: for strikes k₁ < k₂ in the same ladder group, `P(X ≥ k₂) ≤ P(X ≥ k₁)`, i.e.
  `yes_bid(k₂) ≤ yes_ask(k₁) + f(·)`.
- **Rule basis**: identical rule text with only the numeral changing —
  *"If the Washington Pro Football team wins at least 1 games in the 2026-27 regular season"* vs
  *"… at least 8 games …"*; strike_type `greater_or_equal` on both.
- **Scope**: 1,895 ladder groups / 8,261 legs / 178 series. 20,789 ordered pairs, **13,978**
  with both required sides quoted.
- **Exactness**: exact. Both legs of a pair always share the same event, so they share the
  postponement and void language verbatim.
- **Failure modes**: (a) a leg finalized while its neighbour is active — a settled `1+ wins`
  leg no longer hedges; (b) different `early_close_condition` between legs of the *same* event
  is not observed, but different `settlement_timer_seconds` is; (c) legs whose subject prefix
  collides — e.g. `KXNFLTSPEC` mixes team and player legs in one event and must be excluded.
- **Live check**: **0 gross violations, 0 net violations** out of 13,978. Tightest observed
  pair leaves −$0.0042 of edge (`KXMLBHR-…-LAAJADELL7-1` bid $0.03 vs
  `KXMLBTB-…-LAAJADELL7-4` ask $0.03: gross exactly zero, fees $0.0042). **Consistent.**

### C2 — Spread ⟹ moneyline

- **Inequality**: `P(team wins by > k−0.5) ≤ P(team wins)` for every k ≥ 2.
- **Rule basis**: *"If Orlando wins by more than 1.5 goals in the Orlando vs Leon professional
  Leagues Cup soccer game … after 90 minutes plus stoppage time (does not include extra time or
  penalties)"* vs *"If Orlando wins the Orlando vs Leon … after 90 minutes plus stoppage time
  (does not include extra time or penalties)"* — identical time basis.
- **Exactness**: exact where the time bases match (verified identical for Leagues Cup, UEL,
  MLB, NFL). No `k = 1` (i.e. "wins by over 0.5") leg exists in any spread family — the minimum
  strike is 1.5 — so the relation is strictly one-directional and can never be closed into an
  equality.
- **Failure modes**: NFL ties resolve moneyline to $0.50/$0.50 while every spread leg resolves
  No, so the hedge pays $1.50 rather than $1.00 in a tie (favourable, not adverse).
  UCL-W spread legs say *"Goal Diff Reg Time"* while the moneyline says *"after 90 minutes plus
  stoppage time"* — same basis, different phrasing; do not pattern-match on the string.
- **Live check**: 1,019 checkable, **0 gross, 0 net**. Tightest:
  `KXMLBSPREAD-26AUG021510KCCOL-KC2` bid $0.01 vs `KXMLBGAME-26AUG021510KCCOL-KC` ask $0.02,
  net −$0.0121. **Consistent.**

### C3 — Sub-period total ⟹ full-period total

- **Inequality**: `P(1H total ≥ k) ≤ P(full total ≥ k′)` for k′ ≤ k; likewise
  `P(first-5-innings runs ≥ k) ≤ P(full-game runs ≥ k′)`.
- **Rule basis**: *"If the total goals scored by Orlando and Leon is more than 0.5 goals in the
  1st Half …"* vs *"If over 0.5 goals are scored in the … game … after 90 minutes plus stoppage
  time"*. Goals/runs are monotone accumulators, so the first-half count is a lower bound on the
  full-time count.
- **Exactness**: exact.
- **Failure modes**: the 1H market's secondary rules differ — *"If the game is cancelled or
  rescheduled to over 48 hours away, the market will resolve to a fair price"* — while the
  MLB F5 markets say *"the market will remain open and close after the rescheduled game has
  finished (within two days)"*. A postponement can void one leg and carry the other. The 1H
  market closes on "after the half ends"; the full-game total closes "early if the event
  occurs" — different early-close triggers.
- **Live check**: 1H⟹full 517 checkable, **0/0**; MLB F5⟹full 134 checkable, **0/0**.
  Tightest: `KXUEL1HTOTAL-26AUG06THUREY-1` bid $0.81 vs `KXUELTOTAL-26AUG06THUREY-1` ask $0.99
  (net −$0.19). **Consistent.**

### C4 — Team total ⟹ game total

- **Inequality**: `P(team scores ≥ k) ≤ P(both teams combined ≥ k′)`, k′ ≤ k.
- **Rule basis**: *"If Arizona scores 2+ runs in the San Diego vs Arizona professional baseball
  game …"* vs *"If San Diego and Arizona collectively score more 2.5 runs …"*.
- **Exactness**: exact (a team's score is a component of the total). Own goals are credited to
  the scoring team in soccer per the team-total secondary rules, which does not disturb the sum.
- **Failure modes**: `settlement_timer_seconds` is 300 on team totals but 60 (MLB) / 30
  (soccer) on game totals.
- **Live check**: 1,041 checkable, **0/0**. Tightest `KXLIGAMXTEAMTOTAL-26AUG02AMESLA-AME1`
  bid $0.90 vs `KXLIGAMXTOTAL-26AUG02AMESLA-1` ask $0.96, net −$0.069. **Consistent.**

### C5 — MLB player-prop stat lattice (cross-series, same player, same game)

Seven exact implications, all following from the definitions in `rules_primary`
(*"records 2+ total bases"*, *"records 1+ hits"*, *"records 1+ home runs"*,
*"records 1+ total hits + runs + rbis"*, *"records 1+ RBIs"*):

| relation | reason |
|---|---|
| `HR(k) ⟹ HIT(k)` | a home run is a hit |
| `HR(k) ⟹ RBI(k)` | a home run drives in at least the batter |
| `HR(k) ⟹ TB(4k)` | a home run is 4 total bases |
| `HR(k) ⟹ HRR(3k)` | a home run yields 1 hit + 1 run + 1 RBI |
| `HIT(k) ⟹ TB(k)` | total bases ≥ hits |
| `HIT(k) ⟹ HRR(k)` | H+R+RBI ≥ H |
| `TB(k) ⟹ HIT(⌈k/4⌉)` | k bases need ≥ ⌈k/4⌉ hits |

- **Scope**: 196 (game, player) groups shared by `KXMLBHIT`/`KXMLBHRR`/`KXMLBTB`/`KXMLBHR`,
  195 for `KXMLBRBI`, 185 for `KXMLBSB`. `KXMLBKS` (pitcher strikeouts) shares **zero** player
  keys with the batting series — do not attempt to relate them.
- **Exactness**: exact on the settled state.
- **Failure modes**: the void clause. All five batting series carry the *same* rules_secondary
  text — *"If Freddie Freeman is scratched or not included in the starting lineup, the market
  will resolve to the fair market price"* — but "fair market price" is determined
  **per market**, so a scratch converts a locked hedge into two independent
  administratively-priced settlements whose difference is unbounded within [−1, 1]. The
  implication holds on realised stats; it does **not** hold through a void. Also note the pinch-
  hit carve-out: *"pinch hit at bats will not count towards the market"*.
- **Live check**: 1,220 checkable pairs across the seven relations, **0 gross, 0 net**.
  Tightest is `HR(1) ⟹ TB(4)`: `KXMLBHR-26AUG021515MILLAA-LAAJADELL7-1` bid $0.03 vs
  `KXMLBTB-26AUG021515MILLAA-LAAJADELL7-4` ask $0.03 — gross exactly $0, net −$0.0042.
  **Consistent.**

### C6 — Correct-score grid ⟹ 1X2 (one-directional only)

- **Inequality**: for a single cell, `P(score h–a) ≤ P(the corresponding 1X2 leg)`; for the
  sub-basket, `Σ_{cells where home wins} ask ≥ ... ` — only
  `Σ_{cells} P ≤ P(1X2 leg)` is valid.
- **Rule basis**: *"If the result is a 0-0 draw … after 90 minutes plus stoppage time (does not
  include extra time or penalties)"* vs *"If Orlando wins the … game … after 90 minutes plus
  stoppage time (does not include extra time or penalties)"* — same basis. Join via
  `custom_strike.home_team_id`/`away_team_id` UUID against `custom_strike.soccer_team`.
- **Exactness**: **the reverse is invalid.** The grid stops at 5 goals per side and omits 4-4,
  5-3, 5-4, 5-5. Selling the sub-basket and buying the 1X2 leg is naked to any uncovered score.
  This is the canonical gap-in-partition trap for this category.
- **Failure modes**: draw sub-basket has only 4 cells (0-0…3-3) against an unbounded set of
  higher draws; grid legs have a 300s settlement timer vs 30s on the 1X2 legs.
- **Live check**: single-cell ⟹ 1X2, 157 checkable, **0/0**; sub-basket ⟹ 1X2 (buy cells / sell
  1X2), 151 checkable, **0/0**. Tightest: `KXUELGAME-26AUG06LARIBE-TIE` bid $0.28 vs the four
  draw cells asking $0.34 combined (net −$0.096). **Consistent.**

### C7 — Tennis exact-match score = match winner (exact identity)

- **Identity**: `P(A wins 2–0) + P(A wins 2–1) = P(A wins the match)`.
- **Rule basis**: *"If Adam Walton wins the … match … by a set score of 2-0"* + *"…2-1"* versus
  *"If Adam Walton wins the Walton vs Brooksby professional tennis match … after a ball has been
  played"*. Best-of-3, `mutually_exclusive: True`, 4 legs tiling the space.
- **Additional**: `P(A wins 2–0) ≤ P(A wins set 1)` and `≤ P(A wins set 2)` against
  `KXATPSETWINNER-<key>-{1,2}`.
- **Exactness**: exact for a completed match. A retirement partway through has a defined match
  winner (*"after a ball has been played"*) but no defined 2-0/2-1 set score — the exact-score
  legs' treatment of a retirement is not stated in the metadata and is an open question.
- **Failure modes**: the ticker mismatch (`WALBRO` vs `WALJBRO`) breaks the naive join on 1 of
  33 ATP matches; `KXWTAEXACTMATCH` **does not exist** (WTA has `MATCH` + `SETWINNER` only), so
  the identity is ATP-only.
- **Live check**: 128 identity checks (both directions), **0 violations**; 124 exact-2-0 ⟹
  set-winner checks, **0/0**. Tightest identity: `KXATPMATCH-26AUG01KOVBOR-BOR` bid $0.75
  against the two exact legs asking $0.77 (net −$0.047). **Consistent.**

### C8 — Esports: winning maps 1 and 2 ⟹ winning a best-of-3

- **Inequality**: `P(match A) ≥ P(map1 A) + P(map2 A) − 1` (Boole). Executable as
  YES(match A) + NO(map1 A) + NO(map2 A), minimum payoff $1.
- **Rule basis**: *"If METANOIA WOLVES wins map 2 in the BetBoom Storm 2026 … CS2 match"* and
  *"If METANOIA WOLVES wins the … match"*.
- **Exactness**: exact **only for best-of-3**. `KXLOLTOTALMAPS`/`KXCS2TOTALMAPS` strikes reveal
  the format: of the 93 events carrying a total-maps market, 90 have only an "Over 2.5 maps"
  leg (bo3) and 3 (all LoL) have `{4, 5}` strikes and no 2.5 leg at all — those are best-of-5,
  where maps 1+2 do not clinch. Those 3 were excluded. **`KXVALORANT` has no `TOTALMAPS` series
  at all**, so its format cannot be verified from metadata; the 48 Valorant checks below assume
  bo3 on the evidence that every Valorant match has exactly map-1 and map-2 events.
- **Failure modes**: format misidentification; map events for maps not yet scheduled
  (`KXLOLMAP` has 52 matches with a map-1 event but only 49 with map-2 and 3 with map-3).
- **Live check**: LoL 92, CS2 84, Valorant 48 checkable — **0 violations** in all three.
  Tightest `KXLOLGAME-26AUG041100KOIAUB-KOIA`: map bids $0.92/$0.92 against a match ask of
  $0.97, net −$0.143. **Consistent.**

### C9 — CFP progression chain (NCAAF)

- **Inequality**: `P(champion) ≤ P(finalist) ≤ P(semifinalist) ≤ P(quarterfinalist) ≤ P(playoff)`
  per team; also `P(top-4 seed) ≤ P(playoff)`.
- **Rule basis**: *"If Ohio St. wins the College Football Playoff National Championship Game"* ⊂
  *"…is one of the teams to reach the College Football Playoff National Championship Game"* ⊂
  *"…qualifies for the College Football Playoff Semifinals in the 2026-27 season"* ⊂
  *"…qualifies for the College Football Playoff Quarterfinals"* ⊂ *"…is one of the teams to
  qualify for the College Football Playoffs"*.
- **Exactness**: exact under the 12-team CFP bracket (a team cannot reach the title game without
  first qualifying for the semifinal).
- **Failure modes**: the year token differs (`KXNCAAFPLAYOFF-**26**` vs `KXNCAAF**-27**`), and
  the close times run in the *wrong* order — `KXNCAAFFINALIST-27-SCAR` closes 2027-01-25 while
  `KXNCAAFSF-27-SCAR` closes 2027-02-07, so the "general" leg outlives the "specific" one.
- **Live check**: 92 checkable pairs, **1 gross violation which survives fees**:

  ```
  KXNCAAFFINALIST-27-SCAR   yes_bid $0.05  (bid size    5.00)
  KXNCAAFSF-27-SCAR         yes_ask $0.04  (ask size  250.00)
  gross  $0.0100
  fees   f(0.05)=$0.0034  +  f(0.04)=$0.0027  =  $0.0061
  net    +$0.0039 per contract, capacity 5 contracts -> $0.0195 total
  ```

  **Violated, but the entire violation is worth 2 cents.** The direction is right (reaching the
  final is priced above reaching the semifinal) and the cause is quote staleness on a 5-contract
  bid, not a mispriced curve.

### C10 — CFP seed partition = playoff qualification (exact identity)

- **Identity**: `Σ_{s=1..12} P(team is the #s seed) = P(team qualifies for the playoff)`, and
  `Σ_{s=1..4} P(team is the #s seed) = P(team is a top-4 seed)`.
- **Rule basis**: *"If Ohio St. is selected as the #9 seed in the 2026-27 College Football
  Playoff"* over s = 1…12 against *"If Ohio St. is one of the teams to qualify for the College
  Football Playoffs"*; every playoff team receives exactly one seed in 1…12. Each
  `KXNCAAFSEED-27S<s>` event is itself `mutually_exclusive: True` over 50 teams.
- **Exactness**: exact provided the seed goes to one of the 50 listed teams.
- **Failure modes**: the 50-team menu is not the whole FBS — a surprise qualifier outside the
  menu breaks the per-seed sum-to-one (though not the per-team seed sum).
- **Live check**: 49 buy-legs/sell-aggregate checks, **0 violations**, but the margin is
  grotesque: e.g. Indiana's 12 seed legs ask $4.76 in total against a $0.72 playoff bid. The
  per-seed baskets are equally unusable — `KXNCAAFSEED-27S2`'s 50 asks sum to $21.40 for a
  claim that must total $1.00, and only 9 of the 600 seed legs carry any bid at all. This
  relation is *structurally* exact and *practically* dead.

### C11 — NFL stage-of-elimination identities

Three exact relations off the 6-leg partition (`REG WC DIV CONF FL FW`):

| relation | rule basis |
|---|---|
| `P(SOE-FW) = P(KXSB-27 team)` | *"Championship Winner: …wins the Pro Football Championship game"* ≡ *"If Arizona wins the 2027 Pro Football Championship"* |
| `P(SOE-FL) + P(SOE-FW) = P(conference champion)` | reaching the title game ≡ winning your conference |
| `Σ all 6 legs = 1` | the six legs exhaust a team's season end-states |
| `Σ_B P(matchup A vs B) = P(A wins conference)` | *"If Baltimore and Arizona is confirmed to be the matchup in the Championship Game"* summed over the 16 opponents |
| `Σ_{pairs ∋ A} P(AFC-final matchup) = P(SOE-CONF) + P(SOE-FL) + P(SOE-FW)` | reaching the conference title game ≡ eliminated no earlier than it |

- **Failure modes**: the SOE legs are thinly quoted (many at 1-contract to 50-contract depth
  with zero OI), and the 1-cent tick floor means a 6-leg partition of near-zero probabilities
  cannot quote below 6c in aggregate. That floor is the direct cause of the one violation below.
- **Live check**:
  - `SOE-FW ⟹ SB` and `SB ⟹ SOE-FW`: 23 + 23 checkable. One **gross** violation
    (`KXSB-27-LAR` bid $0.15 vs `KXNFLSTAGEOFELIM-27LAR-FW` ask $0.14) which fees kill
    (net −$0.0075). **Fee-consistent.**
  - `SOE(FL)+SOE(FW) = conference champion`: 51 checks, **1 net violation**:

    ```
    sell KXNFLSTAGEOFELIM-27CLE-FL  bid $0.01 (size 50)
    sell KXNFLSTAGEOFELIM-27CLE-FW  bid $0.01 (size 50)
    buy  KXNFLAFCCHAMP-27-CLE       ask $0.01 (size 448,571)
    proceeds $0.0200 - fees $0.0014 ; cost $0.0100 + fee $0.0007
    net +$0.0079 per contract, capacity 50 -> $0.395 total
    ```

    **Violated**, and the cause is purely the 1c tick: two legs whose true probabilities are
    ~0.2% each cannot be bid below 1c, while their union quotes 1c.
  - 6-leg basket = $1: 54 checks, **0 violations** (tightest buy-side margin −$0.0995).
  - Super Bowl matchup sum = conference champion: 28 checks, **0 violations**, but see the
    $0.44-placeholder problem — Seattle's 16 legs ask $5.82 against a $0.12 conference bid.
  - AFC-final matchup sum = SOE(CONF+FL+FW): 11 checks, **0 violations**.

### C12 — Tournament round nesting (March Madness, NBA/NHL/MLB conferences, World Cup)

- **Inequalities**:
  `P(champion) ≤ P(reach final) ≤ P(reach F4) ≤ P(reach R8) ≤ P(reach R16) ≤ P(reach R32)`
  (`KXMARMAD` / `KXMARMADROUND-27{T2,F4,R8,R16,R32}`, women's equivalent `KXWMARMAD` /
  `KXWMARMADROUND-27{FIN,SEMI,QF,R16,R32}`);
  `P(top-2 seed) ≤ P(top-3) ≤ P(top-4) ≤ P(top-5)` (`KXMARMADSEED-27T{2..5}`);
  `P(league champion) ≤ P(conference champion)` for NBA/NHL/MLB;
  `P(World Cup champion) ≤ P(World Cup qualifier)`.
- **Rule basis**: *"If Butler qualifies for the 2027 Men's College Basketball Championship
  Game"* vs *"If Butler is the 2026-27 Division 1 Men's College Basketball National Champion"*;
  *"If Mexico is the 2030 FIFA Men's World Cup champion"* vs *"If Mexico qualifies for the 2030
  Men's FIFA World Cup main tournament"*.
- **Exactness**: exact, with one important carve-out — `KXWC-30` has 82 legs but `KXWCQUAL-30`
  has only 76. The six champion-only teams are **Argentina, Portugal, Morocco, Uruguay, Spain,
  Paraguay**: the 2030 hosts, who auto-qualify and therefore have no qualifier contract. The
  implication is undefined, not violated, for those six.
- **Live check**: MARMAD round chain 12 + 24 + 35 + 44 checkable, champion⟹final 56; seed
  nesting 0 checkable (no bids anywhere on `KXMARMADSEED`); women's chain 15;
  champion⟹conference 80 (NBA 15, NHL 25, MLB 23, NCAAF conference 17); World Cup 42.
  **0 gross and 0 net violations everywhere.** Tightest: `KXNHL-27-BOS` bid $0.01 vs
  `KXNHLEAST-27-BOS` ask $0.02 (net −$0.0121). **Consistent.**

### C13 — Division exact-order = division winner; WS matchup grid = pennant

- **Identity**: `Σ_{orders with A first} P(order) = P(A wins the division)`
  (`KXNFLDIVISIONORDER-27NFCWEST`, 24 = 4! legs, against `KXNFLNFCWEST-27`);
  `Σ_{pairs ∋ A} P(WS matchup) = P(A wins its pennant)`
  (`KXTEAMSINWS-26`, 225 = 15×15 legs, against `KXMLBAL-26` / `KXMLBNL-26`).
- **Rule basis**: *"If Seattle finishes first, San Francisco finishes second, Arizona finishes
  third, and Los Angeles R finishes fourth in the NFC West at the conclusion of the 2026-27 Pro
  Football regular season"*, with *"Final standings … determined by the Governing League's
  official tie-breaking methodology"* — the tiebreak clause is what makes the 24-way partition
  exhaustive (no shared positions).
- **Exactness**: exact.
- **Failure modes**: the WS grid is `AL team vs NL team`, so a team appears in exactly 15 legs;
  the division-order legs must be parsed from `yes_sub_title` (`"1: Seattle / 2: …"`) because the
  ticker concatenates codes without a separator (`SEASFARILAR`).
- **Live check**: division order — 24 single-leg implications and 32 basket checks,
  **0 violations** (tightest: NFC West's six LAR-first orders ask $0.80 against a $0.50 winner
  bid). WS grid — 92 single-leg implications and 19 basket checks, **0 violations**; the
  tightest basket in the whole category is San Diego, whose 15 pair legs ask $0.07 more than the
  NL pennant bid. **Consistent.**

### Non-constraints, explicitly

- **Correlation is not structure.** Season win totals and individual game moneylines for the
  same team are statistically related but carry no settlement implication in either direction
  (a team can win any single game and miss any win threshold).
- **Total maps** (`KXLOLTOTALMAPS` "Over 2.5 maps") is not derivable from the map-winner
  marginals: `P(3 maps) = P(A wins m1, B wins m2) + P(B wins m1, A wins m2)` requires the joint.
- **First-5-innings spread** does not imply the game moneyline; a first-5 lead can be lost.
- **First team to score** (`*FTTS`) is scoped *"during the entire game (regulation, stoppage and
  any extra time periods)"* while the total/1X2 markets in the same event are regulation-only.
  Only the one-directional `P(FTTS = No Goal) ≤ 1 − P(regulation total > 0.5)` survives that
  mismatch; do not treat FTTS as regulation-scoped.

---

## Traps a scanner must encode

1. **`mutually_exclusive` gates sum-to-one, and it is not sufficient.** 1,946 of 3,920 sports
   events are mutex, but mutex ≠ exhaustive. The five events whose asks sum below $1 net of fees
   in this snapshot are *all* non-exhaustive menus:
   `KXNEXTTEAMNFL-26BSOR` (32 NFL teams, $0.32 — the player may sign nowhere),
   `KXNCAAMBNEXTCOACH-KU26` (25 named coaches, $0.45),
   `KXJOINCLUB-26OCT02RLEAO` (13 clubs, $0.85), `KXNFLENDSTREAK-40NYJ` (5 seasons, $0.91 — the
   drought can outlast 2030-31), `KXJOINCLUB-26OCT02CROMERO` ($0.93). **There is no genuine
   mutex-basket arbitrage in Sports on this snapshot** — every candidate is a partition with a
   hole.
2. **Correct-score grids are truncated.** 30 cells covering 0-5 per side; 4-4, 5-3, 5-4, 5-5
   and everything above 5 pay nothing. Sub-basket ≤ 1X2 is valid; the reverse is naked.
3. **The $0.44 phantom ask.** 650 zero-bid, zero-OI markets quote exactly $0.4400 (401 in
   `KXNFLMATCHUP`, 228 in `KXBRASILEIROSCORE`); another 2,004 quote $0.99. 11,160 markets in
   total have an ask, no bid and no open interest. Basket sums built from `yes_ask_dollars`
   without a bid/OI filter are meaningless — Seattle's 16 Super Bowl matchup legs "cost" $5.82.
4. **The 1-cent tick floors multi-leg partitions.** A 6-leg or 12-leg partition of near-zero
   probabilities cannot bid below 1c per leg. This alone produces the only surviving basket
   violation in the category (`KXNFLSTAGEOFELIM-27CLE`, $0.395 of capacity).
5. **The year token is not a join key.** `KXNCAAFPLAYOFF-26` belongs to the same lattice as
   `KXNCAAFQF-27`/`KXNCAAFSF-27`/`KXNCAAF-27`; `KXNCAAFSEC-26` to `KXNCAAF-27`. Match on the
   lattice, not on the suffix.
6. **`KXMARMADSEED-27T5` means "top-5 seed", not "the #5 seed"**, whereas `KXNCAAFSEED-27S9`
   means "exactly the #9 seed". Same word, opposite semantics, different families. `T`-prefixed
   slots nest; `S`-prefixed slots partition.
7. **Ticker codes for the same entity differ across series.** ATP: `WALBRO` in `KXATPMATCH` vs
   `WALJBRO` in `KXATPEXACTMATCH`/`KXATPSETWINNER` for the same Aug-3 match (1 of 33). Fall back
   to a `(date, {player names})` join.
8. **Player-prop void resolves to "fair market price", per market.** Five MLB batting series
   share one void clause but resolve independently; a scratch turns an exact cross-stat hedge
   into two administratively-priced legs. The lattice holds on realised stats only.
9. **Time bases differ within one game event.** Soccer 1X2/total/spread/correct-score are
   *"after 90 minutes plus stoppage time (does not include extra time or penalties)"*; FTTS is
   *"during the entire game (regulation, stoppage and any extra time periods)"*. MLB F5/F7
   markets carve out innings. Never assume two legs of the same event share a scope.
10. **Settlement timers and early-close triggers differ leg-by-leg.** Inside one Leagues Cup
    event: 30s on moneyline/spread/1H, 300s on correct-score/team-total/FTTS; and
    "close early *if* the event occurs" vs "close *after* a winner is declared". Legs of a hedge
    do not stop trading or become final together.
11. **The general leg can close before the specific one.** `KXNCAAFFINALIST-27-SCAR` closes
    2027-01-25; `KXNCAAFSF-27-SCAR` closes 2027-02-07.
12. **Finalized legs live inside active events.** 518 markets are `finalized` while their event
    siblings trade. Drop them and reduce the expected basket size before testing sum-to-one.
13. **NFL ties resolve the moneyline pair to $0.50/$0.50**, so the 2-leg basket sums to exactly
    $1 in every state — but every spread leg resolves No in a tie. Postponement handling also
    varies: MLB *"remain open and close after the rescheduled game has finished (within two
    days)"* vs soccer *"cancelled or rescheduled to over 48 hours away → fair price"*.
14. **`liquidity_dollars` is 0.0000 on all 35,344 markets**; `notional_value_dollars` is
    1.0000 on all of them. Neither field carries information in this snapshot.
15. **World Cup hosts have no qualifier contract.** `KXWC-30` has 82 legs, `KXWCQUAL-30` has 76;
    Argentina, Portugal, Morocco, Uruguay, Spain and Paraguay auto-qualify.
16. **Esports format must be read from `TOTALMAPS` strikes.** Of the 93 matches carrying a
    total-maps market, 90 are best-of-3 (a lone "Over 2.5" leg) and 3 are best-of-5 (`{4, 5}`
    strikes, no 2.5 leg), where map-1 + map-2 does not clinch. `KXVALORANT` publishes no
    `TOTALMAPS` series, so its 24 matches have no metadata-derivable format at all.

### Parser defects found in `taxonomy.py` (handled locally here)

- `parse_threshold()` matches only **49.6%** (4,205 / 8,471) of sports ladder legs.
  `_RE_THRESHOLD_PLUS` is anchored with `$` after an optional `pts|points|%`, so any other
  trailing noun fails: `"6+ wins"`, `"1+ wins"`, `"Freddie Freeman: 3+"` (survives, since the
  colon lands in `subject`), and every subject-prefixed over leg — `"Arizona over 1.5 runs
  scored"`, `"Orlando over 0.5 goals"`, `"Carolina wins by over 16.5 points"`,
  `"Jenson Brooksby -4.5 games"` — returns `None`.
  **Fix used here**: take the strike from the market ticker's trailing integer and the subject
  from the prefix; gate on `strike_type ∈ {greater, greater_or_equal}`. Cross-checked against
  the subtitles, the ticker integer ordering is correct in every group (the 173 apparent
  disagreements are artefacts of "last number in the subtitle" — `"Over 0.5 1H goals"` ends in
  the `1` of `1H`, `"Arizona -2.5 first 5 innings"` ends in `5`).
- `classify_event()` reports 19 `combination` events; **11 are false positives**. The
  `re.search(r"\band\b")` clause fires on national-team names — `Bosnia and Herzegovina`,
  `Antigua and Barbuda`, `St. Kitts and Nevis`, `Trinidad and Tobago` — inside `KXWC`,
  `KXUEFAEURO`, `KXCOPAAMERICA`, `KXCONCACAFGC`, `KXCONCACAFNL`, `KXCPL`, `KXCPLMATCH`, which
  are ordinary entity menus. Only `KXPGA3BALL` and `KXNFLTSPEC`
  (`"Cam Skattebo records 75+ rushing yards and 75+ receiving yards in a single game"`) are
  genuine conjunctions. A safer test is "**every** leg contains a conjunction", which yields 8.
- `classify_event()` labels 2,909 events `entity_menu`, absorbing most season-win and
  spread ladders because their subtitles carry a subject prefix. `strike_type` is the reliable
  discriminator in this category, not subtitle shape.

---

## Open questions

1. **Tennis retirement and the exact-score identity.** `KXATPMATCH` explicitly settles *"after a
   ball has been played"*, so a retirement produces a match winner. `KXATPEXACTMATCH` legs say
   *"by a set score of 2-0"*; nothing in the metadata says how a retirement at 1-0 in sets
   resolves the four exact-score legs. If they all resolve No, the identity in C7 fails and the
   basket is short a state. Resolvable only from the contract terms document.
2. **"Fair market price" mechanics.** Player props, cancelled games and postponed-beyond-window
   games all resolve *"to a fair price in accordance with the rules"*. The metadata does not
   define the reference (last trade? midpoint? time-weighted?), so every void-exposed hedge has
   an unquantifiable basis leg.
3. **Exhaustiveness of the seed and next-team menus.** `KXNCAAFSEED-27S<s>` is mutex over 50
   named teams; whether Kalshi guarantees the seed lands inside that 50 (and what happens if it
   does not) is not in the metadata. Same for `KXNEXTTEAMNBA` — the `"Stays with Boston or
   Retires"` leg suggests deliberate exhaustiveness, but `KXNEXTTEAMNFL` has no such leg and
   quotes as if the residual state exists.
4. **`DIRECNET` collateral.** 30 events use it rather than `MECNET` or blank. Which families,
   and what netting behaviour it implies for multi-leg positions, is not derivable here.
5. **Maker-fee eligibility for the passive side of these relations.** Every relation above is
   tested against taker prices. Resting the passive leg on one of the 56 maker-fee series costs
   `0.0175·P(1−P)`, but whether a two-leg cross-series structure can be quoted as a single
   maker order (and whether it nets collateral across events, given `MECNET` is event-scoped)
   is a platform question, not a metadata one.
6. **Placeholder quote provenance.** The uniform $0.44 ask on 650 zero-OI markets looks
   machine-generated. Whether it is an exchange-side seeded quote or one participant's default
   determines whether it is executable at all.
7. **Valorant match format.** `KXVALORANTGAME` (24 matches) and `KXVALORANTMAP` (map-1 and
   map-2 for all 24) exist, but there is no `KXVALORANTTOTALMAPS` series, so nothing in the
   metadata states whether these are bo3 or bo5. The C8 conjunction bound is only valid for the
   former.
8. **`KXNFLTSPEC` conjunction legs** (`"75+ rushing yards and 75+ receiving yards in a single
   game"`) have no single-stat single-game counterpart in this snapshot, so their conjunction
   bounds cannot be closed. Whether Kalshi lists the marginals elsewhere during the season is
   unknown.
