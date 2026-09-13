<div align="center">

# NurosOS

### A Runtime for Synthetic Minds and Artificial Organisms

*We don't want to merely build larger models. We want to explore the computational conditions under which artificial systems can develop memory, agency, prediction, adaptation, self-modeling, and embodied behavior.*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0--alpha-orange.svg?style=flat-square)](https://github.com/modarresi1913/NurosOS/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75+-ce422b.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-yellow.svg?style=flat-square)](#status)
[![Tests](https://img.shields.io/badge/tests-33%20passing-brightgreen.svg?style=flat-square)](#testing)

**[Overview](#overview) · [Architecture](#architecture) · [Mind Contracts](#mind-contracts) · [Quickstart](#quickstart) · [Organisms](#organisms) · [Roadmap](#roadmap) · [Philosophy](#philosophy)**

</div>

---

## Overview

NurosOS is an **open, modular, event-driven substrate** for experimenting with the computational conditions under which artificial systems can develop memory, agency, prediction, adaptation, self-modeling, and embodied behavior.

> **NurosOS is not an operating system for AI. It is a runtime for systems that can become intelligent.**

### What NurosOS Is

- An **executable substrate** in which artificial cognitive organisms can be instantiated, developed, embodied, evaluated, forked, and experimentally studied
- A **modular architecture** with clear separation between neural substrate, cognitive kernel, organismic kernel, safety kernel, and mind contracts
- A **research infrastructure** where every extraordinary claim ships with a reproducible experiment

### What NurosOS Is NOT

- ❌ A claim of machine consciousness
- ❌ A claim of artificial life
- ❌ A replacement for neuroscience
- ❌ A general-purpose LLM agent framework
- ❌ A production deployment platform

NurosOS is **experimental research infrastructure**.

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

## Quickstart

```bash
git clone https://github.com/modarresi1913/NurosOS.git
cd NurosOS

# Run the test suite
python -m pytest nuros/tests/ -v

# Create and run an organism
python -c "
from nuros.organism import Organism, OrganismConfig
from nuros.environment import GridWorld

env = GridWorld(10, 10)
env.reset()

org = Organism(OrganismConfig(name='explorer', environment=env))
org.birth()

for i in range(100):
    result = org.tick()
    if i % 25 == 0:
        print(f'Tick {i}: stage={result[\"stage\"]}, hash={org.state_hash()}')

print('Snapshot:', org.snapshot())
"
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
# Run all 33 tests
python -m pytest nuros/tests/ -v

# Run specific test class
python -m pytest nuros/tests/test_core.py::TestEpistemicKernel -v
python -m pytest nuros/tests/test_core.py::TestSafetyKernel -v
python -m pytest nuros/tests/test_core.py::TestOrganism -v
```

All 33 tests passing ✅

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
