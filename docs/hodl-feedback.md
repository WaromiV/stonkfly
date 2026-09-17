# HODL-relative feedback (paper experiment)

Enable on a **new single-product paper run**:

```sh
python -m stonkfly run --products SOL-USDC --paper-fee 0.0008 \
  --daily-orders 0 --hodl-feedback growing-gap --out runs/sol-hodl
```

The default is `--hodl-feedback off`. The fee above is a configurable assumption
of 0.08% per side, not a claim about a currently available exchange account tier.
Prices still come from Coinbase public spot data. This is not MEXC futures execution.

## Reference portfolio

HODL starts with the paper account's initial cash and buys once at the first
observation's **ask**, paying the configured paper fee. Quantity rounds down to the
market's base increment; unused cash remains cash. An unaffordable minimum order
leaves the reference in cash. Thereafter its equity is cash plus quantity times the
current **bid**, using the same observation as the fly. Neither marked equity
deducts a hypothetical exit fee. The reference never submits an order.

This is a fully invested passive comparator: it ignores the fly's $10 per-order
cap and gradual deployment of capital. It matches starting capital, entry costs
and marking convention, not all execution constraints. It is an observed
counterfactual value, not a forecast of an expected future price.

## Feedback rule

Let `E[t]` be the fly's marked equity, `H[t]` the HODL equity, and
`S[t] = max(0, H[t] - E[t])` its positive shortfall, all in USDC.

1. Calculate the existing P&L stimulus from `E[t] - E[t-1]`.
2. If `S[t] - S[t-1] >= reward_deadband` (default **0.01 USDC**), use an aversive
   stimulus instead, even if the fly made money in absolute terms.
3. Otherwise keep the ordinary P&L stimulus. A closing deficit does not by itself
   create a reward; an absolute loss can still trigger ordinary aversive feedback.

Example: fly equity rises from 100 to 100.10 while HODL rises from 101 to 101.20.
The shortfall grows from 1 to 1.10: the resulting stimulus is **aversive**. If both
values then remain unchanged, there is **no further stimulus for that old deficit**.
If the deficit closes and later opens again, that new widening can trigger feedback.
Sub-cent changes are not accumulated; the anchor advances on each committed tick.

There is at most **one existing 200 ms PPL101 pulse per default observation**,
with the existing configured current. Its duration/current are not scaled by the
shortfall and it does not stack with a simultaneous P&L punishment. The diagnostic
`meta_penalty_usdc` records a shortfall increase, not money deducted from the account.
Changing neural timing settings can shorten this pulse as before.

The full retained graph, candidate plasticity rule, fixed buy/sell decoder and
execution guard are unchanged. This deliberately adds a human-chosen preference
for keeping up with HODL; it is not a bias-free objective or a modeled brain
mechanism. It may encourage exposure in rising markets and does not establish
profitable learning. The stimulus still accompanies the current observation;
delayed action-specific credit assignment remains an open research problem.

## Persistence and audit

`observation.hodl` stores the original reference, marked value and shortfall in the
same SQLite transaction as the equity anchor and neural checkpoint pointer.
`observation.feedback` and event rows record base/effective stimulus, P&L delta,
HODL delta, relative delta, deficit change, threshold and reason. Restarts preserve
the entry price and comparison anchor. A new run's first tick establishes the
comparison without applying an extra penalty.

For an existing run, merely adding the flag is intentionally rejected by the
settings/provenance checks. A reviewed migration must stop the paper worker,
verify source and checkpoint hashes and unresolved orders, back up its ledger and
checkpoint, reconstruct HODL from the **original first quote**, and seed its previous
mark using the last committed quote and **equity anchor** (not a post-fill balance).
Then update the settings/provenance and observation atomically while preserving
orders, cash, holdings, tick and neural state. Log the activation boundary: earlier
ticks were trained with a different objective. Never silently reset the benchmark
or charge the entire historical deficit on activation.

## Evidence boundaries

This is engineered reward shaping. The policy-invariance results of
[Ng, Harada and Russell (1999)](https://ai.stanford.edu/~ang/papers/shaping-icml99.pdf)
do **not** establish policy invariance for this negative-only pulse override.
The existing candidate fly plasticity mechanism is discussed in
[the model notes](model.md); its biological references do not validate a HODL objective.
Evaluate this change against an unmodified control on matched, unseen market
traces with costs and exposure reported. Multiple runs and uncertainty matter;
see [Agarwal et al. (2021)](https://arxiv.org/abs/2108.13264). Neither a triggered
pulse nor changing synapses demonstrates that the fly learned the intended lesson.
