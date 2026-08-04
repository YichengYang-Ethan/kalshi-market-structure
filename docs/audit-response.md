# External audits: findings and disposition

## Round one, 2026-08-03 (commit `7078f00`)

An independent adversarial audit was run against commit `7078f00` using the published
index and the live API. Its findings are reproduced here with what verification showed
and what changed. Nothing is filed as "won't fix" without a reason.

## Confirmed and fixed

| Severity | Finding | Verification | Disposition |
| --- | --- | --- | --- |
| **Critical** | `two_sided` tested string truthiness, so `"0.0000"` counted as a live quote | `bool("0.0000")` is `True`; **73,964 of 73,964** published rows were set to 1 | Fixed with a numeric `quoted()` helper; index regenerated; regression test added |
| **High** | Only active legs were classified, so a ladder with one rung left became `binary` | Exactly **44** events matched (multi-market, one active, labelled binary) — the audit's count was precise | `classify_event()` now labels the generator from all legs; `active_only=True` gives the tradeable shape |
| **High** | The threshold branch ran before combination detection | Source positions 6363 < 6400; `KXCPICOMBO-26JULB` and `KXEMPLOYMENTCOMBO-26JUL` were both labelled `threshold` | Combination is now decided first, since its legs also satisfy the threshold grammar |
| **High** | `Partition.evaluate_buy_all()` gated on `tiled` alone, admitting `implicit` and `none` partitions to a synthetic-$1 path | The guard was `if not self.tiled` with no reference to the grade | Requires `exhaustiveness == "explicit"`; returns `None` otherwise, because the payoff is undefined rather than uncertain |
| Medium | Template table in `taxonomy.md` was stale | Doc said `entity_menu` 4,591 / `combination` 51; index had 4,073 / 16 — the table was never updated after the classifier was fixed | Regenerated from the committed index |
| Medium | `boards.md` omitted Transportation and the null category | Confirmed absent | Rows added |
| Medium | "13 of 14 explicit partitions are annual GDP ladders" | The explicit set contains **6** `KXGDPYEAR` events, not 13 | Corrected, with the full list named |
| Medium | The `implicit` grade was described as uniformly four-decimal with 1e-4 gaps | Written gaps span 0.01 (12 events), 1e-4 (14), 1e-7 (3), 1e-9 (2) | Corrected |
| Medium | `taxonomy.md` said the classifier reads `strike_type`, `custom_strike` and `mutually_exclusive` | It reads none of them | Corrected, and noted that `strike_type` would be the stronger signal |

## Confirmed and corrected in substance

**The headline claim was overstated.** `boards.md` asserted that generation ratio
"predicts almost everything" and that traded share "tracks scale, not subject". The
association is real (Pearson −0.56, Spearman −0.80 across 17 boards) but weaker than
simpler measures — active markets per event explains 44% of variance, log active markets
39%, generation ratio 31%. The audit's counterexample stands: Financials and
Entertainment have generation ratios of 1.710 and 1.705 and traded-leg shares of 44.8%
and 80.2%. The specific claim that the four sub-60% boards are the four largest by
listing count was **false** — Crypto is sixth. All of this is rewritten.

**The audit's own stronger result is now the headline.** Leg-level traded share conflates
ladder width with attention. At least one leg had traded in **87% of Crypto events** and
**95.3% of Financials events**. The untouched tail is inside wide ladders, not across
whole questions. That is both more defensible and more useful than the board-level
attention story it replaces, and it was not in this repository before the audit.

**"Almost certainly exhaustive" was too generous.** These crypto contracts settle on a
60-second average of a CF Benchmarks index and no rule states how that average is
rounded, so an averaged value can fall between two written ranges. The audit checked all
31 events, 16 series and 2,500 rule fields to establish this. The `implicit` grade
survives; the confidence attached to it does not.

**Scope leakage was real.** Sentences that describe one snapshot of the open surface were
written as statements about the exchange. Every instance the audit quoted is qualified,
and `boards.md` and `settlement-patterns.md` now carry a scope banner. The relevant scale:
over 100,000 settled events exist against 8,478 open ones, and Crypto alone has settled
more than 43,000 against 108 open — a board can look small here and be among the most
active by turnover.

**The worst overclaim was correctly identified**: "The exchange is structurally consistent
to the tick almost everywhere." The price inputs are not committed, so the ~120,000 checks
are not reproducible from this repository alone; the scope is open events only; relation
coverage is not exhaustive; and the partition evaluator had the defect above. Rewritten
to state what was scanned rather than what the venue is.

## Open

**Six Commodities events** — `KXB65-{JUL,AUG,SEP}26` and `KXB85-{JUL,AUG,SEP}26` — were
live at audit time, predate the snapshot, and are absent from the index. The API exposes
no status history, so reactivation and omission are indistinguishable. Recorded as an
unresolved omission candidate rather than dismissed.

## Note on method

The audit was given the published index, the classifier source, and the API, and asked to
reproduce rather than inspect. Every finding above was verified locally before being
accepted; none was taken on the reviewer's word. The critical defect is the case for that
arrangement: it was invisible in every aggregate this repository published, and became
obvious the moment someone read the line that produced the column.


## Round two, 2026-08-03 (commit `d068463`)

A second adversarial pass checked whether the round-one fixes were real and hunted for
defects the fixes introduced. It found that only one of six was cleanly fixed. Every
finding below was verified locally before acceptance.

### Confirmed and fixed

| Severity | Finding | Verification | Disposition |
| --- | --- | --- | --- |
| **Critical** | Both partition evaluators ignore which markets they are handed | A 3-leg partition priced from 2 quotes returned **+$0.80**; a 2-leg partition priced from the same leg twice returned **+$0.60**. Both packages pay zero in states the partition covers. | `_covers()` now requires the quotes to be exactly the legs, once each, on both paths |
| **High** | The round-one classifier fix caused reverse regressions | `FEDHIKE` and `KXALBUMRELEASEDATETRIPPIE` are deadline ladders published as `entity_menu` | Root cause was narrower than reported: `parse_deadline` could not read "Before July 2026" (no day) or "Before June" (no year), and `DEACTIVATED` tombstone legs sat in the vote's denominator. Both fixed; the two events now classify as `deadline` |
| High | Three parser failures carried over from round one | `79° or below`, `$4/MTok or below`, `before September` all failed to parse | Unit glyphs and per-unit suffixes are stripped; abbreviated months parse |
| High | **The unauthenticated orderbook claim was false** | `KXPRESNOMD-28-AOC` returns **61 yes / 90 no** levels without authentication | Depth is in the `orderbook_fp` key, not `orderbook`. This repository read the wrong key and concluded for weeks that depth was unavailable. Corrected wherever stated |
| High | The artifact-consistency test overclaimed its coverage | It compared two global totals and returned silently when the index was absent | Now reconciles every rollup field per series, checks each event's market count and template against the market index, and fails when an artifact is missing |
| Medium | README still carried the exact scope leakage said to be fixed | "census of the whole exchange" and "structurally consistent to the tick almost everywhere" both remained | Both rewritten. The round-one response claimed every instance was qualified; it had only covered `docs/` |
| Medium | The replacement attention claim was itself overstated | 14 Crypto and 21 Financials events are wholly untouched, holding **30.4%** and **35.0%** of those boards' untraded legs | "Not across whole questions" was wrong and is corrected: about a third of the inactivity is whole questions |
| Medium | `data/README.md` documented two of four published files | Regenerated by the builder, which had not been updated | Documents all four, and states that rollup counters span all markets rather than active ones |

### Confirmed after the fact

The audit reported **516,108** settled events against the scope banner's "roughly
100,000+". An independent crawl completed after that response was written and returned
**516,232** distinct events over 2,582 pages with the cursor exhausted — the 124-event
difference is settlement during the two hours between crawls. The banner understated the
figure by a factor of five and has been rewritten with the measurement.

The consequence is larger than the correction. The open surface this repository censused
is **8,478 of 524,710 events, or 1.6%**, and the ratio is wildly uneven: Crypto has
settled 219,237 events against 108 open, a 2,030:1 ratio driven by hourly ladder rolls,
while Politics is 5:1. Every statement here about which boards are large or active
describes a snapshot of listings, not turnover, and Crypto is the case where those two
things diverge most.

### Note

The orderbook finding is the one that matters most beyond this repository. Full book
depth has been available on every market this whole time; the conclusion that only
top-of-book was visible came from reading `orderbook` instead of `orderbook_fp` on a
response that returns HTTP 200 either way. Every analysis here that reasoned about
executable size did so with less information than was actually available.

## Round three, 2026-08-04 (commit `b835c78`): the relation families

The 41 discovered families were re-audited externally against the live API under a strict
evidence rubric: a stored example that is not a real market ticker makes the row
FABRICATED even where a narrower repaired relation exists, and a relation qualifies only
if **every settlement branch** preserves it, not just the ordinary event predicates.

Result: **7 CONFIRMED, 4 ONE-DIRECTIONAL, 2 NEEDS-RULE-CHECK, 13 BROKEN, 15 FABRICATED.**
Of the 22 this repository had labelled CONFIRMED, 14 fell.

### What the verdicts actually mean, verified locally

**The FABRICATED count is mostly a data-quality indictment, not a fabrication one.**
Local verification found the example tickers this repository's audit prompt highlighted
(`KXLEAGUESCUPSPREAD-26AUG04CINPAC-CIN2`, `KXPRESNOMD-28-AOC`, `KXU3-26SEP-T4.4`) all
return HTTP 200 — but **9 of 41 stored rows carry garbage in their example field**:
literal ellipsis placeholders (`KXUCLWSPREAD-...`), event-level identifiers where market
tickers belong, and one free-text description. The discovery agents emitted them and the
verification pass fetched rules by searching the snapshot rather than strictly resolving
each stored ticker, so the garbage survived into the published CSV. Under a rubric where
the stored row is the unit of audit, those rows are correctly failed. The relation logic
behind several of them remains salvageable and the audit says so explicitly.

**The BROKEN verdicts are the substantive finding, and they expose a systematic blind
spot: this repository verified event predicates, not payout branches.** Confirmed
locally: the first-half total's `rules_secondary` reads *"If the game is cancelled or
rescheduled to over 48 hours away, the market will resolve to a fair price"* — and the
full-time leg of the same game carries **no such clause**. A cancelled match can hand the
1H leg a positive discretionary fair-market price while the full-time predicate never
occurs. The nesting of the predicates is intact; the nesting of the **payouts** is not.
The same mechanism — independent FMP/cancellation/retirement/scratch branches per leg —
breaks the MLB player-stat lattice, tennis exact-score refinement, and others. Every
future relation must be verified on the full settlement branch tree, including the
discretionary branches.

**One genuinely new family was found and is adopted**:
`all-of-threshold-vector-dominance` — two ALL-of conjunction contracts over the same
component subjects, where the stricter threshold vector implies the looser one
(`KXBLUETSUNAMICOMBO-27FEB` ⟹ `KXBLUEWAVECOMBO-27FEB`: H≥235∧S≥51 ⟹ H≥218∧S≥49). Both
tickers verified 200; the rule text was confirmed against this repository's own snapshot.

### Disposition

- `data/discovered_families.csv` now carries `reaudit_verdict` and `reaudit_detector`
  columns for all 41 rows plus the new family.
- Only the 7+1 CONFIRMED, detector-OK families are candidates for mechanisation; the
  BROKEN rows stay in the file as documented negative results.
- Two process rules adopted: every stored example ticker must resolve with a live
  `GET /markets/{ticker}` before a row may be published, and relation verification must
  enumerate the full settlement branch tree, not the ordinary predicates alone.

## Round four, 2026-08-04 (commit `f8d1898`): the negative result

The zero-capacity conclusion was audited externally with instructions to break it. It
broke, in the most instructive way available.

### The counterexample, verified live here

The capacity run priced only the 8 CONFIRMED families and excluded every ONE-DIRECTIONAL
one. That exclusion was a category error: an implication **is** one-directional, and a
deterministic inequality is exactly as arbitrage-capable as an identity. The excluded
`matchup-outcome-split` family contains, live: with M = "Ossoff and Rubio are the
nominees", D = "Ossoff defeats Rubio", R = "Rubio defeats Ossoff", the rules give D ⊆ M,
R ⊆ M, D ∩ R = ∅, so the basket M-YES + D-NO + R-NO floors at $2. Books at 07:13Z: cost
$1.989 per contract, common depth 257, **net +$0.6355 after fees** — reproducing the
auditor's 06:50Z figure to the third decimal. A second triple (AOC/Vance) was
fee-positive at 8 contracts. Across 16 live matchup triples, seven were gross-positive
and three fee-positive.

### Identities do get mispriced — the tape says so

The public trade tape shows, on 2026-08-02 at 19:12:08, a 10-contract YES at $0.96 on
`KXBBCHARTPOSITIONALBUM-26AUG08IMT-1` and 22.97 ms later a 10-contract NO at $0.03 on
`KXTOPALBUM-26AUG08-IMT` — the same album, chart and week: a $0.99 package on a $1
identity, ~5¢ net after fees. Verified here from the trades endpoint. The previous
document's claim that "identities are priced correctly by construction" was wrong twice
over: they are priced correctly because someone harvests them, and 22.97 ms is what the
harvesting looks like.

### Other verified findings

- The ESPN-vs-FIFA settlement-source split is real but League-Cup-specific; other league
  pairs share overlapping sources. The general claim is downgraded to: source sets are
  frequently unequal, so source basis risk must be checked per pair.
- The severity-family instance count is disputed (7 reported, 8 structural overlaps per
  the family's own definition) and the 22,110-instance run has no committed manifest, so
  its exact composition is not reproducible. Reproducibility discipline that applies to
  the census must apply to capacity runs too.
- A Fréchet lower bound inside the confirmed BTTS family (P(BTTS) ≥ P(H)+P(A)−1) was
  never priced; the auditor screened all 59 live triples and found no violation, which
  simultaneously confirms the current zero there and proves the run was incomplete.

### The corrected verdict, adopted verbatim in spirit

The investigation establishes: **no large, continuously standing, taker/taker riskless
capacity in the examined families at the examined times.** It does not establish that
identities cannot be mispriced (the tape disproves it), nor anything about cross-venue
arbitrage, maker-side returns, listing/news windows, general multi-leg baskets, or the
settled lifecycle. Small transient exact arbitrage exists and is occasionally live in
omitted corners; monitoring for it is an option on rare microstructure failures with a
defensible yield of hundreds to low thousands of dollars a year. That is the honest
floor and ceiling of this strategy class on this exchange.
