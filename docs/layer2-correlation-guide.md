# Layer 2: the correlation track

> **[中文版 →](layer2-correlation-guide.zh.md)**

This document is the research map of the project. Its job is to answer three questions
with measured numbers: **which groups of Kalshi markets share a driver without being
bound by settlement rules, how much money each group can actually hold, and therefore
which directions deserve research investment next.**

The premise comes from Layer 1: everywhere the rules *bind* two markets, the market
already holds them tight — that surface is catalogued, and its capacity is small.
Layer 2 is everything the rules do **not** bind — different functions of
one state variable, with nothing forcing them to agree. No binding means no riskless
correction, no arbitrage capital closing gaps, and mispricings that persist for days to
weeks instead of milliseconds. That persistence is measured below, not assumed.

Every number here was computed on the 2026-08-04 census snapshot (9,820 open events,
77,784 active markets) or re-measured against fresh public-API candlesticks the same
day. Nothing is carried forward on faith.

## The verified scorecard

| Driver class | Clusters | Active markets | 24h volume (share) | Open interest | 24h vol / OI | Two-sided quoted | Horizon | Maker fee |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 same game | 539 | 10,803 | 5.85M (11.7%) | 5.5M | **1.06** | 85.6% | median 5 days | **charged** on flagship series |
| 2 same race | 505 | 7,404 | 153k (0.31%) | **13.2M** | **0.012** | **98.9%** | election 2026-11-03 | **0** on all 67 series |
| 3 same underlying | 20 | 8,941 | 2.16M (4.31%) | 23.8M | 0.091 | 29.0% | 79% expire < 1 day | 0 (hourly) |
| 4 same release | 5 | 1,446 | 303k (0.61%) | 9.5M | 0.032 | 74.2% | scheduled prints | **charged** on 7 headline series |

Volumes above are contracts. Two measurement traps: race markets all carry the
placeholder `close_time` 2027-11-03 (the economic horizon is election day, 2026-11-03 —
91 days from snapshot); and `liquidity_dollars` is unpopulated across the snapshot, so
depth must come from `yes_bid_size`/`yes_ask_size`.

## What each direction can hold (measured capacity, in dollars)

Premium = contracts × price. "Deploy now" = the dollars executable against the standing
top-of-book (`Σ ask_size×ask + Σ bid_size×bid`). "Envelope" = a stated-assumption
sustainable book: 10% participation of premium ADV × class-typical holding days — a
heuristic, not an impact model.

| Class | Premium $/day | Deploy now | OI value | Envelope (holding assumption) |
| --- | --- | --- | --- | --- |
| 1 games | $2.85M | $8.6M | $2.6M | ~$57k (0.2d intra-game) |
| 2 races | $75.6k | $857k | **$6.2M** | ~$38k (5d recycle) — ~$227k (30d news hold) |
| 3 windows | $951k | $1.4M buy-side* | $3.4M | ~$48k (0.5d) |
| 4 releases | $114k | $703k | $1.9M | ~$34k (3d straddle) |

*Class 3's sell side quotes $17.4M but it is dominated by 99¢ deep-ITM resting bids on
KXBTCD threshold markets — technically executable, zero edge capacity; the $1.4M
buy-side is the honest gauge.

**The honest headline: today, the entire Layer-2 surface supports book sizes in the
tens to low hundreds of thousands of dollars — this is a research field, not an
immediate deployment venue.** Three qualifiers keep that from being a dismissal:

- Class 2's constraint is *flow*, not *inventory*: $6.2M of open-interest value sits
  against $75.6k/day of trading. The books exist; they are dormant until election
  season. How much the season multiplies volume is **unmeasured** — Kalshi no longer
  serves 2024-cycle market data through the public API (the 2024 events exist but
  their markets and candlesticks are purged; verified 2026-08-04), so the seasonal
  upside rests on the parked OI and the 91-day calendar, not on a measured multiple.
- ADV is a single-day snapshot (2026-08-04), and class 1's slate changes daily.
- Depth is top-of-book only: it understates thick books and overstates stale quotes.

## The research agenda (ranked directions)

Ordering: races first (measured persistence, no resident fast money, maker-free,
seasonal runway), releases second (scheduled catalysts, everything trades — but
persistence unmeasured and headline series charge makers), games third (most flow,
occupied fast lane), windows last as a venue (79% intraday — the speed game) while
staying the best laboratory for term-structure models. Within each direction, this is
where the liquidity actually is:

### Class 2 — the races worth studying (top of 505, by premium $/day)

What is correlated with what: each row is one cluster of distinct markets repricing on
the same reality — the correlation lives *between the members inside the row*. Statewide
rows (MI, TX, GA, NE, ME) pair the governor-party market with the senate-party market:
one state, one election day, one electorate, so both load on state mood plus the
national wave — and the class-6 combo grids price exactly that correlation (MI implied
φ ≈ +0.55). District rows (OH-07, TX-15, TX-28) hold one race's winner market, both
parties' margin ladders, and turnout — four functions of one polling state; OH-07's
4-day ladder lag (below) is what that correlation looks like when nobody enforces it.
Member tickers for every row are in `race_clusters.csv`'s `members` column; the dollar
columns are only the screen for where research time pays.

| Race | Families | Premium $/day | OI value | Top-of-book depth |
| --- | --- | --- | --- | --- |
| MI (Gov+Sen) | 2 | $20,970 | $181k | $4.8k |
| TX (Gov+Sen) | 2 | $20,536 | **$2.54M** | $22.5k |
| GA (Gov+Sen) | 2 | $8,876 | $396k | $11.9k |
| OH-07 (House) | 4 | $5,631 | $17.8k | $1.7k |
| TX-Sen | 3 | $3,286 | $22.5k | $1.1k |
| TX-15 (House) | 4 | $2,580 | $39.9k | $1.1k |
| TX-28 (House) | 4 | $1,483 | $12.5k | $1.6k |
| PA-03 (House) | 3 | $1,210 | $0.8k | $1.7k |
| NE (Gov+Sen) | 2 | $1,105 | $177k | $16.1k |
| ME (Gov+Sen) | 2 | $1,040 | **$952k** | $20.8k |

The dropoff is steep and defines the research universe: top-5 races = 78% of class
premium volume, top-20 = 95%, and only 33 of 505 clusters trade ≥ $100/day. A lead-lag
study should start with the four-family House races that actually trade (OH-07, TX-15,
TX-28 — winner + both margin ladders + turnout all listed) and the statewide Gov+Sen
pairs (MI, TX, GA) where the combo grids also price the correlation. ME and TX are the
inventory plays — massive parked OI against trickle volume.

### Class 3 — the underlyings that are alive (of 20 ranked)

BTC is the complex: $678k/day premium — 71% of the class. Then WTI ($92k), INX ($47k),
GOLD ($38k), ETH ($38k), SOL ($20k), NASDAQ100 ($14k), SILVER ($11k); everything below
COPPER/NATGAS (~$3.4k) is dust, and the tail is dead (DOGE $138, DJI $65, SHIBA $39,
NEAR $0/day). A window/term-structure model has exactly one first target (BTC's 8
window series) and four second targets; the other twelve underlyings are not worth
research time at current liquidity.

### Class 4 — the releases (all 5 ranked)

U3 ($38.1k/day), CPI ($32.8k), FED ($32.1k) are the working surface — three roughly
equal complexes with real depth ($72k–$292k top-of-book). RATECUT trades little
($6.1k/day) but holds the class's largest inventory ($918k OI value — long-duration
positioning). GDP is the weakest ($4.6k/day). Release-chain research = U3/CPI/FED
first; remember all three headline series charge maker fees.

### Class 1 — the game complexes (top series, aggregated across games)

| Series | Games (Aug 4) | Premium $/day | Maker fee |
| --- | --- | --- | --- |
| KXARGNACBGAME (Argentine 2nd div) | 3 | $492k | **free** |
| KXMLBGAME | 41 | $455k | charged |
| KXLOLGAME (LoL esports) | 66 | $304k | **free** |
| KXATPMATCH (tennis) | 28 | $218k | charged |
| KXCLUBFGAME (club friendlies) | 34 | $141k | **free** |
| KXLEAGUESCUPGAME | 36 | $129k | **free** |
| KXKBOGAME (Korean baseball) | 21 | $69k | **free** |

The useful surprise: the maker-fee flagships (MLB, ATP, WNBA) are *not* where the
per-game density is. Argentine second-division soccer, LoL esports, club friendlies and
KBO run comparable dollar flow **maker-free** — those are the venues where an intra-game
lead-lag model can quote passively without paying the 2.94¢ round-trip. Game keys churn
daily; the durable research direction is the series complex, not the individual game.

## Class-by-class detail

### Class 1 — same game: (scoreline, clock) drives up to 18 books at once

539 games ([`game_clusters.csv`](../data/layer2/game_clusters.csv)) carry 2+ market
types simultaneously (moneyline, spread, total, team totals, player props, first-half
variants); the densest carry 18. One run scored reprices all of them — which book moves
first is the intra-game lead-lag question. Verified profile: 11.7% of exchange 24h
contract volume, $2.85M/day premium, median top-of-book depth 392 contracts (deepest
class), 85.6% two-sided. But the class turns over its entire open interest daily
(ratio 1.06) — resident fast money — and the flagship series (the MLB/NFL/ATP/UCL/WNBA
game, spread and total books) charge maker fees. Capacity: the flow is the deepest of
the four classes but the 0.2-day holding window caps a 10%-participation book at ~$57k.
Same-game series also settle off different sources (ESPN vs league-official) with
different cancellation branches. Verdict: the right venue for *measuring* microstructure
lead-lag — start in the maker-free complexes (ARGNACB, LOL, KBO) — the wrong venue for
slow capital.

### Class 2 — same race: polling state drives winner, margin ladder, and turnout

The flagship. 505 races for Nov 2026 carry ≥2 independent market families; 320 carry
all three (winner, margin-of-victory ladder per party, turnout). All repricing on one
latent variable — the race's polling/news state. What is actually measured (fresh
candles, 2026-04-01 → 2026-08-04; both exemplar races are rows in
[`race_clusters.csv`](../data/layer2/race_clusters.csv)):

- **The base leads the derivative, by days.** OH-07: the
  [winner market](https://kalshi.com/markets/kxhouserace/house-race-winner/kxhouserace-oh07-26)
  moved +25.5¢ (mid 0.365 → 0.620, Jul 26 → 29, volume-confirmed). The same-party
  [margin leg](https://kalshi.com/markets/kxmidtermmov/midterm-margin-of-victory/kxmidtermmov-oh07d)
  (OH07D-P2) captured 18% of that move on day one, then sat frozen through Aug 1 —
  it first reached even 25% of the base move on Aug 2, **4 days after the move
  completed**. And the window was liftable, not just visible at mid: P2's ask sat
  unmoved at 34¢ from Jul 28 through Aug 1 with zero contracts printed, then traded
  600 contracts on Aug 2 and bid 47¢ on Aug 3 — a standing +13¢ repricing available
  for four days. (Quoted size is not recorded in daily candles, so the depth of that
  window is the one thing this measurement cannot pin.)
- **Mispricings stay open for weeks.** VA-06: the
  [D-by-3+ margin leg](https://kalshi.com/markets/kxmidtermmov/midterm-margin-of-victory/kxmidtermmov-va06d)
  has priced *above* the
  [D-winner leg](https://kalshi.com/markets/kxhouserace/house-race-winner/kxhouserace-va06-26)
  (which it logically implies) for **47 consecutive days at mid, 15 consecutive days
  tradably (margin bid > winner ask), and was still crossed in the snapshot**.
  (Quote-based: whether a real lift fades or partial-fills is untested — one micro-lift
  would convert this from quote evidence to execution evidence.) Net of fees the recent
  edge is ~0–2¢ on 15–100 contracts — not an income stream, but a standing sign that
  nobody is enforcing coherence here — or that the prize is too small for any resident
  to bother, which at this size is indistinguishable.
- **The lag is conditional, not universal.** VA-06's own +40¢ repricing in May was
  tracked by every margin leg with 0-day lag; OH-07's opposite-party ladder was also
  fast (0–1 days). The slow legs are the thin, same-party, off-focus ones. Modelling
  *when* the ladder is slow is the actual research problem — and the reason this is a
  strategy space rather than a mechanical harvest.

Execution profile: 98.9% two-sided (an MM quotes essentially every race) but thin —
median top depth 200 contracts, volume concentrated (top-10 markets = 69% of class
volume). All 67 series are maker-free with standard taker fees (the well-known
zero-taker political series — KXTRUMPOUT, KXGREENLAND, etc. — are one-off topicals,
*not* these race families). Capacity: ~$38k book under 5-day convergence recycling,
~$227k under a 30-day news-cycle hold, against $6.2M of parked OI — flow-constrained
today, inventory-rich for the season. The play: maker-first convergence and lead-lag
capture, sized to grow as election-season volume arrives. Two honesty notes: most race
markets print zero contracts most days, so a resting quote may never fill — and the
taker who does cross it is plausibly informed, so time-to-fill and post-fill markout
are stage-one paper-trading measurements. And the empty-lane reading was taken
off-season; the same seasonal volume that brings fills can bring competition, so
occupancy must be re-measured as volume arrives.

### Class 3 — same underlying, many windows: one price path, 104 series

20 underlyings ([`underlying_windows.csv`](../data/layer2/underlying_windows.csv) —
[BTC](https://kalshi.com/markets/kxbtc), ETH, S&P, Nasdaq, WTI, gold, silver, …) each
feed 2–11 window series — hourly range, daily threshold, monthly/annual extremes,
relative-value pairs — all 104 verified live. 8,941 active markets (dense strike
ladders), $951k/day premium of which BTC is 71%. But: 79% of active markets expire
within a day (KXNASDAQ100U alone is 2,800 markets), only 29% are two-sided at any
moment, and the identity-arb harvester measured at 22.97ms operates in the adjacent
Layer-1 space — this is the speed lane. Capacity: ~$48k envelope at intraday holding;
the headline deploy-now number is inflated by deep-ITM bids (see capacity table). Fee
oddities worth knowing: the annual crypto series KXBTCY/KXETHY are **zero-fee both
sides** (the cheapest correlation legs on the exchange), while KXINXY/KXNASDAQ100Y
charge makers. Use this class to *fit* window/term-structure models on the BTC complex;
trade it only with infrastructure already proven at millisecond scale.

### Class 4 — same release: one macro print reprices whole families

Five families ([`release_families.csv`](../data/layer2/release_families.csv):
[CPI](https://kalshi.com/markets/kxcpi) ×10 series, [Fed](https://kalshi.com/markets/kxfed) ×9,
GDP ×5, U3 ×3, rate-cut ×2) — 29 series, 112 events, 1,446 active markets. Uniquely,
everything here actually trades: median *lifetime* volume per active market is 368
contracts, versus 0 in every other class and 2 exchange-wide. The catalyst is scheduled
to the minute, the family repricing is simultaneous and cross-checkable (headline vs
core vs YoY ladders vs point-mass menus vs combo grids), and 72% of the book is
long-dated strips, so positioning ahead of a print is structurally possible. Capacity:
~$34k envelope on a 3-day straddle window, $703k standing at top-of-book. The tax: the
7 headline series charge maker fees, so release-day passive quoting pays; chain trades
that cross spreads pay 2.94¢ round-trip at mid-range prices. Second-best direction: the
known-catalyst structure compensates the fee drag, and the point-mass ⊆ ladder
relations inside each family double as free risk checks (those pairs are Layer-1
bindings; the rest of the family is shared-driver).

### Class 5 — same narrative: co-movement without a measurable driver

Iran-escalation, Greenland-acquisition, Trump-legal clusters: legs that reprice on one
news stream but share no settlement variable. Audited conclusion stands: **not bound** —
a narrative spread can widen without limit, and there is no machine-readable universe to
enumerate. Kept as a research option, never as a systematic book.

### Class 6 — the national swing factor: measured, not assumed

Every partisan race loads on one national factor, and the exchange itself prices the
loading: the nine state Governor×Senate combo grids imply a joint distribution.
Recomputed from snapshot mids (renormalised 2×2 grids, Pearson φ on Dem-win indicators):

| [KS](https://kalshi.com/markets/kxkssengovcombo) | [OH](https://kalshi.com/markets/kxohsengovcombo) | [MN](https://kalshi.com/markets/kxmnsengovcombo) | [MI](https://kalshi.com/markets/kxmisengovcombo) | [IA](https://kalshi.com/markets/kxiasengovcombo) | [AK](https://kalshi.com/markets/kxaksengovcombo) | [GA](https://kalshi.com/markets/kxgasengovcombo) | [ME](https://kalshi.com/markets/kxmesengovcombo) | [NH](https://kalshi.com/markets/kxnhsengovcombo) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| +0.57 | +0.56 | +0.56* | +0.55 | +0.45 | +0.44 | +0.37 | +0.24 | **−0.13** |

Median +0.45; the national House×Senate combo implies +0.34. The outliers are
interpretable, which is what makes the lens credible: NH's firmly negative φ (bid/ask
corner range entirely below zero) is a split-ticket state — Republican-favorite governor
race alongside a Democratic-favorite Senate race; ME's low +0.24 is Collins-specific.
(*MN is weakly identified — both cross legs one-sided. GA, ME and MI each carry one
one-sided near-zero leg, and ME has the largest renormalisation slack, mids summing
1.055; NH is the firm one — all four legs two-sided, corner range entirely negative.)
Use: hedge ratios for cross-race books, and a live wave-factor gauge no poll aggregator
publishes.

### Class 7 — same question, two venues: unexplored

Kalshi vs Polymarket duplicate questions. Not collected in this repo; public L2 archives
make the study feasible, and the Layer-1 work found the only genuinely open riskless
residual sits cross-venue (zero-fee negRisk structures). The lead-lag version — which
venue's politics prices move first — is an obvious, untouched study.

## Starting a study (the intended first experiment)

1. Pick pairs from [`race_clusters.csv`](../data/layer2/race_clusters.csv) — start with
   the agenda table above (OH-07, TX-15, TX-28 for four-family lead-lag; MI/TX/GA for
   statewide pairs); the OH-07/VA-06 rows are worked examples of what to look for.
2. Pull both legs' history: `GET /series/{s}/markets/{t}/candlesticks` (daily reaches
   back to 2024-11, hourly covers months; `src/kalshi_structure/history.py` is a
   checkpointed collector). Forward-fill bid/ask closes — candles are omitted on
   no-update days, and trade-based `price.close` goes stale.
3. Estimate the lag event-time: condition on base-leg moves ≥ N¢, measure the
   derivative's response-time distribution, and **model the conditioning** — same-party
   vs opposite-party leg, ladder depth, distance from focus (the lag is episodic, and
   the episodes are the trade).
4. Paper-trade maker-first convergence (race series charge no maker fee), gated by the
   Layer-1 condition checklist (settlement-source parity, payout-branch parity).
5. Pre-register kill conditions before looking at P&L — the discipline that kept this
   project honest.

## The warnings that transfer

- **No floor.** A Layer-2 spread can widen forever; Iran-cluster legs are not bound.
  Size like a model trade, never like an arbitrage.
- **The lag is not a law.** Fast episodes (0-day tracking) and slow episodes (4-day
  lag) coexist in the same race. Trade the conditions, not the average.
- **Beta is regime-dependent.** NH's −0.13 is a split-ticket story, not noise; a wave
  hedge calibrated on the +0.5 pack fails exactly there.
- **Capacity numbers are envelopes, not promises.** Single-day ADV snapshot,
  top-of-book depth only, a heuristic participation assumption, and an unmeasured
  seasonal multiple (2024-cycle data is purged from the public API). Re-measure before
  sizing anything.
- **Instrument traps.** Race `close_time` is a placeholder a year past the election;
  `liquidity_dollars` is dead in the census; thin legs quote one-sided and bias mids;
  class 3's sell-side depth is inflated by 99¢ deep-ITM bids.
- **Check the [Layer-3 trap list](correlation-taxonomy.md) first.** Several "obvious"
  co-movers (spot vs daily-extremum, monthly-max vs annual-max) are look-alikes with
  different observation windows, not shared drivers.
