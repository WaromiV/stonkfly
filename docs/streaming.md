# One-second observations on CPU

`--stream` is an opt-in **paper-only** protocol. It gives the existing full brain a changing image each second while retaining minute-scale price history. It does not add an action-selection policy or establish improved learning.

```sh
python -m stonkfly run --stream --products SOL-USDC \
  --paper-fee 0.0008 --daily-orders 0 \
  --hodl-feedback growing-gap --account-feedback --out runs/sol-stream
python dashboard/server.py runs/sol-stream
```

Use a new directory for a new experiment. Existing directories have strict settings/source signatures: changing a flag or installing this version does not silently migrate them. A reviewed migration must preserve and verify the ledger, active native checkpoint, original HODL reference, execution outcomes and source hashes, back them up, then update the declared settings/provenance. Do not clear a signature error just to get a run started. The deployed experiment was migrated in place under those checks; its protocol change is a comparison boundary.

## Three separate clocks

| Clock | Behavior at defaults |
| --- | --- |
| Market observation | One current snapshot/image per second from a continuously received public WebSocket stream |
| Neural time | Alternate 8.3 / 8.3 / 8.4 ms steps: exactly 500 ms per 60 observations, at the original 0.1 ms integration resolution |
| Decision and reinforcement | At least 60 wall-clock seconds between decision boundaries; one fixed-decoder proposal and at most one new imposed pulse per boundary |

Membrane state, eligibility, adaptation and synaptic memory persist between slices. All 166,700 neurons and 25,582,938 retained edges remain present. The native neural kernel, plasticity rule, dopamine cell identities and fixed decoder are unchanged. Counts accumulate across the entire decision window; firing rates use its **actual** simulated duration, not a hard-coded half second.

The scheduler skips overdue observation slots and reports them. It does not run a backlog of observations, trades or punishments. A synchronous checkpoint or REST execution check can interrupt the one-second cadence. The next decision deadline starts after decision work finishes, so a window may contain slightly more or fewer than 60 observations. This is a one-second target, not a hard real-time guarantee. With `--neural-ms 600`, the budget would be 10 ms per observation; the chosen default preserves the previous nominal neural-time budget.

## Genuine minute candles

The adapter subscribes to public `market_trades`, `ticker` and `heartbeats`. Coinbase's `candles` WebSocket channel supplies **five-minute** buckets, so it is not used for one-minute charts. Instead:

1. Seed up to 120 completed `ONE_MINUTE` REST candles. Discard any unfinished/future seed bar.
2. Aggregate trades into UTC buckets starting at `floor(exchange_trade_time / 60) * 60`.
3. Update open, high, low, close and volume within that bucket; create a new bar only when the UTC minute changes.
4. Deduplicate trade IDs and use trade time/ID ordering for open and close even if messages arrive out of order.
5. Mark the first streaming minute **partial** because the connection may have missed earlier trades. A subscription snapshot is not assumed to contain the whole minute.
6. Carry forward the last close with zero volume for minutes with no observed trades; label these bars **synthetic**. Fill missing historical time slots rather than squeezing the time axis.

The eye image contains the last 100 minute candles (120 retained), plus wallet cues when enabled. A one-second observation does not become a new “minute.” Historical candles are public-market data; the recorded neural observations are not a full one-second replay archive.

For SOL-USDC, Coinbase documents that the public USDC subscription aliases the matching USD market. The observation adapter explicitly subscribes to **SOL-USD** and labels this in telemetry. Paper balances/orders remain **SOL-USDC**; each attempted execution still obtains a fresh SOL-USDC REST quote and current tradeability metadata, and applies the existing slippage, affordability and risk checks. This is still a long-only spot paper experiment, not MEXC perpetual execution. The configured fee is applied by the existing paper broker.

## Reinforcement delivery and restart behavior

At a decision boundary, evaluate portfolio P&L, HODL shortfall change and the preceding decision's balance-rejection outcome once. Their existing combination selects at most one pulse. The resulting `feedback` field has `delivery: "scheduled"`: it describes a **new request**, not stimulation already delivered.

A normal 200 ms neural pulse runs across about 24 one-second observations at the default budget, then ends. It is not a fresh 200 ms pulse every second. The current window's `neural.delivered_feedback`, `stimulus_ms` and `stimulus` describe what actually entered that window. Endogenous dopamine spikes are still distinct from imposed pulses. A rejection is visible in the next sensory update; its new reinforcement request is evaluated at the next decision boundary. Rewards therefore have a different temporal relationship to changing images than in the old single-image protocol. That is an experimental change, not a biologically validated improvement.

At each decision boundary, the native checkpoint, accumulated observation report, fractional budget carry and newly queued pulse state are committed together with the ledger anchor. After interruption, the brain and queued stimulation restore from that last durable boundary. Unsaved intra-minute neural work is lost, not added twice to saved state; restarting also reseeds price history and marks the new startup minute partial. A pending pulse cannot be overwritten by another request: if prolonged overruns leave it unfinished at the next boundary, execution stops for review.

Missing heartbeats, sequence gaps, invalid quotes/trades, background WebSocket exceptions or stale quotes stop the worker. There is no silent reconnect inside the adapter that pretends the intervening candle history was observed. A service restart must pass the existing reconciliation/resume checks and reseed the feed. Financial stops and uncertain order outcomes retain their existing handling.

## Dashboard and storage

The bundled read-only dashboard adds `/stream.json`. Its compact latest snapshot is replaced atomically each second; it is not an ever-growing one-second log. It includes:

- feed/paper product identities, observation sequence, feed age and current minute OHLC/volume;
- neural slice duration, measured wall compute time and advancing neural clock;
- up to 60 recent observation timestamps and a cumulative skipped-slot count for this process;
- current wallet sensory cues and the corresponding photoreceptor samples;
- requested/delivered/remaining pulse duration and its source decision/reason.

The dashboard refreshes streaming status and the eye image every second. Decision charts and neuron spike animation still summarize completed windows, and update when a new decision record arrives. Scheduled and delivered feedback are labeled separately. The eye image and JSON are separate atomic files, so a client reading across a write boundary can transiently see adjacent samples; neither is treated as an exact archived replay.

Only minute decisions append to `events.jsonl`; checkpoints still alternate between two files. The additional data are one small PNG and one bounded JSON snapshot. Dataset and neural state remain private/ignored.

The dashboard code derives from [Bgihe/stonkfly-dashboard](https://github.com/Bgihe/stonkfly-dashboard), under the repository's MIT license, with this fork's English, wallet/HODL and streaming additions. Optional animation videos are not bundled here; set `STONKFLY_ANIM` to an existing animation directory. `HOST` defaults to localhost, `PORT` to 8765; `STONKFLY_ROOT`, `STONKFLY_DATA` and `STONKFLY_VIZ_CACHE` can point to an existing deployment. The public deployment retains its existing videos.

## CPU measurement and tests

Measured on the deployment's x86 CPU with its retained brain checkpoint (2026-09-17 UTC): 12 isolated 8.3 ms slices averaged **0.137 s**, maximum **0.162 s**. An independent live-feed paper trial then ran **121 observations and two decisions** with the full graph: the final 60 slices averaged **0.134 s** wall time, maximum **0.222 s**; their mean observation interval was **0.998 s**, maximum **1.015 s**. One observation slot was skipped around decision/checkpoint work. Those figures are a short feasibility check, not a guaranteed latency bound or a profitability experiment.

Post-deployment verification observed two consecutive decision windows 61.83 seconds apart. Live slices averaged **0.135 s**, maximum **0.299 s** in the last 60 samples; observation intervals averaged **1.017 s**, maximum **2.649 s** across checkpoint work. Two slots had been skipped since startup. The second completed window recorded exactly one **200 ms** imposed pulse. Source/checkpoint hashes matched, with no halted state or unresolved orders. Desktop/mobile browser checks verified advancing observations, eye-image loading, separate scheduled/delivered feedback labels and read-only HTTP behavior.

The automated suite passed **90 tests**, with one optional dataset test skipped; the separate live CPU trial above exercised the actual full graph. Tests cover minute aggregation, duplicates/out-of-order trades, startup and missing minutes, bounded history, stale feed/sequence gaps, exact neural budget/resume carry, pulse duration across slices, illegal live/unpaced modes, and independent decision/rejection-feedback clocks under overruns. No test result establishes that more frequent input improves financial performance. That requires matched held-out/frozen controls with explicit protocol versions.

## Primary implementation references

- [Coinbase WebSocket endpoints and channels](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-endpoints): public endpoint, ticker/heartbeat channels, five-minute candle bucket, USDC-to-USD alias.
- [Coinbase market-trades schema](https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/websocket/market-trades): trade identifiers, exchange timestamps, size/price and batched updates.
- [Official Python SDK WebSocket implementation](https://github.com/coinbase/coinbase-advanced-py/blob/master/coinbase/websocket/websocket_base.py): public client lifecycle and background exception handling. This change uses the already-installed pinned SDK; it adds no feed dependency.
