# Layer 2: the correlation track

Markets that are different functions of one state variable: the state moves, all reprice
together, nothing binds them. No floor — these are model trades (lead-lag, RV, hedging),
and this is the open research space of the project.

## The seven driver classes

| # | Shared state | Size (2026-08-04) | Pair data | The trade |
| --- | --- | --- | --- | --- |
| 1 | (scoreline, clock) of one game | 539 multi-market games; up to 18 types/game | `data/layer2/game_clusters.csv` | intra-game lead-lag (seconds) |
| 2 | polling/news state of one race | 505 races ≥2 families, 320 with winner+margin+turnout | `data/layer2/race_clusters.csv` | news lead-lag — **measured: base leads derivative 3–8 days** |
| 3 | one price path, many windows | 20 underlyings (S&P 11 window-series, BTC 8, WTI 8) | `data/layer2/underlying_windows.csv` | curve/window RV |
| 4 | one macro release | CPI 10 series, FED 9, GDP 5 | `data/layer2/release_families.csv` | release-day chains |
| 5 | one narrative | Iran / Greenland / Trump-legal clusters | catalog + taxonomy docs | narrative RV — audited NOT bound, no floor |
| 6 | national swing | every partisan leg; implied ρ from state combos: 0.4–0.6, NH −0.13, ME +0.20 | combo events | factor hedge, cross-race RV |
| 7 | same question, two venues | Kalshi vs Polymarket | not collected here | cross-venue lead-lag (unexplored) |

## What is already measured (use it, don't re-derive it)

- **Slow lead-lag exists and persists**: a base market repriced 25¢ on news while its
  margin ladder sat still for 3 days; another pair stayed crossed 8 days.
- **The fast end is taken**: a harvester executed two legs of an identity 22.97 ms
  apart. Speed competition starts there; the days-scale lane had no visible occupant.
- **Implied correlation is extractable from combos**: nine Gov×Sen state combos gave
  ρ ≈ 0.4–0.6 with interpretable outliers (NH split-ticket −0.13, ME Collins +0.20).
  Method: ρ = (p(DD) − pG·pS) / √(pG(1−pG)pS(1−pS)) on renormalised combo mids.

## Starting a study (the intended first experiment)

1. Pick pairs from `race_clusters.csv` (class 2 is slowest, most measurable).
2. Pull both legs' history: `GET /series/{s}/markets/{t}/candlesticks` — 1440-interval
   reaches back to 2024-11; 60-interval covers months; trades endpoint pages the full
   tape. (`src/kalshi_structure/history.py` has a checkpointed collector.)
3. Estimate the lag: event-time alignment on base-leg moves ≥ N¢, measure the
   derivative's response time distribution.
4. Paper-trade convergence capture maker-first (politics maker fee = 0), with the
   Layer-1 condition checklist as the risk gate.
5. Pre-register kill conditions before looking at P&L — the discipline that kept this
   project honest.

## The warnings that transfer

No floor: a Layer-2 spread can widen forever (Iran-cluster legs are NOT bound). Beta is
regime-dependent (NH's −0.13 is a split-ticket story, not noise). And check every pair
against the [Layer-3 trap list](correlation-taxonomy.md) first — several "obvious"
co-movers (spot vs daily-extremum, monthly-max vs annual-max) are look-alikes with
different observation windows, not shared drivers.
