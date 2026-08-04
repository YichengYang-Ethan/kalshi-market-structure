# data/layer2 — the shared-driver pair universes

The starting datasets for Layer-2 (correlation) research: every cluster of markets that
share one underlying state variable, so a move in the state reprices all of them
together **without any settlement binding between them**. Identifiers only — no prices,
volumes or rule text (Kalshi's terms bar redistribution; join to price history yourself
via the candlesticks endpoint, see below).

Snapshot: 2026-08-04T06:02Z. Regenerate anytime with
`python3 scripts/build_layer2_pairs.py` against a fresh census.

## game_clusters.csv — 539 rows, one per multi-market game

| Column | Meaning |
| --- | --- |
| `game_key` | the shared event-ticker suffix, e.g. `26AUG042040TBCOL` = Aug 4 2026, 20:40, TB @ COL |
| `n_market_types` | how many series trade on this one game |
| `series` | the series list, `\|`-separated |

**How to read a row.** `26AUG042040TBCOL, 18, KXMLBEXTRAS|KXMLBF3|KXMLBF5|...` means
one baseball game carries 18 market types — the full list includes KXMLBGAME (moneyline),
KXMLBSPREAD, KXMLBTOTAL, team totals, player hits/HR/strikeouts, first-5-innings
variants — all functions of (score, clock).
A run scored repricing all 18 at once is the shared driver; which book moves first is
the intra-game lead-lag question. Reconstruct any market ticker as
`<series>-<game_key>[-<leg>]`.

**Caveat carried from Layer 1:** same-game series often settle off different sources
(ESPN vs FIFA class of problem) and carry different cancellation branches. For
correlation research that is usually harmless; for anything resembling a hedge, run the
four verification axes in [layer1-arbitrage-guide](../../docs/layer1-arbitrage-guide.md).

## race_clusters.csv — 505 rows, one per 2026 race with ≥2 market families

| Column | Meaning |
| --- | --- |
| `race_key` | district/state code, e.g. `VA06`, `TX34`, `AZSEN` |
| `n_families` | how many families cover the race |
| `members` | `family:event_ticker` pairs, `\|`-separated; families are `winner`, `margin` (per party), `turnout` |

**How to read a row.** `VA06, 4, margin:KXMIDTERMMOV-VA06D|margin:KXMIDTERMMOV-VA06R|
turnout:KXMIDTERMVOTETURN-VA06|winner:KXHOUSERACE-VA06-26` — one House race, four
market families, all repricing on the same polling/news state. **This exact row is where
the measured crossing lives** (re-checked 2026-08-04: crossed 47 consecutive days at
mid, 15 days tradably, still open), and the OH-07 row is where the base repriced +25.5¢
while the same-party margin ladder took 4 days to respond. The 320 rows with all three
families are the
richest lead-lag candidates.

## underlying_windows.csv — 20 rows, one per price underlying

| Column | Meaning |
| --- | --- |
| `underlying` | the price process (BTC, INX=S&P, WTI…) |
| `n_window_series` | how many observation-window series exist on it |
| `window_suffixes` | `BASE`=hourly range, `D`=daily threshold, `Y`=annual, `MAXY/MINY`=running extremes, `VSGOLD`=relative, … |

**How to read a row.** `BTC, 8, BASE|D|MAXMON|MAXY|MINMON|MINY|VSGOLD|Y` — one spot path
feeds eight market families with different windows/transformations. They are near-
perfectly co-driven but **not** mutually bound (each window anchors its own issuance —
the monthly-max ⊄ annual-max trap is documented in the taxonomy). Curve/window RV
material.

## release_families.csv — 5 rows, one per macro release

**How to read a row.** `CPI, 10, KXCPI|KXCPICOMBO|KXCPICORE|...` — one BLS print
reprices ten series simultaneously (headline/core/YoY ladders, point-mass menus, combo
grids). Release-day chain trades start here; note the pointmass⊆ladder pairs inside the
family are Layer-1 bindings, the rest is shared-driver.

## Joining to price history

```python
# daily candles back to ~2024-11, hourly for months:
GET /trade-api/v2/series/{series}/markets/{ticker}/candlesticks
      ?start_ts=...&end_ts=...&period_interval=1440   # or 60
# full trade tape, cursor-paged:
GET /trade-api/v2/markets/trades?ticker={ticker}&limit=1000
```

`src/kalshi_structure/history.py` is a checkpointed collector for exactly this. The
intended first experiment is written out in
[layer2-correlation-guide.md](../../docs/layer2-correlation-guide.md).
