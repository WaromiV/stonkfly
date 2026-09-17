import dataclasses
import json
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest

from stonkfly.account import account_observation, execution_outcome
from stonkfly.config import D, Settings
from stonkfly.display import market_frame
from stonkfly.ledger import Ledger
from stonkfly.market import Quote
from stonkfly.neural.sensory import retinal_samples
from stonkfly.reinforcement import account_reinforcement
from stonkfly.risk import Guard, Veto, order_capacity


def quote(**changes):
    return dataclasses.replace(
        Quote("SOL-USDC", D("100"), D("100.01"), time.time(),
              D(".00000001"), D(".01"), D(".01"), D("1"), D(".00000001")),
        **changes,
    )


@pytest.mark.parametrize("cash,held", [(".485", ".986"), ("100", "0"), ("1", ".001"), ("1.03", "1")])
def test_cues_and_guard_agree_on_affordability(tmp_path, cash, held):
    s = Settings(products=("SOL-USDC",), account_feedback=True)
    ledger = Ledger(tmp_path / "ledger.sqlite", s, "paper")
    ledger.put("cash", cash)
    ledger.put("positions", {"SOL-USDC": held})
    # Isolate sizing from the independent portfolio loss-stop check.
    ledger.put("initial_cash", str(D(cash) + D(held) * 100))
    q = quote()
    cues = account_observation(s, ledger, q)
    guard = Guard(s, ledger, tmp_path / "STOP")
    assert D(cues["cash_fraction"]) + D(cues["inventory_fraction"]) == 1
    for side in ("BUY", "SELL"):
        capacity = order_capacity(s, cash, held, q, side)
        assert cues[side.lower() + "_affordable"] == capacity["affordable"]
        if capacity["affordable"]:
            plan = guard.plan("SOL-USDC", side, {"SOL-USDC": q})
            assert plan["base_size"] == capacity["base_size"]
            if side == "BUY":
                assert D(plan["base_size"]) * D(plan["limit_price"]) + D(plan["fee_ceiling"]) <= min(D(cash), D(s.order_limit))
        else:
            with pytest.raises(Veto) as error:
                guard.plan("SOL-USDC", side, {"SOL-USDC": q})
            assert error.value.code == ("insufficient_cash" if side == "BUY" else "insufficient_inventory")
    ledger.close()


@pytest.mark.parametrize("status,code,side,penalized", [
    ("VETO", "insufficient_cash", "BUY", True),
    ("VETO", "insufficient_inventory", "SELL", True),
    ("VETO", None, "BUY", False),  # Cooldown, stale book, spread, etc.
    ("VETO", "insufficient_inventory", "BUY", False),
    ("FILLED", None, "BUY", False),
    ("HOLD", None, "HOLD", False),
])
def test_rejection_feedback_is_specific_and_preserves_pnl_evidence(status, code, side, penalized):
    account = {"previous_execution": execution_outcome(7, "SOL-USDC", side, {
        "status": status, "reason_code": code,
    })}
    original = {"policy": "growing-gap", "base_stimulus": "reward", "reason": "portfolio_pnl",
                "meta_triggered": False, "pnl_delta_usdc": ".1"}
    kind, feedback = account_reinforcement("reward", D(".1"), original, account)
    assert kind == ("aversive" if penalized else "reward")
    assert feedback["rejection_triggered"] is penalized
    assert feedback["base_stimulus"] == "reward" and feedback["pnl_delta_usdc"] == ".1"
    assert "rejection_triggered" not in original
    assert feedback["rejection_source_tick"] == (7 if penalized else None)


def test_rejection_and_hodl_use_one_existing_pulse():
    account = {"previous_execution": execution_outcome(7, "SOL-USDC", "BUY", {
        "status": "VETO", "reason_code": "insufficient_cash",
    })}
    kind, f = account_reinforcement("aversive", D(".1"), {
        "base_stimulus": "reward", "meta_triggered": True, "reason": "hodl_shortfall_grew",
    }, account)
    assert kind == "aversive" and f["meta_triggered"] and f["rejection_triggered"]
    assert f["reason"] == "balance_rejection"


def test_stale_result_is_not_punished_again_after_checkpoint_restart(tmp_path):
    s = Settings(products=("SOL-USDC",), account_feedback=True)
    ledger = Ledger(tmp_path / "ledger.sqlite", s, "paper")
    ledger.put("tick", 7)
    ledger.put("execution_outcome", execution_outcome(7, "SOL-USDC", "BUY", {
        "status": "VETO", "reason_code": "insufficient_cash",
    }))
    cues = account_observation(s, ledger, quote())
    assert account_reinforcement("reward", D(1), None, cues)[0] == "aversive"
    ledger.commit_tick(D(100), {"file": "test"}, {"account": cues})
    ledger.close()
    # Simulate crash after this checkpoint, before recording the next execution.
    ledger = Ledger(tmp_path / "ledger.sqlite", s, "paper")
    cues = account_observation(s, ledger, quote())
    assert cues["previous_execution"] is None
    assert account_reinforcement("reward", D(1), None, cues)[0] == "reward"
    ledger.close()


def test_wallet_cues_reach_retinal_sampler(tmp_path):
    s = Settings(products=("SOL-USDC",), account_feedback=True)
    ledger = Ledger(tmp_path / "ledger.sqlite", s, "paper")
    cash_only = account_observation(s, ledger, quote())
    ledger.put("cash", ".485")
    ledger.put("positions", {"SOL-USDC": ".986"})
    invested = account_observation(s, ledger, quote())
    args = ("SOL-USDC", [100.0] * 100, D("100"), D("100.01"))
    baseline = market_frame(*args)
    first, second = market_frame(*args, cash_only), market_frame(*args, invested)
    # Sample bar centers and affordability blocks through the real adapter.
    uv = np.array([[70 / 319, 49 / 179], [225 / 319, 49 / 179],
                   [40 / 319, 80 / 179], [200 / 319, 80 / 179]], np.float32)
    light1, light2 = retinal_samples(first, uv), retinal_samples(second, uv)
    assert light1[0] > light2[0] and light1[1] < light2[1]
    assert light1[2] > light2[2] and light1[3] < light2[3]
    assert np.array_equal(first[94:], second[94:])  # Wallet cannot invent a price.
    assert np.array_equal(baseline, market_frame(*args, None))
    invested["previous_execution"] = execution_outcome(1, "SOL-USDC", "BUY", {"status": "VETO"})
    rejected = market_frame(*args, invested)
    assert not np.array_equal(rejected[63:84, 80:155], second[63:84, 80:155])
    ledger.close()


def test_account_mode_configuration_and_live_rejection(tmp_path):
    assert not Settings().account_feedback
    with pytest.raises(ValueError, match="boolean"):
        Settings(account_feedback=1)
    with pytest.raises(ValueError, match="exactly one"):
        Settings(account_feedback=True, products=("SOL-USDC", "BTC-USDC"))
    out = tmp_path / "live"
    result = subprocess.run([sys.executable, "-m", "stonkfly", "run", "--live",
                             "--account-feedback", "--out", str(out)], capture_output=True, text=True)
    assert result.returncode == 2 and "only in paper mode" in result.stderr
    assert not out.exists()


def test_each_cue_intersects_the_retained_retinal_projection():
    from stonkfly.neural.common import GRAPH

    if not GRAPH.exists():
        pytest.skip("Requires an already prepared graph; never downloads data")
    with np.load(GRAPH) as graph:
        uv = graph["uv"]
    account = {"cash_fraction": ".5", "inventory_fraction": ".5",
               "buy_affordable": False, "sell_affordable": False, "previous_execution": None}
    args = ("SOL-USDC", [100.0] * 100, D(100), D("100.01"))
    baseline = retinal_samples(market_frame(*args, account), uv)
    variants = [
        {"cash_fraction": "1"}, {"inventory_fraction": "1"},
        {"buy_affordable": True}, {"sell_affordable": True},
        {"previous_execution": {"side": "BUY", "status": "VETO"}},
        {"previous_execution": {"side": "SELL", "status": "VETO"}},
    ]
    for changed in variants:
        light = retinal_samples(market_frame(*args, {**account, **changed}), uv)
        assert np.count_nonzero(light != baseline) > 0, changed


def test_cli_rejected_buy_is_punished_once_across_restarts(tmp_path, monkeypatch):
    from stonkfly import cli, data, market
    from stonkfly.neural import controller

    pulses, frames, restores = [], [], []
    sides = iter(["BUY", "HOLD", "HOLD"])

    class TestController:
        def __init__(self, settings):
            self.brain = SimpleNamespace(circuit={"report": {}}, visual_report={})

        def observe(self, frame, kind):
            frames.append(frame.copy())
            pulses.append(kind)
            return {"side": next(sides), "stimulus": kind, "memory": {"changed_edges": 0}}

        def save(self, path):
            path.write_bytes(b"test neural checkpoint")

        def restore(self, path):
            restores.append(path.read_bytes())

    class TestMarket:
        def __init__(self, products):
            self.tick = 0
            self.history = {"SOL-USDC": [100.0] * 120}

        def snapshot(self):
            price = D("100") + D(self.tick) / 10
            self.tick += 1
            return {"SOL-USDC": quote(bid=price, ask=price + D(".01"))}

        def record(self, quotes):
            self.history["SOL-USDC"].append(float(quotes["SOL-USDC"].bid))

    monkeypatch.setattr(data, "verify", lambda: {})
    monkeypatch.setattr(controller, "FlyController", TestController)
    monkeypatch.setattr(market, "FixtureMarket", TestMarket)
    out = tmp_path / "paper"
    s = Settings(products=("SOL-USDC",), paper_fee=".0008", hodl_feedback="growing-gap", account_feedback=True)
    ledger = Ledger(out / "ledger.sqlite", s, "paper")
    ledger.put("cash", ".485")
    ledger.put("positions", {"SOL-USDC": "1"})
    ledger.close()
    monkeypatch.setattr(sys, "argv", ["stonkfly", "run", "--fixture", "--fast", "--steps", "1",
        "--products", "SOL-USDC", "--paper-fee", ".0008", "--hodl-feedback", "growing-gap",
        "--account-feedback", "--out", str(out)])
    for _ in range(3):
        cli.main()
    rows = [json.loads(row) for row in (out / "events.jsonl").read_text().splitlines()]
    assert pulses == ["reward", "aversive", "reward"]
    assert len(restores) == 2
    assert rows[0]["execution"]["reason_code"] == "insufficient_cash"
    assert rows[0]["neural"]["side"] == "BUY"  # Cues never substitute HOLD/SELL.
    assert rows[1]["account"]["previous_execution"]["tick"] == 1
    assert rows[1]["feedback"]["rejection_source_tick"] == 1
    assert D(rows[1]["pnl_delta_usdc"]) > 0
    assert rows[2]["feedback"]["rejection_triggered"] is False
    assert not np.array_equal(frames[0][63:84, 80:155], frames[1][63:84, 80:155])
