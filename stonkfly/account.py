"""Engineered wallet observations; never selects or replaces a neural action."""

from .config import D
from .risk import order_capacity


def account_observation(settings, ledger, quote):
    cash = ledger.cash
    base = ledger.positions.get(quote.product, D(0))
    inventory = base * quote.bid
    total = cash + inventory
    if min(cash, base) < 0 or total <= 0:
        raise ValueError("Invalid account observation")
    previous = ledger.get("execution_outcome")
    # A crash between checkpoint commit and execution can leave an older result.
    # Do not present that stale result as the immediately preceding action.
    if previous and (
        previous["tick"] != ledger.get("tick")
        or previous["product"] != quote.product
    ):
        previous = None
    return {
        "model": "account-visual-v1",
        "product": quote.product,
        "cash_usdc": str(cash),
        "base_size": str(base),
        "inventory_usdc": str(inventory),
        "cash_fraction": str(cash / total),
        "inventory_fraction": str(inventory / total),
        "minimum_quote_usdc": str(quote.minimum_quote),
        "buy_affordable": order_capacity(settings, cash, base, quote, "BUY")["affordable"],
        "sell_affordable": order_capacity(settings, cash, base, quote, "SELL")["affordable"],
        "previous_execution": previous,
    }


def execution_outcome(tick, product, side, order):
    return {
        "tick": tick,
        "product": product,
        "side": side,
        "status": order["status"],
        "reason": order.get("reason"),
        "reason_code": order.get("reason_code"),
    }
