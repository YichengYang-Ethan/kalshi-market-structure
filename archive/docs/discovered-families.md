# Discovered relation families

A six-way parallel discovery pass, each agent reading one board's rules and ticker
grammar, proposed 46 candidate arbitrage-capable families beyond the 9 already
mechanised. Each was then adversarially verified against the actual contract text by a
separate agent instructed to break it. **41 survived, 5 were rejected with concrete
settlement counterexamples.** No prices were read at any point — a family is here because
the rules bind the prices, not because a divergence exists today.

Together the survivors add roughly **2,140 arbitrage-capable instances**, almost all in
Sports and Entertainment, which the earlier generic catalogue barely touched. The earlier
8,422-relation catalogue was dominated by generic mutex baskets and single-subject
ladders; these are the domain-specific cross-market bindings *inside* a game or a release.

## Verdict split

| Verdict | Families | Meaning |
| --- | ---: | --- |
| `CONFIRMED` | 22 | rule text supports the binding exactly, both direction and condition |
| `ONE-DIRECTIONAL` | 15 | a real implication one way only (a coarser event, a non-exhaustive grid) |
| `NEEDS-RULE-CHECK` | 4 | binding plausible but a clause or window must be confirmed per instance |
| **rejected** | **5** | a concrete settlement state resolves both legs against the binding |

14 of the 41 carry a *detection-needs-fix* flag: the logic is sound but the proposed
mechanical signature would mis-select instances (unit mismatch, boilerplate rules, wrong
join key) and must be tightened before scanning.

## The highest-value new families

| Family | Board | ~Inst | Exactness | The binding |
| --- | --- | ---: | --- | --- |
| `econstat-pointmass-vs-ladder` | Economics | 354 | exact | "Exactly v%" menu ⊆ "Above x%" ladder: Σ exact-legs above x ≤ P(above x) |
| `spread-implies-moneyline` | Sports | 321 | exact | wins by >X.5 ⟹ wins; joined on the soccer_team UUID |
| `firsthalf-subset-fulltime` | Sports | 206 | exact | 1st-half Over/BTTS ⟹ full-time Over/BTTS |
| `award-nom-win` | Entertainment | 120 | exact | wins award ⟹ nominated (Oscars/Grammys/Emmys) |
| `extremum-window-envelope` | Economics | 120 | one-dir | point-value > X ⟹ window-max > X |
| `song-chart-depth` | Entertainment | 100 | exact | #1 ⟹ top-10 ⟹ top-20, same artist/week |
| `pres-vp-nominee-mutex` | Elections | 80 | exact | a person can't be both P and VP nominee: P(pres)+P(vp) ≤ 1 |
| `teamtotal-implies-total` | Sports | 72 | exact | a team's total ⟹ the game total at the same line |
| `btts-implies-teamtotal` | Sports | 72 | exact | both-teams-score ⟹ each team over 0.5 |
| `correct-score-refines-outcome` | Sports | 60 | exact | a scoreline cell fixes moneyline/total/spread/BTTS |
| `no-goals-equality` | Sports | 60 | exact | SCORE 0-0 ≡ NOT(total over 0.5) — an equality, both directions |
| `albumunits-domination` | Entertainment | 51 | exact | album-equivalent units ≥ pure sales for the same title |
| `crypto-range-ladder-identity` | Crypto | 22 | exact | a range bucket = the negative first difference of the threshold ladder |
| `mlb-player-stat-dominance` | Sports | 21 | exact | a player's total-bases ≥ hits ≥ ... a within-player stat lattice |
| `control-marginal-sum` | Elections | 4 | exact | chamber-control D = sum of the balance-of-power D legs |

The full list of 41, with detection signatures and per-family evidence, is in
`data/discovered_families.csv` and `data/discovered_families_full.json`.

## What was rejected, and why it matters

The rejections are the useful part — each is a binding that *looks* exact and is not:

- **`primary-victory-nominee`** — winning the first round does not imply becoming the
  nominee: the in-data SC GOP Senate special has a plurality leader below the majority
  threshold, forcing a runoff. Plurality ≠ nomination.
- **`seatcount-vs-district-winners`** — "0 Democrats in the state" does not force every
  district to resolve Republican; an independent breaks it.
- **`primary-place-antinominee`** — a candidate placing k-th and still becoming nominee is
  a reachable both-Yes state, so the ≤1 bound is not rule-enforced.
- **`intraday-implies-dailyhigh`** — a spot temperature reading at 4 PM does not imply the
  daily-high market resolves above it, because they key off different observation
  conventions.
- **`count-subset-tail-dominance`** — the Fed "changes ≥ cuts" link breaks pathwise and
  the stochastic-dominance direction is indeterminate.

Each shows the same lesson the price scanner kept teaching: a relation that is obvious in
prose can have a concrete settlement state that voids it, and only reading the rule finds
it.

## Next

These 41 families are proposals with verified logic, not yet mechanised. The next step is
to encode the CONFIRMED, detection-sound ones into `catalog.py` so the price-free
monitoring surface grows from 8,422 to include the ~2,140 new instances, then let the
scanner price them. The 14 detection-needs-fix families need their signature corrected
first; the rejected 5 stay rejected.
