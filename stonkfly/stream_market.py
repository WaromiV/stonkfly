"""Public WebSocket observations and UTC minute candles, paper mode only."""

import json
import threading
import time
from collections import deque

from .config import D
from .market import CoinbaseMarket, Quote, unwrap, utc_timestamp


class FeedUnavailable(RuntimeError):
    pass


class MinuteCandles:
    """Aggregate actual trades; observations never append extra minute bars."""

    def __init__(self, started, seed=(), limit=120):
        self.started = float(started)
        self.cutoff = int(started // 60) * 60
        self.limit = limit
        self.bars = {}
        self.seen = set()
        self.seen_order = deque()
        for row in seed:
            start = int(row["start"])
            if start >= self.cutoff:
                continue
            prices = {k: D(row[k]) for k in ("open", "high", "low", "close")}
            if start % 60 or not 0 < prices["low"] <= min(prices["open"], prices["close"]) <= max(prices["open"], prices["close"]) <= prices["high"]:
                raise ValueError("Invalid historical minute candle")
            volume = D(row["volume"])
            if volume < 0:
                raise ValueError("Invalid historical volume")
            self.bars[start] = {"start": start, **prices, "volume": volume,
                                "partial": False, "synthetic": False}
        if not self.bars:
            raise ValueError("No completed minute candles")
        # Some markets omit empty candles. Keep their time on the chart rather
        # than compressing several wall-clock minutes into one horizontal slot.
        close = self.bars[min(self.bars)]["close"]
        for start in range(min(self.bars), max(self.bars) + 1, 60):
            if start not in self.bars:
                self.bars[start] = {"start": start, **dict.fromkeys(("open", "high", "low", "close"), close),
                                    "volume": D(0), "partial": False, "synthetic": True}
            close = self.bars[start]["close"]
        self._trim()

    def _trim(self):
        for start in sorted(self.bars)[:-self.limit]:
            del self.bars[start]

    def advance(self, now):
        minute = int(now // 60) * 60
        last = max(self.bars)
        close = self.bars[last]["close"]
        for start in range(max(last + 60, minute - (self.limit - 1) * 60), minute + 1, 60):
            self.bars[start] = {"start": start, **dict.fromkeys(("open", "high", "low", "close"), close),
                                "volume": D(0), "partial": start <= self.cutoff, "synthetic": True}
        self._trim()

    def trade(self, trade_id, timestamp, price, size):
        price, size = D(price), D(size)
        if price <= 0 or size <= 0:
            raise ValueError("Invalid public trade")
        start = int(timestamp // 60) * 60
        if start < self.cutoff or str(trade_id) in self.seen:
            return
        self.seen.add(str(trade_id))
        self.seen_order.append(str(trade_id))
        if len(self.seen_order) > 20000:
            self.seen.discard(self.seen_order.popleft())
        if start < min(self.bars):
            return
        self.advance(timestamp)
        row = self.bars[start]
        key = (float(timestamp), int(trade_id))
        if row["synthetic"]:
            row.update({**dict.fromkeys(("open", "high", "low", "close"), price),
                        "volume": size, "synthetic": False, "_first": key, "_last": key})
        else:
            row["high"], row["low"] = max(row["high"], price), min(row["low"], price)
            row["volume"] += size
            if key < row["_first"]:
                row["open"], row["_first"] = price, key
            if key > row["_last"]:
                row["close"], row["_last"] = price, key

    def view(self, now):
        self.advance(now)
        return [{k: str(v) if k in ("open", "high", "low", "close", "volume") else v
                 for k, v in row.items() if not k.startswith("_")}
                for _, row in sorted(self.bars.items())]


class CoinbaseStreamMarket:
    def __init__(self, products, client=None, ws_factory=None):
        if len(products) != 1:
            raise ValueError("Streaming currently requires one paper product")
        self.product = products[0]
        # Coinbase public -USDC subscriptions alias -USD, documented explicitly.
        self.feed_product = self.product.removesuffix("-USDC") + "-USD"
        self.rest = CoinbaseMarket(products, client)
        self.ws_factory = ws_factory
        self.ws = None
        self.lock = threading.RLock()
        self.quote = None
        self.heartbeat_at = 0
        self.sequence = None
        self.error = None
        self.history = {self.product: []}
        self.candles = None
        self.book = None
        self.meta = None

    def start(self):
        now = time.time()
        end = int(now // 60) * 60
        seed = unwrap(self.rest.client.get_public_candles(
            self.feed_product, str(end - 120 * 60), str(end), "ONE_MINUTE", limit=120
        )).get("candles", [])
        # REST execution checks and increment metadata remain on the paper pair.
        self.rest.snapshot()
        self.meta = self.rest.meta[self.product]
        self.book = MinuteCandles(now, seed)
        if self.ws_factory is None:
            from coinbase.websocket import WSClient
            self.ws_factory = WSClient
        self.ws = self.ws_factory(api_key=None, api_secret=None, on_message=self.on_message,
                                  retry=False, timeout=10)
        self.ws.open()
        self.ws.heartbeats()
        self.ws.ticker([self.feed_product])
        self.ws.market_trades([self.feed_product])
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            with self.lock:
                if self.error:
                    raise FeedUnavailable(self.error)
                if self.quote and self.heartbeat_at:
                    return
            time.sleep(.05)
        raise FeedUnavailable("Public stream did not become ready")

    def on_message(self, raw):
        with self.lock:
            try:
                row = json.loads(raw)
                if row.get("type") == "error":
                    raise ValueError("Subscription rejected")
                seq = row.get("sequence_num")
                if seq is not None:
                    if self.sequence is not None and seq != self.sequence + 1:
                        raise ValueError("WebSocket sequence gap; restart to reseed candles")
                    self.sequence = seq
                channel = row.get("channel")
                if channel == "heartbeats":
                    self.heartbeat_at = time.time()
                elif channel == "ticker":
                    timestamp = utc_timestamp(row["timestamp"])
                    for event in row["events"]:
                        for ticker in event.get("tickers", []):
                            if ticker["product_id"] != self.feed_product:
                                raise ValueError("Unexpected stream product")
                            m = self.meta
                            self.quote = Quote(self.product, D(ticker["best_bid"]), D(ticker["best_ask"]), timestamp,
                                D(m["base_increment"]), D(m["quote_increment"]),
                                D(m.get("price_increment", m["quote_increment"])),
                                D(m["quote_min_size"]), D(m["base_min_size"]))
                elif channel == "market_trades":
                    trades = [t for event in row["events"] for t in event.get("trades", [])]
                    for trade in sorted(trades, key=lambda t: (t["time"], int(t["trade_id"]))):
                        if trade["product_id"] != self.feed_product:
                            raise ValueError("Unexpected stream product")
                        timestamp = utc_timestamp(trade["time"])
                        if timestamp > time.time() + .5:
                            raise ValueError("Future stream trade")
                        self.book.trade(trade["trade_id"], timestamp, trade["price"], trade["size"])
            except Exception as exc:
                # Keep raw upstream payloads out of error messages.
                self.error = str(exc) if type(exc) is ValueError else "Invalid public stream message"

    def snapshot(self):
        self.ws.raise_background_exception()
        with self.lock:
            if self.error:
                raise FeedUnavailable(self.error)
            if not self.quote or time.time() - self.heartbeat_at > 5:
                raise FeedUnavailable("Stale public WebSocket heartbeat")
            self.candles = self.book.view(time.time())
            self.history[self.product] = [float(D(c["close"])) for c in self.candles]
            return {self.product: self.quote}

    def execution_snapshot(self):
        return self.rest.snapshot()

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass  # Cleanup must not hide the original feed/worker failure.
            self.ws = None
