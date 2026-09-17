# Stonkfly

Fork of [nftechie/stonkfly](https://github.com/nftechie/stonkfly). The research direction here is to make learning measurable, then test a small number of additional neural mechanisms. Upstream authorship and the original license are preserved.

## Research goals · a detailed eight-week plan

**Status: proposed work, not completed features.** This README documents the plan; publishing it does not implement the experiments or validate the model. The existing implementation and installation instructions follow [below](#current-model).

- [ ] Establish reproducible, chronological experiments with explicit clocks, costs, checkpoints and controls.
- [ ] Test acquisition, reversal, extinction, retention and the causal contribution of learned state.
- [ ] Add and evaluate short-term synaptic depression and facilitation in a selected circuit.
- [ ] Test slow homeostatic regulation without selecting a preferred trading action.
- [ ] Explore compartment-specific learning, forgetting and recurrent feedback.
- [ ] Make mechanism measurements, uncertainty and failed experiments inspectable.
- [ ] Publish a reproducible result, whether positive, negative or inconclusive.
- [ ] Optionally substitute a structural-plasticity or neuron-growth track using a separate synthetic circuit.

**Working assumption:** one developer, approximately 30–40 hours per week, for eight weeks: **40 working days across 56 calendar days**. Each week has five scheduled workdays; its two remaining calendar days are rest or unattended, checkpointed computation, not hidden implementation time. Day 20 is a useful four-week stopping point. Day estimates are planning judgments, not estimates supplied by the cited papers. A missed scientific or engineering gate moves the dependent work; it does not justify fabricating a successful result.

**Daily rhythm:** roughly one hour reading/design, three to four hours implementation, one to two hours tests/analysis, and half an hour recording decisions. Benchmark campaigns may run longer than a workday, subject to the measured hardware budget. Friday work includes review and contingency. Prefer finishing one comparison to accumulating untested mechanisms.

**Success:** explain whether a particular mechanism changes measured behavior under a declared protocol, and whether that change survives appropriate controls. Weight movement, a dramatic graph and a profitable hour are insufficient. Full biological replication, a new GPU backend, a full MEXC perpetuals engine, consciousness claims and guaranteed profitability are outside this schedule.

### Read the plan

| Stage | Days | Result to aim for |
| --- | --- | --- |
| [Starting point and experimental rules](#experimental-contract) | Before implementation | A declared baseline and limits on interpretation |
| [Week 1: reproducibility](#week-1) | 01–05 | Identical observations and recoverable state across conditions |
| [Week 2: learning assays](#week-2) | 06–10 | Acquisition, reversal, retention and timing measurements |
| [Week 3: short-term plasticity](#week-3) | 11–15 | One independently switchable mechanism with reference tests |
| [Week 4: first result](#week-4) | 16–20 | A controlled, held-out four-week report |
| [Week 5: homeostasis](#week-5) | 21–25 | A bounded activity-regulation experiment |
| [Week 6: memory compartments](#week-6) | 26–30 | A limited test of different memory timescales and feedback |
| [Week 7: observability and ablations](#week-7) | 31–35 | Inspectable mechanisms and a frozen final protocol |
| [Week 8: evaluation and release](#week-8) | 36–40 | A reproducible result with explicit claim boundaries |
| [Optional growth experiment](#growth-experiment) | A replacement track | Synthetic rewiring or neuron addition, separately labeled |
| [Research references](#research-references) | Throughout | Primary sources, their relevance and transfer limitations |

<a id="experimental-contract"></a>

## Starting point and experimental contract

### What exists today

This roadmap is anchored to upstream commit [`78ef3e0`](https://github.com/nftechie/stonkfly/tree/78ef3e05ab0fa086032098558d893667068944a0), with the source inspected on **2026-09-17**. The numbers below describe this implementation, not universal properties of a fly brain. See [model details](docs/model.md), [validation history](docs/validation.md), and the MaleCNS release.[^malecns]

| Component | Existing behavior | What needs evidence or new work |
| --- | --- | --- |
| Retained graph | 166,700 neurons, 25,582,938 directed edges, 124,177,617 synaptic contacts | Connectivity does not supply calibrated cell dynamics or receptor physiology |
| Neurons | Approximate leaky integrate-and-fire dynamics, 0.1 ms integration, selected KC adaptation | Activity ranges, numerical sensitivity and input sensitivity |
| Sensory adapter | RGB chart input through 3,335 brightness and 811 R8 color inputs | Whether useful cue differences reach memory and output cells |
| Existing plasticity | A candidate eligibility/rate rule on 7,835 existing KC→MBON07/MBON11 edges | Whether changes create an association or improve an out-of-sample decision |
| Reinforcement | Equity changes trigger engineered PAM11 or PPL101 stimulation | Delayed credit, fees, passive exposure and endogenous dopamine confounds |
| Action readout | Fixed DNp20 right-minus-left firing difference, gated by DNpe017 | Directional bias and whether memory changes reach this readout |
| Execution | Guarded Coinbase spot orders or long-only paper fills | Comparable replay costs; a fee setting alone is not a MEXC futures simulator |
| Growth | Fixed topology; no neuron birth or structural growth rule | Any growth experiment requires an explicitly separate model |

The baseline is a wiring-constrained experiment. Other connectome models provide useful precedents for comparing neural predictions with measurements, but do not validate this model's trading behavior.[^shiu2024][^flyvis2024]

### Boundaries that every stage preserves

1. **Keep the complete retained graph.** An experiment can change a selected mechanism or reversibly silence a pathway for an ablation, but must retain node/edge identity and restore the baseline. Small synthetic circuits are explicitly unit/reference models; their results are not full-connectome results.
2. **Separate the causal chain.** Observation → sensory adapter → neural dynamics → plasticity → fixed decoder → execution guard → paper fill → next feedback. A guard may reject a proposal and log why. It must not invent a replacement action. Record neural proposals and executed orders separately.
3. **Admit engineered assumptions.** The input display, timing, reward mapping, activity targets and decoder are design choices. Biological inspiration does not remove those choices or make the agent unbiased. Freeze them for a comparison and disclose changes.
4. **Keep research paper-only.** No funded trades are required for any day in this plan. Use isolated output directories; never overwrite or resume an operational run under a changed model signature. Keep credentials, account identifiers and private run artifacts outside Git.
5. **Add one interpretable difference at a time.** Every new mechanism has an off switch, a saved-state definition, a reference test, a runtime measurement and a matched baseline. Publish failed runs and parameter searches alongside successes.
6. **Separate implementation from outcome.** A mechanism can be correctly implemented and fail to help. A positive toy conditioning result does not establish biological fidelity, and neither establishes useful market learning.

### Three clocks, not one ambiguous timestamp

The existing defaults advance 500 ms of neural time per market observation, while ordinary observations are at least 60 wall-clock seconds apart. Replay must therefore record **market timestamp**, **simulated neural time** and **compute duration** independently. Eligibility, recovery and forgetting equations use declared neural-time units. Fees, funding if ever modeled, quote age and execution scheduling use market-time semantics.

For example, ten default observations represent five neural seconds. If replay observations are one market minute apart, those same ten steps span ten market minutes. Neither equals the CPU time consumed. The 1,800-neural-second decay parameter must not be described as a 30-minute market memory. A one-day biological retention protocol may be computationally unaffordable; compressed or shortened tests must be labeled accordingly.[^handler2019][^huang2024]

### Comparisons and measurements to define before tuning

| Condition | Purpose | What stays matched |
| --- | --- | --- |
| Baseline learning | Measure the existing candidate rule | Input data, initial state, decoder, costs and execution rules |
| Long-term weights frozen | Isolate learned efficacy changes | Neural propagation and any separately declared short-term dynamics |
| All adaptive mechanisms disabled | Recover the original non-adapting comparison | Graph, observations and execution environment |
| No external reinforcement | Separate imposed P&L pulses from endogenous DAN activity | Network and sensory input; do not claim dopamine is absent |
| Permuted/replayed reinforcement | Break the intended cue–feedback relation | A declared donor pulse sequence and its marginal pulse counts |
| Learned-state reset and sham reset | Test whether retained state contributes | Evaluation cues, portfolio state and non-target state at intervention |
| Cash and buy-and-hold | Measure passive exposure and cost effects | Starting capital, instrument, time window and available fill assumptions |

An offline replay of a pulse sequence is a different experimental environment from closed-loop rewards generated by the model's own trades. Label both. Do not silently substitute one for the other or interpret their difference as a pure timing effect.

Report acquisition contrast, reversal latency, retention at each neural delay, reset effect, firing distributions, decoder margins, gate activity, efficacy saturation and failures. For market runs also report starting/ending equity, realized and unrealized P&L, spread/fees/slippage assumptions, turnover, exposure, fills, veto reasons and drawdown. Use a common terminal inventory-marking or liquidation convention across policies.

Treat independent initializations, stimulus assignments and market periods as different sources of variation. Merely setting ten seed labels on a deterministic calculation does not create ten independent experiments. A pilot target is 5 distinct assay replicates; a confirmatory target is at least 10 meaningful replicates where runtime allows. These are engineering budgets, not a power calculation. Choose final counts and smallest relevant effect after the pilot, before accessing the holdout. Report intervals and all samples; overlapping market windows and ticks from one run are not independent replicates.[^agarwal2021]

For market uncertainty, first compare paired outcomes over predeclared chronological periods. Any block-resampling analysis needs a stated block length and dependence/stationarity assumptions; it cannot make a nonstationary market or an adaptive trading policy magically exchangeable. Never independently shuffle price bars to create a purported market confidence interval.[^politis1994]

### Proposed implementation map

Existing files below are real; new paths are **proposals**, not available commands or implemented modules. Keep the current CLI working while introducing the research harness incrementally.

| Responsibility | Existing integration points | Proposed additions |
| --- | --- | --- |
| Replay and event clocks | `stonkfly/market.py`, `cli.py`, `risk.py`, `broker.py` | `stonkfly/experiments/replay.py`, `clock.py`, `runner.py` |
| Experiment contracts | `config.py`, `ledger.py`, `neural/brain.py` | `stonkfly/experiments/schema.py`, `configs/experiments/` |
| Conditioning and controls | `reinforcement.py`, `neural/controller.py` | `stonkfly/experiments/assays.py`, `controls.py` |
| Short-term plasticity | `neural/kernel.cpp`, `state.py`, `brain.py` | `neural/short_term.py` as a small reference implementation |
| Homeostasis | `neural/kernel.cpp`, `brain.py` | `neural/homeostasis.py` as reference equations/configuration |
| Compartments and memory | `neural/circuit.py`, `rule.py`, `brain.py` | Explicit compartment parameter records and checkpoint versioning |
| Reports and inspection | Local experiment output; no dashboard app is bundled upstream | `stonkfly/experiments/report.py`, exported HTML/SVG/CSV summaries |
| Regression coverage | `tests/test_neural.py`, `test_market.py`, `test_execution.py` | `tests/test_replay.py`, `test_assays.py`, `test_short_term.py`, `test_homeostasis.py` |

Plan storage before long runs: one extra float32 per directed edge is about 102 MB decimal before indexing, timestamps and checkpoint copies. Prefer state only for selected synapses, coarse aggregate telemetry and a few predeclared spike probes. Measure available RAM/disk and reserve enough for interrupted-write recovery. Full spike dumps and 40-day checkpoint accumulation are not default requirements.

<a id="week-1"></a>

## Week 1 · make experiments reproducible

**Dependency:** the existing project installs and the retained dataset is available. **Weekly exit:** the same declared observations reach each condition, and an interrupted run resumes without changing its scientific meaning.

### Day 01 — inventory the baseline and write the questions

- **Read and trace:** follow the current [model](docs/model.md), [validation](docs/validation.md), `circuit.py`, `rule.py`, `controller.py` and `reinforcement.py`. Read Shiu et al. as an example of testing a connectome-derived model against specific sensorimotor predictions, rather than treating the wiring diagram as validation.[^shiu2024]
- **Build:** record the upstream SHA, dataset/array hashes, cell counts, model parameters, compiler and dependency versions. Write three questions: does conditioning change a predefined neural response; does that change survive retention and reset controls; does any corresponding market effect beat matched non-learning/exposure baselines?
- **Check:** run the existing unit suite and the opt-in full-connectome test when resources permit. Record failures and skips separately; an old validation report is not a new test run. Preserve the baseline parameter set and inspect whether current files differ from it.
- **Deliver:** a machine-readable baseline manifest and an experiment question sheet with one primary endpoint per question. **Done when:** another developer can identify the exact graph and implementation, and can distinguish a mechanism test from a behavioral or financial claim. No new learning rule today.

### Day 02 — measure the actual compute and storage budget

- **Read/design:** inspect `neural/kernel.cpp`, state allocation and checkpoint fields. Use the full-model precedent only to motivate measurement; published performance on another connectome or machine is not a runtime estimate for this fork.[^shiu2024]
- **Build:** a benchmark that separates initial load, native build, neural integration, frame rendering, telemetry and checkpoint writing. Measure representative blank, chart and strongly activating inputs, because spike traffic can change runtime. Record median and slow-case duration, peak resident RAM and checkpoint size.
- **Check:** project the cost of `conditions × replicates × observations × measured seconds/observation`, plus I/O. Test one interrupted checkpoint write in an isolated output directory. Confirm enough disk remains for the old and new checkpoint together; do not delete operational evidence to make a benchmark fit.
- **Deliver:** a budget sheet, maximum concurrent workers, logging frequency and stop-on-low-space threshold. **Done when:** the month-one matrix fits the measured budget or has an explicit reduced exploratory scope. If CPU performance is insufficient, shorten declared assays or defer mechanisms; do not prune the retained graph and call it equivalent.

### Day 03 — implement an observation-driven replay clock

- **Read/design:** inspect `FixtureMarket.snapshot()` and both snapshot calls in `cli.py`. The fixture currently increments on every snapshot, including an execution refresh; that is unsuitable as the clock for matched policy comparisons. Experimental reproducibility requires recording what changed between conditions.[^agarwal2021]
- **Build:** a replay source with explicit observation advance, immutable timestamped quotes and read-only execution-quote lookup. Repeated quote access must not consume the next neural observation. Keep chart history limited to information available at the observation timestamp; implement a separate deterministic clock for guard age/cooldown checks.
- **Check:** run two scripted test policies that issue different numbers of quote requests and verify identical observation IDs, timestamps and frames. These scripts are harness tests, never presented as neural policies. Reject unordered/duplicate records, invalid bid/ask and undeclared gaps. Verify an execution lookup cannot expose a future quote to the neural input.
- **Deliver:** proposed `replay.py`/`clock.py` modules, a tiny synthetic fixture and tests for action-independent replay. **Done when:** HOLD and attempted-trade paths see the same observation sequence under the same replay configuration.

### Day 04 — make paper costs and accounting explicit

- **Read/design:** audit `PaperBroker`, `Quote`, the guard and the equity anchor. Read the exchange's official fee material, including the distinction between API and web/app schedules; an old hard-coded percentage is not a verified current rate.[^mexcfees]
- **Build:** a cost manifest containing venue, instrument type, maker/taker assumption, rate as a decimal fraction, effective/retrieval dates and source URL. Separate spread, commission and optional slippage. Buy at the declared ask-side execution price and sell at the bid-side price. Use `Decimal` and the same increments/minimums for all relevant comparators.
- **Check:** a hand-calculated round trip, no-trade case, changing spread, rejected fill and terminal open position. Confirm fees are booked exactly once, replay quote age uses replay time, and a veto changes neither balances nor observed neural output. If historical bid/ask data are missing, label any synthetic spread and test its sensitivity.
- **Deliver:** cost/accounting fixtures and a clear report label such as “Coinbase SOL spot replay with an explicitly specified fee scenario.” **Done when:** equity reconciles exactly to the ledger. MEXC funding, contract sizing, leverage and liquidation remain unimplemented unless separately specified; copying its commission does not add them.

### Day 05 — checkpoint every state needed for a fair comparison

- **Read/design:** inspect `MemoryBrain.checkpoint()`/`restore()` and run provenance. In particular, restore loads `weights_frozen`; an experimental condition must not silently inherit the opposite setting from a saved run. Control labels need to correspond to actual treatment state.[^agarwal2021]
- **Build:** versioned experiment metadata for replay position, all clocks, RNG state where used, pending feedback, sensory history, model/condition configuration and accounting. Define when a checkpoint can be cloned into another condition and require explicit intervention metadata for such clones.
- **Check:** compare an uninterrupted run with a stop-and-resume run on the same build. Compare logical array/event content, not only compressed archive bytes or wall-time fields. Deliberately try mismatched graph, timing and mechanism configurations; require rejection rather than partial restore. Test a missing/corrupt checkpoint without mutating the original.
- **Deliver:** a reproducible baseline run, a resume comparison and a manifest of every adaptive/dynamic state field. **Week-one gate:** identical observations, reconciled accounting and resume-equivalent state. If this fails, use the next workdays to repair it before collecting learning evidence.

<a id="week-2"></a>

## Week 2 · establish learning assays before adding complexity

**Dependency:** week-one gate. **Weekly exit:** a conditioning protocol can separate sensory response, learned state and output behavior, even if the result is that the current model fails to learn.

### Day 06 — define cues, responses and counterbalancing

- **Read/design:** study the temporal-pairing logic in Hige et al. and the use of reversed cue assignments in Aso and Rubin. Those experiments use fly olfaction; the proposed visual-chart assay is an adaptation, not a replication.[^hige2015][^aso2016]
- **Build:** a small suite of neutral RGB cues and a separate chart-like suite. Match simple brightness/contrast statistics where possible. Counterbalance which cue receives reinforcement, and choose the response measurement before looking at reward-dependent results. Measure both a compartment response and the existing fixed decoder, without fitting a new decoder to the desired answer.
- **Check:** establish untrained responses to each cue, KC recruitment, DAN background and DNp20/DNpe017 output. Distinguish “the circuit distinguishes the cues” from “the circuit acquired a preference.” A large innate cue difference needs a before/after contrast and assignment reversal, not a new story about learning.
- **Deliver:** cue-generation seeds, stimulus hashes, timing tables and a written assay endpoint. **Done when:** the cues are perceptibly different to the modeled circuit or a sensory bottleneck has been documented. Do not force reward into the decoder to bypass an unresponsive sensory pathway.

### Day 07 — run the first acquisition experiment

- **Read/design:** use cue–DAN pairing as a mechanistic starting point, following the experimental logic of Hige et al.; do not import their biological effect size or stimulus parameters without justification.[^hige2015]
- **Build:** separate baseline probes, training pairings and reward-free test probes. Begin with a declared pilot, for example 30 training pairings and 10 probes per cue, with counts revised only using development data. Clone evaluation checkpoints when probes themselves would modify memory. Record a trained-cue versus control-cue response contrast relative to the pre-training contrast.
- **Check:** compare learning, long-term-frozen, no external pulse and explicitly unpaired-pulse conditions. Measure stimulus delivery, DAN spikes, eligible KC activity, efficacy changes and downstream response. Keep missing output spikes and failed acquisitions in the results. Report all cue assignments rather than only the assignment with favorable direction.
- **Deliver:** an acquisition plot and a stage-by-stage causal trace. **Done when:** the assay reliably reports an effect or its absence and controls are executed correctly. A synaptic effect with no output change is reported as a synaptic effect, not successful behavioral learning.

### Day 08 — test reversal and extinction separately

- **Read/design:** Aso and Rubin distinguish updating memories from their original formation; Handler et al. motivate checking the order of cue and reinforcement.[^aso2016][^handler2019]
- **Build:** after acquisition, reverse the A/B reinforcement assignment without resetting the learned state. In a separate branch, present unreinforced cues to measure extinction. Add an unchanged-assignment branch matched for elapsed neural time and number of presentations. Predefine reversal latency, such as trials until a signed contrast crosses a chosen criterion for consecutive probes.
- **Check:** counterbalance the original assignment and presentation order. Score never-reversed runs as censored/failures, not as missing observations. Compare reversals with simple passive decay and with frozen weights. Track whether an apparent reversal merely reflects changed sensory order, output saturation or a decoder gate turning off.
- **Deliver:** acquisition→reversal trajectories and a distinct extinction analysis. **Done when:** the assay can tell new association learning, loss of an old response and nonspecific activity loss apart. If the baseline never acquires an association, report reversal as uninterpretable and investigate the earlier failure.

### Day 09 — retention, selective resets and sham interventions

- **Read/design:** use the memory-timescale question in Huang et al. as motivation while retaining explicit units and the model's actual compartment identities.[^huang2024]
- **Build:** clone the same post-training checkpoint into several delay conditions. A feasible pilot might use 0, 1, 5 and 20 neural seconds under identical neutral input; these are proposed simulation delays, not biological hour/day equivalents. Probe each clone independently so an earlier probe cannot train the later one.
- **Check:** compare untouched, sham-restored, efficacy-reset and fully reset branches. A weights-only reset leaves other traces behind; state exactly which eligibility, short-term, adaptation, homeostatic or slow-memory states are retained. Keep portfolio state unchanged when isolating neural memory in a market assay. Full reinitialization is a separate, broader intervention.
- **Deliver:** retention curves, intervention manifests and a table of surviving state. **Done when:** loss of a response after an intervention can be attributed to the declared state change rather than unequal input, elapsed time or a broken restore. A null reset effect is a result worth retaining.

### Day 10 — measure reward timing and isolate exposure credit

- **Read/design:** study Handler et al. for order-sensitive fly plasticity and Izhikevich for an eligibility-based delayed-reward model. Neither supplies a validated financial reward mapping for Stonkfly.[^handler2019][^izhikevich2007]
- **Build:** a small signed delay sweep, for example reinforcement offsets of −1, −0.5, 0, +0.5 and +1 neural second relative to a defined cue event. Keep total trial duration and pulse counts equal. In market traces, decompose feedback into inventory price movement, fill costs and any explicitly defined comparison reward.
- **Check:** log scheduled and actual delivery times. Distinguish imposed pulses from endogenous DAN spiking. Document that P&L on an existing holding does not identify the most recent action as its cause. Any exposure-adjusted or counterfactual reward is a named alternative hypothesis, never silently substituted for the baseline or allowed to select an order.
- **Deliver:** timing-response curves and the minimal conditioning benchmark report. **Week-two gate:** interpretable acquisition/retention/timing measurements with working controls, or a reproducible negative diagnosis. New mechanisms may investigate that diagnosis, but cannot be reported as improvements until the assay is trustworthy.

<a id="week-3"></a>

## Week 3 · add short-term synaptic plasticity

**Dependency:** a trustworthy assay and baseline, not necessarily positive learning. **Weekly exit:** a selected-synapse mechanism that matches a reference implementation and can be switched off without changing the baseline.

### Day 11 — specify depletion, recovery and facilitation

- **Read/design:** read Tsodyks and Markram on depression and Markram, Wang and Tsodyks on target-dependent depression/facilitation. These are neocortical studies; using their phenomenological mechanism here is a cross-system modeling hypothesis, not measured fly parameterization.[^tsodyks1997][^markram1998]
- **Build:** write a model contract for a bounded available-resource variable `x`, a utilization variable `u`, recovery/facilitation times, event ordering and the multiplier applied to baseline transmission. Specify whether the first rested pulse preserves baseline strength or includes a utilization factor; do not let an unnoticed gain change masquerade as short-term plasticity.
- **Check:** select an anatomical subset before testing returns; the already identified KC→MBON edges are a manageable candidate, not evidence that the chosen dynamics are correct there. Estimate state bytes, index lookup overhead and interaction with the existing learned efficacy. Preserve sign, fixed endpoints and long-term state independently.
- **Deliver:** equations, units, an initial parameter range and a state diagram. **Done when:** depression-only, facilitation-only, combined and disabled modes have unambiguous semantics, and each parameter is labeled measured, borrowed or engineering-chosen.

### Day 12 — implement the small reference model first

- **Read/design:** work through the dynamic-synapse models sufficiently to choose an explicit discrete-event convention; different conventions for updating `u` before release can produce different first-pulse amplitudes.[^tsodyks1997][^markram1998]
- **Build:** a simple scalar/vector reference outside the large kernel. For the chosen approximation, specify decay/recovery between events and resource consumption at each spike; document numerical limits and normalization. Generate isolated spikes, paired pulses, a short burst, a long recovery gap and repeated bursts.
- **Check:** resources/utilization remain within their declared bounds; recovery approaches the defined resting state; no spikes do not consume resources; disabled mode is exactly the old transmission. Compare against hand-computed event sequences and a sufficiently fine numerical reference, rather than testing one copy of the implementation against another identical formula.
- **Deliver:** response curves, equation-to-code notes and meaningful limiting-case tests. **Done when:** the expected depressing/facilitating regimes appear for the proposed parameters and the reference can serve as an independent oracle. If behavior depends on an arbitrary update ordering, fix or disclose it before integration.

### Day 13 — integrate with the native event path

- **Read/design:** inspect delivery queues, source event times, postsynaptic accumulation and the event-driven subthreshold optimization. The dynamic-synapse literature motivates stateful transmission; it does not guarantee a correct integration into this kernel.[^markram1998]
- **Build:** add state only for selected edges, and update it at a declared presynaptic release/delivery event. Handle the existing transmission delay consistently. Preserve the immutable baseline weight and apply the effective short-term factor without repeatedly multiplying the long-term weight in place.
- **Check:** a minimal two-cell or small synthetic reference circuit matches Python for a deterministic spike train. Exercise simultaneous arrivals, long inactivity, queue wraparound, zero selected edges and numerical limits. Run a full retained-graph disabled-mode comparison to verify node/edge hashes and original spike/output behavior on the same build.
- **Deliver:** native integration, selection metadata and a measured overhead comparison. **Done when:** the feature affects only selected transmissions and its disabled path recovers baseline behavior. If an optimization changes event order or precision, quantify the difference before using that build for a scientific comparison.

### Day 14 — save the new state and define what “frozen” means

- **Read/design:** distinguish transient transmission dynamics from learned long-term efficacies. A frozen long-term-weight condition can legitimately retain short-term dynamics, but it must be named accordingly.[^tsodyks1997]
- **Build:** checkpoint resource/utilization values, last-event timing and mechanism configuration. Add explicit condition flags for long-term learning, short-term dynamics and any parameter adaptation. Record a state-format version and reject incompatible restores rather than silently initializing missing resources.
- **Check:** interrupt a burst, save/restore, and compare the remaining response to an uninterrupted burst. Run a silence/recovery interval across a checkpoint. Test frozen-long-term/STP-on, frozen-all and STP-off conditions. Confirm the selected-edge mask and original connectome hashes survive each round trip.
- **Deliver:** a condition truth table and resume tests covering active and quiescent states. **Done when:** every comparison states exactly what can still change, and a checkpoint reload cannot accidentally make a condition “learn” or reset its short-term memory.

### Day 15 — test behavior and decide whether to retain the mechanism

- **Read/design:** use the uncertainty-aware comparison principles of Agarwal et al.; a plausible response curve is not evidence of a task benefit.[^agarwal2021]
- **Build:** run the same acquisition, reversal and short retention development assays with STP off/on and the same long-term rule. Include a constant-gain control matched to a declared transmission statistic to check whether a result merely comes from changing mean synaptic strength. Keep the decoder and reward mapping fixed.
- **Check:** measure cue responses, output contrast, weight saturation, reversal latency, compute cost and replicate variability. Compare depression-only and facilitation-only only if the pilot budget allows; log these as additional comparisons. Inspect cases where STP removes activity or amplifies a pre-existing directional bias.
- **Deliver:** a mechanism report with beneficial, neutral and harmful effects separated by assay. **Week-three gate:** reference agreement, restart equivalence, bounded state and no unexplained baseline drift. A correctly implemented but unhelpful mechanism can remain experimental/off by default; do not select it solely because one market window rose.

<a id="week-4"></a>

## Week 4 · finish the four-week experiment

**Dependency:** stable replay, usable assays and a tested STP implementation or a documented decision to defer it. **Weekly exit:** the first defensible report. This week is deliberately reserved for evaluation and repair rather than adding another mechanism.

### Day 16 — preregister the month-one comparison

- **Read/design:** use Agarwal et al. for uncertainty-aware evaluation and Politis/Romano for the limits of resampling dependent data.[^agarwal2021][^politis1994]
- **Build:** record a protocol commit with hypotheses, primary endpoints, smallest useful effect, parameter bounds, seed/cue assignments, data hashes, chronological train/development/test boundaries and a complete condition list. Reserve separate month-one and month-two test periods now. Keep one instrument fixed for the main market question; SOL is a project choice, not a claim that it is the optimal or most volatile coin.
- **Check:** choose observation count and replicate count from Day 02 runtime plus pilot variability. Separate mechanism-level conditioning from market-level performance. Define whether long-term learning continues during test-time market replay: frozen-after-training and online adaptation are different, separately named evaluation protocols.
- **Deliver:** an immutable experiment specification and a costed run manifest. **Done when:** all planned runs, exclusions, stopping rules and analysis choices can be enumerated before the final test is opened. Pilot data and tuned development results remain explicitly exploratory.

### Day 17 — run paired development comparisons

- **Read/design:** pair conditions by common input, initialization and cue assignment to reduce avoidable variance, without claiming that pairs from one market period are independent markets.[^agarwal2021]
- **Build:** execute the registered matrix on development data first. At minimum compare original learning, frozen weights, STP plus learning and STP with long-term weights frozen; run the declared reward controls and passive baselines where meaningful. Use condition-specific directories and immutable manifests.
- **Check:** monitor progress using completed/failed run counts, elapsed compute and disk usage. Stop only for predefined integrity/resource failures, not disappointing scores. Verify realized mechanism flags, data IDs and initial states rather than trusting directory names. Re-run an interrupted subset through the recovery path.
- **Deliver:** a complete development run table, including failures and reasons. **Done when:** every planned condition is either present or explicitly unresolved, and no result has been chosen by visually scanning equity curves. A smaller completed matrix is preferable to a larger collection of selectively missing outcomes.

### Day 18 — inspect confounds and freeze the corrected protocol

- **Read/design:** revisit the model's own [known limitations](docs/model.md) and the measured-neural-response emphasis in FlyVis.[^flyvis2024]
- **Build:** diagnostic plots for left/right output rates, gate spikes, sensory brightness, active KCs, reward counts, saturation, inventory exposure and veto frequency. Trace suspicious performance back through observation, proposal, fill and feedback. A buy-biased decoder in a rising market is an exposure explanation to test.
- **Check:** verify chart history is causal, terminal valuation is identical, fee records agree with the cost manifest and execution lookups cannot advance observation time. Evaluate reward shuffling under its declared open-loop semantics. Make any fixes on development data only, invalidate affected runs and record the reason.
- **Deliver:** a confound audit and the final locked month-one protocol. **Done when:** either the remaining comparison is interpretable or the report explicitly says why it is not. If a material change is made, rerun the affected development controls before proceeding; the holdout stays closed.

### Day 19 — evaluate the untouched period once

- **Read/design:** distinguish a held-out evaluation from repeated selection on a nominal test set; interval estimates must reflect meaningful replication rather than repeated copies of the same deterministic run.[^agarwal2021]
- **Build:** execute the frozen protocol on the reserved chronological market period and reserved conditioning assignments. Keep input warm-up strictly in the past and state transfer exactly as preregistered. Run cash/buy-and-hold with the same valuation convention and report both actual exposure and the limitations of comparators with different order schedules.
- **Check:** aggregate paired differences and display individual outcomes, sample counts, failures, exposure, costs and uncertainty. Avoid annualizing a tiny market sample or reporting a universal probability of future profit. Treat any post-test hypothesis as a new development idea needing another untouched evaluation.
- **Deliver:** unedited test results tied to the protocol commit and data manifest. **Done when:** the declared test matrix completes or transparently records its missing coverage. A disappointing or inconclusive test does not trigger a quiet parameter retune and a replacement “first” test.

### Day 20 — publish the first-month report and make a scope decision

- **Read/design:** compare each proposed claim with the evidence level defined at the top of this README and the evaluation cautions in the research references.[^agarwal2021]
- **Build:** a report containing questions, exact implementation, parameter sources, run matrix, condition counts, results, uncertainty, runtime, failures and limitations. Include a small reproduction fixture and commands that actually exist by this date. Publish derived summaries only when they contain no credentials/private account data and underlying data terms permit it.
- **Check:** reproduce at least one acquisition comparison and one paper replay from a fresh output directory. Check that captions distinguish synthetic cues, historical replay and any separately collected live paper trace. Update checklist items only when their acceptance criteria passed; an implemented mechanism and a helpful mechanism get separate statuses.
- **Deliver:** a tagged four-week milestone, with a decision to stop, repair the assay, continue STP investigation or begin homeostasis. **Month-one gate:** a reproducible result, including a valid negative result. If integrity or runtime remains unresolved, spend month two on that bottleneck instead of promising two more mechanisms.

<a id="week-5"></a>

## Week 5 · test slow homeostatic regulation

**Dependency:** the month-one report and enough measured budget for another mechanism. **Weekly exit:** a bounded, independently controlled activity regulator whose effects on existing memory are measured.

### Day 21 — choose one homeostatic hypothesis

- **Read/design:** Turrigiano et al. demonstrate activity-dependent synaptic scaling in cultured neocortical neurons. Use it as motivation for a limited regulation model; it does not establish appropriate target rates or timescales for MaleCNS cells.[^turrigiano1998]
- **Build:** choose one initial mechanism: for example, a slow postsynaptic multiplier on selected excitatory inputs. Write the activity estimator, update interval, rate target/band, lower/upper multiplier bounds and an explicit off switch. Keep distinct cell classes distinct; do not force all 166,700 neurons to one mean rate.
- **Check:** choose target ranges using declared baseline/assay measurements, with sensitivity bounds, never by maximizing returns. Define behavior for silent populations, sustained bursts and absent input. Ensure the regulator consumes neural activity only, not the desired trading action, P&L or future data. Explain the engineered target rather than claiming “no bias.”
- **Deliver:** a homeostasis model card and state/units specification. **Done when:** the hypothesis is narrow enough to test in four remaining workdays and has a matched fixed-gain control. Threshold adaptation and inhibitory plasticity are alternative projects, not extra features silently added to this week.

### Day 22 — test the regulator against known perturbations

- **Read/design:** distinguish the empirical scaling observation from the numerical controller chosen for this fork.[^turrigiano1998]
- **Build:** a reference implementation using a smoothed rate and a bounded slow update. A candidate engineering form is a multiplicative gain update driven by target-minus-observed rate, with every factor's units declared. Couple it to a minimal neuron/synapse reference and test a step up/down in input plus a return to baseline.
- **Check:** test the direction of correction, overshoot, slow recovery, clipping and the zero-error limit. Preserve relative input strengths within the chosen scaled group until other plasticity changes them. Establish a gain/rate range that does not oscillate under the reference conditions; this is controller calibration, not proof of stability in the full network.
- **Deliver:** perturbation response plots, numerical/reference tests and a bounded parameter sweep. **Done when:** the update is understandable and numerically stable in the declared range. If a target cannot be reached under a given input, report persistent error/clipping rather than increasing gain without limit.

### Day 23 — integrate slow updates and checkpoint their state

- **Read/design:** inspect how the existing event-driven kernel handles inactive neurons. Slow homeostatic updates must occur on a defined neural-time schedule even if a monitored population is quiet; wall-clock sleeps are not the integration clock.
- **Build:** add rate estimates, scaling state, update accumulators and configuration hashes to the checkpoint contract. Compose baseline magnitude, learned efficacy, short-term factor and homeostatic multiplier in a documented order. Do not overwrite the baseline array or scale an already scaled value repeatedly by accident.
- **Check:** compare the native implementation with the reference on the same activity sequence. Verify disabled-mode equivalence, sign preservation, state bounds, checkpoint continuation through a quiet interval and unchanged graph topology. Benchmark update cost at the actual monitored-population size.
- **Deliver:** an integrated mechanism and a clear flag matrix distinguishing frozen long-term learning from frozen homeostasis. **Done when:** a researcher can enable exactly the intended treatment without a hidden reset or altered baseline. This is implementation of the Day 21 hypothesis, not an additional empirical conclusion from the source paper.[^turrigiano1998]

### Day 24 — check that regulation does not erase the measured memory

- **Read/design:** combine the declared scaling hypothesis with the existing acquisition/retention assay; the interaction is this fork's experiment, not a result already supplied by either source.[^turrigiano1998][^huang2024]
- **Build:** compare homeostasis off/on after identical training, both with fixed long-term weights and with learning enabled. Include normal input, sustained high input and low-input periods. Keep a constant-gain comparator so a one-time increase in effective input is distinguishable from adaptive regulation.
- **Check:** measure rate recovery, cue-response contrast, retention, reversal latency, weight/gain saturation and decoder bias. If a memory disappears, distinguish normalization of an activity offset from loss of learned cue specificity. Check behavior over different declared homeostatic targets and timescales, recording the entire tested grid.
- **Deliver:** a stability–retention tradeoff report. **Done when:** the model's activity regulation and its effect on learned responses are quantified separately. Reducing firing variance alone is not evidence that learning improved, and a busier output neuron is not automatically a better decision-maker.

### Day 25 — review the mechanism and lock its status

- **Read/design:** review the original scope and the uncertainty in the small development comparison.[^agarwal2021]
- **Build:** run a paired development replication of the chosen homeostasis variant, with the original model and STP settings held fixed. Summarize when the multiplier is active, at a bound or ineffective. Record runtime and checkpoint overhead relative to the month-one build.
- **Check:** repeat a known perturbation, a normal-input assay and a restart. Decide whether the default remains off, the mechanism is retained for the final ablation, or implementation needs repair. An exploratory favorable result is not grounds to change the final holdout or claim that stability has been proven globally.
- **Deliver:** a reviewed homeostasis configuration, rejected alternatives and a short mechanism report. **Week-five gate:** stable bounded operation in tested cases, reliable restart and interpretable effects. If unmet, reserve next week for repair or keep homeostasis out of the final combined model; do not stack a second unverified adaptation on top.

<a id="week-6"></a>

## Week 6 · model limited differences between memory compartments

**Dependency:** the assay remains interpretable after earlier changes. **Weekly exit:** one scoped compartment extension with declared anatomical support, distinct timing parameters and a testable feedback hypothesis.

### Day 26 — map the proposed compartments before assigning functions

- **Read/design:** Huang et al. study interactions involving γ1, α2 and α3 memory modules; the current code selects α1/PAM11/MBON07 and γ1pedc/PPL101/MBON11. These are not interchangeable labels. Ichinose et al. provide a different α1 recurrent-reward precedent.[^huang2024][^ichinose2015]
- **Build:** a table mapping paper terminology to available MaleCNS type annotations, exact IDs, existing KC inputs and candidate feedback paths. Select at most one additional supported compartment, or stay with the current pair and explicitly name a simpler timescale hypothesis. Do not infer homologous identities from similar strings alone.
- **Check:** inspect connection direction, transmitter annotations, unresolved signs and the original source's species/sex/preparation limits. Adding a plasticity rule to an existing edge does not prove its biological plasticity. Missing anatomical or physiological evidence belongs in an uncertainty column, not in an invented connection.
- **Deliver:** a compartment-selection manifest and a written transfer argument. **Done when:** every selected unit has traceable anatomical identity, the full graph is preserved and the scope can fit the remaining week. A full reproduction of Huang et al. is not the promised deliverable.

### Day 27 — implement a reference with distinct timescales

- **Read/design:** use the compartment-specific learning differences in Aso/Rubin and the interacting-memory question in Huang et al. to motivate the hypotheses.[^aso2016][^huang2024]
- **Build:** parameterize learning strength, eligibility, decay and any slow state per selected compartment. First reproduce the old equal-parameter setting exactly. Then introduce one named fast/slow contrast in a small reference model, documenting whether a new state represents filtered efficacy, a persistent trace or a hypothetical consolidation process.
- **Check:** zero learning, equal-timescale, infinite/very-long retention approximation and zero-coupling limits. Guard against double-applying passive decay in both Python and native code. The existing two-state `u`/`w` rule already includes memory decay and filtering; merely renaming these variables “short-term” and “long-term” is not a new memory mechanism.
- **Deliver:** equations, source-versus-assumption annotations and reference trajectories. **Done when:** each additional state has a necessary, distinguishable role and the baseline remains recoverable. Do not add molecular receptor claims to a phenomenological rate rule.

### Day 28 — test acquisition and retention on feasible neural times

- **Read/design:** translate the memory-timescale question into tests affordable under the measured simulator speed; preserve the distinction between modeled delay and biological retention duration.[^huang2024]
- **Build:** paired fast/slow-compartment conditioning with several predeclared delays and the same training exposure. Use independent post-training clones for each probe. Include equal-timescale and slow-state-disabled controls so longer retention cannot be explained only by an extra gain or more training.
- **Check:** quantify initial response, retention loss, interference and subsequent reversal. A longer-lasting trace can also obstruct learning a changed association; report that tradeoff. If scaling every time constant would be needed to run the test, treat the scaled system as a different model and document its dimensionless ratios and limits.
- **Deliver:** compartment response and retention curves with neural-time axes and compute costs. **Done when:** the selected extension exhibits or fails to exhibit the predicted separation under declared conditions. No statement about hours of fly memory follows merely from a fast computer run or compressed market timestamps.

### Day 29 — inspect and test one recurrent feedback pathway

- **Read/design:** Ichinose et al. motivate examining an α1 recurrent reward circuit. A circuit described in another preparation provides a hypothesis to map, not permission to invent an all-purpose “consolidation loop.”[^ichinose2015]
- **Build:** trace the supported pathway in the retained graph and identify what is already active in the existing simulator. Define one reversible functional intervention: for example, disabling a declared feedback contribution while preserving the underlying graph and all other inputs. Log the intervention mask and model signature.
- **Check:** compare acquisition and post-training evolution with feedback intact versus the declared intervention, using the same starting state. Match baseline activity where possible with a separate documented control. If anatomy exists but receptor/sign/effect assumptions are unresolved, report a hypothesis-level perturbation rather than claiming a biological knockout replication.
- **Deliver:** an annotated circuit diagram, intervention metadata and a small feedback comparison. **Done when:** the proposed loop has a measurable predicted consequence or a documented null effect. If no defensible pathway mapping exists, defer this experiment; adding decorative connections is not a substitute.

### Day 30 — integrate compartment state and run the week-six gate

- **Read/design:** revisit the distinction between the limited implementation and the broader biological models that motivated it.[^huang2024][^ichinose2015]
- **Build:** store per-compartment parameters, selected-edge masks, slow state and feedback-intervention flags in the versioned checkpoint. Add reports that identify each compartment by source IDs and annotation version, so a future dataset update cannot silently relabel results.
- **Check:** equal-parameter baseline equivalence, slow-state reset, feedback off/on, interrupt/resume during retention and composition with STP/homeostasis. Confirm a reused checkpoint cannot cross incompatible compartment assignments. Run a small full-graph assay with each new feature isolated before any combined comparison.
- **Deliver:** a stable experimental build and a report of supported versus unresolved claims. **Week-six gate:** correct reference behavior, complete saved state, preserved topology and interpretable assays. If this fails, use week seven for repair and remove the incomplete mechanism from confirmatory comparisons rather than hiding its instability in an average.

<a id="week-7"></a>

## Week 7 · expose the mechanism and freeze the final experiment

**Dependency:** only mechanisms that passed their engineering gates enter this week. **Weekly exit:** inspectable reports, a tractable ablation matrix and a final protocol frozen before the second holdout is opened.

### Day 31 — define compact, scientifically useful telemetry

- **Read/design:** use the question-to-measurement discipline in connectome modeling: plots should expose testable circuit behavior rather than decorate a trading trace.[^shiu2024][^flyvis2024]
- **Build:** an event schema containing observation ID, all three clocks, condition, cue/reward identity, selected population rates, decoder margin/gate, neural proposal, veto/fill result and paper accounting. Add compartment efficacy quantiles, bound-hit fractions, STP resource summaries and homeostatic gain statistics. Preserve a small, predefined set of raw probe traces for debugging.
- **Check:** distinguish external pulse commands from measured DAN activity, state a sampling rate for every summary and test aggregation against a small raw trace. Confirm no credentials, account identifiers or full production logs enter an export. Measure telemetry overhead and cap it independently of the number of graph edges.
- **Deliver:** a versioned schema plus one complete example from a synthetic research run. **Done when:** a reader can follow one observation through the model and execution boundary, and can tell missing measurements from zeros. A confidence-looking score must not be inferred from an uncalibrated firing difference.

### Day 32 — build the experiment inspection view

- **Read/design:** use the experiment contract and uncertainty reporting requirements rather than adding new scientific claims.[^agarwal2021]
- **Build:** a lightweight exported report or read-only viewer with linked panels for the observed frame, cue/feedback timing, firing, adaptive state, decoder output and equity/costs. Display condition names, exact time units, model SHA and incomplete-run status. Make comparison plots use consistent axes and show individual runs plus aggregate uncertainty where justified.
- **Check:** verify a displayed point against its raw event, a plot against its numerical summary and a restarted run against its continuation metadata. Do not bridge an unobserved time gap with a confident line. Label downsampling and provide an appropriate data export. Test empty data, partial runs and nonfinite values without hiding errors.
- **Deliver:** an inspectable specimen report and a reproducible export command. **Done when:** someone can explain which measured neural signal produced a proposal, which guard accepted/rejected it and which evidence supports a learning claim. Upstream currently has no bundled dashboard; integrating an external viewer is a separate implementation choice.

### Day 33 — run ablations that identify the useful component

- **Read/design:** use the mechanisms' source papers to state hypotheses and uncertainty-aware evaluation to avoid choosing a favorable combination after many unreported trials.[^tsodyks1997][^turrigiano1998][^huang2024][^agarwal2021]
- **Build:** if budget permits, enumerate the eight on/off combinations of STP, homeostasis and the compartment extension, with the original baseline included. Keep training schedule, reward mapping, decoder and costs fixed. Add a long-term-frozen comparison for the candidate combined model; explicitly state whether transient dynamics still operate.
- **Check:** estimate the full matrix cost before launch. If eight combinations are unaffordable, preregister a reduced baseline-plus-single-additions-plus-combination design and state that interaction effects cannot all be identified. Pair conditions on inputs and initial state. A changed clock or reward mapping needs its own contrast, not an unnoticed difference attached to one mechanism.
- **Deliver:** a complete development ablation matrix with effect sizes, uncertainty and cost. **Done when:** the proposed final configuration has an interpretable rationale, or the report says no reliable advantage was found. Do not combine features merely because each has an individually attractive plot.

### Day 34 — test interference, noise and changed conditions

- **Read/design:** Aso/Rubin motivate testing memory updating; FlyVis motivates examining stimulus-dependent responses. The proposed market stress tests remain engineering tests, not reproductions of either study.[^aso2016][^flyvis2024]
- **Build:** predeclare a small development suite: reversed cue assignments, distracting visual input, modest brightness/contrast perturbations, a changed reinforcement delay and a chronological shift in market behavior. Keep these challenges separate enough to explain which change causes degradation. Include unchanged-condition reruns as controls.
- **Check:** measure retained old associations, acquisition of new ones, forgetting, output bias and saturation. Verify that a renderer change does not encode hidden future information. If the model only works at one exact display theme or one delay, state that dependence instead of tuning every stress case separately.
- **Deliver:** a robustness table with failure examples and model-selection decisions restricted to development data. **Done when:** the limits of the candidate configuration are characterized well enough to write a falsifiable final claim. Do not promote a failed robustness case into the test set after it has already guided tuning.

### Day 35 — lock the final claim, configuration and analysis

- **Read/design:** revisit uncertainty, dependence and the distinction between exploratory comparisons and confirmatory reporting.[^agarwal2021][^politis1994]
- **Build:** commit the final model flags/parameters, test-period hashes reserved on Day 16, independent-replicate definition, seed/assignment list, primary contrasts, effect thresholds, exclusions, uncertainty method and report script version. Predeclare any limited cost/seed robustness analyses for next week. List exploratory metrics separately.
- **Check:** verify final test data have not influenced model selection. Audit all tested development configurations and record the search count. Confirm budget and disk headroom for the actual matrix, including passive controls, restarts and failed-run reruns governed by integrity rules. Ensure a test-time learning policy cannot read future prices or future reward labels.
- **Deliver:** a frozen final experiment manifest and a launch checklist based on demonstrated operation. **Week-seven gate:** the full evaluation can be launched with no new design choices made from its outcomes. If not, finish the protocol and accept a shorter or later report rather than label development data “unseen.”

<a id="week-8"></a>

## Week 8 · evaluate, reproduce and publish

**Dependency:** the final protocol is frozen. **Weekly exit:** a release whose claims can be checked from its protocol, artifacts and uncertainty, with unfinished items still visibly unfinished.

### Day 36 — launch the final held-out matrix

- **Read/design:** use the locked protocol and the evaluation principles already selected; today is execution, not an opportunity to invent a better-looking metric.[^agarwal2021]
- **Build/run:** execute final conditioning assignments and the second chronological market holdout. Record exact code/data/checkpoint hashes and progress per condition. Use a common execution/valuation environment and the registered online-adaptation or frozen-evaluation semantics. Keep original baseline and passive comparators in the same report.
- **Check:** verify observation equality, initial-state policy and actual adaptive flags on sampled runs. Monitor only integrity, resource limits and completion during collection; do not stop a sound run because its curve looks bad. Preserve failure reasons, incomplete intervals and the number of outcomes included in each analysis.
- **Deliver:** the raw research-run matrix and an integrity summary. **Done when:** all required conditions complete or their absence is explicitly reported. If a real bug requires a model change, invalidate affected results and version the protocol; do not silently patch and pool incompatible runs.

### Day 37 — compute the registered robustness and uncertainty analyses

- **Read/design:** keep uncertainty tied to actual independent variation; time-series block methods require dependence assumptions and do not generate new independent market histories.[^agarwal2021][^politis1994]
- **Build:** run only the seed/cost/initial-state checks registered on Day 35 as confirmatory robustness tests. Plot paired mechanism effects, individual runs, interval estimates and aggregate counts. Show drawdown, turnover, fees, exposure and terminal inventory alongside equity so an apparent advantage has an interpretable source.
- **Check:** distinguish changing random cue assignment from perturbing neural initial state and from testing a different market period. If the network is deterministic, identical reruns demonstrate reproducibility, not a narrow biological confidence interval. Label any additional analysis inspired by the test result as post hoc.
- **Deliver:** a results table with explicit denominators, missingness and sensitivity limitations. **Done when:** every interval's sampling unit is stated and the main conclusion follows the registered contrast. An interval compatible with both harm and benefit warrants “inconclusive,” not “promising profit” as a substitute.

### Day 38 — audit causality, state recovery and deferred growth work

- **Read/design:** return to the distinction between a measured memory effect, a learned action and a financial outcome. If growth remains interesting, review the separate [replacement track](#growth-experiment); its sources do not justify relabeling weight updates as neuron birth.[^draelos2016][^fernandez2013]
- **Build/check:** reproduce the strongest registered learned-state reset/sham comparison and one informative failure. Verify the plotting pipeline against raw data and exercise checkpoint recovery in the final build. Confirm the retained graph hash is unchanged in the core experiments. Do not add a new mechanism to the already tested model today.
- **Scope decision:** if the optional growth track was not substituted earlier, deliver its design and deferred status, not a rushed biological claim. If it was completed, include its independent synthetic results and resource-matched controls, with no mixing into the full-connectome headline.
- **Deliver:** a causal-claims audit: what intervention changed what measurement, with unresolved alternatives listed. **Done when:** each conclusion can be traced to a completed comparison and every unimplemented idea remains labeled as such.

### Day 39 — reproduce from a clean checkout

- **Read/design:** use reproducibility as an operational requirement: a README command must recover the declared experiment rather than depend on an undocumented local cache.[^agarwal2021]
- **Build/run:** in a separate checkout/output directory, install the documented pinned environment, verify dataset hashes and run the small offline assay and a representative full-graph comparison. Rebuild the native component from source. Reproduce one result figure from saved summaries and record wall time and peak resource use.
- **Check:** repeat interrupt/resume, verify native/Python parameter agreement and confirm all planned commands exist. Different compilers/architectures may require a declared numerical tolerance rather than a bitwise-identical claim; measure any divergence and its effect on the conclusion. Inspect exactly which files will be published, preserving upstream licenses and dataset attribution.
- **Deliver:** tested reproduction instructions, environment metadata and known portability limits. **Done when:** the supported setup reproduces the result without private data or an undocumented service. If another machine was not tested, say so; a fresh directory on one host is not cross-platform validation.

### Day 40 — release the research record and decide what follows

- **Read/design:** compare the final evidence with the initial hypotheses and the transfer limits of each cited biological mechanism.[^hige2015][^huang2024][^turrigiano1998]
- **Build:** publish a report with the source baseline, implemented mechanisms, equations/units, parameter provenance, data split, complete run counts, search history, controls, effect sizes, uncertainty, failures, runtime and reproduction commands. Include a compact visual trace of one representative experiment and one failure, selected by a declared rule rather than aesthetic appeal.
- **Check:** separate four possible statements: mechanism implemented; synthetic association demonstrated; repeatable held-out behavioral effect demonstrated; net paper-market improvement demonstrated. Claim only the levels actually supported. Biological equivalence, consciousness and reliable future profits do not follow from any of these alone.
- **Deliver:** a tagged eight-week milestone, updated completion checklist and a ranked next-work list justified by remaining bottlenecks. **Final gate:** a stranger can distinguish fact, model assumption and future work. Negative or inconclusive results with working controls count as a completed research project; unfinished software or missing comparisons remain open.

<a id="growth-experiment"></a>

## Optional replacement track · structural plasticity or neuron growth

**Budget: five workdays replacing Days 26–30, not five extra days secretly added to the eight-week schedule.** Choose this track instead of the compartment extension if growth is the higher research priority. It is a small synthetic proof of concept. Do not attempt both rewiring and neuron birth within the five-day budget. If the reference framework is not ready, deliver the specification and explicitly defer implementation.

**Structural plasticity** changes which neurons connect. **Neurogenesis** adds neurons. **Synaptic plasticity** changes the efficacy of an existing connection. They are different interventions. The main Stonkfly graph remains intact; a growing synthetic circuit must never be described as an unchanged MaleCNS reconstruction.

There are relevant but limited precedents: Butz/van Ooyen model activity-dependent structural reorganization; Draelos et al. explore adding units in artificial networks; Fernández-Hernández et al. report adult fly neurogenesis in the optic-lobe medulla cortex, including a response to injury. None establishes that adding arbitrary cells to mushroom-body circuitry will improve this project's learning.[^butz2013][^draelos2016][^fernandez2013]

### G1 / replacement Day 26 — define one falsifiable growth question

- **Read:** compare the biological location and experimental conditions in the fly study with the task and architecture in the artificial-network work. Decide whether the project question concerns recovery after lost input, adaptation to a new cue set or reduced forgetting; these are separate endpoints.[^fernandez2013][^draelos2016]
- **Build:** specify a small synthetic network, for example 64 starting units with a hard cap of 80, and a sequence of two cue tasks. The sizes are engineering budgets, not biological counts. Select either new-edge formation/removal or neuron addition, define when growth is allowed and fix the maximum resource increase.
- **Check/deliver:** an experiment manifest with one primary endpoint, growth trigger, stopping rule and controls. No market-return-based growth trigger or hidden action chooser. **Done when:** success and failure are defined without requiring the network to improve, and every artificial cell ID is distinguishable from a dataset neuron.

### G2 / replacement Day 27 — implement a fixed-size synthetic baseline

- **Read/design:** use the structural/growing-network papers to motivate the test, while keeping their specific architectures separate from this new reference.[^butz2013][^draelos2016]
- **Build:** reuse the small reference integration/assay infrastructure to train task A, introduce task B and retest A. Record acquisition, interference, retention, activity, number of edges/units and elapsed computation. Keep weights, topology and unit identity serializable from the beginning.
- **Check/deliver:** deterministic reset/resume tests, a fixed-size baseline and an ordinary learning-only comparator. Counterbalance task order. **Done when:** forgetting or adaptation can be measured without any growth; a growth mechanism cannot be interpreted if the baseline task is already broken or has no learnable signal.

### G3 / replacement Day 28 — implement the single chosen intervention

- **Structural route:** define candidate connections, activity-based formation/removal criteria, degree/edge caps, sign constraints and update cadence. Log each topology event and its trigger. This is inspired by structural models, not a claimed reproduction of cortical lesion recovery.[^butz2013]
- **Neuron-addition route:** allocate new units with unique IDs, declared initial state, bounded connectivity and a specified maturation/learning schedule. Define how new state enters checkpoints and how removal is handled, or explicitly disallow removal. Unit growth inspired by artificial networks is not evidence of biological neuron differentiation.[^draelos2016]
- **Check/deliver:** save/restore across an actual structural event, enforce resource bounds and test invalid/dangling indices. Keep the original connectome files and hashes untouched. **Done when:** the intervention is reversible at the experiment level and its entire structural history can be reconstructed.

### G4 / replacement Day 29 — control for simply having more capacity

- **Build:** compare no growth, the chosen adaptive intervention, and a resource-matched control. For neuron addition, include a network initialized with the final unit count; for rewiring, include matched random rewiring with the same event/edge budget. If affordable, add a randomly timed growth schedule with the same final capacity.
- **Check:** match training exposure, input sequence and decoder/readout policy. Report parameter count, active edges, computation and memory as well as task scores. The adaptive model's extra capacity cannot be counted as a free biological advantage. If a resource-matched control performs similarly, that limits the growth-specific conclusion.
- **Deliver:** a small paired comparison with complete replicate counts and failure cases. **Done when:** any apparent benefit can be separated, at least at pilot scale, from more units, more training or more computation. Treat small-sample uncertainty explicitly.[^agarwal2021]

### G5 / replacement Day 30 — report the result and isolate the prototype

- **Build:** reproduce the baseline and growth comparison from the same saved task sequence. Export topology-event history, retention/reversal measures and a concise methods report. Keep this experiment in a clearly separate synthetic module/configuration rather than modifying the retained-connectome importer.
- **Check:** verify unchanged MaleCNS hashes, checkpoint recovery and maximum resource use. State whether the implementation added neurons, changed connections or only changed weights. Compare the actual result with the question chosen on G1, including no benefit or worse forgetting.
- **Deliver:** a labeled synthetic growth experiment or an explicit incomplete status. **Done when:** readers cannot confuse an artificial capacity-expansion result with adult fly brain reconstruction. Days 31–40 then evaluate/report this track separately in place of the compartment extension; they do not turn it into a production trading mechanism.[^draelos2016][^fernandez2013]

## How to keep the schedule honest

| Problem discovered | Immediate response | Work to postpone first |
| --- | --- | --- |
| Replay/clock/accounting mismatch | Stop scientific comparisons and repair the harness | Every downstream mechanism comparison |
| Cues fail to recruit the relevant circuit | Diagnose sensory transfer and baseline activity with declared probes | Behavioral-learning and trading-learning claims |
| Weights change but the fixed decoder does not | Report mechanism-level evidence; inspect the intervening circuit | Claims of learned trading decisions |
| No measurable acquisition | Report the negative result; test one explicit hypothesis at a time | Retention or reversal interpreted as learned behavior |
| Kernel/reference disagreement | Reduce to a synthetic failing case and fix the implementation | Full-graph sweeps |
| Full matrix exceeds compute/disk budget | Reduce the preregistered matrix or call the study exploratory | Full factorial ablations and growth |
| Homeostasis erases associations | Quantify the tradeoff; keep the feature off by default | Combined-model conclusions |
| Compartment anatomy/feedback is ambiguous | Record unresolved mappings and use a narrower hypothesis | Added compartments and physiological replication claims |
| Holdout was used for tuning | Relabel it development and reserve a genuinely untouched test | Confirmatory claims until a new test is available |
| Market improvement vanishes after costs/exposure controls | Publish that result | Profitability claims |

Every weekly report should contain: the question, protocol version, changed files/mechanisms, exact data/initial-state identifiers, parameter provenance, completed and failed run counts, primary result with uncertainty, resource cost, remaining confounds and the next decision. Keep an append-only record of protocol changes. Commit code and shareable summaries; retain large datasets/checkpoints under their declared local storage policy.

For a **four-week project**, stop after Day 20 with the harness, conditioning evidence and one evaluated mechanism or a documented failure. For an **eight-week project**, select only extensions that clear the earlier gates. A well-supported negative result about credit assignment, visual input or decoder reachability is more useful than a large collection of unvalidated brain-inspired components.

![Stonkfly: a pixel fly beside a candlestick chart](assets/stonkfly.png)

<a id="current-model"></a>

## Current model

A fly-connectome simulation that can operate a crypto trading account. Actual neural output, actual Coinbase integration. Profitable learning has not been demonstrated.

**How it works:** Public Coinbase prices become an RGB chart. It stimulates 3,335 brightness inputs and 811 R8 color inputs in the retained **MaleCNS v1.0 graph: 166,700 neurons, 25.6 million connections**. A fixed neural readout proposes buy, sell or hold. A custom **Coinbase AgentKit ActionProvider** checks limits and places spot orders through Coinbase Advanced.

Positive portfolio P&L stimulates 15 identified PAM11 dopamine cells; negative P&L stimulates two PPL101 aversive dopamine cells. A candidate memory rule changes existing KC-to-MBON connections. These are engineered reinforcement signals, **not modeled pain receptors**. Synaptic changes do not establish that it learns to trade profitably. [Model and evidence](docs/model.md).

## Run it

Python 3.11, a C++17 compiler, macOS/Linux. Allow several GB for the dataset and dependencies; 16 GB RAM recommended.

```sh
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m stonkfly prepare
python -m stonkfly run
```

Default: **paper trades, real public BTC-USDC data, $100 simulated balance**. No key needed. Local logs, sensory images and resumable brain state go in `runs/paper/`. Ctrl-C stops it; the same command resumes.

For continuous paper operation without a daily order cap, use `python -m stonkfly run --daily-orders 0 --out runs/paper-continuous`. The fly still chooses when to trade, with 60-second pacing and cash/inventory checks. [Paper options and existing-run migration](docs/operations.md#paper-modes).

For a new single-product paper experiment, add `--hodl-feedback growing-gap` to give aversive feedback when the fee-aware buy-and-hold shortfall grows by at least $0.01. An unchanged deficit is not repeatedly penalized. This changes the learning objective; profitable learning remains unproven. [Exact formula, accounting and migration](docs/hodl-feedback.md).

For real orders, first create a dedicated Coinbase Advanced portfolio with **at most 100 USDC** and a portfolio-scoped **ECDSA API key with View + Trade, no Transfer**. Copy `.env.example` to `.env`, fill it in locally, then run these commands yourself:

```sh
python -m stonkfly run --live --preflight-only
python -m stonkfly run --live
```

Defaults: $10 maximum order including reserved fees, 24 attempts/day, no shorts or leverage. A $20 drawdown stops new orders; **it does not liquidate holdings or cap further losses**. [Operation and recovery](docs/operations.md).

```sh
python -m stonkfly status
python -m pytest -q
```

The repo does not come funded or connected to anyone’s account. Live execution needs your local credentials and explicit opt-in.

<a id="research-references"></a>

## Research references and what they support

Sources checked while preparing this roadmap on **2026-09-17**. Citations support the specific biological observation, modeling precedent or evaluation method identified in each note. The day allocations, software architecture, numerical pilot budgets, proposed controls and acceptance criteria are **this fork's research/engineering proposals**. No cited paper establishes that Stonkfly learns profitably, and no figure or full paper is reproduced here. Primary papers are linked directly or through their DOI; open manuscript links are supplied where useful.

[^malecns]: **MaleCNS collaboration.** [MaleCNS connectome downloads](https://male-cns.janelia.org/download/). **Type:** primary dataset release. **Use:** graph provenance, annotations and release/licensing information. **Limit:** the retained counts and simplified dynamics in this README are implementation choices documented in this repository; the dataset is not a validated trading brain. Preserve the release-specific citation and attribution when publishing results.

[^shiu2024]: **Shiu et al. (2024).** [A Drosophila computational brain model reveals sensorimotor processing](https://doi.org/10.1038/s41586-024-07763-9). *Nature*. **Type:** primary experimental/computational study. **Use:** a precedent for specific circuit predictions and validation of connectome-derived dynamics. **Limit:** different reconstruction/model/task; it does not validate MaleCNS parameter choices, this decoder or trading.

[^flyvis2024]: **Lappalainen et al. (2024).** [Connectome-constrained networks predict neural activity across the fly visual system](https://doi.org/10.1038/s41586-024-07939-3). *Nature*. **Type:** primary computational study with comparisons to experimental measurements. **Use:** sensory-response validation and the need to constrain unknown dynamics beyond connectivity. **Limit:** its visual task, optimized model and validation are distinct from this spiking trading experiment; no pretrained FlyVis component is promised here.

[^hige2015]: **Hige, Aso, Modi, Rubin and Turner (2015).** [Heterosynaptic Plasticity Underlies Aversive Olfactory Learning in Drosophila](https://doi.org/10.1016/j.neuron.2015.11.003). *Neuron*. [Author-hosted paper](https://www.janelia.org/sites/default/files/Labs/1-s2.0-S0896627315009824-main.pdf). **Type:** primary fly experiment. **Use:** cue-specific KC→MBON plasticity and temporal pairing as assay motivation. **Limit:** olfactory conditioning is not a chart-reading or market-credit-assignment experiment.

[^aso2016]: **Aso and Rubin (2016).** [Dopaminergic neurons write and update memories with cell-type-specific rules](https://elifesciences.org/articles/16135). *eLife*, 5:e16135. **Type:** primary fly experiment. **Use:** acquisition, updating, cue counterbalancing and differences across memory compartments. **Limit:** one generic dopamine rule should not be presented as an experimentally established rule for every compartment.

[^handler2019]: **Handler et al. (2019).** [Distinct Dopamine Receptor Pathways Underlie the Temporal Sensitivity of Associative Learning](https://doi.org/10.1016/j.cell.2019.05.040). *Cell*. [Open manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/). **Type:** primary fly experiment. **Use:** cue/reinforcement order and bidirectional plasticity motivate explicit timing assays. **Limit:** receptor-specific signaling is not reproduced merely by adding an eligibility time constant to this simulator.

[^huang2024]: **Huang, Luo et al. (2024).** [Dopamine-mediated interactions between short- and long-term memory dynamics](https://doi.org/10.1038/s41586-024-07819-w). *Nature*. [Open manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525173/). **Type:** primary fly experiment and constrained computational model. **Use:** compartment interactions, feedback and different memory timescales; also the source adapted by the existing candidate rule. **Limit:** the paper's γ1/α2/α3 model is not identical to this repository's α1/γ1pedc extension. Neither adding two decay constants nor changing weights constitutes replication of the paper.

[^ichinose2015]: **Ichinose et al. (2015).** [Reward signal in a recurrent circuit drives appetitive long-term memory formation](https://doi.org/10.7554/eLife.10719). *eLife*, 4:e10719. [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC4643015/). **Type:** primary fly experiment. **Use:** an α1 recurrent-reward-circuit hypothesis to check against retained anatomy. **Limit:** circuit identity, physiological effects and consolidation times must be established separately in this reconstruction/model.

[^tsodyks1997]: **Tsodyks and Markram (1997).** [The neural code between neocortical pyramidal neurons depends on neurotransmitter release probability](https://doi.org/10.1073/pnas.94.2.719). *PNAS*, 94:719–723. [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC19580/). **Type:** primary physiology/modeling study. **Use:** activity-dependent synaptic resource depletion/recovery as an STP modeling basis. **Limit:** this is neocortical evidence, not fitted parameters for fly KC→MBON synapses.

[^markram1998]: **Markram, Wang and Tsodyks (1998).** [Differential signaling via the same axon of neocortical pyramidal neurons](https://doi.org/10.1073/pnas.95.9.5323). *PNAS*, 95:5323–5328. [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC20259/). **Type:** primary physiology/modeling study. **Use:** depression/facilitation and target-dependent transmission motivate explicit synapse selection and parameterization. **Limit:** anatomical connection counts alone cannot identify the correct STP dynamics.

[^turrigiano1998]: **Turrigiano, Leslie, Desai, Rutherford and Nelson (1998).** [Activity-dependent scaling of quantal amplitude in neocortical neurons](https://doi.org/10.1038/36103). *Nature*, 391:892–896. **Type:** primary cortical-culture experiment. **Use:** motivation for slowly regulating synaptic strength in response to activity. **Limit:** the proposed numerical gain controller, target rates and fly timescales are engineering hypotheses, not direct measurements from this paper.

[^izhikevich2007]: **Izhikevich (2007).** [Solving the distal reward problem through linkage of STDP and dopamine signaling](https://doi.org/10.1093/cercor/bhl152). *Cerebral Cortex*, 17:2443–2452. [Author page and paper](https://www.izhikevich.org/publications/dastdp.htm). **Type:** primary computational study. **Use:** eligibility-based delayed reinforcement as a modeling precedent. **Limit:** the cortical STDP model is not this fly's existing anti-Hebbian rule and does not solve financial credit assignment merely by citation.

[^agarwal2021]: **Agarwal, Schwarzer, Castro, Courville and Bellemare (2021).** [Deep Reinforcement Learning at the Edge of the Statistical Precipice](https://arxiv.org/abs/2108.13264). *NeurIPS 2021*. **Type:** primary evaluation-methodology study. **Use:** uncertainty-aware reporting, meaningful replication and avoiding rankings from noisy point estimates. **Limit:** its benchmark analysis is not a substitute for power analysis or an independence justification in market time series.

[^politis1994]: **Politis and Romano (1994).** [The Stationary Bootstrap](https://doi.org/10.1080/01621459.1994.10476870). *Journal of the American Statistical Association*, 89:1303–1313. **Type:** primary statistical-methodology paper. **Use:** a basis for considering block resampling under dependence. **Limit:** assumptions about dependence/stationarity and the statistic must be checked; resampling market data is not automatically a valid test of an adaptive policy.

[^butz2013]: **Butz and van Ooyen (2013).** [A Simple Rule for Dendritic Spine and Axonal Bouton Formation Can Account for Cortical Reorganization after Focal Retinal Lesions](https://doi.org/10.1371/journal.pcbi.1003259). *PLOS Computational Biology*, 9:e1003259. **Type:** primary computational study; consult the correction linked by the publisher. **Use:** a model precedent for activity-driven structural changes. **Limit:** cortical structural reorganization is different from adding fly neurons or modifying an unchanged connectome reconstruction.

[^draelos2016]: **Draelos et al. (2016 preprint).** [Neurogenesis Deep Learning](https://arxiv.org/abs/1612.03770). **Type:** primary artificial-network research preprint. **Use:** a precedent for growing model capacity while studying new learning and retained representations. **Limit:** adding artificial units is not demonstrated adult fly neurogenesis; extra-capacity and compute controls are required for the proposed toy experiment.

[^fernandez2013]: **Fernández-Hernández, Rhiner and Moreno (2013).** [Adult Neurogenesis in Drosophila](https://doi.org/10.1016/j.celrep.2013.05.034). *Cell Reports*, 3:1857–1865. [Indexed abstract](https://pubmed.ncbi.nlm.nih.gov/23791523/). **Type:** primary fly experiment. **Use:** evidence specific to adult optic-lobe medulla cortex, including injury-associated proliferation. **Limit:** it does not establish routine neuron addition throughout adult mushroom-body circuits or provide an implementation rule for this project.

[^mexcfees]: **MEXC, official operational sources.** [Fee overview](https://www.mexc.com/en-GB/fee) and [announcement introducing API futures trading on March 31, 2026](https://www.mexc.com/announcements/article/introducing-api-futures-trading-on-mar-31-2026-17827791534551). **Type:** exchange documentation, not research evidence. **Use:** fee provenance and the distinction between API and web/app schedules. **Limit:** rates can vary with time, instrument, region and account conditions. Record the applicable schedule for each experiment instead of treating a copied constant as universally current; these sources do not turn a spot paper broker into a futures simulator.
