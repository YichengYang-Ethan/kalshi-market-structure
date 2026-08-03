# data/

Structure index for the 2026-08-02 census: identifiers and derived classifications only.

| File | Rows | Contents |
| --- | ---: | --- |
| `events_index.csv` | 8,478 | one row per open event, plain CSV |
| `events_index.csv.gz` | 8,478 | the same rows, gzip |
| `markets_index.csv.gz` | 73,964 | one row per market |
| `series_rollup.csv` | 3,083 | per-series counts aggregated from the market index |

**No market data is here.** No prices, no sizes, no volumes, no open interest, no
contract text — those belong to the exchange and its terms bar redistribution. What is
published is the set of identifiers plus the classifications this repository derives from
them, so that the inferences every count rests on can be checked row by row.

`template`, `partition_tiled` and `exhaustiveness` are **inferences**, produced by
`src/kalshi_structure/taxonomy.py`. They are the most likely thing in this repository to
be wrong, which is why they are the part published in full. `ever_traded` and
`traded_24h` are booleans derived from volume; the volumes themselves are not published.

To reconstruct anything else, run `src/kalshi_structure/fetch.py` against the public API.
