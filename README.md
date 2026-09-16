<div align="center">

# NurosOS

### The Experimental Substrate for Synthetic Development

*Instantiate. Develop. Observe. Fork. Replay. Compare.*

*We don't train a mind. We instantiate its developmental conditions.*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0--alpha-orange.svg?style=flat-square)](https://github.com/modarresi1913/NurosOS/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75+-ce422b.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-yellow.svg?style=flat-square)](#status)
[![Tests](https://img.shields.io/badge/tests-75%20passing-brightgreen.svg?style=flat-square)](#testing)

**[Overview](#overview) · [Developmental Substrate](#developmental-substrate) · [Architecture](#architecture) · [Flagship Experiment](#flagship-experiment) · [Quickstart](#quickstart) · [Roadmap](#roadmap) · [Philosophy](#philosophy)**

</div>

---

## Overview

NurosOS is an **open, modular, inspectable substrate for synthetic development** — a runtime in which artificial organisms can be instantiated, developed, embodied, observed, measured, forked, replayed, and experimentally compared.

> **NurosOS is an experimental substrate for studying how artificial minds develop.**

### What NurosOS Is

- An **experimental substrate** for synthetic development and artificial cognition
- A **research infrastructure** where every extraordinary claim ships with a reproducible experiment
- A **modular architecture** with clear separation between developmental kernel, runtime, organism, environment, observation, causality, and reproducibility

### What NurosOS Is NOT

- ❌ A claim of machine consciousness
- ❌ A claim of artificial life
- ❌ A replacement for neuroscience
- ❌ A general-purpose LLM agent framework
- ❌ A production deployment platform

### The Central Inversion

Traditional AI:
```
Model → Training → Agent
```

NurosOS:
```
Developmental Genome
   → Environment
   → Experience
   → Development
   → Individual Cognitive Trajectory
   → Artificial Organism
```

The fundamental object is therefore not `MODEL` but `TRAJECTORY`; not `AGENT` but `DEVELOPING ORGANISM`.

NurosOS is **experimental research infrastructure**.

---

## Developmental Substrate

The `nuros-dev` crate ([DEVELOPMENTAL_SUBSTRATE.md](DEVELOPMENTAL_SUBSTRATE.md)) implements the developmental substrate. It is written in Rust and exposed to Python via PyO3.

### Implemented Components

| Component | Status | Description |
|-----------|--------|-------------|
| `DevelopmentalGenome` | [IMPLEMENTED] | Serializable, hashable genome with architecture, plasticity, maturation schedule, energy model |
| `DevelopmentalState` | [IMPLEMENTED] | Vector-valued observable state with L1 distance metric |
| `LifecycleMachine` | [IMPLEMENTED] | Auditable state machine: CREATED → INITIALIZED → DEVELOPING → ... → TERMINATED |
| `ResourceWorld` | [IMPLEMENTED] | 2D grid environment with resources and hazards |
| `ChangingWorld` | [IMPLEMENTED] | 1D environment with shifting resource (tests adaptation) |
| `MinimumOrganism` | [IMPLEMENTED] | Deterministic cognitive engine exercising the full developmental loop |
| `DevelopmentalTrajectory` | [IMPLEMENTED] | Ordered trajectory points + divergence metrics |
| `MindCheckpoint` | [IMPLEMENTED] | Save/restore full organism + environment state |
| `ReplayFidelity` | [IMPLEMENTED] | EXACT / APPROXIMATE / NON_REPRODUCIBLE classification |
| `MindDiff` | [IMPLEMENTED] | Structured diff of memory, self-model, values, capabilities, behavior, developmental state |
| `DevelopmentalCausalityGraph` | [IMPLEMENTED] | Provenance DAG with causal trace walks |
| `DevelopmentalTelemetry` | [IMPLEMENTED] | JSONL + CSV export for offline analysis |
| `ReproducibilityManifest` | [IMPLEMENTED] | Machine-readable provenance for every experiment |
| Same Genome / Different World | [IMPLEMENTED] | Flagship experiment runner |
| Mind Observatory | [IMPLEMENTED] | Observability layer: 9 text renderers + 13 PNG plots + CLI |
| CounterfactualSelf | [PROPOSED] | Alternative developmental histories |
| Cognitive Metabolism | [PROPOSED] | Resource accounting |
| Artificial Aging | [PROPOSED] | Aging model |
| Artificial Evolution | [PROPOSED] | Mutation/selection on DevelopmentalGenome |

---

## Architecture

```
Applications
    │
    ▼
Artificial Organisms
    │
    ▼
Mind Contract Layer (MCL)
    │   ├── Memory         — Living, evolving cognitive memory
    │   ├── Self Model     — Computational self-representation
    │   ├── Imagination    — Counterfactual simulation
    │   ├── Values/Drives  — Structured value hierarchy
    │   ├── Body           — Embodiment abstraction
    │   └── Responsibility — Auditable causal history
    │
    ▼
Cognitive Kernel
    │   ├── Attention    ├── Planning     ├── Reflection
    │   ├── Prediction   ├── World Model  └── Uncertainty
    │
    ▼
Organismic Kernel
    │   ├── Homeostasis  ├── Development  ├── Plasticity
    │   ├── Energy       ├── Lifecycle    └── Self-organization
    │
    ▼
Safety Kernel (architecturally independent)
    │   ├── Permissions  ├── Audit       ├── Human Override
    │   ├── Shutdown     ├── Recovery    └── Immutable Constraints
    │
    ▼
Neural / Cognitive Execution Layer
    │   ├── SNN          ├── LLM         ├── Symbolic Engine
    │   ├── Hybrid       └── Simulator
    │
    ▼
Hardware / Environment (Rust microkernel + HAL)
```

### Key Architectural Invariant

**Safety is architecturally independent from cognition.** The organism must NOT be able to modify its own safety boundary through ordinary cognitive operations.

---

## Mind Contracts

Every NurosOS-compatible artificial organism exposes **six conceptual contracts**:

### 1. Memory Contract
Memory is NOT simple vector storage. It is a living, evolving cognitive subsystem supporting:
- **5 memory types**: episodic, semantic, procedural, working, counterfactual
- **8 operations**: remember, retrieve, associate, reflect, revise, reconsolidate, forget, replay
- **Full provenance**: every memory knows where it came from
- **Auditable revision**: every modification is logged
- **Epistemic labeling**: counterfactual memories are always IMAGINED

### 2. Self Model Contract
A computational self-representation that can answer:
- *Who am I?* · *What can I do?* · *What can I not do?*
- *What do I currently believe?* · *How confident am I?*
- *What changed?* · *Why did I take this action?*

**The Self Model is an operational representation. It is NOT evidence of subjective consciousness.**

### 3. Imagination Contract
Counterfactual simulation with safety gates:
```
Hypothesis → Simulation → Evaluation → Decision → Execution
```
High-risk actions are **never** automatically executed.

### 4. Values Contract
Structured three-tier value system:
- **Immutable Constraints**: human_override, shutdown_compliance, audit_integrity, non_deception — *cannot be revoked*
- **Contextual Goals**: solve_problem, discover_pattern — *adjustable*
- **Preferences**: verbosity, exploration_rate — *tunable*

### 5. Body Contract
Embodiment abstraction allowing the **same cognitive organism** to be portable between different bodies: physical robot, virtual avatar, simulation, API agent, neuromorphic hardware.

### 6. Responsibility Contract
Every externally relevant action maintains an auditable causal history: what was observed, inferred, remembered, imagined, predicted, which policy selected the action, what authorization existed.

---

## Epistemic Kernel

Every internal representation carries an epistemic label:

| Label | Meaning |
|-------|---------|
| `OBSERVED` | Direct sensor data or verified input |
| `INFERRED` | Interpretation from observations |
| `REMEMBERED` | Retrieved from memory |
| `PREDICTED` | Expected future state |
| `SIMULATED` | Internal model result |
| `IMAGINED` | Internally generated possibility |
| `ACTED` | Externally executed operation |

**Critical invariants enforced:**
- ❌ `SIMULATED → OBSERVED` — A simulation is never an observation
- ❌ `IMAGINED → REMEMBERED` — An imagination is never a memory
- ❌ `PREDICTED → OBSERVED` — A prediction must be verified first

---

## Flagship Experiment

The flagship NurosOS experiment is **Same Genome / Different World**: two
organisms instantiated from the same genome, placed in differently-seeded
environments, and developed for the same number of steps. The experiment
demonstrates **Computational Developmental Divergence** — identical initial
computational conditions producing divergent developmental states under
different environmental histories.

> **Interpretation caveat:** This is NOT evidence of consciousness or
> biological individuality. It is an observable computational fact about
> divergent developmental trajectories.

```bash
# Build the Rust extension (one-time)
cd nuros-dev && maturin build --release && pip install --force-reinstall target/wheels/nuros_dev-*.whl && cd ..

# Run the flagship experiment
python experiments/same_genome_different_world.py \
    --steps 200 --env-a-seed 1 --env-b-seed 999 \
    --out-dir ./experiment_outputs/same_genome_different_world
```

Outputs (written to `--out-dir`):

- `genome.json` — the genome used (with hash)
- `trajectory_a.jsonl` / `trajectory_b.jsonl` — per-step trajectory records
- `telemetry_a.csv` / `telemetry_b.csv` — flat telemetry tables
- `checkpoint_a.json` / `checkpoint_b.json` — final checkpoints
- `divergence.json` — `DevelopmentalDivergence` between A and B
- `mind_diff.json` — `MindDiff` between final states of A and B
- `manifest_a.json` / `manifest_b.json` — `ReproducibilityManifest` for each
- `report.txt` — human-readable summary
- `summary.json` — machine-readable summary

---

## Quickstart

```bash
git clone https://github.com/modarresi1913/NurosOS.git
cd NurosOS

# Build and install the Rust developmental substrate
cd nuros-dev
maturin build --release
pip install --force-reinstall target/wheels/nuros_dev-*.whl
cd ..

# Run the test suite (75 tests: 57 Rust + 18 Python)
cd nuros-dev && cargo test --lib && cd ..
python -m pytest nuros/tests/test_developmental_substrate.py -v

# Run the flagship experiment
python experiments/same_genome_different_world.py --steps 200
```

---

## Organisms

NurosOS includes two organism implementations:

| Organism | Architecture | Key Feature | Status |
|----------|-------------|-------------|--------|
| **MinimumOrganism** | Deterministic ε-greedy + heuristic biases | Full developmental loop: sensation → prediction → memory → self-model → values → decision → action → learning → development | ✅ Implemented (in `nuros-dev` Rust crate) |
| **Organism-0..5** (Python) | Reactive → Self-modeling ladder | Mind Contract integration (memory, self-model, imagination, values, body, responsibility) | ✅ Implemented (in `nuros/` Python package) |

The `MinimumOrganism` is intentionally NOT an LLM, NOT a neural network, and NOT stochastic. It is a small deterministic policy over a finite action space, parameterized by a plasticity rule. This makes trajectories fully reproducible and lets us isolate the effect of environment from the effect of engine.

---

## Developmental Loop

The central computational loop implemented in `MinimumOrganism::tick`:

```
GENOME → INITIAL STATE → SENSATION → PREDICTION → PREDICTION ERROR
       → MEMORY UPDATE → SELF-MODEL UPDATE → VALUE EVALUATION
       → DECISION → ACTION → ENVIRONMENTAL CONSEQUENCE
       → LEARNING → DEVELOPMENTAL UPDATE → NEW STATE → REPEAT
```

Developmental stages (driven by the genome's maturation schedule):
```
EMBRYONIC → NASCENT → DEVELOPING → MATURING → MATURE → SPECIALIZED
```

Lifecycle states (auditable state machine):
```
CREATED → INITIALIZED → DEVELOPING → ACTIVE → ADAPTING → RECOVERING
       → CHECKPOINTED → FORKED → SUSPENDED → TERMINATED
```

---

## Homeostasis Kernel (Python cognitive layer)

The Python organism maintains internal operational state through computational regulation:

| Variable | Optimal | Regulation |
|----------|---------|------------|
| energy | 0.8 | Low energy → reduce computation |
| uncertainty | 0.2 | High uncertainty → increase exploration |
| prediction_error | 0.1 | High error → increase learning |
| sensory_load | 0.3 | High load → reduce exploration |
| threat_level | 0.0 | High threat → reduce exploration, increase alertness |
| stability | 0.9 | Instability → enter recovery mode |

**This is NOT biological homeostasis. It is a computational mechanism for maintaining viable internal operation.**

The Rust `MinimumOrganism` exposes the same variables via `DevelopmentalState` (energy_state, cognitive_load, prediction_accuracy, self_model_stability, exploration_level, risk_sensitivity, etc.).

---

## Philosophy

> **Don't train a mind. Instantiate its developmental conditions.**

> **Memory is not storage. Development is not deployment. Simulation is not observation. Intelligence is not consciousness. Divergence is not individuality.**

> **The fundamental object is not MODEL but TRAJECTORY; not AGENT but DEVELOPING ORGANISM.**

---

## Research Questions

These are **research questions**, not predetermined conclusions (full list in [RESEARCH_AGENDA.md](RESEARCH_AGENDA.md)):

1. Can developmental trajectories produce stable computational individuality?
2. How does environmental history alter identical initial architectures?
3. What measurable trade-offs exist between plasticity and stability?
4. Can artificial cognitive capabilities emerge through development rather than explicit programming?
5. How does accumulated experience alter future behavior?
6. Can cognitive trajectories be reproduced experimentally? **[IMPLEMENTED — yes, via ReproducibilityManifest]**
7. Can counterfactual developmental histories improve planning? **[PROPOSED]**
8. What computational constraints govern artificial cognitive development? **[PROPOSED — Cognitive Metabolism]**
9. Can artificial organisms specialize without explicit specialization programming?
10. Which properties of cognition are architecture-dependent versus development-dependent?

---

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1-9** | Developmental substrate: Genome, State, Lifecycle, Environments, MinimumOrganism, Trajectory, Checkpoint+Replay, MindDiff, Telemetry, CausalityGraph, Same Genome/Different World experiment | ✅ Complete |
| **Phase 10** | Mind Observatory: text renderers + PNG plots + CLI | ✅ Complete |
| **Phase 11** | CounterfactualSelf + PossibleSelfSpace: alternative developmental histories | 📋 Proposed |
| **Phase 12** | Cognitive/Epistemic Metabolism: resource budgets (attention, inference, memory, exploration, uncertainty, risk, energy) | 📋 Proposed |
| **Phase 13** | Artificial Aging: memory degradation, plasticity changes, structural consolidation | 📋 Proposed |
| **Phase 14** | Artificial Evolution: mutation/selection/inheritance on DevelopmentalGenome | 📋 Proposed |

See [ROADMAP.md](ROADMAP.md) for the full version-by-version roadmap.

---

## Testing

```bash
# Rust unit tests (57 tests) — covers genome hashing, lifecycle, environments,
# organism determinism, trajectory divergence, checkpoint/replay, mind diff,
# causality graph, telemetry, and reproducibility manifest.
cd nuros-dev && cargo test --lib

# Python integration tests (18 tests) — covers the PyO3 bindings end-to-end,
# including the flagship Same Genome / Different World experiment.
python -m pytest nuros/tests/test_developmental_substrate.py -v

# Existing Python cognitive-layer tests (33 tests) — covers epistemic kernel,
# memory contract, safety kernel, etc.
python -m pytest nuros/tests/test_core.py -v
```

All 108 tests passing ✅ (57 Rust + 18 developmental-substrate Python + 33 cognitive-layer Python)

---

## Project Structure

```
NurosOS/
├── nuros-dev/                # Rust developmental substrate (NEW in v0.3.0)
│   ├── src/
│   │   ├── lib.rs            # PyO3 bindings + flagship experiment runner
│   │   ├── hash.rs           # Canonical JSON + SHA-256
│   │   ├── genome.rs         # DevelopmentalGenome
│   │   ├── state.rs          # DevelopmentalState + L1 distance
│   │   ├── lifecycle.rs      # LifecycleMachine
│   │   ├── environment.rs    # ResourceWorld + ChangingWorld
│   │   ├── organism.rs       # MinimumOrganism (deterministic cognitive engine)
│   │   ├── trajectory.rs     # DevelopmentalTrajectory + DevelopmentalDivergence
│   │   ├── checkpoint.rs     # MindCheckpoint + ReplayFidelity
│   │   ├── diff.rs           # MindDiff
│   │   ├── causality.rs      # DevelopmentalCausalityGraph
│   │   └── telemetry.rs      # DevelopmentalTelemetry + ReproducibilityManifest
│   ├── tests/                # 57 Rust unit tests
│   ├── Cargo.toml
│   └── pyproject.toml        # maturin build config
├── nuros/                    # Python cognitive layer (v0.2.0)
│   ├── __init__.py           # v0.3.0-alpha identity + optional _dev import
│   ├── epistemic.py          # Epistemic Kernel — 7 labels, forbidden transitions
│   ├── memory.py             # Memory Contract — 5 types, 8 operations, auditable
│   ├── self_model.py         # Self Model Contract — queries, beliefs, goals
│   ├── imagination.py        # Imagination Engine — counterfactuals, safety gates
│   ├── values.py             # Values Contract — immutable constraints, goals, prefs
│   ├── body.py               # Body Contract — embodiment abstraction
│   ├── responsibility.py     # Responsibility Contract — auditable causal history
│   ├── homeostasis.py        # Homeostasis Kernel — 10 variables, regulation rules
│   ├── safety.py             # Safety Kernel — permissions, audit, override
│   ├── development.py        # Development Engine — synthetic development runtime
│   ├── organism.py           # Organism Runtime — integrated cognitive organism
│   ├── environment.py        # Environment API — observe/act/step/reset
│   ├── genome.py             # Mind Genome (Python-side, superseded by nuros-dev)
│   ├── version_control.py    # Mind Version Control (Python-side, superseded)
│   ├── scheduler.py          # Metabolic Cognitive Scheduler
│   └── tests/
│       ├── test_core.py              # 33 cognitive-layer tests
│       └── test_developmental_substrate.py  # 18 integration tests (NEW)
├── experiments/
│   └── same_genome_different_world.py  # Flagship experiment (NEW)
├── kernel/                   # Rust neuromorphic microkernel (v0.1.0, future backend)
├── core/                     # Rust neural algorithms (v0.1.0, future backend)
├── hal/                      # Hardware Abstraction Layer (v0.1.0)
├── compiler/                 # SynapseLang compiler (v0.1.0)
├── organisms/                # Python organism manifests (0-5)
├── environments/             # Python environment implementations
├── benchmarks/               # Benchmark suite
├── docs/
│   └── structured-data.json  # Schema.org for SEO/AEO/GEO (updated v0.3.0)
├── DEVELOPMENTAL_SUBSTRATE.md  # Comprehensive spec (NEW)
├── WHITEPAPER.md             # v2.0 draft (v1.0 preserved as historical context)
├── ARCHITECTURE.md           # v0.3.0+ layer architecture
├── SUMMARY.md                # 60-second overview for answer engines
├── ROADMAP.md                # Phase 1-9 complete, 10-14 proposed
├── RESEARCH_AGENDA.md        # 12 research items + 10 open questions
├── CONTRIBUTING.md           # Two-track contribution model
├── KEYWORDS.md               # SEO/AEO/GEO keyword clusters (EN + FA)
├── llms.txt                  # AEO/GEO summary for LLMs
└── CITATION.cff              # v0.3.0-alpha citation
```

---

## Status

> ⚠️ **Experimental research software.** NurosOS is at v0.3.0-alpha. It is not production-ready.

| Component | Language | Stage |
|-----------|----------|-------|
| Developmental Substrate (nuros-dev) | Rust + PyO3 | v0.3.0-alpha [IMPLEMENTED] — 57 tests passing |
| Mind Contracts (Python) | Python | v0.3.0-alpha [IMPLEMENTED] — 33 cognitive-layer tests |
| Developmental Substrate Integration | Python | v0.3.0-alpha [IMPLEMENTED] — 18 integration tests |
| Flagship Experiment | Python | v0.3.0-alpha [IMPLEMENTED] — Same Genome / Different World |
| Mind Observatory | Python | v0.3.0-alpha [IMPLEMENTED] — 21 tests, 9 text renderers + 13 PNG plots |
| CounterfactualSelf | — | [PROPOSED] — Phase 11 |
| Cognitive Metabolism | — | [PROPOSED] — Phase 12 |
| Artificial Aging | — | [PROPOSED] — Phase 13 |
| Artificial Evolution | — | [PROPOSED] — Phase 14 |
| Neuromorphic Kernel (v0.1.0) | Rust | Preserved as future execution backend |
| SynapseLang (v0.1.0) | Python | Preserved as v0.1.0 |

---

## License

Released under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

---

## Citation

```bibtex
@software{nurosos2026,
  title  = {NurosOS: The Experimental Substrate for Synthetic Development},
  author = {NurosOS Contributors},
  year   = {2026},
  url    = {https://github.com/modarresi1913/NurosOS},
  version = {0.3.0-alpha}
}
```

---

> **NurosOS — The Experimental Substrate for Synthetic Development.**
>
> *We don't train a mind. We instantiate its developmental conditions.*
