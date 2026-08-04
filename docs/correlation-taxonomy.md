# The correlation taxonomy: every kind of relatedness found on Kalshi

This project's deliverable, restated as a correlation study: between any two Kalshi
markets there are exactly four layers of relatedness, ordered from strongest to weakest.
Every family we verified belongs to one layer, and every future strategy (lead-lag,
relative value, market making) starts by asking which layer its pairs live in.

## Layer 1 — Deterministic settlement binding (rule-forced, correlation = 1 in the limit)

Prices are bound because the contracts' settlement rules share outcome states. This is
stronger than correlation: divergence beyond fees is arbitrage. Four mechanisms:

### 1a. Containment / implication (A ⊆ B) — the dominant class, ~28,000 independent constraints

| Sub-type | What contains what | Verified examples |
| --- | --- | --- |
| Threshold nesting | higher strike ⊆ lower strike | price ladders, win totals, margin ladders (largest single class) |
| Temporal nesting | earlier deadline ⊆ later; sub-period ⊆ full period | "before 2027" ⊆ "before 2029"; 1st-half ⊆ full-time; first-5-innings ⊆ game; weekly ⊆ monthly window |
| Severity nesting | stricter category ⊆ looser | major hurricanes ⊆ named storms |
| Stage progression | later round ⊆ earlier round | champion ⊆ league champion; finalist ⊆ semifinalist |
| Semantic subset | specific event ⊆ general event | Greenland ⊆ any-territory (the cleanest verified lock) |
| Refinement | fine outcome fixes coarse outcomes | correct score ⇒ moneyline/total/spread/BTTS; exact set score ⇒ match winner |
| Derivative ⇒ base | a derived stat implies the base result | margin ⇒ winner; vote share >50% ⇒ nominee; spread ⇒ moneyline |
| Conjunction ⇒ components | an ALL-of contract implies each part | matchup ⇒ both nominees; combo leg ⇒ each base; threshold-vector dominance (Tsunami ⇒ Wave) |

### 1b. Mutual exclusion (at most one of A, B)

Mutex candidate menus (3,978 events); outcome splits (D and R disjoint inside M — the
family with the live $0.64 basket); same-rank exclusivity on one chart week.

### 1c. Identity / partition (P(A) = P(B), or Σ = 1)

Duplicate listings (same rules+times under two tickers); alias equalities (album-#1 dual
listings; 0-0 ≡ NOT Over-0.5); difference identities (crypto range bucket = threshold
ladder first difference); marginal identities (chamber control = sum of combo legs);
exhaustive partitions (14 with explicit precision clauses, mostly GDP ladders).

### 1d. Sum bounds

Fréchet: P(A∧B) ≥ P(A)+P(B)−1 (BTTS vs team totals); cardinality: at most K of N
nominee legs settle Yes.

## Layer 2 — Conditional binding (exact only under named conditions)

The same mechanisms as Layer 1, degraded by an operational mismatch we catalogued:

| Condition that must hold | Trap when it doesn't | Example |
| --- | --- | --- |
| Same settlement source | two sources can disagree on one goal | SCORE settles ESPN, TOTAL settles FIFA — every league pair checked mismatched |
| Matching payout branches | one leg FMP on cancellation, other binary | 1st-half vs full-time totals |
| Event completes normally | retirement/abandonment splits the legs | tennis exact-score vs match |
| Participant plays | scratch triggers FMP on both strikes | MLB player-stat ladders |
| Single-match tie | two-legged rounds break win ⇒ advance | EFL Cup yes, Copa do Brasil no |

Layer 2 is tradeable only with the condition priced as a tail.

## Layer 3 — Statistical / narrative correlation (no settlement link; genuine research space)

Prices co-move through shared drivers, not shared rules. Divergence is NOT arbitrage.
This is the layer where lead-lag and relative value are real strategies:

- **Same-race correlation, measured**: implied Gov×Sen correlation extracted from the
  nine state combo markets — typically ρ ≈ 0.4–0.6, with NH at −0.13 (split-ticket
  tradition) and ME at 0.20 (Collins personal vote). This is the project's one completed
  piece of Layer-3 measurement.
- **The wave factor**: every Democratic leg loads on the national swing; CONTROLH-D
  (~83¢) acts as the systematic factor of the elections board.
- **Narrative clusters**: Iran (leader/democracy/election/recognition), Greenland
  (buy/territory/statehood/price), Trump-legal. Both external auditors confirmed these
  are NOT settlement-linked — they co-move on news only.
- **Same-underlying, different windows**: BTC hourly/daily/annual ladders correlate
  through the spot path but each anchors its own observation window (the
  monthly-max ⊄ annual-max trap: each anchors at its own issuance).
- **Lead-lag, measured**: the liquid base leg reprices first; the illiquid derivative
  follows in minutes to days (OH-07: 3 days; VA-06: 8 days crossed). At the fast end a
  harvester operates at 22.97 ms. This is Layer 1/2 pairs exhibiting Layer-3 dynamics in
  the interim — the convergence-trade thesis.

## Layer 4 — Spurious relatedness (looks correlated, is not)

The rejected families, kept as the trap catalogue:

- Primary plurality ⇏ nomination (runoffs; SC special)
- State seat-count ⇏ every district winner (independents)
- k-th place and nominee are NOT exclusive (replacement paths)
- Spot reading ⇏ daily extremum (different observation conventions)
- Identical rule text ⇏ same contract (reading vs math test scores — the rules omit the subject)
- Fed "changes" ⊅ "cuts" pathwise
- Same person P & VP nominee is NOT rule-forbidden (empirically near-impossible only)

## How the layers map to strategies

| Layer | Strategy class | Status |
| --- | --- | --- |
| 1 | riskless arbitrage | priced: standing ≈ $0, transient ~$0.64 best observed |
| 2 | tail-priced relative value | families graded; tails named per family |
| 3 | lead-lag, RV, factor hedging | pair universe mapped; dynamics measured on a handful; **the open research space** |
| 4 | do-not-trade list | 7+ documented traps |

## The shared-driver enumeration (Layer 3 made concrete)

A trader's restatement: drop the tail distinctions and split the world in two — pure
arbitrage (binding, with or without bp-tails) versus **co-movement without binding**:
markets that are different functions of one underlying state variable, so a move in the
state reprices all of them together, with no arbitrage tying them. This is where
lead-lag, relative value and cross-hedging live. Counted on the 2026-08-04 snapshot:

| Driver class | The shared state | Size | The trade |
| --- | --- | --- | --- |
| Same game | (scoreline, clock) — a goal moves 1X2, totals, spreads, BTTS, props at once | **1,555 game-keys**; 7 games carry 18 market types, 60 carry 11+ | intra-game lead-lag (seconds), the World Cup pattern |
| Same race | polling/news state — a scandal moves winner, margin, turnout together | **505 races with ≥2 families; 320 with winner+margin+turnout** | news lead-lag (measured: base leads derivative by 3–8 days) |
| Same price path | one spot process behind many windows | INX 11 window-series, WTI 8, BTC 8 (hourly/daily/annual/max/min/vs-gold) | curve RV, window-spread trades |
| Same macro release | one print reprices the whole family | CPI 10 series, FED 9, GDP 5 | release-day chains (CPI → Fed odds → rate-cut count) |
| Same person/narrative | one news flow | Iran, Greenland, Trump-legal clusters (audited: NOT bound) | narrative RV, no floor — model risk only |
| Party/wave factor | national swing | every D leg; implied ρ from combos 0.4–0.6, NH −0.13, ME 0.20 | factor hedging, cross-race RV |
| Cross-venue | same question, different oracle | Kalshi vs Polymarket — unexplored here | classic cross-listing lead-lag |
