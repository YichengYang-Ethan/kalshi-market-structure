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

### Disputed

The audit reports **516,108** settled events against the scope banner's "roughly
100,000+". An independent crawl here was still running past 150,000 when this was
written and had not terminated, so the direction is confirmed — the banner understated —
but the specific figure is not verified. The banner is being rewritten to cite the
measurement rather than a round number.

### Note

The orderbook finding is the one that matters most beyond this repository. Full book
depth has been available on every market this whole time; the conclusion that only
top-of-book was visible came from reading `orderbook` instead of `orderbook_fp` on a
response that returns HTTP 200 either way. Every analysis here that reasoned about
executable size did so with less information than was actually available.
