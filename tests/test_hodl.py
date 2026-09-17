import dataclasses
import json
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from stonkfly.benchmark import HodlBenchmark
from stonkfly.config import D, Settings
from stonkfly.ledger import Ledger
from stonkfly.market import Quote
from stonkfly.reinforcement import hodl_reinforcement


def quote(**changes):
    return dataclasses.replace(
        Quote("SOL-USDC", D("99"), D("100"), 1000,
              D(".001"), D(".01"), D(".01"), D("1"), D(".001")),
        **changes,
    )


def test_hodl_pays_entry_fee_and_spread_keeps_rounding_cash():
    b = HodlBenchmark.start("100", quote(), ".0008", 1)
    assert D(b.base_size) == D(".999")
    assert D(b.entry_fee) == D(".07992")
    assert D(b.cash) == D(".02008")
    assert b.equity(quote()) == D("98.92108")
    assert b.equity(quote(bid=D("110"), ask=D("111"))) == D("109.91008")
    assert HodlBenchmark.restore(json.loads(json.dumps(b.json()))) == b


def test_unaffordable_hodl_is_cash():
    b = HodlBenchmark.start(".50", quote(), ".0008", 1)
    assert D(b.base_size) == 0
    assert D(b.entry_fee) == 0
    assert b.equity(quote()) == D(".50")


def test_hodl_rejects_bad_reference_or_mark():
    b = HodlBenchmark.start("100", quote(), ".0008", 1)
    with pytest.raises(ValueError, match="accounting mismatch"):
        HodlBenchmark.restore({**b.json(), "cash": "1"})
    with pytest.raises(ValueError, match="product mismatch"):
        b.equity(quote(product="ETH-USDC"))
    with pytest.raises(ValueError, match="precedes"):
        b.equity(quote(timestamp=999))


def mark(hodl, equity):
    return {"reference": {"fixed": True}, "equity_usdc": hodl,
            "shortfall_usdc": str(max(D(0), D(hodl) - D(equity)))}


@pytest.mark.parametrize(
    "old_e,new_e,old_h,new_h,kind,triggered",
    [
        ("100", "100.10", "101", "101.20", "aversive", True),
        ("100", "100", "101", "101", "none", False),
        ("100", "100.10", "101", "101.05", "reward", False),
        ("100", "99.9", "101", "100.5", "aversive", False),
        ("100", "100", "99.9", "100.02", "aversive", True),
        ("100", "100", "101", "101.01", "aversive", True),
        ("100", "100", "101", "101.009", "none", False),
        ("100", "100.1", "100", "100.1", "reward", False),
        ("100", "100.1", "99", "99.5", "reward", False),
    ],
)
def test_only_growing_positive_shortfall_overrides_pnl(
    old_e, new_e, old_h, new_h, kind, triggered
):
    actual, delta, feedback = hodl_reinforcement(
        new_e, old_e, ".01", mark(new_h, new_e), mark(old_h, old_e)
    )
    assert actual == kind
    assert delta == D(new_e) - D(old_e)
    assert feedback["meta_triggered"] is triggered
    assert D(feedback["excess_delta_usdc"]) == delta - (D(new_h) - D(old_h))


def test_first_mark_does_not_punish_historical_deficit():
    kind, _, f = hodl_reinforcement("100", "100", ".01", mark("110", "100"), None)
    assert kind == "none"
    assert f["initialized"] and not f["meta_triggered"]
    assert f["shortfall_change_usdc"] is None


def test_reference_and_anchor_cannot_silently_change():
    previous, current = mark("101", "100"), mark("102", "101")
    with pytest.raises(ValueError, match="Previous HODL shortfall"):
        hodl_reinforcement("101", "99", ".01", current, previous)
    previous["reference"] = {"fixed": False}
    with pytest.raises(ValueError, match="reference changed"):
        hodl_reinforcement("101", "100", ".01", current, previous)


def test_restart_preserves_entry_and_does_not_repeat_old_penalty(tmp_path):
    settings = Settings(products=("SOL-USDC",), hodl_feedback="growing-gap")
    b = HodlBenchmark.start("100", quote(), ".0008", 1)
    latest = quote(bid=D("110"), ask=D("111"), timestamp=2000)
    snapshot = b.mark(latest, "100")
    ledger = Ledger(tmp_path / "ledger.sqlite", settings, "paper")
    ledger.commit_tick(D("100"), {"file": "test"}, {"hodl": snapshot})
    ledger.close()
    resumed = Ledger(tmp_path / "ledger.sqlite", settings, "paper")
    previous = resumed.get("observation")["hodl"]
    restored = HodlBenchmark.restore(previous["reference"])
    current = restored.mark(latest, "100")
    kind, _, feedback = hodl_reinforcement(
        "100", resumed.get("anchor"), ".01", current, previous
    )
    assert kind == "none" and not feedback["meta_triggered"]
    assert current == snapshot and restored.entry_tick == 1
    resumed.close()


def test_hodl_configuration_and_live_rejection(tmp_path):
    assert Settings().hodl_feedback == "off"
    with pytest.raises(ValueError, match="exactly one product"):
        Settings(products=("SOL-USDC", "BTC-USDC"), hodl_feedback="growing-gap")
    with pytest.raises(ValueError, match="Unknown HODL"):
        Settings(hodl_feedback="always")
    out = tmp_path / "live-run"
    result = subprocess.run(
        [sys.executable, "-m", "stonkfly", "run", "--live", "--hodl-feedback",
         "growing-gap", "--preflight-only", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 2 and "only in paper mode" in result.stderr
    assert not out.exists()


def test_cli_delivers_override_and_resumes_without_repeating_it(tmp_path, monkeypatch):
    from stonkfly import cli, data, market
    from stonkfly.neural import controller

    pulses, restores = [], []

    class TestController:
        def __init__(self, settings):
            self.brain = SimpleNamespace(circuit={"report": {}}, visual_report={})

        def observe(self, frame, kind):
            pulses.append(kind)
            return {"side": "HOLD", "stimulus": kind,
                    "memory": {"changed_edges": 0}}

        def save(self, path):
            path.write_bytes(b"test neural checkpoint")

        def restore(self, path):
            restores.append(path.read_bytes())

    class TestMarket:
        def __init__(self, products):
            self.tick = 0
            self.history = {"SOL-USDC": [100.0] * 120}

        def snapshot(self):
            price = D("100") if self.tick == 0 else D("101")
            self.tick += 1
            return {"SOL-USDC": quote(bid=price, ask=price + D(".01"),
                                       timestamp=time.time())}

        def record(self, quotes):
            self.history["SOL-USDC"].append(float(quotes["SOL-USDC"].bid))

    monkeypatch.setattr(data, "verify", lambda: {})
    monkeypatch.setattr(controller, "FlyController", TestController)
    monkeypatch.setattr(market, "FixtureMarket", TestMarket)
    out = tmp_path / "paper"
    args = ["stonkfly", "run", "--fixture", "--fast", "--products", "SOL-USDC",
            "--paper-fee", ".0008", "--hodl-feedback", "growing-gap",
            "--out", str(out), "--steps"]
    monkeypatch.setattr(sys, "argv", [*args, "2"])
    cli.main()
    monkeypatch.setattr(sys, "argv", [*args, "1"])
    cli.main()
    events = [json.loads(row) for row in (out / "events.jsonl").read_text().splitlines()]
    assert pulses == ["none", "aversive", "none"]
    assert restores == [b"test neural checkpoint"]
    assert [e["tick"] for e in events] == [1, 2, 3]
    assert events[1]["feedback"]["meta_triggered"]
    assert events[1]["pnl_delta_usdc"] == "0"
    assert events[0]["hodl"]["reference"] == events[2]["hodl"]["reference"]
