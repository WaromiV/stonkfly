"""Continuous small steps with the original full brain and fixed decoder."""

import hashlib
import time
from fractions import Fraction

import numpy as np

from ..config import D


class NeuralBudget:
    """Distribute a minute's neural budget at 0.1 ms resolution, without drift."""

    def __init__(self, neural_ms, decision_seconds, observation_seconds=1, credit="0"):
        self.per_step = Fraction(D(neural_ms) * 10 * D(observation_seconds)) / Fraction(D(decision_seconds))
        self.credit = Fraction(credit)
        if self.per_step < 1 or not 0 <= self.credit < 1:
            raise ValueError("Invalid continuous neural budget")

    def next_ms(self):
        self.credit += self.per_step
        ticks = int(self.credit)
        self.credit -= ticks
        return ticks / 10


class ContinuousController:
    def __init__(self, controller, state=None):
        self.c = controller
        self.b = controller.brain
        self.pending = 0
        self.total_pulse = 0
        self.kind = "none"
        self.feedback = None
        self.source_tick = None
        self._reset_window()
        if state:
            self.kind = state["kind"]
            self.pending = state["remaining_ticks"]
            self.total_pulse = state["total_ticks"]
            self.feedback = state["feedback"]
            self.source_tick = state["source_tick"]
            if (self.kind not in ("none", "reward", "aversive")
                    or type(self.pending) is not int or type(self.total_pulse) is not int
                    or not 0 <= self.pending <= self.total_pulse <= round(controller.s.pulse_ms / self.b.dt)
                    or (self.kind == "none" and self.total_pulse)):
                raise ValueError("Invalid checkpointed reinforcement queue")

    def _reset_window(self):
        self.counts = np.zeros(self.b.n, dtype=np.int32)
        self.window_ms = 0.0
        self.steps = 0
        self.wall = 0.0
        self.delivered_ms = 0.0
        self.delivered_kind = "none"
        self.delivered_feedback = None
        self.input_hash = None

    def queue(self, kind, feedback, source_tick):
        if self.pending:
            raise RuntimeError("Prior reinforcement pulse has not finished")
        if kind not in ("none", "reward", "aversive"):
            raise ValueError("Unknown reinforcement")
        self.kind, self.feedback, self.source_tick = kind, dict(feedback), source_tick
        self.pending = self.total_pulse = round(self.c.s.pulse_ms / self.b.dt) if kind != "none" else 0

    def state(self):
        # Saved only at decision boundaries, when accumulated counts are reset.
        if self.steps:
            raise RuntimeError("Checkpoint continuous state only at a decision boundary")
        return {"kind": self.kind, "remaining_ticks": self.pending,
                "total_ticks": self.total_pulse, "feedback": self.feedback,
                "source_tick": self.source_tick}

    def step(self, rgb, duration_ms):
        started = time.perf_counter()
        remaining = round(duration_ms / self.b.dt)
        if remaining < 1 or abs(remaining * self.b.dt - duration_ms) > 1e-7:
            raise ValueError("Step must be a positive multiple of neural dt")
        delivered = 0
        while remaining:
            n = min(remaining, round(self.c.s.neural_bin_ms / self.b.dt))
            stimulus = None
            if self.pending:
                n = min(n, self.pending)
                stimulus = (self.b.circuit[self.kind], self.c.s.pulse_current)
            counts, _ = self.b.rgb_step(rgb, n * self.b.dt,
                                       learning=self.c.s.learning, stimulation=stimulus)
            self.counts += counts
            remaining -= n
            if stimulus is not None:
                self.pending -= n
                delivered += n
                self.delivered_kind = self.kind
                self.delivered_feedback = {**self.feedback, "scheduled_at_tick": self.source_tick}
        elapsed = time.perf_counter() - started
        self.window_ms += duration_ms
        self.steps += 1
        self.wall += elapsed
        self.delivered_ms += delivered * self.b.dt
        self.input_hash = hashlib.sha256(np.asarray(rgb).tobytes()).hexdigest()
        return {"neural_ms": duration_ms, "compute_seconds": elapsed,
                "brain_ms": self.b.sim_ms, "input_sha256": self.input_hash,
                "stimulus": self.kind if delivered else "none",
                "stimulus_ms": delivered * self.b.dt,
                "pulse_remaining_ms": self.pending * self.b.dt,
                "pulse_delivered_ms": (self.total_pulse - self.pending) * self.b.dt,
                "pulse_total_ms": self.total_pulse * self.b.dt,
                "feedback_tick": self.source_tick, "feedback": self.feedback}

    def finish_window(self):
        if not self.steps:
            raise RuntimeError("No neural observations in decision window")
        self.b.counts[:] = self.counts
        result = {
            **self.c.decoder.decode(self.counts, self.window_ms / 1000),
            "brain_ms": self.b.sim_ms, "compute_seconds": self.wall,
            "window_ms": self.window_ms, "observations": self.steps,
            "stimulus": self.delivered_kind, "stimulus_ms": self.delivered_ms,
            "delivered_feedback": self.delivered_feedback,
            "reward_spikes": int(self.counts[self.b.circuit["reward"]].sum()),
            "aversive_spikes": int(self.counts[self.b.circuit["aversive"]].sum()),
            "KC_spikes": int(self.counts[self.b.circuit["kc"]].sum()),
            "total_spikes": int(self.counts.sum()),
            "spike_sha256": hashlib.sha256(self.counts.tobytes()).hexdigest(),
            "input_sha256": self.input_hash, "memory": self.b.memory(),
        }
        self._reset_window()
        return result
