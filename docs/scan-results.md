# Exchange-wide constraint scan

`scripts/run_scan.py` runs six mechanised relation families against the census snapshot
with per-series fees and audit-hardened gating. This documents what a full scan of the
open surface actually returns, and why the number is small.

## The result is small, and gets smaller as the scan gets more careful

A first run of the comprehensive scanner reported **414 net-positive "violations"
totalling $141**. Almost none were real. Each was an instance of a trap this repository
already documents, and fixing the scanner to respect those traps drove the count down:

| Scanner state | Net-positive hits | Sum of net edge |
| --- | ---: | ---: |
| Naive | 414 | $141.9 |
| + require both legs two-sided and traded | 112 | $34.1 |
| + fix spelled-out magnitudes (`$500 billion` → 5e11, not 500) | 17 | $1.63 |
| + require identical unit skeleton before comparing thresholds | 11 | $0.19 |
| + flag subject-omitting duplicates as candidates | 11 (2 downgraded) | $0.19 |

The direction is the answer to "surely careful analysis finds more". Careful analysis
finds **fewer**, because most of what a loose scan surfaces is:

- **Phantom quotes** — a resting price on a leg nobody has traded is not an edge. Two of
  the three biggest first-run families were untouched books (`KXGOVTSPEND`, `KXMUSKNW`).
- **Unit non-normalisation** — `Above $500 billion` parsed to 500 and `Above $2.5
  trillion` to 2.5, so the scanner ordered ladders backwards and reported locks on
  non-implications. Same failure with time: `30 days` vs `5 years`. Both fixed.
- **Boilerplate rule text** — every leg of the "best NYC restaurant" menu shares one
  templated rule with the restaurant name only in the subtitle, so a rules-keyed dedup
  called all 299 pairs duplicates. And `KXUSTESTSREADING` / `KXUSTESTSMATH` have
  byte-identical rules that never name reading or math, so they look like one contract
  and are two.

Every one of these is a documented trap. The scan is valuable precisely because it keeps
rediscovering them at scale — three genuine parser defects were fixed because this run
surfaced them.

## What survives on the current snapshot

Eleven candidates, none large, and they must still be verified per contract:

| Family | Example | Net/contract | Status |
| --- | --- | ---: | --- |
| F5 margin → winner | `KXMIDTERMMOV-NY02D-P2` → `KXHOUSERACE-NY02-26-D` | +2.3¢ | Real edge, but the relation is BROKEN (party-switch tail); size on a low-volume leg |
| F3 buy-all | `KXGDPYEAR-29` 14-leg basket | +5.0¢ | Fee-free, explicit exhaustiveness — genuinely riskless, but the binding leg has ~0 depth |
| F6 semantic subset | `KXGREENTERRITORY-29` ⊆ `KXUSAEXPANDTERRITORY` | +0.5¢ | EXACT by two reviewers; the cleanest true lock |
| F4 duplicate | `KXRONI-27APR` / `-27APR2` same strike | +1.9¢ | Same series stem, plausible re-listing — verify |
| F4 candidate | `KXUSTESTSREADING` / `KXUSTESTSMATH` | +4.7¢ | Rules omit the subject; **probably not one contract** |
| F1 threshold | `KXMUSKWEALTH-27` adjacent strikes | +0.9¢ | Real inversion, near noise |

Total genuine, verified, executable net edge across the whole open surface is on the
order of a **few cents per contract per opportunity**, concentrated in a handful of
low-liquidity markets. This reproduces mechanically what the earlier hand analysis found:
the exchange is priced tightly wherever anyone is looking, and the residue is small,
capacity-limited, and mostly carries a tail rather than being a clean lock.

## Reproduce

```bash
python3 scripts/run_scan.py    # needs a census in ~/Developer/kalshi-research-data
```
