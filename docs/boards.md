# Every board, compared

Each API category has been inventoried with the same pipeline used for Elections +
Politics: union universe, contract-template classification, activity flags, fee surface,
partition diagnostics. Outputs live in per-board directories under the data root.

Snapshot 2026-08-02. Events are attributed to a single board by `event.category` here;
the per-board inventories use the union definition and therefore overlap slightly (141
events, 1.7%, carry a `series.category` that disagrees with their `event.category`).

## The comparison

| Board | Events | Active mkts | Traded | Volume | Ladder events | Mutex | Tiled | 0-fee series | Maker-fee series |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Elections | 2,226 | 11,356 | 56.6% | 491.7M | 1,033 | 1,058 | 2 | 2 | 0 |
| Sports | 3,920 | 34,756 | 47.3% | 458.8M | 1,068 | 1,946 | 0 | 0 | 56 |
| Politics | 493 | 1,995 | **95.9%** | 97.8M | 166 | 45 | 1 | 5 | 0 |
| Crypto | 108 | 2,629 | **28.5%** | 70.1M | 58 | 32 | **31** | 2 | 1 |
| Economics | 352 | 3,265 | 89.3% | 64.8M | 210 | 79 | 18 | 2 | 10 |
| Science & Technology | 119 | 702 | 90.3% | 49.0M | 52 | 13 | 0 | 0 | 1 |
| Entertainment | 498 | 6,405 | 80.2% | 37.2M | 153 | 131 | 0 | 0 | 7 |
| Financials | 443 | 8,093 | 44.8% | 28.6M | 351 | 37 | 8 | 0 | 3 |
| Companies | 71 | 495 | 97.6% | 9.0M | 37 | 3 | 0 | 0 | 0 |
| Climate & Weather | 137 | 879 | 95.4% | 3.7M | 26 | 87 | 2 | 0 | 0 |
| Mentions | 58 | 957 | 95.4% | 2.5M | **0** | **0** | 0 | 0 | 0 |
| Commodities | 29 | 801 | 63.2% | 1.5M | 21 | 1 | 1 | 0 | 0 |
| Health / World / Social | 22 | 65 | ~96% | 1.4M | 3 | 5 | 0 | 0 | 0 |

*Ladder events* = events with two or more nested legs, i.e. the surface on which
implication constraints can exist. *Tiled* = mutually exclusive numeric partitions whose
gaps pass the structural check.

## What separates the boards

**Generation ratio.** Sports (4.91 events per series) and Elections (3.50) are template
factories: one series stamped across every game or district. Everything else runs near
1.0 — a series is a single bespoke question. The ratio predicts almost everything else.

**Traded share tracks scale, not subject.** The four boards below 60% traded are the four
largest by listing count (Crypto 28.5%, Financials 44.8%, Sports 47.3%, Elections 56.6%).
The boards at 95%+ are the small ones. Batch generation produces a long tail nobody
looks at; bespoke listing does not, because a question gets listed when someone wants to
trade it.

**Crypto is the extreme case and the most interesting.** 2,629 active markets, only 28.5%
ever traded — the lowest on the exchange — yet 31 cleanly tiled partitions, the most
anywhere. It is dense with structure and thin on attention, which is exactly the
combination that produced findings in Elections. Its ladders are also the tightest priced
on the venue (`KXBTCY` sum-of-bids 0.9960 with zero fees), so the structure is already
enforced where anyone looks.

**Mentions has no internal structure at all.** Zero ladder events, zero mutually exclusive
events, 100% `entity_menu`. Every event is a menu of things someone might say, and no leg
excludes another. There is nothing to constrain, so it can be excluded from constraint
scanning entirely rather than scanned and found empty.

**Fees split the exchange in two.** All 56 maker-fee sports series and the 10 in Economics
sit on the highest-flow products; every other board has free resting orders. Passive
execution is therefore free precisely where books are thin and taxed where they are deep.

## Exhaustiveness, graded

A tiled partition is not automatically a synthetic $1. Grading the 63 tiled partitions by
what the contract text actually supports:

| Board | Tiled | `explicit` | `implicit` | `none` |
| --- | ---: | ---: | ---: | ---: |
| Crypto | 31 | 0 | 31 | 0 |
| Economics | 18 | 13 | 5 | 0 |
| Financials | 8 | 0 | 6 | 2 |
| Elections | 2 | 0 | 2 | 0 |
| Climate & Weather | 2 | 0 | 0 | 2 |
| Commodities | 1 | 1 | 0 | 0 |
| Politics | 1 | 0 | 0 | 1 |
| **Total** | **63** | **14** | **44** | **5** |

- `explicit` — the contract states the reporting precision or that bounds are inclusive
  (`"rounded to one decimal place"`, `"All stated bounds are inclusive"`). Safe.
- `implicit` — no such sentence, but every gap equals the precision to which the bounds
  are written and the buckets are equal width. Crypto's entire set grades this way:
  bounds to four decimals, 1e-4 gaps, uniform width, matching the CF Benchmarks index
  they settle against. Almost certainly exhaustive; not stated.
- `none` — neither. Only `sum(P) ≤ 1` is available.

**Only 14 partitions on the whole exchange have an explicit exhaustiveness guarantee**,
and 13 of them are the annual GDP ladders. Any buy-all-YES basket outside that set is
resting on an inference.

## A correction worth recording

This repository previously used `KXGREENLANDPRICE-29JAN21` as its standard example of a
partition with a settlement hole, reasoning that a $9.5B acquisition falls between the
"$1B to $9B" and "$10B to $99B" legs. **That was wrong.** The contract's
`rules_secondary` reads *"Values are rounded to the nearest $1 billion USD"*, and a
further sentence assigns the no-acquisition case to the `$0` bracket. The partition is
exhaustive.

The claim survived several passes, propagated into three documents, and was used as the
`BROKEN` calibration anchor in the external audit pack — which means it told two
reviewers the answer to a question whose real answer is the opposite. Neither caught it,
though one flagged in its confidence note that the rounding clause was exactly what it
would need to be sure. The anchor was hand-written prose rather than generated from the
contract text, so the rule this repo imposes on reviewers — never assert a settlement
fact without the clause in hand — was not being applied to the pack itself. It is now:
anchors quote their deciding clause, and the replacement is a soccer correct-score grid
whose omission is in the enumeration (17 of 36 scorelines listed, nothing above 5 goals,
so a 4-4 draw pays no leg) and therefore has no gap arithmetic to misread.
