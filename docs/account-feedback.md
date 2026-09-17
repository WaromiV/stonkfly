# Account cues and balance-rejection feedback

On a new single-product **paper** run, add `--account-feedback`:

```sh
python -m stonkfly run --products SOL-USDC --paper-fee 0.0008 \
  --daily-orders 0 --hodl-feedback growing-gap --account-feedback \
  --out runs/sol-wallet
```

The option is off by default and rejected in live mode. It changes observations
and reinforcement, so existing runs require a reviewed settings/source migration.

## What reaches the existing eyes

The upper strip below the header of the 320×180 input image contains broad visual cues:

- Cash and marked inventory fractions appear as two fixed-position brightness bars.
- BUY and SELL affordability appear as bright/dark blocks, calculated using the
  **same sizing function as the guard**, including increments, minimum size,
  the per-order cap, slippage allowance and fee reserve.
- Separate BUY/SELL outcome blocks show the immediately previous known result:
  cyan for filled, red for vetoed, and dark for no outcome for that side.

The chart occupies the area below the cues. All cues pass through the existing
R1–R6/R8 display adapter; the full graph, synapses and fixed decoder are retained.
Text labels help humans inspect the frame; no reading or currency understanding
is assumed. Affordability represents funds and order minima, not permission to
ignore cooldown, stale quotes or other execution checks. Cues do not replace an
unaffordable neural BUY with a programmed SELL or HOLD.

## What produces the rejection pulse

At tick `t`, the controller sees the wallet, proposes a trade and execution records
the result. A BUY veto coded `insufficient_cash`, or a SELL veto coded
`insufficient_inventory`, produces one **aversive pulse at tick `t+1`**. That next
observation includes the prior action's result block and updated wallet cues.

The pulse uses the existing PPL101 stimulus (200 ms with default neural timing).
It overrides a positive P&L reward. If P&L or HODL already calls for aversive
feedback, only one pulse is delivered, with both causes retained in diagnostics.
There is no growing punishment strength and no account balance deduction.
Cooldowns, price changes, network errors and other vetoes do not receive this
extra punishment. Repeated new unaffordable attempts can each receive feedback.

`execution_outcome` records the result in SQLite after execution. The next
observation accepts it only when its tick/product match the immediately preceding
committed tick. The new checkpoint, observation and equity anchor commit together.
A restart after that commit cannot punish the same stale result again. A crash
between execution and recording its result can leave that outcome unknown; it is
not invented or replayed as a new rejection. Existing order reconciliation remains
responsible for money accounting.

The dashboard's **Wallet signals** panel shows the **pre-decision snapshot** sent
to the fly, BUY/SELL affordability, previous execution outcome, whether a pulse was
delivered, its source tick, and whether the current rejection is awaiting the next
observation. Its recent-veto counter includes historical ticks before activation.
The main reinforcement panel distinguishes balance rejection, HODL shortfall and
ordinary P&L. `account`, `feedback` and coded `execution` fields are also logged.

## Migration and interpretation

Stop the paper worker, verify source/provenance and checkpoint hashes, confirm no
unresolved orders, and back up the ledger, active checkpoint and service settings.
Enable the setting and update reviewed provenance, preserving cash, holdings,
orders, neural state, HODL reference and anchors. Record the first affected tick.
Activation starts without charging historical rejections that occurred before
these cues existed. Preserve all existing halts unless separately reviewed.

This is an engineered observation/reward change. Seeing cues and receiving pulses
does not demonstrate learned affordability, effective delayed credit assignment,
biological understanding or improved profitability. Evaluate rejection frequency
alongside proposals, fills, exposure, costs and P&L against a matched control.
