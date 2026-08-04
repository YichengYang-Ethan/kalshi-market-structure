# Layer 2: the correlation track

This is the core result of the project. Layer 1 proved that everywhere settlement rules
*bind* two markets together, the market already holds them tight — standing riskless
capacity ≈ $0, and the fast end is harvested by a millisecond-scale participant. Layer 2
is everything the rules do **not** bind: markets that are different functions of one
state variable. The state moves, all of them should reprice together, and nothing forces
them to. That difference — no binding, therefore no riskless correction, therefore no
arbitrage capital closing gaps — is exactly why mispricings here persist for days to
weeks instead of milliseconds, and why this is the open strategy space.

Every number below was recomputed on the 2026-08-04 census snapshot (9,820 open events,
77,784 active markets) and, for the dynamics claims, re-measured against fresh public-API
candlesticks pulled the same day. Nothing is carried forward on faith.

## The verified scorecard

| Driver class | Clusters | Active markets | 24h volume (share) | Open interest | 24h vol / OI | Two-sided quoted | Horizon | Maker fee |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 same game | 539 | 10,803 | 5.85M (11.7%) | 5.5M | **1.06** | 85.6% | median 5 days | **charged** on flagship series |
| 2 same race | 505 | 7,404 | 153k (0.31%) | **13.2M** | **0.012** | **98.9%** | election 2026-11-03 | **0** on all 67 series |
| 3 same underlying | 20 | 8,941 | 2.16M (4.31%) | 23.8M | 0.091 | 29.0% | 79% expire < 1 day | 0 (hourly) |
| 4 same release | 5 | 1,446 | 303k (0.61%) | 9.5M | 0.032 | 74.2% | scheduled prints | **charged** on 7 headline series |

Exchange totals for scale: 50.1M contracts/24h, 649M open interest. Two measurement
traps: race markets all carry the placeholder `close_time` 2027-11-03 (the economic
horizon is election day, 2026-11-03 — 91 days from snapshot); and `liquidity_dollars`
is unpopulated ("0.0000") across the entire snapshot, so book depth must come from
`yes_bid_size`/`yes_ask_size`, not that field.

## Why the ranking comes out the way it does

A correlation trade needs six things. Score each class against them and the ranking is
not a matter of taste:

1. **Proof that mispricing persists** — the whole premise. Class 2 has it measured
   (below: a 4-day ladder lag and a 47-day crossing, ongoing). Classes 1 and 3 have the
   opposite evidence: turnover of 1.06 and 0.091 means fast money is already resident.
2. **An execution surface** — you must be able to get filled. Class 2 is 98.9%
   two-sided (a market maker blankets every race), the highest of the four classes
   measured;
   class 3 is 29% (far-OTM ladder rungs are unquoted).
3. **Fee regime** — correlation trades are maker-style (post, wait for convergence).
   All 67 race series are maker-free; the flagship game series (KXMLBGAME, KXNFLGAME/
   SPREAD/TOTAL, KXATPMATCH, KXUCLGAME, KXWNBAGAME) and the 7 headline release series
   (KXCPI, KXCPIYOY, KXFED, KXFEDDECISION, KXGDP, KXRATECUTCOUNT, KXU3) charge makers.
   At a 30¢ price the taker fee is 1.47¢/contract/leg — a 2.94¢ round-trip that a
   maker-free class simply does not pay.
4. **Competition** — class 2's 24h-volume/OI of 0.012 is 91× slower than the game
   clusters, and a tradable violation sat open 15 consecutive days without being
   lifted. That is consistent with an empty slow lane — but at ~0–2¢ net on ≤100
   contracts it is also a violation no resident would bother lifting, so absence of
   enforcement at this size does not prove absence of competition at economic size.
5. **Instrumentation** — a machine-readable pair universe plus an observable catalyst.
   Class 2 ships 505 clusters (320 with winner+margin+turnout all listed) and its
   catalysts are public (polls, filings, news). Class 5 (narratives) fails exactly here.
6. **Runway** — class 2 carries 13.2M contracts of open interest that must activate
   into the Nov-2026 midterms; volume in these markets is seasonal and the season is
   ahead, not behind.

**Class 2 (races) is the primary target — here is the honest tally, not a clean
sweep.** It wins outright on persistence (the only class with a *measured* multi-day
mispricing) and on competition (turnover 91× slower than the games). On fees it ties
class 3's maker-free hourly series — and the single cheapest legs on the exchange are
actually class 3's zero-fee annual crypto series. On execution it trades depth for
breadth: quoted everywhere, but thinner at top of book (200) than the games (392). The
runway axis is a judgment, not a measurement: 13.2M OI parked ahead of one scheduled
national event. So the primary-target call rests on axes 1 and 4 plus that seasonal
judgment, stated as such. The ordering below it is likewise a weighing, not arithmetic:
class 4 second because its known-catalyst structure is the closest substitute — noting
that persistence there is **unmeasured**, not confirmed (running the OH-07-style lag
study on a CPI family is an open task). Class 1 third: most 24h volume and deepest
books, but the fast lane is occupied and the flagships charge makers. Class 3 last as a
trading venue (79% expires within a day — structurally the speed game) while remaining
the best *laboratory* for window/term-structure models.

## Class-by-class detail

### Class 1 — same game: (scoreline, clock) drives up to 18 books at once

539 games carry 2+ market types simultaneously (moneyline, spread, total, team totals,
player props, first-half variants); the densest carry 18. One run scored reprices all of
them — which book moves first is the intra-game lead-lag question. Verified profile:
11.7% of exchange 24h volume lives here (top clusters on 2026-08-04: an Argentine
second-division match at 1.09M contracts, a LoL esports series at 461k, a club friendly
at 392k — note how far down the sporting food chain real volume reaches), median top-of-
book depth 392 contracts (deepest class), 85.6% two-sided. But the class turns over its
entire open interest daily (ratio 1.06) — resident fast money — and the flagship
series (the MLB/NFL/ATP/UCL/WNBA game, spread and total books) charge maker fees, so
the passive side of a convergence trade there pays up to 2.94¢ round-trip. (The
snapshot's highest-volume clusters — Argentine soccer, LoL — are maker-free; the fee
map is series-by-series, not class-wide.) Same-game series also settle off different sources (ESPN vs league-official)
with different cancellation branches. Verdict: the right venue for *measuring* microstructure
lead-lag; the wrong venue for slow capital.

### Class 2 — same race: polling state drives winner, margin ladder, and turnout

The flagship. 505 races for Nov 2026 carry ≥2 independent market families; 320 carry
all three (winner, margin-of-victory ladder per party, turnout). All repricing on one
latent variable — the race's polling/news state. What is actually measured (fresh
candles, 2026-04-01 → 2026-08-04):

- **The base leads the derivative, by days.** OH-07: the winner market moved +25.5¢
  (mid 0.365 → 0.620, Jul 26 → 29, volume-confirmed). The same-party margin leg
  (OH07D-P2) captured 18% of that move on day one, then sat frozen through Aug 1 —
  it first reached even 25% of the base move on Aug 2, **4 days after the move
  completed**. And the window was liftable, not just visible at mid: P2's ask sat
  unmoved at 34¢ from Jul 28 through Aug 1 with zero contracts printed, then traded
  600 contracts on Aug 2 and bid 47¢ on Aug 3 — a standing +13¢ repricing available
  for four days. (Quoted size is not recorded in daily candles, so the depth of that
  window is the one thing this measurement cannot pin.)
- **Mispricings stay open for weeks.** VA-06: the D-by-3+ margin leg has priced *above*
  the D-winner leg (which it logically implies) for **47 consecutive days at mid, 15
  consecutive days tradably (margin bid > winner ask), and was still crossed in the
  snapshot**. (Quote-based: whether a real lift fades or partial-fills is untested —
  one micro-lift would convert this from quote evidence to execution evidence.) Net of fees the recent edge is ~0–2¢ on 15–100 contracts — not an income
  stream, but a standing proof that nobody is enforcing coherence here.
- **The lag is conditional, not universal.** VA-06's own +40¢ repricing in May was
  tracked by every margin leg with 0-day lag; OH-07's opposite-party ladder was also
  fast (0–1 days). The slow legs are the thin, same-party, off-focus ones. Modelling
  *when* the ladder is slow is the actual research problem — and the reason this is a
  strategy space rather than a mechanical harvest.

Execution profile: 98.9% two-sided (an MM quotes essentially every race) but thin —
median top depth 200 contracts, 24h volume concentrated (top-10 markets = 69% of class
volume; today's hot spots are the TX/MI/GA governor+senate pairs). All 67 series are
maker-free with standard taker fees (the well-known zero-taker political series —
KXTRUMPOUT, KXGREENLAND, etc. — are one-off topicals, *not* these race families; do not
carry that assumption over). The play: maker-first convergence and lead-lag capture,
sized to grow as election-season volume arrives. Two honesty notes before sizing
anything: most race markets print zero contracts most days, so a resting quote may
simply never fill — and the taker who does cross it is plausibly informed (a fresh
poll, a local filing), so expected time-to-fill and post-fill markout are stage-one
paper-trading measurements, not afterthoughts. And the empty-lane reading above was
taken off-season; the same seasonal volume that will bring fills can bring competition,
so occupancy must be re-measured as volume arrives.

### Class 3 — same underlying, many windows: one price path, 104 series

20 underlyings (BTC, ETH, S&P, Nasdaq, WTI, gold, silver, …) each feed 2–11 window
series — hourly range, daily threshold, monthly/annual extremes, relative-value pairs —
all 104 verified live. 8,941 active markets (dense strike ladders), 4.31% of exchange
24h volume, BTC alone 1.46M contracts/day. But: 79% of active markets expire within a
day (the hourly complexes; KXNASDAQ100U alone is 2,800 markets), only 29% are two-sided
at any moment, and the identity-arb harvester measured at 22.97ms operates in the
adjacent Layer-1 space — this is the speed lane. Fee oddities worth knowing: the annual
crypto series KXBTCY/KXETHY are **zero-fee both sides** (the cheapest correlation legs
on the exchange), while KXINXY/KXNASDAQ100Y charge makers. Use this class to *fit*
window/term-structure models (the data is abundant and clean); trade it only with
infrastructure you have already proven at millisecond scale.

### Class 4 — same release: one macro print reprices whole families

Five families (CPI ×10 series, Fed ×9, GDP ×5, U3 ×3, rate-cut ×2) — 29 series, 112
events, 1,446 active markets. Uniquely, everything here actually trades: median
*lifetime* volume per active market is 368 contracts, versus 0 in every other class and
2 exchange-wide (elsewhere volume concentrates in a few legs while ladder tails sit
untouched). The catalyst is
scheduled to the minute, the family repricing is simultaneous and cross-checkable
(headline vs core vs YoY ladders vs point-mass menus vs combo grids), and 72% of the
book is long-dated strips, so positioning ahead of a print is structurally possible.
The tax: the 7 headline series charge maker fees, so release-day passive quoting pays;
chain trades that must cross spreads pay 2.94¢ round-trip at mid-range prices. Second-
best class: the known-catalyst structure compensates the fee drag, and the point-mass ⊆
ladder relations inside each family double as free risk checks (those specific pairs are
Layer-1 bindings; the rest of the family is shared-driver).

### Class 5 — same narrative: co-movement without a measurable driver

Iran-escalation, Greenland-acquisition, Trump-legal clusters: legs that reprice on one
news stream but share no settlement variable. Audited conclusion stands: **not bound** —
a narrative spread can widen without limit, and there is no machine-readable universe to
enumerate. Kept as a research option, never as a systematic book.

### Class 6 — the national swing factor: measured, not assumed

Every partisan race loads on one national factor, and the exchange itself prices the
loading: the nine state Governor×Senate combo grids imply a joint distribution. Recomputed
from snapshot mids (renormalised 2×2 grids, Pearson φ on Dem-win indicators):

| KS | OH | MN | MI | IA | AK | GA | ME | NH |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| +0.57 | +0.56 | +0.56* | +0.55 | +0.45 | +0.44 | +0.37 | +0.24 | **−0.13** |

Median +0.45; the national House×Senate combo implies +0.34. The outliers are
interpretable, which is what makes the lens credible: NH's firmly negative φ (bid/ask
corner range entirely below zero) is a split-ticket state — Republican-favorite governor
race alongside a Democratic-favorite Senate race; ME's low +0.24 is Collins-specific.
(*MN is weakly identified — both cross legs one-sided. GA, ME and MI each carry one
one-sided near-zero leg, and ME has the largest renormalisation slack, mids summing
1.055; NH is the firm one — all four legs two-sided, corner range entirely negative.)
Use: hedge ratios
for cross-race books, and a live wave-factor gauge no poll aggregator publishes.

### Class 7 — same question, two venues: unexplored

Kalshi vs Polymarket duplicate questions. Not collected in this repo; public L2 archives
make the study feasible, and the Layer-1 work found the only genuinely open riskless
residual sits cross-venue (zero-fee negRisk structures). The lead-lag version — which
venue's politics prices move first — is an obvious, untouched study.

## Starting a study (the intended first experiment)

1. Pick pairs from `data/layer2/race_clusters.csv` — start with the 320 fully-
   instrumented races; the OH-07/VA-06 rows are worked examples of what to look for.
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
- **The lag is not a law.** The refuted claim "margin ladders always lag" matters as
  much as the confirmed ones — fast episodes (0-day tracking) and slow episodes (4-day
  lag) coexist in the same race. Trade the conditions, not the average.
- **Beta is regime-dependent.** NH's −0.13 is a split-ticket story, not noise; a wave
  hedge calibrated on the +0.5 pack fails exactly there.
- **Instrument traps.** Race `close_time` is a placeholder a year past the election;
  `liquidity_dollars` is dead in the census; thin legs quote one-sided and bias mids.
- **Check the [Layer-3 trap list](correlation-taxonomy.md) first.** Several "obvious"
  co-movers (spot vs daily-extremum, monthly-max vs annual-max) are look-alikes with
  different observation windows, not shared drivers.
