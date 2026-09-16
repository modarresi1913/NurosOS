# NurosOS Developmental Substrate

> **Status:** [IMPLEMENTED] Phases 1–9 of the developmental substrate roadmap.
> [PROPOSED] Phases 10–14 (Observatory, CounterfactualSelf, Metabolism, Aging, Evolution).

This document describes the `nuros-dev` crate — the Rust-backed developmental
substrate that turns NurosOS from a runtime for AI agents into an experimental
platform for synthetic development.

---

## Central Thesis

> **NurosOS is an experimental substrate for studying how artificial minds develop.**

The fundamental object is not `MODEL` but `TRAJECTORY`; not `AGENT` but
`DEVELOPING ORGANISM`. The central research question is:

> What happens when we stop programming the final behavior of an artificial
> mind and instead program the conditions under which its cognitive structure
> can develop?

---

## What Is Implemented

### [IMPLEMENTED] Developmental Genome (`DevelopmentalGenome`)

A serializable, hashable specification of an organism's initial developmental
conditions. Includes: architecture, initial memory, initial capabilities,
plasticity rules, biases, maturation schedule, homeostasis setpoints, energy
model, and mutation parameters.

- Canonical SHA-256 hash (`genome_hash`) — same logical genome always
  produces the same hash, regardless of field declaration order.
- JSON round-trip preserves the hash.
- Used as the primary key in every checkpoint, trajectory, and manifest.

### [IMPLEMENTED] Developmental State (`DevelopmentalState`)

A vector-valued observable state of an organism at one point in time.
Includes: age, developmental stage, maturity, plasticity, stability,
adaptability, energy, cognitive load, memory capacity, prediction accuracy,
self-model stability, exploration level, risk sensitivity, capabilities,
and developmental event count.

- L1 distance metric between two states (`state.distance(other)`).
- Canonical hash for provenance.

### [IMPLEMENTED] Lifecycle State Machine (`LifecycleMachine`)

An explicit, auditable state machine for the organism's operational state:
`CREATED → INITIALIZED → DEVELOPING → ACTIVE → ADAPTING → RECOVERING →
CHECKPOINTED → FORKED → SUSPENDED → TERMINATED`.

- Every transition is recorded with (from, to, step, reason).
- Terminal state (`TERMINATED`) cannot be left.

### [IMPLEMENTED] Environments (`ResourceWorld`, `ChangingWorld`)

Two environments that exercise different aspects of development:

- **`ResourceWorld`** — 2D grid with limited resources and hazards. The
  organism must locate and consume resources while avoiding hazards.
  Tests: energy regulation, exploration vs. exploitation, risk sensitivity.
- **`ChangingWorld`** — 1D world where the resource location shifts at
  fixed intervals. Tests: adaptation, plasticity, unlearning.

Both environments are deterministic (given a fixed seed) and support:
`reset()`, `observe()`, `step(action)`, `snapshot()`, `restore()`, `hash()`.

### [IMPLEMENTED] Minimum Organism (`MinimumOrganism`)

A deterministic cognitive engine that exercises the full developmental loop:

```
GENOME → INITIAL STATE → SENSATION → PREDICTION → PREDICTION ERROR
       → MEMORY UPDATE → SELF-MODEL UPDATE → VALUE EVALUATION
       → DECISION → ACTION → ENVIRONMENTAL CONSEQUENCE
       → LEARNING → DEVELOPMENTAL UPDATE → NEW STATE → REPEAT
```

The engine is intentionally NOT an LLM, NOT a neural network, and NOT
stochastic. It is an ε-greedy policy over a small action space, with
hand-coded heuristic biases for environment-sensitivity. This makes
trajectories fully reproducible and lets us isolate the effect of
environment from the effect of engine.

### [IMPLEMENTED] Developmental Trajectory + Divergence

- `DevelopmentalTrajectory` — ordered list of `TrajectoryPoint` records.
- `DevelopmentalDivergence` — quantitative comparison of two trajectories.
  Metrics: reward distance, prediction-error distance, action distance,
  mean state distance, final state distance, stage divergence, per-step
  state distance series.

### [IMPLEMENTED] Mind Checkpoint + Replay

- `MindCheckpoint` — captures the full state needed to resume or analyze
  an organism. Includes genome, environment snapshot, organism state,
  runtime version, and provenance hashes.
- `replay_from_checkpoint()` — deterministic replay from a checkpoint,
  with explicit fidelity classification: `EXACT`, `APPROXIMATE`,
  `NON_REPRODUCIBLE`.

### [IMPLEMENTED] Mind Diff (`MindDiff`)

Structured comparison of two organism states across: memory, self-model,
values (action preferences), capabilities, prediction, behavior, and
developmental state. Machine-readable JSON + human-readable rendering.

### [IMPLEMENTED] Developmental Causality Graph

A provenance DAG that records, for every cognitive change, the chain of
events that produced it. Vocabulary: **causal trace**, **candidate causal
dependency**, **provenance dependency**. NOT a claim of philosophical
causality.

### [IMPLEMENTED] Developmental Telemetry

Per-step structured records exported as JSONL and CSV. Researchers can
analyze trajectories outside NurosOS using any tool that reads these
formats.

### [IMPLEMENTED] Reproducibility Manifest

A machine-readable document that records all the hashes and seeds needed
to reproduce an experiment: `mind_id`, `genome_hash`, `runtime_hash`,
`environment_hash`, `experiment_hash`, `random_seed`, `environment_seed`,
`checkpoint_hash`, `configuration_hash`, `dependency_versions`, `timestamp`,
`n_steps`, `limitations`.

### [IMPLEMENTED] Same Genome / Different World Experiment

The flagship experiment. Instantiates two organisms from the same genome,
places them in differently-seeded `ResourceWorld`s, develops both, and
computes the developmental divergence between them. Produces 13 artifacts:
genome, trajectories (JSONL), telemetry (CSV), checkpoints, divergence,
mind diff, manifests, report, and summary.

---

## What Is Proposed (Not Implemented)

### [IMPLEMENTED] Mind Observatory

A visualization/observability layer for inspecting the full developmental
loop. Implemented in `nuros/observatory.py` with a CLI in
`experiments/observatory.py`.

**Text renderers** (for terminal inspection):
- Timeline replay — step-by-step (action, reward, prediction_error, stage, energy, plasticity, memory_size, state_hash)
- Mind diff — structured comparison of final states
- Causal trace — trajectory backbone (observation → action → outcome)
- Environment events — per-step (on_resource, on_hazard, distance, total_left, agent_pos)
- Checkpoints overview — all checkpoint metadata
- Manifests — full reproducibility manifests
- Divergence summary — developmental divergence metrics

**PNG plots** (paper-ready figures):
- Developmental trajectory (plasticity, energy, prediction accuracy)
- Prediction error + reward (2-panel)
- Memory changes + cumulative reward (twin-axis)
- State transitions (step function of developmental stages)
- Resource consumption (energy + plasticity)
- Mind diff (bar chart of deltas)
- Per-step divergence (L1 state distance)
- Divergence comparison (cumulative reward A vs B)

**CLI**: `python experiments/observatory.py <experiment_dir> <command> [options]`

**`render_all`**: generates all 9 text reports + 13 PNG plots into a directory.

### [IMPLEMENTED] CounterfactualSelf + PossibleSelfSpace

Allows an organism to evaluate alternative developmental histories: "What if
environment E2 had occurred?", "What if action A had not been taken?".
Implemented in `nuros-dev/src/counterfactual.rs` with PyO3 bindings.

**Architecture**: CurrentSelf → CounterfactualGenerator → AlternativeTrajectory → Simulation → Evaluation

**API**:
- `CounterfactualSelf::what_if_environment(alt_env, n_steps)` — replay from checkpoint in alternative environment
- `CounterfactualSelf::what_if_actions(env, actions, n_steps)` — replay with forced action sequence
- `CounterfactualSelf::compare_to_actual(counterfactual)` — divergence between counterfactual and actual
- `PossibleSelfSpace::new(current_self, checkpoint_hash)` — build the space
- `PossibleSelfSpace::add_future(future)` — add a possible future
- `PossibleSelfSpace::coverage()` — mean pairwise L1 distance between final states of all futures
- `PossibleSelfSpace::distances_from_current()` — distance of each future from current self

**Safety invariants**:
1. Counterfactual simulations run against an environment *snapshot* — never the live environment.
2. Every counterfactual trajectory is marked `["SIMULATED", "COUNTERFACTUAL"]`.
3. `executed_in_real_environment: false` is enforced and auditable.

**Interpretation caveat**: PossibleSelfSpace is an experimental abstraction. It
does NOT represent phenomenological identity. The "possible selves" are
reachable computational states under counterfactual perturbations — nothing more.

### [IMPLEMENTED] Cognitive Metabolism

Resource accounting for attention, inference, memory, exploration,
uncertainty, risk, and energy. The organism can ask: "Is this information
worth the cognitive cost?" Implemented in `nuros-dev/src/metabolism.rs`.

**Budgets** (7): `attention`, `inference`, `memory`, `exploration`, `uncertainty`, `risk`, `energy`.

**Operations** (9): `Perceive`, `Predict`, `Memorize`, `Plan`, `Simulate`, `Act`, `Explore`, `ReduceUncertainty`, `TakeRisk`.

**API**:
- `CognitiveMetabolism::new(budget, costs)` — construct with budgets + cost model
- `can_afford(op)` — check whether an operation is affordable under current budgets
- `spend(op)` — spend budget for an operation (returns false if refused)
- `is_worth_it(expected_info_gain, op)` — value-of-information decision rule
- `remaining_fractions()` — remaining fraction of each budget (for telemetry)
- `reset_tick()` — reset per-tick spending (cumulative `total_spending` preserved)
- `refusals` — count of operations refused due to insufficient budget

**PyO3 bindings**:
- `run_metabolism_sweep(budget_values, n_steps)` — sweep energy budget across multiple values
- `evaluate_value_of_information(operation, expected_info_gain)` — evaluate VoI rule for one operation

**Interpretation caveat**: This is a computational abstraction inspired by
resource-constrained organisms. It does NOT reproduce biological metabolism.

### [IMPLEMENTED] Artificial Aging

An experimental aging model with 5 configurable dimensions: memory
degradation, plasticity changes, processing constraints, experience
accumulation, structural consolidation. Implemented in
`nuros-dev/src/aging.rs`.

**Dimensions**:
1. **Memory degradation** — `memory_degradation_rate`, `memory_degradation_onset`
2. **Plasticity changes** — `plasticity_decay_rate`, `plasticity_decay_onset`, `plasticity_floor`
3. **Processing constraints** — `cognitive_load_increase`, `energy_efficiency_decay`, `max_cognitive_load`
4. **Experience accumulation** — `stability_improvement_rate`, `max_stability`, `prediction_accuracy_improvement`
5. **Structural consolidation** — `self_model_consolidation_rate`, `max_self_model_stability`

**Presets**: `AgingModel::no_aging()`, `AgingModel::default()` (gentle), `AgingModel::rapid_aging()`

**PyO3 binding**: `run_aging_comparison(aging_model_json, n_steps)` — develops two organisms (no aging vs. with aging) and compares final developmental states.

**Interpretation caveat**: Aging is configurable. Do not impose biological
aging assumptions without evidence. The purpose is to investigate: *How does
accumulated computational history affect future cognition?*

### [PROPOSED] Artificial Evolution

Mutation, selection, variation, inheritance, evaluation operating on
`DevelopmentalGenome`. To be implemented only after deterministic
developmental experiments are functional.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        experiments/                                  │
│  same_genome_different_world.py — flagship experiment runner         │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    nuros._dev (PyO3 bindings)                        │
│  PyGenome · PyResourceWorld · PyChangingWorld · PyOrganism           │
│  run_same_genome_different_world() · mind_diff()                     │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    nuros-dev (Rust crate)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  hash    │ │  genome  │ │  state   │ │ lifecycle│ │environment│ │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ │
│  │ organism │ │trajectory│ │checkpoint│ │   diff   │ │causality │ │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ │
│  │telemetry │ │ manifest │ │          │ │          │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Quickstart

### Build the Rust extension

```bash
cd nuros-dev
maturin build --release
pip install --force-reinstall target/wheels/nuros_dev-*.whl
```

### Run the flagship experiment

```bash
cd /path/to/NurosOS
python experiments/same_genome_different_world.py \
    --steps 200 --env-a-seed 1 --env-b-seed 999 \
    --out-dir ./experiment_outputs/same_genome_different_world
```

### Run the test suite

```bash
# Rust unit tests (57 tests)
cd nuros-dev && cargo test --lib

# Python integration tests (18 tests)
python -m pytest nuros/tests/test_developmental_substrate.py -v
```

### Use the substrate directly in Python

```python
from nuros import _dev

# Construct a genome.
genome = _dev.DevelopmentalGenome("my_experiment")
print(f"genome_hash: {genome.hash}")

# Instantiate two organisms from the same genome.
org_a = _dev.MinimumOrganism(genome)
org_b = _dev.MinimumOrganism(genome)
assert org_a.genome_hash == org_b.genome_hash

org_a.initialize(); org_a.begin_development()
org_b.initialize(); org_b.begin_development()

# Place each in a different environment.
env_a = _dev.ResourceWorld(6, 6, seed=1)
env_b = _dev.ResourceWorld(6, 6, seed=999)
env_a.reset(); env_b.reset()

# Develop both.
for _ in range(100):
    org_a.tick_resource(env_a)
    org_b.tick_resource(env_b)

# The two organisms now have different developmental states
# despite sharing the same genome.
print(f"organism A state_hash: {org_a.state_hash}")
print(f"organism B state_hash: {org_b.state_hash}")
assert org_a.state_hash != org_b.state_hash
```

---

## Scientific Status Labels

Every claim in NurosOS documentation is labeled with one of:

| Label | Meaning |
|-------|---------|
| `[IMPLEMENTED]` | The feature is built, tested, and demonstrable. |
| `[EXPERIMENTAL]` | The feature is built but not yet validated at scale. |
| `[PROPOSED]` | The interface is designed; implementation is planned. |
| `[SPECULATIVE]` | The concept is described but not yet designed or built. |

Documentation must never imply that an unimplemented concept already exists.

---

## Interpretation Caveats

The phenomenon measured by the Same Genome / Different World experiment —
**Computational Developmental Divergence** — is NOT evidence of:

- consciousness,
- biological individuality,
- subjective experience,
- artificial life,
- sentience.

It is an observable computational fact: identical initial conditions,
different environmental histories, divergent developmental states. The
scientific interest is in characterizing *how* this divergence emerges
as a function of environmental structure, genome parameters, and runtime
properties.

---

## Module Reference

| Module | Responsibility |
|--------|----------------|
| `nuros-dev/src/hash.rs` | Canonical JSON + SHA-256 |
| `nuros-dev/src/genome.rs` | `DevelopmentalGenome` |
| `nuros-dev/src/state.rs` | `DevelopmentalState` + distance metric |
| `nuros-dev/src/lifecycle.rs` | `LifecycleMachine` |
| `nuros-dev/src/environment.rs` | `Environment` trait + `ResourceWorld` + `ChangingWorld` |
| `nuros-dev/src/organism.rs` | `MinimumOrganism` — deterministic cognitive engine |
| `nuros-dev/src/trajectory.rs` | `DevelopmentalTrajectory` + `DevelopmentalDivergence` |
| `nuros-dev/src/checkpoint.rs` | `MindCheckpoint` + `replay_from_checkpoint` |
| `nuros-dev/src/diff.rs` | `MindDiff` |
| `nuros-dev/src/causality.rs` | `DevelopmentalCausalityGraph` |
| `nuros-dev/src/telemetry.rs` | `DevelopmentalTelemetry` + `ReproducibilityManifest` |
| `nuros-dev/src/lib.rs` | PyO3 bindings + flagship runner |
| `experiments/same_genome_different_world.py` | Flagship experiment CLI |
| `nuros/tests/test_developmental_substrate.py` | Python integration tests |
