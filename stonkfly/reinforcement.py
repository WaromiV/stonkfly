from .config import D


def reinforcement(equity, anchor, deadband):
    """Incremental marked-to-bid portfolio P&L, including booked trading fees.
    The broker rejects external deposits/withdrawals before this is evaluated.
    This is an engineered stimulus, not a statement that a fly understands money.
    """
    delta = D(equity) - D(anchor)
    threshold = D(deadband)
    kind = (
        "reward"
        if delta >= threshold
        else "aversive"
        if delta <= -threshold
        else "none"
    )
    return kind, delta


def hodl_reinforcement(equity, anchor, deadband, current, previous):
    """Override the ordinary pulse when a positive HODL shortfall grows.

    The same bounded aversive pulse is used even if both signals are negative.
    No action is selected here. First observations establish a comparison anchor.
    """
    base_kind, delta = reinforcement(equity, anchor, deadband)
    shortfall = max(D(0), D(current["equity_usdc"]) - D(equity))
    if D(current["shortfall_usdc"]) != shortfall:
        raise ValueError("Current HODL shortfall accounting mismatch")
    change = hodl_delta = excess = None
    triggered = False
    if previous is not None:
        if current["reference"] != previous["reference"]:
            raise ValueError("HODL reference changed within run")
        old_shortfall = max(D(0), D(previous["equity_usdc"]) - D(anchor))
        if D(previous["shortfall_usdc"]) != old_shortfall:
            raise ValueError("Previous HODL shortfall accounting mismatch")
        change = shortfall - old_shortfall
        hodl_delta = D(current["equity_usdc"]) - D(previous["equity_usdc"])
        excess = delta - hodl_delta
        triggered = change >= D(deadband)
    kind = "aversive" if triggered else base_kind
    feedback = {
        "policy": "growing-gap",
        "base_stimulus": base_kind,
        "effective_stimulus": kind,
        "reason": "hodl_shortfall_grew" if triggered else "portfolio_pnl",
        "initialized": previous is None,
        "pnl_delta_usdc": str(delta),
        "hodl_delta_usdc": str(hodl_delta) if hodl_delta is not None else None,
        "excess_delta_usdc": str(excess) if excess is not None else None,
        "shortfall_usdc": str(shortfall),
        "shortfall_change_usdc": str(change) if change is not None else None,
        "meta_triggered": triggered,
        "meta_penalty_usdc": str(change) if triggered else "0",
        "deadband_usdc": str(D(deadband)),
    }
    return kind, delta, feedback


def account_reinforcement(kind, delta, feedback, account):
    """One next-observation aversive pulse for a recorded balance rejection.

    The outcome must come from account_observation's tick-matched ledger record.
    Portfolio/HODL evidence remains logged; pulses do not stack or grow in strength.
    """
    previous = account["previous_execution"]
    rejected = bool(
        previous and previous["status"] == "VETO"
        and (previous["side"], previous.get("reason_code")) in (
            ("BUY", "insufficient_cash"), ("SELL", "insufficient_inventory")
        )
    )
    result = dict(feedback) if feedback else {
        "policy": "portfolio-pnl",
        "base_stimulus": kind,
        "pnl_delta_usdc": str(delta),
        "reason": "portfolio_pnl",
    }
    result.update({
        "account_feedback": True,
        "stimulus_before_account_feedback": kind,
        "rejection_triggered": rejected,
        "rejection_source_tick": previous["tick"] if rejected else None,
        "rejected_side": previous["side"] if rejected else None,
        "rejection_code": previous["reason_code"] if rejected else None,
    })
    if rejected:
        kind = "aversive"
        result["reason"] = "balance_rejection"
    result["effective_stimulus"] = kind
    return kind, result
