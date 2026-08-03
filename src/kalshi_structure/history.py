"""Historical data collection for the research universe.

Collects daily candlesticks and the full trade tape per market, with checkpointing so a
run can be resumed, and writes one JSONL shard per market family. Designed to be re-run:
completed tickers are skipped unless `--refresh` is passed.

Endpoint behaviour established by probing on 2026-08-02:

- `/markets/{ticker}/orderbook?depth=N` returns **full book depth without
  authentication**, but the levels sit under the `orderbook_fp` key as `no_dollars` and
  `yes_dollars` arrays of `[price, size]`. The `orderbook` key is always empty, and
  reading it is why this project spent weeks believing depth was unavailable. A liquid
  market returns 60-90 levels per side.
- Daily candles reach back to **2024-11-07** on long-lived series — nearly two years.
- `period_interval=1` (minute) works only over short windows; `60` and `1440` accept
  long spans. Minute data therefore has to be windowed and is left to a separate pass.
- Trades paginate by cursor with no apparent history limit; a liquid market returned
  6,000+ trades over six pages and was still not exhausted.
- Unauthenticated throughput of ~4-6 requests/second drew no 429s.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

BASE = "https://api.elections.kalshi.com/trade-api/v2"
USER_AGENT = "kalshi-market-structure/0.3 (research)"


@dataclass
class Throttle:
    """Token-bucket pacing. The public API tolerated ~6/s in probing; stay under it."""
    rate: float = 5.0
    _last: float = field(default=0.0, repr=False)

    def wait(self) -> None:
        gap = 1.0 / self.rate
        delta = time.monotonic() - self._last
        if delta < gap:
            time.sleep(gap - delta)
        self._last = time.monotonic()


class Client:
    def __init__(self, throttle: Throttle | None = None, tries: int = 5):
        self.throttle = throttle or Throttle()
        self.tries = tries
        self.calls = 0

    def get(self, path: str, **params) -> dict:
        url = f"{BASE}{path}"
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        for attempt in range(self.tries):
            self.throttle.wait()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    self.calls += 1
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code in (400, 404):        # permanent for this ticker
                    return {"_error": e.code}
                time.sleep(min(2 ** attempt, 30))
            except Exception:
                time.sleep(min(2 ** attempt, 30))
        return {"_error": "exhausted"}


def fetch_daily_candles(client: Client, series_ticker: str, ticker: str,
                        lookback_days: int = 800) -> list[dict]:
    now = int(time.time())
    d = client.get(f"/series/{series_ticker}/markets/{ticker}/candlesticks",
                   start_ts=now - lookback_days * 86400, end_ts=now, period_interval=1440)
    return d.get("candlesticks") or []


def fetch_trades(client: Client, ticker: str, max_pages: int = 60) -> list[dict]:
    """Full tape, newest first. max_pages bounds the very deepest books."""
    out: list[dict] = []
    cursor = None
    for _ in range(max_pages):
        d = client.get("/markets/trades", ticker=ticker, limit=1000, cursor=cursor)
        batch = d.get("trades") or []
        out.extend(batch)
        cursor = d.get("cursor")
        if not cursor or not batch:
            break
    return out


class Checkpoint:
    """Records which tickers are done so a run can resume after interruption."""

    def __init__(self, path: str):
        self.path = path
        self.done: set[str] = set()
        if os.path.exists(path):
            with open(path) as f:
                self.done = {line.strip() for line in f if line.strip()}
        self._fh = open(path, "a")

    def mark(self, ticker: str) -> None:
        self.done.add(ticker)
        self._fh.write(ticker + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def collect(markets: list[dict], out_dir: str, what: str, rate: float = 5.0,
            refresh: bool = False, min_volume: float = 0.0) -> dict:
    """Collect `what` in {'candles','trades'} for the given markets."""
    os.makedirs(out_dir, exist_ok=True)
    ck = Checkpoint(os.path.join(out_dir, f"_checkpoint_{what}.txt"))
    client = Client(Throttle(rate))
    out_path = os.path.join(out_dir, f"{what}.jsonl")
    stats = {"requested": 0, "skipped": 0, "empty": 0, "rows": 0, "errors": 0}
    t0 = time.time()

    with open(out_path, "a") as sink:
        for i, m in enumerate(markets):
            ticker = m["ticker"]
            if ticker in ck.done and not refresh:
                stats["skipped"] += 1
                continue
            try:
                vol = float(m.get("volume_fp") or 0)
            except (TypeError, ValueError):
                vol = 0.0
            if what == "trades" and vol < min_volume:
                ck.mark(ticker)
                stats["skipped"] += 1
                continue

            stats["requested"] += 1
            if what == "candles":
                rows = fetch_daily_candles(client, m["series_ticker"], ticker)
            else:
                rows = fetch_trades(client, ticker)

            if rows:
                sink.write(json.dumps({"ticker": ticker,
                                       "series_ticker": m.get("series_ticker"),
                                       what: rows}) + "\n")
                sink.flush()
                stats["rows"] += len(rows)
            else:
                stats["empty"] += 1
            ck.mark(ticker)

            if stats["requested"] % 250 == 0:
                el = time.time() - t0
                rem = (len(markets) - i - 1) * el / max(stats["requested"], 1)
                print(f"  [{what}] {i+1}/{len(markets)} req={stats['requested']} "
                      f"rows={stats['rows']:,} {el/60:.1f}m elapsed, ~{rem/60:.0f}m left",
                      flush=True)
    ck.close()
    stats["seconds"] = round(time.time() - t0, 1)
    stats["api_calls"] = client.calls
    return stats


def main() -> None:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from kalshi_structure.universe import DEFAULT_DATA, active_markets, build

    ap = argparse.ArgumentParser()
    ap.add_argument("--what", choices=["candles", "trades"], required=True)
    ap.add_argument("--out", default=os.path.join(DEFAULT_DATA, "elections_politics"))
    ap.add_argument("--rate", type=float, default=5.0)
    ap.add_argument("--min-volume", type=float, default=1.0,
                    help="skip trades for markets below this lifetime volume")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    events = build()
    markets = active_markets(events)
    print(f"universe: {len(events)} events / {len(markets)} active markets", flush=True)
    stats = collect(markets, args.out, args.what, rate=args.rate,
                    refresh=args.refresh, min_volume=args.min_volume)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
