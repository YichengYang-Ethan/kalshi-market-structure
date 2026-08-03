# Fee model

Verified against the official fee schedule PDF effective 2026-07-07 and cross-checked
against the live `/series` endpoint on 2026-08-02. Where the static PDF and the API
disagree, **the API is authoritative** — see [Resolving fees correctly](#resolving-fees-correctly).

## Formulas

```
taker fee = ceil_centicent( fee_multiplier × 0.07 × C × P × (1 − P) )
maker fee = ceil_centicent(                  0.0175 × C × P × (1 − P) )   [only on maker-fee series]
settlement fee = 0
```

`P` is the fill price in dollars and `C` the contract count. Rounding is up to a
centicent ($0.0001) per order, so splitting one order into many small fills costs
slightly more than a single fill.

The taker fee peaks at `P = 0.50` (1.75¢ per contract at multiplier 1) and vanishes at
the extremes. A two-leg package traded taker/taker near mid therefore carries roughly
3.5¢ of fees — which is the number any structural edge has to clear.

## The fee surface is not uniform

Of 12,370 series:

| `fee_type` | `fee_multiplier` | Series | Meaning |
| --- | --- | --- | --- |
| `quadratic` | 1 | 12,226 | Standard: taker pays, maker free |
| `quadratic_with_maker_fees` | 1 | 130 | Both sides pay; maker at 25% of taker |
| `quadratic` | 0 | 14 | Free on both sides |

Restricted to series with open markets (3,083), the exceptions are 78 maker-fee series
and 11 zero-fee series.

### Zero-fee series (live)

| Series | API category | Subject |
| --- | --- | --- |
| `KXGREENLAND` | Politics | US purchase of Greenland |
| `KXGAMBLINGREPEAL` | Politics | Federal gambling-tax repeal |
| `KXDOED` | Politics | Department of Education elimination |
| `KXIRANDEMOCRACY` | Politics | Democratic transition in Iran |
| `KXELECTIRAN` | Elections | Iranian election |
| `KXPAHLAVIHEAD` | Financials *(mislabelled)* | Who leads Iran |
| `KXBTCY` | Crypto | Bitcoin year-end price |
| `KXETHY` | Crypto | Ether year-end price |
| `KXGDPYEAR` | Economics | Annual GDP growth |
| `KXCITRINI` | Economics | (thematic index) |
| `KXLAYOFFSYINFO` | Economics | Annual layoffs |

Three further zero-fee series (`KXEXPAND`, `KXNEXTIRANLEADER`, `KXTRUMPOUT`) currently
have no open markets.

On these series **both** sides are free, so any positive gross edge is a positive net
edge. That makes them the cheapest place to test a structural
constraint — the constraint either holds or it does not, with no fee wall to argue about.

### Maker-fee series (live): the liquidity tax

The 78 live maker-fee series are not a random sample. They are, almost exactly, the
highest-flow products listed:

| Group | Count | Examples |
| --- | --- | --- |
| Sports | 56 | `KXNFLGAME`, `KXMLBGAME`, `KXNBA`, `KXUCL`, `KXATPMATCH`, `KXSB` |
| Macro releases | 10 | `KXCPI`, `KXFED`, `KXFEDDECISION`, `KXGDP`, `KXPAYROLLS`, `KXU3`, `KXRATECUTCOUNT` |
| Awards | 7 | `KXEMMY*`, `KXHEISMAN`, `KXBALLONDOR`, `KXSUPERBOWLHEADLINE` |
| Annual index ranges | 3 | `KXINXY`, `KXNASDAQ100Y`, `KXIPO` |
| Other | 2 | `KXLLM1`, `KXBTCMAX150` |

This produces a structural tension worth stating plainly: **resting orders are free
exactly where the books are thin, and taxed exactly where they are deep.** Any approach
that depends on passive execution is pushed toward the illiquid long tail, where the
constraint violations are larger but the fills are uncertain. Any approach that wants
size is pushed into the deep books, where the maker fee removes the free-execution
advantage. The fee schedule is doing real work in shaping which strategies can exist.

Note that the daily/hourly/weekly index series (`KXINXU`, `KXNASDAQ100U`) are taker-only
while the *yearly* ranges (`KXINXY`, `KXNASDAQ100Y`) charge maker fees — the split is by
series, not by underlying.

## Resolving fees correctly

The published PDF lags the exchange. Two documented cases as of 2026-08-02:

1. The February 2026 schedule carried a 0.035 coefficient for S&P 500 / Nasdaq-100
   series. The July 2026 schedule dropped it; `/series/fee_changes?show_historical=true`
   shows `KXINX*` and `KXNASDAQ100*` moving to `fee_type=quadratic, fee_multiplier=1`
   effective 2026-07-03T17:00Z.
2. `KXTRUMPOUT` and `KXNEXTIRANLEADER` do not appear in the July PDF's non-standard-fee
   table, but the live API returns `fee_multiplier=0` for both.

Therefore: **resolve `fee_multiplier` and `fee_type` per series from the API immediately
before pricing, and fail closed at multiplier 1 when unknown.** Never hard-code a
zero-fee list from a document. `GET /series/fee_changes?show_historical=true` gives the
change log if provenance matters.

## Collateral and capital

- **Mutually-exclusive collateral netting (`MECNET`)** — within a single mutually
  exclusive event, Kalshi holds only the maximum possible loss rather than the full
  notional of each leg. Buying NO on every leg of an N-way event therefore ties up far
  less capital than the sum of the premiums, and the structural profit is returned as
  cash at entry.
- Netting is **opt-in and off by default**, and the setting **locks at the event level
  when the first order in that event is submitted — even if that order never fills.**
  A probe order can therefore permanently fix the collateral treatment of an event.
- Enabling it can make positions **unsellable** before settlement ("we may be unable to
  sell positions for which you've already had collateral returned"), converting a
  netted package into hold-to-expiry.
- There is **no cross-event netting**. Two legs in different events each post collateral
  independently, which is what makes long-dated cross-event structures capital-expensive.
- Open positions and cash both accrue interest (documented at 3.25% APY, variable), so
  the carrying cost of a hold-to-settlement leg is the T-bill yield minus that rate
  rather than the full risk-free rate.
