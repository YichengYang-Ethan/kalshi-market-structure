# Verification manifest

Every count this repository asserts, and the public API call that reproduces it. No
authentication is required for any of these. Snapshot taken 2026-08-02T20:52Z; counts
drift as Kalshi lists and settles markets, so reproduce the *method*, not the digits —
a mismatch of a few percent on a later date is expected, a mismatch of a category is not.

## How the corpus was collected

```
GET https://api.elections.kalshi.com/trade-api/v2/events?status=open&with_nested_markets=true&limit=200
    then follow the `cursor` field until it is empty (46 pages on this snapshot)
GET https://api.elections.kalshi.com/trade-api/v2/series
    returns the full catalog in one response, no cursor
```

Three properties of this that a reviewer should check rather than take on trust:

1. **`status=open` is the only status fetched.** Settled and unopened events are
   excluded by construction. Any claim here about the exchange is a claim about its
   open surface.
2. **`/events` ignores `category`.** Passing `?category=Elections` returns mixed
   categories — the filter is silently dropped. All category filtering in this repo is
   client-side, which is why the full corpus must be paginated before any board can be
   analysed.
3. **Nested markets come back empty for settled events**, so the same call cannot be
   reused for historical work.

## Assertions

| Quantity | Value | Reproduce |
| --- | ---: | --- |
| Open events | 8,478 | count rows after full pagination |
| Open markets | 73,964 | sum `len(event.markets)` |
| Active markets | 72,401 | filter `market.status == 'active'` |
| Series in catalog | 12,370 | `len(GET /series)` |
| Series with open markets | 3,083 | distinct `event.series_ticker` |
| Distinct `event.category` values | 17 | `set(event.category)` |
| Events where series.category != event.category | 142 | join events to series on ticker |

## Per-board counts

Attributed by `event.category`, one board per event.

| Board | Events | Markets | Active | Ever traded | Series |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sports | 3,920 | 35,344 | 34,756 | 16,435 | 799 |
| Elections | 2,226 | 11,476 | 11,356 | 6,425 | 636 |
| Entertainment | 498 | 6,789 | 6,405 | 5,136 | 292 |
| Politics | 493 | 2,170 | 1,995 | 1,914 | 443 |
| Financials | 443 | 8,152 | 8,093 | 3,623 | 259 |
| Economics | 352 | 3,337 | 3,265 | 2,917 | 228 |
| Climate and Weather | 137 | 883 | 879 | 839 | 83 |
| Science and Technology | 119 | 802 | 702 | 634 | 103 |
| Crypto | 108 | 2,646 | 2,629 | 750 | 78 |
| Companies | 71 | 507 | 495 | 483 | 60 |
| Mentions | 58 | 983 | 957 | 913 | 57 |
| Commodities | 29 | 807 | 801 | 506 | 26 |
| Social | 9 | 30 | 30 | 30 | 9 |
| World | 7 | 23 | 23 | 19 | 5 |
| Health | 6 | 12 | 12 | 12 | 6 |
| NULL | 1 | 2 | 2 | 2 | 1 |
| Transportation | 1 | 1 | 1 | 1 | 1 |

## Contract-template mix

Templates are inferred, not published. `classify_event()` in
`src/kalshi_structure/taxonomy.py` is the definition; disagreement with these numbers
most likely means disagreement with that classifier, which is the useful thing to argue
about.

| Template | Events |
| --- | ---: |
| `entity_menu` | 4,073 |
| `threshold` | 2,959 |
| `binary` | 1,142 |
| `deadline` | 219 |
| `bucket` | 69 |
| `combination` | 16 |

## Partition diagnostics

- mutually exclusive events: **3,438**
- of those, numeric partitions passing the structural tiling check: **63**
- graded `explicit` / `implicit` / `none`: **14 / 44 / 5**

The explicit set is the only one where a buy-all-YES basket is supported by contract
text rather than inference. Tickers, so this is checkable one by one:

- `KXFEDTWEETS-26AUG06` (KXFEDTWEETS)
- `KXGDPYEAR-26` (KXGDPYEAR)
- `KXGDPYEAR-27` (KXGDPYEAR)
- `KXGDPYEAR-28` (KXGDPYEAR)
- `KXGDPYEAR-29` (KXGDPYEAR)
- `KXGDPYEAR-30` (KXGDPYEAR)
- `KXGDPYEAR-31` (KXGDPYEAR)
- `KXIMFTWEETS-26AUG06` (KXIMFTWEETS)
- `KXLFPRATE-27JAN08` (KXLFPRATE)
- `KXM2GROWTH-27JAN26` (KXM2GROWTH)
- `KXPSAVERT-27JAN` (KXPSAVERT)
- `KXSCFI-26DEC25` (KXSCFI)
- `KXWEFTWEETS-26AUG06` (KXWEFTWEETS)
- `KXWTIW-26AUG0714` (KXWTIW)

## Fee surface

Resolve per series from `GET https://api.elections.kalshi.com/trade-api/v2/series/{ticker}`; the published PDF has lagged the
API at least twice.

- zero-fee series in catalog: **14** — `KXBTCY`, `KXCITRINI`, `KXDOED`, `KXELECTIRAN`, `KXETHY`, `KXEXPAND`, `KXGAMBLINGREPEAL`, `KXGDPYEAR`, `KXGREENLAND`, `KXIRANDEMOCRACY`, `KXLAYOFFSYINFO`, `KXNEXTIRANLEADER`, `KXPAHLAVIHEAD`, `KXTRUMPOUT`
- of those, currently listing open markets: **11**
- maker-fee series in catalog: **130**, live: **78**

## What would falsify the collection

- A series with open markets that appears in `GET /series` but in none of our events.
- An `event.category` value we do not list.
- A page of `/events` reachable by cursor that our page count cannot account for.
- A market with `status='active'` inside an event we classify as having none.

Any of these means the corpus is incomplete and every count above is suspect.
