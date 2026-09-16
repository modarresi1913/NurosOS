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
| Mind Observatory | [PROPOSED] | Visualization layer |
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

NurosOS includes progressively complex experimental organisms:

| Organism | Architecture | Key Feature | Status |
|----------|-------------|-------------|--------|
| **Organism-0** | Reactive | sensory → response | ✅ Implemented |
| **Organism-1** | Reactive + Memory | sensory → memory → response | ✅ Implemented |
| **Organism-2** | Predictive | memory → prediction → action | ✅ Implemented |
| **Organism-3** | Imaginative | prediction → imagination → action | ✅ Implemented |
| **Organism-4** | Homeostatic | homeostasis → development → adaptation | ✅ Implemented |
| **Organism-5** | Self-modeling | memory → self-model → imagination → development | ✅ Implemented |

---

## Development Engine

**Core principle: Program the conditions under which a mind can develop, not every behavior the mind must contain.**

Developmental trajectory:
```
EMBRYONIC → NASCENT → DEVELOPING → MATURING → MATURE → SPECIALIZED
```

Instead of specifying every behavior, the programmer specifies:
- Rules and constraints
- Environment and resources
- Plasticity mechanisms
- Developmental objectives

---

## Homeostasis Kernel

The organism maintains internal operational state through computational regulation:

| Variable | Optimal | Regulation |
|----------|---------|------------|
| energy | 0.8 | Low energy → reduce computation |
| uncertainty | 0.2 | High uncertainty → increase exploration |
| prediction_error | 0.1 | High error → increase learning |
| sensory_load | 0.3 | High load → reduce exploration |
| threat_level | 0.0 | High threat → reduce exploration, increase alertness |
| stability | 0.9 | Instability → enter recovery mode |

**This is NOT biological homeostasis. It is a computational mechanism for maintaining viable internal operation.**

---

## Philosophy

> **Don't program the mind. Program the conditions under which it can develop.**

> **Memory is not storage. Development is not deployment. Simulation is not observation. Intelligence is not consciousness.**

---

## Research Questions

These are **hypotheses**, not established facts:

- **Development**: Can complex adaptive behavior emerge from simple developmental rules?
- **Memory**: How does persistent associative memory alter long-horizon behavior?
- **Plasticity**: Can structural adaptation outperform static architectures?
- **Homeostasis**: Can internal stability variables produce more robust adaptive behavior?
- **Embodiment**: How does coupling cognition to environmental constraints change behavior?
- **Self-model**: Does an explicit self-model improve planning or recovery?
- **Imagination**: Does counterfactual simulation improve decision quality?
- **Sleep**: Can offline replay and consolidation improve long-term performance?
- **Evolution**: Can populations of artificial organisms develop useful behavioral diversity?

---

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 0** | Scientific cleanup, claim audit, reproducibility standards | ✅ Complete |
| **Phase 1** | Cognitive substrate: memory API, epistemic labels, observability | ✅ Complete |
| **Phase 2** | Organismic runtime: homeostasis, scheduler, lifecycle | ✅ Complete |
| **Phase 3** | Development engine: rules, plasticity, checkpoints | ✅ Complete |
| **Phase 4** | Mind contracts: self-model, imagination, values, body, responsibility | ✅ Complete |
| **Phase 5** | Artificial organisms: manifests, environments, benchmarks | 🚧 In progress |
| **Phase 6** | Mind version control: snapshots, fork, diff, replay, restore | 🚧 Experimental |
| **Phase 7** | Artificial evolution: population runtime, mutation, selection | 📋 Proposed |

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
├── nuros/                    # Core Python package (NEW)
│   ├── __init__.py          # Package identity
│   ├── epistemic.py         # Epistemic Kernel — 7 labels, invariant enforcement
│   ├── memory.py            # Memory Contract — 5 types, 8 operations, auditable
│   ├── self_model.py        # Self Model Contract — queries, beliefs, goals
│   ├── imagination.py       # Imagination Engine — counterfactuals, safety gates
│   ├── values.py            # Values Contract — immutable constraints, goals, prefs
│   ├── body.py              # Body Contract — embodiment abstraction
│   ├── responsibility.py    # Responsibility Contract — auditable causal history
│   ├── homeostasis.py       # Homeostasis Kernel — 10 variables, regulation rules
│   ├── safety.py            # Safety Kernel — permissions, audit, override
│   ├── development.py       # Development Engine — synthetic development runtime
│   ├── organism.py          # Organism — integrated artificial cognitive organism
│   ├── environment.py       # Environment API — observe/act/step/reset
│   ├── genome.py            # Mind Genome — blueprint specification
│   ├── version_control.py   # Mind Version Control — snapshot/fork/diff
│   ├── scheduler.py         # Metabolic Cognitive Scheduler
│   └── tests/               # 33 comprehensive tests
├── kernel/                   # Rust microkernel (existing)
├── compiler/                 # SynapseLang compiler (existing)
├── core/                     # Core neural algorithms (existing)
├── hal/                      # Hardware Abstraction Layer (existing)
├── organisms/                # Experimental organism manifests
├── environments/             # Environment implementations
├── experiments/              # Scientific experiments
├── benchmarks/               # Benchmark suite
└── docs/                     # Documentation
```

---

## Status

> ⚠️ **Experimental research software.** NurosOS is at v0.2.0-alpha. It is not production-ready.

| Component | Language | Stage |
|-----------|----------|-------|
| Mind Contracts (Python) | Python | v0.2.0-alpha (33 tests passing) |
| Epistemic Kernel | Python | IMPLEMENTED |
| Homeostasis Kernel | Python | IMPLEMENTED |
| Safety Kernel | Python | IMPLEMENTED |
| Development Engine | Python | IMPLEMENTED |
| Organism Runtime | Python | IMPLEMENTED |
| Mind Genome | Python | EXPERIMENTAL |
| Mind Version Control | Python | EXPERIMENTAL |
| Kernel (Rust) | Rust | v0.1.0-alpha (existing) |
| SynapseLang | Python | v0.1.0-alpha (existing) |

---

## License

Released under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

---

## Citation

```bibtex
@software{nurosos2026,
  title  = {NurosOS: A Runtime for Synthetic Minds and Artificial Organisms},
  author = {NurosOS Contributors},
  year   = {2026},
  url    = {https://github.com/modarresi1913/NurosOS},
  version = {0.2.0-alpha}
}
```

---

> **NurosOS — The Runtime for Synthetic Minds.**
>
> *We don't build minds. We build the worlds in which minds can emerge.*
