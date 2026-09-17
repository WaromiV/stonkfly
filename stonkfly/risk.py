"""Execution limits can veto a neural proposal, never substitute a strategy."""

import time

from .config import D, down, up


class Veto(Exception):
    def __init__(self, reason, code=None):
        super().__init__(reason)
        self.code = code


def order_capacity(settings, cash, holdings, quote, side):
    """Pure balance/minimum-order calculation shared by cues and execution.

    Affordability is not permission to trade: other guard checks still apply.
    """
    reserve = D(settings.fee_reserve)
    if side == "BUY":
        limit = up(quote.ask * (1 + D(settings.slippage)), quote.price_increment)
        budget = min(D(settings.order_limit), D(cash)) / (1 + reserve)
        size = down(budget / limit, quote.base_increment)
    elif side == "SELL":
        limit = down(quote.bid * (1 - D(settings.slippage)), quote.price_increment)
        size = down(
            min(D(holdings), D(settings.order_limit) / quote.ask), quote.base_increment
        )
    else:
        raise ValueError("Invalid side")
    return {
        "base_size": str(size),
        "limit_price": str(limit),
        "fee_ceiling": str(size * limit * reserve),
        "affordable": limit > 0 and size >= quote.minimum_base
        and size * limit >= quote.minimum_quote,
    }


class Guard:
    def __init__(self, settings, ledger, stop_file):
        self.s = settings
        self.l = ledger
        self.stop_file = stop_file

    def check(self, quotes, now):
        if self.stop_file.exists():
            raise Veto("STOP file present")
        if self.l.get("halted"):
            raise Veto(self.l.get("halted"))
        if self.l.pending():
            raise Veto("Order outcome unresolved")
        if set(quotes) != set(self.s.products):
            raise Veto("Incomplete market snapshot")
        for product, q in quotes.items():
            if q.product != product:
                raise Veto("Quote identity mismatch")
            if not -0.5 <= now - q.timestamp <= self.s.max_quote_age:
                raise Veto("Stale or future quote")
            if (q.ask - q.bid) / q.bid > D(self.s.spread_limit):
                raise Veto("Spread limit")
        if self.l.equity(quotes) <= D(self.l.get("initial_cash")) - D(self.s.loss_stop):
            self.l.halt("Loss stop reached; holdings remain exposed")
            raise Veto("Loss stop reached")

    def plan(self, product, side, quotes, now=None):
        now = time.time() if now is None else now
        self.check(quotes, now)
        if product not in self.s.products or side not in ("BUY", "SELL"):
            raise Veto("Invalid neural proposal")
        if now - self.l.get("last_attempt") < self.s.interval_seconds:
            raise Veto("Order cooldown")
        if self.s.daily_orders == 0 and self.l.get("mode") != "paper":
            raise Veto("Unlimited daily orders require paper mode")
        if self.s.daily_orders and self.l.attempts_today(now) >= self.s.daily_orders:
            raise Veto("Daily order limit")
        q = quotes[product]
        capacity = order_capacity(
            self.s, self.l.cash, self.l.positions.get(product, D(0)), q, side
        )
        if not capacity["affordable"]:
            raise Veto(
                "Insufficient funds/position or below exchange minimum",
                "insufficient_cash" if side == "BUY" else "insufficient_inventory",
            )
        return {
            "product": product,
            "side": side,
            **{k: capacity[k] for k in ("base_size", "limit_price", "fee_ceiling")},
            "observed_bid": str(q.bid),
            "observed_ask": str(q.ask),
            "quote_timestamp": q.timestamp,
            "settings": self.s.signature(),
            "order_type": "limit_limit_fok",
        }

    def before_submit(self, plan):
        # Called after exchange preview and balance checks, at the final send boundary.
        if self.stop_file.exists() or self.l.get("halted"):
            raise Veto("Execution stopped")
        if not -0.5 <= time.time() - plan["quote_timestamp"] <= self.s.max_quote_age:
            raise Veto("Quote expired before submission")
        pending = self.l.pending()
        if (
            len(pending) != 1
            or pending[0]["id"] != plan["client_order_id"]
            or pending[0]["status"] != "PREPARED"
        ):
            raise Veto("Intent ownership mismatch")
