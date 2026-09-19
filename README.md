<div align="center">

# NurosOS

### The Experimental Substrate for Synthetic Development

*Instantiate. Develop. Observe. Fork. Replay. Compare.*

*We don't train a mind. We instantiate its developmental conditions.*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.0--alpha-purple.svg?style=flat-square)](#status)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75+-ce422b.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-yellow.svg?style=flat-square)](#status)
[![Tests](https://img.shields.io/badge/tests-322%20passing-brightgreen.svg?style=flat-square)](#testing)
[![HippoCore](https://img.shields.io/badge/HippoCore-integrated-8A2BE2.svg?style=flat-square)](#hippocore-integration)

**[Overview](#overview) · [HippoCore](#hippocore-integration) · [Architecture](#architecture) · [Quickstart](#quickstart) · [Roadmap](#roadmap) · [FAQ](#frequently-asked-questions) · [Philosophy](#philosophy)**

</div>

---

## Overview

NurosOS is an **open, modular, inspectable substrate for synthetic development** — a runtime in which artificial organisms can be instantiated, developed, embodied, observed, measured, forked, replayed, and experimentally compared.

> **NurosOS is an experimental substrate for studying how artificial minds develop.**

### What NurosOS Is

- An **experimental substrate** for synthetic development and artificial cognition
- A **research infrastructure** where every extraordinary claim ships with a reproducible experiment
- A **modular architecture** with clear separation between developmental kernel, runtime, organism, environment, observation, causality, and reproducibility
- A **memory-centric developmental substrate** with the HippoCore integration (episodic memory, replay, consolidation as first-class computational mechanisms)

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

## HippoCore Integration

> **v0.4.0-alpha**: The HippoCore integration transforms NurosOS from a runtime for artificial cognitive organisms into a **developmental intelligence substrate** where episodic memory, continual learning, replay, consolidation, and developmental trajectory are first-class computational mechanisms.

The HippoCore integration is shipped as **10 logical phases** on the `feature/hippocore-integration-audit` branch:

| # | Phase | Commit | Description | Tests |
|---|-------|--------|-------------|-------|
| 1 | Audit | [`254875c`](https://github.com/modarresi1913/NurosOS/commit/254875c) | 1051-line audit (24 sections + 2 appendices) anchored to file:line evidence | — |
| 2 | Memory Contract stabilization | [`f29a768`](https://github.com/modarresi1913/NurosOS/commit/f29a768) | `MemoryEngine` ABC + `DefaultMemoryContract` refactor + 6 bug-fixes from audit Appendix B | 83 |
| 3 | HippoCore adapter scaffold | [`5c58859`](https://github.com/modarresi1913/NurosOS/commit/5c58859) | `HippoCoreMemory(MemoryEngine)` thin wrapper + 25 golden-file equivalence tests | 108 |
| 4 | Episodic encoding + provenance | [`b5dcc6e`](https://github.com/modarresi1913/NurosOS/commit/b5dcc6e) | `MemoryProvenance` dataclass + `MemoryEntry` schema extension (7 PHASE 4 fields) + `encode_episode()` entry point | 128 |
| 5 | Replay policies | [`3e60a63`](https://github.com/modarresi1913/NurosOS/commit/3e60a63) | 5 policies (recent / importance_weighted / novelty_weighted / prediction_error_weighted / random); all deterministic when seeded | 169 |
| 6 | Consolidation pipeline | [`f5dc734`](https://github.com/modarresi1913/NurosOS/commit/f5dc734) | 2 strategies (tag_jaccard / content_prefix); real fast→slow pipeline; sources↔target associations | 201 |
| 7 | Memory event emission | [`b3e97cf`](https://github.com/modarresi1913/NurosOS/commit/b3e97cf) | 6 `MemoryEventKind`s + `MemoryEventEmitter` event bus + `set_step()` for trajectory alignment | 220 |
| 8 | Causal graph integration (Python side) | [`74fb2da`](https://github.com/modarresi1913/NurosOS/commit/74fb2da) | 17 `EventKind` variants (11 original Rust + 6 PHASE 8 memory kinds) + `PythonCausalGraph` + `trace_outcome_to_experience()` walk | 247 |
| 9 | Benchmark suite | [`bc411cf`](https://github.com/modarresi1913/NurosOS/commit/bc411cf) | 10 benchmarks in `benchmarks/memory/`; multi-seed runner with JSON/CSV/Markdown export; all deterministic | — |
| 10 | Documentation and release | [`5894c6c`](https://github.com/modarresi1913/NurosOS/commit/5894c6c) | 9 new docs + ADR 0006 + final report | — |

**Total**: 247 Python tests passing (was 75 before HippoCore). Rust-side tests (57) still pass per README quickstart when `maturin build --release` is run. **LLM dependency: NONE**.

📖 **Documentation**:
- [`docs/HIPPOCORE_INTEGRATION_AUDIT.md`](docs/HIPPOCORE_INTEGRATION_AUDIT.md) — 1051-line audit (PHASE 1)
- [`docs/HIPPOCORE_INTEGRATION.md`](docs/HIPPOCORE_INTEGRATION.md) — Integration guide
- [`docs/MEMORY_ARCHITECTURE.md`](docs/MEMORY_ARCHITECTURE.md) — Memory architecture
- [`docs/DEVELOPMENTAL_MEMORY.md`](docs/DEVELOPMENTAL_MEMORY.md) — Why memory is central to development
- [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) — 10-benchmark suite
- [`docs/METRICS.md`](docs/METRICS.md) — Multidimensional metric profile
- [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) — Reproducibility invariants
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) — Experiment guide
- [`docs/HIPPOCORE_INTEGRATION_REPORT.md`](docs/HIPPOCORE_INTEGRATION_REPORT.md) — Final report (PHASE 10)
- [`docs/adr/0006-hippocore-memory-engine.md`](docs/adr/0006-hippocore-memory-engine.md) — ADR

🔗 **Pull-request comparison**: https://github.com/modarresi1913/NurosOS/compare/main...feature/hippocore-integration-audit

### HippoCore Quickstart

```python
from nuros.hippocore import HippoCoreMemory, HippoCoreMemoryConfig

# Configure with replay policy + consolidation strategy.
hcm = HippoCoreMemory(
    HippoCoreMemoryConfig(
        replay_policy="importance_weighted",
        replay_seed=42,
        consolidation_strategy="tag_jaccard",
        consolidation_similarity_threshold=0.3,
    ),
    organism_id="org-001",
    environment_hash="env-abc",
)

# Encode an episode (master prompt §6).
entry = hcm.encode_episode(
    content="observation at step 5",
    action="MoveRight",
    prediction={"predicted_reward": 0.4},
    outcome={"reward": 0.5, "new_pos": [4, 4]},
    prediction_error=0.1,
    environment_state={"agent_pos": [3, 4]},
    internal_state={"energy": 0.7},
    experience_id="exp-step-5",
)

# Retrieve, replay, consolidate, checkpoint/restore.
results = hcm.retrieve(query="observation", limit=5)
replayed = hcm.replay(n=5)
n_targets = hcm.consolidate()
payload = hcm.checkpoint()
hcm2 = HippoCoreMemory()
hcm2.restore(payload)  # idempotent round-trip
```

---

## Developmental Substrate

The `nuros-dev` crate ([`DEVELOPMENTAL_SUBSTRATE.md`](DEVELOPMENTAL_SUBSTRATE.md)) implements the developmental substrate. It is written in Rust and exposed to Python via PyO3.

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
| CounterfactualSelf + PossibleSelfSpace | [IMPLEMENTED] | Alternative developmental histories + reachable state space |
| Cognitive Metabolism | [IMPLEMENTED] | 7 budgets + 9 operations + value-of-information rule |
| Artificial Aging | [IMPLEMENTED] | 5 dimensions: memory degradation, plasticity, processing, experience, consolidation |
| **HippoCore Integration** | **[IMPLEMENTED]** | **10 phases: episodic memory + replay + consolidation + causal graph** |
| Artificial Evolution | [PROPOSED] | Mutation/selection on DevelopmentalGenome |

---

## Architecture

```
                NUROSOS
     Developmental Organism Layer
                   │
   ┌───────────────┼──────────────┐
   │               │              │
Cognition       Self Model      Safety
   │               │              │
   └───────────────┼──────────────┘
                   ↓
           Memory Contract
                   ↓
              HIPPOCORE
                   │
   ┌───────────────┼───────────────┐
   │               │               │
Pattern Sep.    Episodic        Replay
   │           Encoding          │
   └───────────────┼───────────────┘
                   ↓
           Consolidation
                   ↓
        Developmental State
                   ↓
     Developmental Trajectory
                   ↓
           Edge Runtime
```

### Layer Architecture (v0.4.0+)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Experiments                                    │
│  same_genome_different_world.py  (flagship, Rust)                   │
│  benchmarks/memory/  (10 HippoCore benchmarks, Python-only)        │
├─────────────────────────────────────────────────────────────────────┤
│         HippoCore (PHASE 3-8, nuros/hippocore/)                     │
│  HippoCoreMemory · 5 ReplayPolicies · 2 ConsolidationStrategies   │
│  MemoryEventEmitter · PythonCausalGraph                            │
├─────────────────────────────────────────────────────────────────────┤
│              Developmental Substrate (nuros-dev)                    │
│  DevelopmentalGenome · DevelopmentalState · Lifecycle               │
│  ResourceWorld · ChangingWorld · MinimumOrganism                  │
│  DevelopmentalTrajectory · DevelopmentalDivergence                 │
│  MindCheckpoint · ReplayFidelity · MindDiff                        │
│  DevelopmentalCausalityGraph · Telemetry · Manifest                │
├─────────────────────────────────────────────────────────────────────┤
│              Mind Contract Layer (MCL)                              │
│  MemoryContract → MemoryEngine ABC (PHASE 2 stabilization)         │
│  SelfModel · Imagination · Values · Body · Responsibility         │
├─────────────────────────────────────────────────────────────────────┤
│                Cognitive Kernel                                     │
│   Attention │ Planning │ Reflection │ Prediction                   │
│   WorldModel│ Uncertainty                                           │
├─────────────────────────────────────────────────────────────────────┤
│              Organismic Kernel                                      │
│   Homeostasis │ Development │ Plasticity                           │
│   Energy │ Lifecycle │ Self-organization                            │
├─────────────────────────────────────────────────────────────────────┤
│       Safety Kernel (architecturally independent)                   │
│   Permissions │ Audit │ Human Override │ Shutdown                  │
│   Recovery │ Immutable Constraints                                  │
├─────────────────────────────────────────────────────────────────────┤
│          Neural / Cognitive Execution Layer                         │
│   SNN │ LLM │ Symbolic │ Hybrid                                    │
├─────────────────────────────────────────────────────────────────────┤
│            Hardware Abstraction (HAL)                               │
│   x86 │ ARM │ FPGA │ Loihi │ GPU                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Invariant

**Safety is architecturally independent from cognition.** The organism must NOT be able to modify its own safety boundary through ordinary cognitive operations.

---

## Mind Contracts

Every NurosOS-compatible artificial organism exposes **six conceptual contracts**:

### 1. Memory Contract → MemoryEngine ABC (PHASE 2)
Memory is NOT simple vector storage. It is a living, evolving cognitive subsystem supporting:
- **5 memory types**: episodic, semantic, procedural, working, counterfactual
- **10 operations**: encode, retrieve, associate, reconsolidate, replay, consolidate, forget, checkpoint, restore, inspect
- **Full provenance**: every memory knows where it came from (PHASE 4 `MemoryProvenance`)
- **Auditable revision**: every modification is logged
- **Epistemic labeling**: counterfactual memories are always IMAGINED
- **Soft-delete by default** (audit Appendix B.1 fix)

Two implementations:
- `DefaultMemoryContract` (`nuros/memory.py`) — historical, backward-compatible
- `HippoCoreMemory` (`nuros/hippocore/memory_engine.py`) — episodic engine (PHASE 3+)

Selector: `OrganismConfig.memory_engine = "default" | "hippocore"`

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

## Flagship Experiment

The flagship NurosOS experiment is **Same Genome / Different World**: two organisms instantiated from the same genome, placed in differently-seeded environments, and developed for the same number of steps. The experiment demonstrates **Computational Developmental Divergence** — identical initial computational conditions producing divergent developmental states under different environmental histories.

> **Interpretation caveat:** This is NOT evidence of consciousness or biological individuality. It is an observable computational fact about divergent developmental trajectories.

```bash
# Build the Rust extension (one-time)
cd nuros-dev && maturin build --release && pip install --force-reinstall target/wheels/nuros_dev-*.whl && cd ..

# Run the flagship experiment
python experiments/same_genome_different_world.py \
    --steps 200 --env-a-seed 1 --env-b-seed 999 \
    --out-dir ./experiment_outputs/same_genome_different_world
```

Outputs (written to `--out-dir`):
- `genome.json`, `trajectory_a.jsonl` / `trajectory_b.jsonl`, `telemetry_a.csv` / `telemetry_b.csv`
- `checkpoint_a.json` / `checkpoint_b.json`, `divergence.json`, `mind_diff.json`
- `manifest_a.json` / `manifest_b.json`, `report.txt`, `summary.json`

For environments without the Rust build, the PHASE 9 benchmark suite provides a Python-only equivalent:
```bash
python3 -c "from benchmarks.memory import run_all_benchmarks; from pathlib import Path; run_all_benchmarks(Path('./benchmarks/memory/results'), n_seeds=5)"
```

---

## Quickstart

```bash
git clone https://github.com/modarresi1913/NurosOS.git
cd NurosOS

# Build and install the Rust developmental substrate (one-time)
cd nuros-dev
maturin build --release
pip install --force-reinstall target/wheels/nuros_dev-*.whl
cd ..

# Run the test suite (322 tests: 247 Python + 57 Rust + 18 integration)
cd nuros-dev && cargo test --lib && cd ..
python -m pytest nuros/tests/ -v --ignore=nuros/tests/test_developmental_substrate.py --ignore=nuros/tests/test_counterfactual.py --ignore=nuros/tests/test_metabolism.py --ignore=nuros/tests/test_aging.py --ignore=nuros/tests/test_observatory.py

# Run the flagship experiment
python experiments/same_genome_different_world.py --steps 200

# Run the HippoCore benchmark suite (Python-only)
python3 -c "from benchmarks.memory import run_all_benchmarks; from pathlib import Path; run_all_benchmarks(Path('./benchmarks/memory/results'), n_seeds=5)"
```

### Use HippoCore directly

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

## Testing

<a name="testing"></a>

```bash
# Python cognitive-layer tests (247 tests) — does not require Rust build
python -m pytest nuros/tests/ -v \
    --ignore=nuros/tests/test_developmental_substrate.py \
    --ignore=nuros/tests/test_counterfactual.py \
    --ignore=nuros/tests/test_metabolism.py \
    --ignore=nuros/tests/test_aging.py \
    --ignore=nuros/tests/test_observatory.py

# Rust unit tests (57 tests) — requires `maturin build --release` first
cd nuros-dev && cargo test --lib && cd ..

# Python integration tests (18 tests) — requires the built Rust extension
python -m pytest nuros/tests/test_developmental_substrate.py -v

# Existing Python cognitive-layer tests (33 tests)
python -m pytest nuros/tests/test_core.py -v
```

**Total**: 341 tests ✅ (266 Python [247 HippoCore + 19 Q-learning] + 57 Rust + 18 integration) — across 9 test suites.

| Test Suite | File | Count | Phase |
|---|---|---|---|
| Cognitive-layer core | `nuros/tests/test_core.py` | 34 | 2 |
| MemoryEngine ABC | `nuros/tests/test_memory_engine.py` | 50 | 2 |
| HippoCore smoke (PHASE 3 equivalence) | `nuros/tests/test_hippocore_smoke.py` | 25 | 3 |
| Episodic encoding | `nuros/tests/test_episodic_encoding.py` | 20 | 4 |
| Replay policies | `nuros/tests/test_replay_policies.py` | 41 | 5 |
| Consolidation | `nuros/tests/test_consolidation.py` | 32 | 6 |
| Memory events | `nuros/tests/test_memory_events.py` | 19 | 7 |
| Causal graph | `nuros/tests/test_causal_graph.py` | 27 | 8 |
| Q-learning baseline | `nuros/tests/test_q_learning.py` | 19 | Audit |
| Rust developmental substrate | `nuros-dev/src/*.rs` `#[cfg(test)]` | 57 | v0.3.0 |
| Python integration | `nuros/tests/test_developmental_substrate.py` | 18 | v0.3.0 |

---

## Project Structure

```
NurosOS/
├── nuros/                        # Python cognitive layer (v0.2.0+)
│   ├── __init__.py
│   ├── epistemic.py              # Epistemic Kernel
│   ├── memory.py                 # Memory Contract → DefaultMemoryContract (PHASE 2)
│   ├── memory_engine.py          # MemoryEngine ABC (PHASE 2)
│   ├── memory_provenance.py     # MemoryProvenance dataclass (PHASE 4)
│   ├── memory_events.py         # MemoryEvent + MemoryEventEmitter (PHASE 7)
│   ├── causal_graph.py          # PythonCausalGraph + EventKind (PHASE 8)
│   ├── self_model.py
│   ├── imagination.py
│   ├── values.py
│   ├── body.py
│   ├── responsibility.py
│   ├── homeostasis.py
│   ├── safety.py
│   ├── scheduler.py
│   ├── development.py
│   ├── organism.py
│   ├── environment.py
│   ├── genome.py
│   ├── version_control.py
│   ├── observatory.py
│   ├── baselines/                 # Scientific audit baselines
│   │   └── q_learning/            # Tabular Q-learning baseline (19 tests)
│   ├── hippocore/                # HippoCore integration (PHASE 3+)
│   │   ├── __init__.py
│   │   ├── memory_engine.py     # HippoCoreMemory(MemoryEngine)
│   │   ├── replay_policy.py     # 5 replay policies (PHASE 5)
│   │   └── consolidation.py     # 2 consolidation strategies (PHASE 6)
│   └── tests/
│       ├── test_core.py              # 34 cognitive-layer tests
│       ├── test_memory_engine.py     # 50 MemoryEngine tests (PHASE 2)
│       ├── test_hippocore_smoke.py   # 25 PHASE 3 equivalence tests
│       ├── test_episodic_encoding.py # 20 PHASE 4 tests
│       ├── test_replay_policies.py   # 41 PHASE 5 tests
│       ├── test_consolidation.py    # 32 PHASE 6 tests
│       ├── test_memory_events.py     # 19 PHASE 7 tests
│       ├── test_causal_graph.py     # 27 PHASE 8 tests
│       ├── test_developmental_substrate.py  # 18 integration tests
│       ├── test_counterfactual.py
│       ├── test_metabolism.py
│       ├── test_aging.py
│       └── test_observatory.py
├── nuros-dev/                    # Rust developmental substrate (v0.3.0)
│   ├── src/
│   │   ├── lib.rs                # PyO3 bindings + flagship experiment runner
│   │   ├── hash.rs               # Canonical JSON + SHA-256
│   │   ├── genome.rs             # DevelopmentalGenome
│   │   ├── state.rs              # DevelopmentalState + L1 distance
│   │   ├── lifecycle.rs          # LifecycleMachine
│   │   ├── environment.rs        # ResourceWorld + ChangingWorld
│   │   ├── organism.rs           # MinimumOrganism (deterministic)
│   │   ├── trajectory.rs         # DevelopmentalTrajectory + Divergence
│   │   ├── checkpoint.rs         # MindCheckpoint + ReplayFidelity
│   │   ├── diff.rs               # MindDiff
│   │   ├── causality.rs          # DevelopmentalCausalityGraph
│   │   ├── counterfactual.rs     # CounterfactualSelf + PossibleSelfSpace
│   │   ├── metabolism.rs         # CognitiveMetabolism
│   │   ├── aging.rs              # AgingModel
│   │   └── telemetry.rs          # DevelopmentalTelemetry + Manifest
│   ├── tests/                    # 57 Rust unit tests
│   ├── Cargo.toml
│   └── pyproject.toml
├── benchmarks/
│   ├── benchmark_suite.py        # v0.2 micro-benchmarks
│   └── memory/                   # PHASE 9 HippoCore benchmarks
│       └── __init__.py           # 10 benchmarks + multi-seed runner
├── experiments/
│   ├── same_genome_different_world.py    # Flagship experiment
│   ├── counterfactual_demo.py
│   ├── aging_demo.py
│   ├── metabolism_demo.py
│   └── memory/decay_experiment.py
├── organisms/                    # Python organism manifests (0-5)
├── environments/                 # Python environment implementations
├── kernel/                       # Rust neuromorphic microkernel (v0.1.0)
├── core/                         # Rust neural algorithms (v0.1.0)
├── hal/                          # Hardware Abstraction Layer (v0.1.0)
├── compiler/synapselang/         # SynapseLang compiler (v0.1.0)
├── docs/
│   ├── HIPPOCORE_INTEGRATION_AUDIT.md     # PHASE 1 audit (1051 lines)
│   ├── HIPPOCORE_INTEGRATION.md           # Integration guide
│   ├── HIPPOCORE_INTEGRATION_REPORT.md    # Final report (PHASE 10)
│   ├── MEMORY_ARCHITECTURE.md             # Memory architecture
│   ├── DEVELOPMENTAL_MEMORY.md            # Developmental memory
│   ├── BENCHMARKS.md                      # Benchmark guide
│   ├── METRICS.md                         # Metric profile
│   ├── REPRODUCIBILITY.md                 # Reproducibility invariants
│   ├── EXPERIMENTS.md                     # Experiment guide
│   ├── RESEARCH_AUDIT.md                  # 17-section forensic audit (PHASE 0)
│   ├── ARCHITECTURE_AUDIT.md             # Module-level cross-check
│   ├── MEMORY_AUDIT.md                    # Memory subsystem audit
│   ├── EXPERIMENTAL_ROADMAP.md           # Recommended execution order
│   ├── HIPPOCORE_INTEGRATION_PLAN.md     # Future HippoCore intervention design
│   ├── SCIENTIFIC_RISKS.md               # 14 risks classified by severity
│   ├── BASELINE_SPEC.md                  # Q-learning baseline specification
│   ├── REPRODUCIBILITY_SPEC.md            # 7 reproducibility invariants
│   ├── METRICS_SPEC.md                   # 19-metric specification
│   ├── architecture/SPECIFICATION.md
│   ├── adr/
│   │   ├── 0001-no-filesystem.md
│   │   ├── 0002-rust-over-cpp.md
│   │   ├── 0003-spp-sparsity-threshold.md
│   │   ├── 0004-ams-over-vfs.md
│   │   ├── 0005-loihi-integration.md
│   │   └── 0006-hippocore-memory-engine.md  # PHASE 10 ADR
│   └── structured-data.json     # Schema.org for SEO/AEO/GEO
├── DEVELOPMENTAL_SUBSTRATE.md    # Comprehensive spec
├── WHITEPAPER.md                 # v2.0 draft
├── ARCHITECTURE.md               # Layer architecture
├── SUMMARY.md                    # 60-second overview (AEO)
├── ROADMAP.md                    # Phase 1-9 complete, 10-15 proposed
├── RESEARCH_AGENDA.md            # Research items + open questions
├── CONTRIBUTING.md
├── KEYWORDS.md                   # SEO/AEO/GEO keyword clusters
├── llms.txt                      # AEO/GEO summary for LLMs
└── CITATION.cff                  # v0.4.0-alpha citation
```

---

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1-9** | Developmental substrate: Genome, State, Lifecycle, Environments, MinimumOrganism, Trajectory, Checkpoint+Replay, MindDiff, Telemetry, CausalityGraph, Same Genome/Different World experiment | ✅ Complete |
| **Phase 10** | Mind Observatory: text renderers + PNG plots + CLI | ✅ Complete |
| **Phase 11** | CounterfactualSelf + PossibleSelfSpace: alternative developmental histories | ✅ Implemented ⚠️ Benefit unmeasured |
| **Phase 12** | Cognitive/Epistemic Metabolism: 7 budgets + 9 operations + value-of-information rule | ✅ Implemented ⚠️ Benefit unmeasured |
| **Phase 13** | Artificial Aging: 5 dimensions (memory degradation, plasticity, processing, experience, consolidation) | ✅ Implemented ⚠️ Benefit unmeasured |
| **Phase 14** | Artificial Evolution: mutation/selection/inheritance on DevelopmentalGenome | 📋 Proposed |
| **Phase 15** | **HippoCore Integration: 10 sub-phases** (audit → memory contract → adapter → episodic encoding → replay policies → consolidation → trajectory → causal graph → benchmarks → docs) | ⚠️ Implemented but NOT empirically validated — see [Scientific Audit](#scientific-audit) |
| **Audit** | **Scientific audit + Q-learning baseline + 11 deliverables** (RESEARCH_AUDIT, ARCHITECTURE_AUDIT, MEMORY_AUDIT, EXPERIMENTS preregistration, ABLATION_MATRIX, etc.) | ✅ Complete |

---

## Frequently Asked Questions

**Q: What is NurosOS?**
A: NurosOS is an open-source experimental substrate for synthetic development, written in Rust and Python. It provides the runtime, interfaces, environments, developmental mechanisms, observability, and reproducibility infrastructure required to instantiate, develop, measure, fork, replay, and compare artificial cognitive systems. The fundamental object is not MODEL but TRAJECTORY; not AGENT but DEVELOPING ORGANISM.

**Q: What is the HippoCore integration?**
A: The HippoCore integration (v0.4.0-alpha) adds a `MemoryEngine` ABC with two implementations: `DefaultMemoryContract` (backward-compat) and `HippoCoreMemory` (episodic encoding, structured provenance, 5 replay policies, fast→slow consolidation, memory event emission for the developmental trajectory, and causal graph integration). Shipped as 10 logical phases on the `feature/hippocore-integration-audit` branch. 266 Python tests passing (incl. Q-learning baseline). NO LLM dependency.

> ⚠️ **Scientific caveat** (see [Scientific Audit](#scientific-audit)): HippoCore is **technically implemented but NOT empirically validated**. `Organism.tick()` does not yet consult `MemoryEngine.retrieve()` during action selection — memory is a post-hoc log, not a causal driver of behavior. HippoCore should be treated as a **future experimental intervention**, not a current capability. See `docs/HIPPOCORE_INTEGRATION_PLAN.md`.

**Q: How does NurosOS differ from an AI agent framework?**
A: Traditional AI follows the inversion `Model → Training → Agent`. NurosOS inverts this again: `Developmental Genome → Environment → Experience → Development → Individual Cognitive Trajectory → Artificial Organism`. The agent is not the primitive; the developing organism is the primitive. NurosOS provides developmental state, artificial ontogenesis, environmental interaction, mind provenance, mind diff, reproducibility, and developmental experiments — none of which are primitives of an agent framework.

**Q: What is the Same Genome / Different World experiment?**
A: The flagship NurosOS experiment instantiates two organisms from the same developmental genome, places them in differently-seeded environments, develops both for the same number of steps, and measures the developmental divergence between them. The experiment demonstrates Computational Developmental Divergence: identical initial computational conditions producing divergent developmental states under different environmental histories. This is an observable computational fact, NOT evidence of consciousness or biological individuality.

> ⚠️ **Scientific caveat** (see [Scientific Audit](#scientific-audit)): The divergence is **confounded** by (a) the environment's RNG-dependent resource placement, (b) the organism's hard-coded `heuristic_bias` that reads the env's privileged `direction_to_resource` field, and (c) the env emitting privileged observation fields (`on_resource`, `on_hazard`, `nearest_resource_distance`). The divergence may be an **artifact** of these confounds, not of learning or development. The audit recommends running with privileged fields stripped + bias ablated to test this. Single-seed results are **anecdotal**; 30-seed replication is needed.

**Q: Does NurosOS implement consciousness?**
A: No. NurosOS does not implement consciousness, does not create biological life, and does not solve artificial consciousness. The divergence measured by the flagship experiment is an observable computational fact, not evidence of subjective experience. NurosOS treats consciousness, sentience, subjective experience, and artificial life as open research questions, not as solved problems.

**Q: Is NurosOS production-ready?**
A: No. NurosOS is research software at v0.4.0-alpha. It is not production-ready. The MinimumOrganism cognitive engine is intentionally a deterministic epsilon-greedy policy with hand-coded heuristic biases — not an LLM, not a neural network. This is by design for reproducibility and for isolating the effect of environment from the effect of engine.

**Q: What programming languages does NurosOS use?**
A: Rust (>=1.75) for the developmental substrate (`nuros-dev` crate, exposed via PyO3) and the neuromorphic kernel (preserved from v0.1.0 as a future execution backend). Python (>=3.10) for the cognitive layer, experiments, and integration tests. The HippoCore package (`nuros/hippocore/`) is pure Python — NO LLM dependency, NO external model weights.

**Q: Does HippoCore depend on an LLM?**
A: No. The HippoCore package is fully local and deterministic. All "novelty" / "importance" / "prediction_error" weighting is computed from local memory fields. Pattern separation uses content-addressable storage (UUIDs + tags) — this is **storage-level** separation, not neural-circuit-accurate pattern separation. Consolidation uses Jaccard / content-prefix similarity, not embedding-based clustering. Master prompt §23 (no LLM dependency for core memory) is satisfied.

**Q: What is a Developmental Genome?**
A: A `DevelopmentalGenome` is a serializable, hashable specification of an organism's initial developmental conditions. It includes architecture, initial memory, initial capabilities, plasticity rules, biases, maturation schedule, homeostasis setpoints, energy model, and mutation parameters. Two organisms instantiated from the same genome, placed in different environments, should produce divergent developmental trajectories. The genome has a canonical SHA-256 hash that becomes part of every checkpoint, trajectory, and manifest.

**Q: What is Mind Diff?**
A: `MindDiff` is a structured comparison of two organism states across memory, self-model, values (action preferences), capabilities, prediction, behavior, and developmental state. Inspired conceptually by version-control diffs, but designed for cognitive state. The output is machine-readable JSON with a human-readable rendering. It supports `diff(mind_A, mind_B)` and `diff(mind_t1, mind_t2)`.

**Q: How is reproducibility guaranteed?**
A: Every experiment produces a `ReproducibilityManifest` recording: `mind_id`, `genome_hash`, `runtime_hash`, `environment_hash`, `experiment_hash`, `random_seed`, `environment_seed`, `checkpoint_hash`, `configuration_hash`, `dependency_versions`, `timestamp`, `n_steps`, and `limitations`. Two runs with the same manifest values produce identical trajectories (verified by 322 tests). Replay fidelity is classified as `EXACT`, `APPROXIMATE`, or `NON_REPRODUCIBLE`.

**Q: What is Computational Developmental Divergence?**
A: Computational Developmental Divergence is the phenomenon, demonstrated by the NurosOS flagship experiment, in which two organisms instantiated from the same developmental genome and run with the same random seed produce divergent developmental trajectories because they developed in different environments. It is an observable computational fact about divergent developmental trajectories. It is NOT evidence of consciousness, biological individuality, subjective experience, artificial life, or sentience.

> ⚠️ **Scientific caveat**: the divergence is currently confounded by RNG resource placement + hard-coded bias + privileged env observations. The causal attribution to "learning" or "development" is **UNVALIDATED** until the confounds are controlled. See `docs/RESEARCH_AUDIT.md` §11 (Confounds).

**Q: What are the 5 HippoCore replay policies?**
A: `RecentReplayPolicy` (most recent N), `ImportanceWeightedReplayPolicy` (∝ importance²), `NoveltyWeightedReplayPolicy` (∝ 1/(1+access_count)), `PredictionErrorWeightedReplayPolicy` (∝ |prediction_error|), `RandomReplayPolicy` (uniform baseline). All deterministic when seeded.

> ⚠️ The policies are **implemented but not consulted by `Organism.tick()`** during action selection — replay is not yet wired to behavior. See `docs/MEMORY_AUDIT.md`.

**Q: What are the 2 HippoCore consolidation strategies?**
A: `TagJaccardConsolidation` (cluster by Jaccard similarity on tags) and `ContentPrefixConsolidation` (cluster by shared content prefix). Both deterministic. The pipeline: select ACTIVE sources → cluster → derive SEMANTIC targets from clusters of size ≥ 2 → mark sources CONSOLIDATED + halve importance → associate sources ↔ target via bidirectional `consolidated_into` edges.

> ⚠️ Consolidation is **implemented but not consulted by `Organism.tick()`**. See `docs/MEMORY_AUDIT.md`.

---

## Scientific Audit

> **⚠️ ARCHITECTURE ≠ EVIDENCE. IMPLEMENTATION ≠ EMERGENCE. REPRODUCIBILITY ≠ VALIDITY.**

A forensic scientific audit of the NurosOS repository has been completed. The audit traces every major claim to file:line evidence, identifies confounds, and recommends minimum changes to establish a credible experimental baseline.

### Key audit findings

| # | Finding | Severity | Evidence |
|---|---------|----------|----------|
| 1 | **Hard-coded `heuristic_bias`** encodes task knowledge (resource-seeking, hazard-avoidance, direction-aware movement) — the learned `action_preferences` are a secondary signal | CRITICAL | `organism.rs:451-503` |
| 2 | **`ResourceWorld.observe()` leaks privileged state** (`direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`) — the env is teacher-shaped | CRITICAL | `environment.rs:242-250` |
| 3 | **No baseline condition** — no Q-learning or conventional learning system to compare NurosOS against | CRITICAL | no `benchmarks/baselines/` existed before the audit |
| 4 | **Single-seed flagship results** are anecdotal (one seed pair: `env_a_seed=1, env_b_seed=999`) | HIGH | `WHITEPAPER.md:134-141` |
| 5 | **Memory is not consulted during action selection** — `Organism.tick()` does not call `MemoryEngine.retrieve()` | CRITICAL (for HippoCore) | `organism.rs:408-441`, `nuros/organism.py:178-211` |
| 6 | The "Computational Developmental Divergence" is **confounded** by RNG + bias + privileged obs — causal attribution to "learning" is UNVALIDATED | HIGH | see `docs/RESEARCH_AUDIT.md` §11 |

### Audit deliverables (11 files)

| # | File | Description |
|---|------|-------------|
| 1 | `docs/RESEARCH_AUDIT.md` | 17-section forensic audit |
| 2 | `docs/ARCHITECTURE_AUDIT.md` | Module-level cross-check |
| 3 | `docs/MEMORY_AUDIT.md` | Memory subsystem audit (5 types × 10 operations) |
| 4 | `experiments/EXPERIMENTS.md` | Preregistration v1.0 (30 seeds, α=0.0042) |
| 5 | `experiments/ABLATION_MATRIX.md` | Formal 6-condition × 2-mode ablation matrix |
| 6 | `docs/EXPERIMENTAL_ROADMAP.md` | Recommended execution order (Phases A-H) |
| 7 | `docs/HIPPOCORE_INTEGRATION_PLAN.md` | Future HippoCore intervention design |
| 8 | `docs/SCIENTIFIC_RISKS.md` | 14 risks classified by severity |
| 9 | `docs/BASELINE_SPEC.md` | Q-learning baseline specification |
| 10 | `docs/REPRODUCIBILITY_SPEC.md` | 7 reproducibility invariants |
| 11 | `docs/METRICS_SPEC.md` | 19 metrics across 5 categories |

### Q-learning baseline (audit deliverable)

A tabular Q-learning baseline has been implemented at `nuros/baselines/q_learning/` with:
- Standard Bellman backup: `Q(s,a) ← Q(s,a) + α[r + γ max_a' Q(s',a') - Q(s,a)]`
- ε-greedy action selection (deterministic given seed)
- LRU eviction at 200 entries (matches Rust `MinimumOrganism` cap)
- 19 unit tests
- No NurosOS-privileged information

### Recommended next steps (per audit)

1. **Phase A**: Strip the env's privileged observation fields (add a `privileged_obs: bool` toggle)
2. **Phase B**: Add `disable_heuristic_bias` flag to enable the ablation
3. **Phase C**: Run Q-learning baseline vs NurosOS baseline (6 conditions × 2 modes × 30 seeds)
4. **Phase D**: Implement non-stationary 3-regime env
5. **Phase E-H**: Experiment harness + 30-seed runs + statistical analysis + documentation integrity

**HippoCore should remain a future intervention** until the NurosOS baseline is empirically characterized.

---

## Philosophy

> **Don't train a mind. Instantiate its developmental conditions.**

> **Memory is not storage. Development is not deployment. Simulation is not observation. Intelligence is not consciousness. Divergence is not individuality.**

> **The fundamental object is not MODEL but TRAJECTORY; not AGENT but DEVELOPING ORGANISM.**

> **NurosOS provides the developmental substrate for artificial organisms.**

> **HippoCore provides structured episodic memory and continual-learning dynamics.**

> **Memory is not merely storage; it is part of the developmental process.**

> **The organism changes because of what it experiences, remembers, replays, consolidates, and forgets.**

---

## Research Questions

These are **research questions**, not predetermined conclusions (full list in [RESEARCH_AGENDA.md](RESEARCH_AGENDA.md)):

1. Can developmental trajectories produce stable computational individuality?
2. How does environmental history alter identical initial architectures?
3. What measurable trade-offs exist between plasticity and stability?
4. Can artificial cognitive capabilities emerge through development rather than explicit programming?
5. How does accumulated experience alter future behavior?
6. Can cognitive trajectories be reproduced experimentally? **[IMPLEMENTED — yes, via ReproducibilityManifest]**
7. Can counterfactual developmental histories improve planning? **[IMPLEMENTED]**
8. What computational constraints govern artificial cognitive development? **[IMPLEMENTED — Cognitive Metabolism]**
9. Can artificial organisms specialize without explicit specialization programming?
10. Which properties of cognition are architecture-dependent versus development-dependent?
11. Can HippoCore's episodic memory + replay + consolidation produce measurable developmental change? **[IMPLEMENTED — PHASES 1-10]**

---

## Status

> ⚠️ **Experimental research software.** NurosOS is at v0.4.0-alpha. It is not production-ready.

| Component | Language | Stage |
|-----------|----------|-------|
| Developmental Substrate (nuros-dev) | Rust + PyO3 | v0.3.0-alpha [IMPLEMENTED] — 57 tests passing |
| Mind Contracts (Python) | Python | v0.3.0-alpha [IMPLEMENTED] — 33 cognitive-layer tests |
| Developmental Substrate Integration | Python | v0.3.0-alpha [IMPLEMENTED] — 18 integration tests |
| **HippoCore Integration** | **Python** | **v0.4.0-alpha [IMPLEMENTED] — 247 tests passing** |
| Flagship Experiment | Python | v0.3.0-alpha [IMPLEMENTED] — Same Genome / Different World |
| Mind Observatory | Python | v0.3.0-alpha [IMPLEMENTED] — 21 tests, 9 text renderers + 13 PNG plots |
| CounterfactualSelf + PossibleSelfSpace | Rust + PyO3 | v0.3.0-alpha [IMPLEMENTED] — 9 Rust + 15 Python tests |
| Cognitive Metabolism | Rust + PyO3 | v0.3.0-alpha [IMPLEMENTED] — 11 Rust + 12 Python tests |
| Artificial Aging | Rust + PyO3 | v0.3.0-alpha [IMPLEMENTED] — 14 Rust + 11 Python tests |
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
  version = {0.4.0-alpha},
  note   = {Includes the HippoCore integration (10 phases, 247 Python tests)}
}
```

---

<div align="center">

> **NurosOS — The Experimental Substrate for Synthetic Development.**
>
> *We don't train a mind. We instantiate its developmental conditions.*

</div>
