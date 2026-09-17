import json
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from stonkfly.config import D, Settings
from stonkfly.market import Quote
from stonkfly.neural.continuous import ContinuousController, NeuralBudget
from stonkfly.stream_market import CoinbaseStreamMarket, FeedUnavailable, MinuteCandles


def candle(start, price="100"):
    return {"start": str(start), "open": price, "high": price, "low": price,
            "close": price, "volume": "1"}


def test_trade_ohlc_updates_same_minute_and_deduplicates_out_of_order_trades():
    book = MinuteCandles(150, [candle(60), candle(180, "999")])
    book.trade("3", 166, "102", "3")
    book.trade("1", 153, "101", "1")
    book.trade("2", 160, "99", "2")
    book.trade("2", 160, "99", "2")
    for second in range(167, 180):
        assert len(book.view(second)) == 2
    current = book.view(179)[-1]
    assert [current[k] for k in ("open", "high", "low", "close", "volume")] == ["101", "102", "99", "102", "6"]
    assert current["partial"]
    book.trade("4", 181, "103", "1")
    assert len(book.view(181)) == 3 and not book.view(181)[-1]["partial"]
    empty = book.view(241)[-1]
    assert empty["synthetic"] and empty["volume"] == "0" and empty["close"] == "103"


def test_candle_history_is_bounded_and_never_recounts_seeded_trades():
    book = MinuteCandles(150, [candle(60)], limit=3)
    book.trade("1", 100, "900", "1")
    assert book.view(150)[0]["close"] == "100"
    bars = book.view(600)
    assert [b["start"] for b in bars] == [480, 540, 600]


def test_missing_historical_minutes_keep_their_time_slots():
    bars = MinuteCandles(250, [candle(60), candle(180, "102")]).view(250)
    assert [b["start"] for b in bars] == [60, 120, 180, 240]
    assert bars[1]["synthetic"] and bars[1]["volume"] == "0"
    assert bars[1]["close"] == "100" and not bars[1]["partial"]
    with pytest.raises(ValueError, match="volume"):
        MinuteCandles(150, [{**candle(60), "volume": "-1"}])


def test_stream_failures_are_not_usable_snapshots(monkeypatch):
    market = CoinbaseStreamMarket(("SOL-USDC",), client=object())
    market.ws = SimpleNamespace(raise_background_exception=lambda: None)
    market.book = MinuteCandles(150, [candle(60)])
    monkeypatch.setattr("stonkfly.stream_market.time.time", lambda: 150)
    market.on_message(json.dumps({"channel": "heartbeats", "sequence_num": 0}))
    market.on_message(json.dumps({"channel": "heartbeats", "sequence_num": 2}))
    with pytest.raises(FeedUnavailable, match="sequence gap"):
        market.snapshot()
    market.error = None
    market.quote = object()
    market.heartbeat_at = 144
    with pytest.raises(FeedUnavailable, match="heartbeat"):
        market.snapshot()


def test_exact_neural_budget_and_resume_fraction():
    budget = NeuralBudget(500, 60)
    steps = [budget.next_ms() for _ in range(60)]
    assert set(steps) == {8.3, 8.4}
    assert sum(steps) == pytest.approx(500)
    budget.next_ms()
    resumed = NeuralBudget(500, 60, credit=str(budget.credit))
    assert [budget.next_ms() for _ in range(60)] == [resumed.next_ms() for _ in range(60)]


class SmallBrain:
    def __init__(self):
        self.n, self.dt, self.sim_ms = 4, .1, 0
        self.circuit = {"reward": np.array([0]), "aversive": np.array([1]), "kc": np.array([2])}
        self.counts = np.zeros(4, np.int32)
        self.luminance = np.zeros(4, np.float32)
        self.r8_light = np.zeros(2, np.float32)
        self.stimulation_ms = 0

    def rgb_step(self, frame, duration_ms, learning, stimulation):
        self.sim_ms += duration_ms
        if stimulation is not None:
            self.stimulation_ms += duration_ms
        return np.ones(4, np.int32), 0

    def memory(self):
        return {"changed_edges": 0}


class SmallController:
    def __init__(self, settings, side="HOLD"):
        self.s, self.brain = settings, SmallBrain()
        self.decoder = SimpleNamespace(decode=lambda counts, seconds: {"side": side, "seconds": seconds})

    def save(self, path):
        path.write_bytes(b"test checkpoint")


def test_pulse_spans_updates_once_and_decode_uses_accumulated_duration():
    c = SmallController(Settings(streaming=True))
    streaming = ContinuousController(c)
    streaming.queue("aversive", {"reason": "test"}, 7)
    saved = streaming.state()
    streaming = ContinuousController(c, saved)
    budget = NeuralBudget(500, 60)
    frame = np.zeros((180, 320, 3), np.uint8)
    samples = [streaming.step(frame, budget.next_ms()) for _ in range(60)]
    report = streaming.finish_window()
    assert sum(s["stimulus_ms"] for s in samples) == pytest.approx(200)
    assert c.brain.stimulation_ms == pytest.approx(200)
    assert report["seconds"] == pytest.approx(.5)
    assert report["delivered_feedback"]["scheduled_at_tick"] == 7
    assert report["observations"] == 60 and streaming.state()["remaining_ticks"] == 0
    assert streaming.step(frame, 8.3)["stimulus_ms"] == 0


def test_pending_pulse_cannot_be_multiplied_or_checkpointed_without_window_boundary():
    streaming = ContinuousController(SmallController(Settings(streaming=True)))
    streaming.queue("reward", {}, 1)
    with pytest.raises(RuntimeError, match="has not finished"):
        streaming.queue("reward", {}, 2)
    streaming.step(np.zeros((180, 320, 3), np.uint8), 8.3)
    with pytest.raises(RuntimeError, match="decision boundary"):
        streaming.state()


def test_streaming_cli_rejects_live_and_unpaced_replay(tmp_path):
    for option in ("--live", "--fixture", "--fast"):
        result = subprocess.run([sys.executable, "-m", "stonkfly", "run", "--stream", option,
                                 "--out", str(tmp_path / "forbidden")], capture_output=True, text=True)
        assert result.returncode == 2
        assert not (tmp_path / "forbidden").exists()


@pytest.mark.parametrize("overrun", [False, True])
def test_observations_do_not_multiply_decisions_or_rejection_pulses(tmp_path, monkeypatch, overrun):
    from stonkfly import risk
    from stonkfly.broker import PaperBroker
    from stonkfly.ledger import Ledger
    from stonkfly.streaming import run_stream

    class Clock:
        value = 1000000000.0
        def time(self): return self.value
        def monotonic(self): return self.value
        def sleep(self, duration): self.value += duration

    clock = Clock()
    monkeypatch.setattr(risk, "time", clock)

    class Feed:
        feed_product = "SOL-USD"
        history = {"SOL-USDC": [100.0] * 100}
        closed = False
        calls = 0
        def start(self): pass
        def close(self): self.closed = True
        def snapshot(self):
            self.calls += 1
            if overrun and self.calls == 2:
                clock.sleep(4)
            self.heartbeat_at = clock.time()
            self.candles = [{**candle(int(clock.time() // 60) * 60), "partial": False, "synthetic": False}]
            return {"SOL-USDC": Quote("SOL-USDC", D(100), D("100.01"), clock.time(),
                    D(".00000001"), D(".01"), D(".01"), D(1), D(".00000001"))}
        execution_snapshot = snapshot

    s = Settings(products=("SOL-USDC",), account_feedback=True, streaming=True, daily_orders=0)
    ledger = Ledger(tmp_path / "ledger.sqlite", s, "paper")
    ledger.put("cash", ".5")
    ledger.put("positions", {"SOL-USDC": ".995"})
    c, feed = SmallController(s, "BUY"), Feed()
    run_stream(s, ledger, PaperBroker(s, ledger), c, feed, tmp_path, steps=3, clock=clock)
    rows = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert len(rows) == 3 and ledger.get("tick") == 3
    assert all(b["wall_time"] - a["wall_time"] >= 60 for a, b in zip(rows, rows[1:]))
    assert all(row["execution"]["reason_code"] == "insufficient_cash" for row in rows)
    assert rows[0]["feedback"]["rejection_triggered"] is False
    assert rows[1]["feedback"]["rejection_source_tick"] == 1
    assert rows[1]["feedback"]["delivery"] == "scheduled"
    assert rows[2]["neural"]["stimulus_ms"] == pytest.approx(200)
    assert c.brain.stimulation_ms == pytest.approx(200)  # Not 60 repeated pulses.
    assert not ledger.pending() and feed.closed
    latest = json.loads((tmp_path / "stream.json").read_text())
    assert latest["sequence"] >= 170
    assert bool(latest["missed_observations_total"]) is overrun
    assert latest["status"] == "stopped"
    assert ledger.get("observation")["stream_state"]["controller"]["source_tick"] == 3
    ledger.close()
