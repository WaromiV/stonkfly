"""One-second sensing; independently paced minute decisions and reward requests."""

import hashlib
import json
import os
import time
import uuid
from collections import deque

from PIL import Image

from .account import account_observation, execution_outcome
from .actions import StonkflyActions
from .benchmark import HodlBenchmark
from .config import D
from .display import market_frame
from .neural.continuous import ContinuousController, NeuralBudget
from .reinforcement import account_reinforcement, hodl_reinforcement, reinforcement
from .risk import Guard, Veto


def atomic_json(path, data):
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(data, allow_nan=False) + "\n")
    os.replace(temporary, path)


def run_stream(settings, ledger, broker, controller, market, out, steps=0, clock=time):
    if broker.mode != "paper" or not settings.streaming:
        raise RuntimeError("Streaming loop requires explicit paper mode")
    previous = ledger.get("observation") or {}
    saved = previous.get("stream_state") or {}
    neural = ContinuousController(controller, saved.get("controller"))
    budget = NeuralBudget(settings.neural_ms, settings.interval_seconds, credit=saved.get("budget_credit", "0"))
    sequence = saved.get("sequence", 0)
    previous_hodl = previous.get("hodl")
    benchmark = HodlBenchmark.restore(previous_hodl["reference"]) if previous_hodl else None
    guard = Guard(settings, ledger, out / "STOP")
    provider = StonkflyActions(guard, broker)
    action = provider.get_actions()[0]
    product = settings.products[0]
    session = uuid.uuid4().hex
    recent = deque(maxlen=60)
    decisions = missed_total = 0
    last_status = None
    try:
        market.start()
        next_observation = clock.monotonic()
        next_decision = next_observation + settings.interval_seconds
        while not steps or decisions < steps:
            if (out / "STOP").exists() or ledger.get("halted"):
                break
            now = clock.monotonic()
            if now >= next_decision:
                broker.reconcile()
                broker.verify_balances()
                quotes = market.snapshot()
                guard.check(quotes, clock.time())
                q, equity = quotes[product], ledger.equity(quotes)
                kind, delta = reinforcement(equity, ledger.get("anchor"), settings.reward_deadband)
                feedback = {"policy": "portfolio-pnl", "base_stimulus": kind,
                            "effective_stimulus": kind, "reason": "portfolio_pnl",
                            "pnl_delta_usdc": str(delta)}
                hodl = None
                if settings.hodl_feedback != "off":
                    if benchmark is None:
                        raise RuntimeError("Streaming HODL reference was not initialized")
                    hodl = benchmark.mark(q, equity)
                    kind, delta, feedback = hodl_reinforcement(
                        equity, ledger.get("anchor"), settings.reward_deadband, hodl, previous_hodl
                    )
                account = account_observation(settings, ledger, q) if settings.account_feedback else None
                if account:
                    kind, feedback = account_reinforcement(kind, delta, feedback, account)
                report = neural.finish_window()
                feedback = {**feedback, "delivery": "scheduled", "pulse_ms_requested": settings.pulse_ms if kind != "none" else 0}
                tick = ledger.get("tick") + 1
                neural.queue(kind, feedback, tick)
                # The queue and anchor commit with the checkpoint. On a crash,
                # uncheckpointed neural work is rolled back, not replayed on top.
                checkpoint = out / f"brain-{ledger.get('tick') % 2}.npz"
                controller.save(checkpoint)
                cp = {"file": checkpoint.name, "sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest()}
                observation = {
                    "neural": report, "product": product, "quote": q.json(),
                    "pnl_delta_usdc": str(delta), "market_history": market.history,
                    "minute_candles": market.candles, "fixture_tick": None,
                    "hodl": hodl, "feedback": feedback, "account": account,
                    "stream_state": {"controller": neural.state(), "budget_credit": str(budget.credit), "sequence": sequence},
                }
                ledger.commit_tick(equity, cp, observation)
                previous_hodl = hodl
                order = {"status": "HOLD"}
                if report["side"] != "HOLD":
                    try:
                        fresh = market.execution_snapshot()
                        if abs(fresh[product].bid - q.bid) / q.bid > D(settings.slippage):
                            raise Veto("Price moved beyond neural observation tolerance")
                        provider.quotes = fresh
                        order = action.invoke({"product": product, "side": report["side"]})
                    except Veto as exc:
                        order = {"status": "VETO", "reason": str(exc), "reason_code": exc.code}
                if settings.account_feedback:
                    ledger.put("execution_outcome", execution_outcome(tick, product, report["side"], order))
                row = {
                    "tick": tick, "wall_time": clock.time(), "product": product, "mode": "paper",
                    "quote": q.json(), "equity_usdc": str(equity), "pnl_delta_usdc": str(delta),
                    "neural": report, "execution": order, "hodl": hodl, "feedback": feedback, "account": account,
                    "streaming": True, "current_candle": market.candles[-1],
                    "timing": {"observation_seconds": 1, "decision_seconds": settings.interval_seconds,
                               "window_neural_ms": report["window_ms"], "window_observations": report["observations"],
                               "missed_observations_total": missed_total},
                }
                with (out / "events.jsonl").open("a") as handle:
                    handle.write(json.dumps(row, allow_nan=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                atomic_json(out / "latest.json", row)
                print(json.dumps({"tick": tick, "side": report["side"], "execution": order["status"],
                                  "equity": str(equity), "observations": report["observations"],
                                  "neural_ms": report["window_ms"], "feedback_scheduled": kind}), flush=True)
                decisions += 1
                # Start after the decision work: never squeeze two attempts or
                # feedback requests closer together to catch up after a delay.
                next_decision = clock.monotonic() + settings.interval_seconds
                if steps and decisions >= steps:
                    break
            now = clock.monotonic()
            if now < next_observation:
                clock.sleep(min(.1, next_observation - now))
                continue
            skipped = max(0, int(now - next_observation))
            missed_total += skipped
            next_observation += 1 + skipped
            quotes = market.snapshot()
            guard.check(quotes, clock.time())
            q = quotes[product]
            if benchmark is None and settings.hodl_feedback != "off":
                benchmark = HodlBenchmark.start(ledger.get("initial_cash"), q, settings.paper_fee, ledger.get("tick") + 1)
            account = account_observation(settings, ledger, q) if settings.account_feedback else None
            frame = market_frame(product, market.history[product], q.bid, q.ask, account, market.candles)
            observed_at = clock.time()
            sample = neural.step(frame, budget.next_ms())
            sequence += 1
            recent.append({"sequence": sequence, "time": observed_at, "compute_seconds": sample["compute_seconds"],
                           "neural_ms": sample["neural_ms"], "minute": market.candles[-1]["start"]})
            image_path = out / "latest-input.partial.png"
            Image.fromarray(frame).save(image_path)
            os.replace(image_path, out / "latest-input.png")
            last_status = {
                "session": session, "sequence": sequence, "wall_time": clock.time(),
                "observation_time": observed_at, "decision_tick": ledger.get("tick"),
                "next_decision_in_seconds": max(0, next_decision - clock.monotonic()),
                "feed_product": market.feed_product, "paper_product": product,
                "quote": q.json(), "quote_age_seconds": clock.time() - q.timestamp,
                "heartbeat_age_seconds": clock.time() - market.heartbeat_at,
                "current_candle": market.candles[-1], "candle_count": len(market.candles),
                "history_start": market.candles[0]["start"], "account": account,
                "neural": sample, "recent_observations": list(recent),
                "missed_observations_total": missed_total,
                "luminance": controller.brain.luminance.astype(float).round(3).tolist(),
                "r8_light": controller.brain.r8_light.astype(float).round(3).tolist(),
                "status": "running",
            }
            atomic_json(out / "stream.json", last_status)
    finally:
        market.close()
        if last_status:
            atomic_json(out / "stream.json", {**last_status, "status": "stopped"})
