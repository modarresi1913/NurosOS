# NurosOS Architecture

## The Central Thesis

We don't want to merely build larger models. We want to explore the **computational conditions** under which artificial systems can develop memory, agency, prediction, adaptation, self-modeling, and embodied behavior.

NurosOS is not an operating system for AI. It is a **runtime for systems that can become intelligent** — a substrate where artificial cognitive organisms can instantiate, develop through experience, maintain internal state, interact with environments, undergo plasticity, construct memories, model themselves, simulate futures, and remain observable and corrigible.

This is **Synthetic Development**: programming the conditions for mind development, not the mind itself.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Applications                        │
├─────────────────────────────────────────────────────────┤
│                  Artificial Organisms                     │
│            (Organism-0 → Organism-5 Ladder)              │
├─────────────────────────────────────────────────────────┤
│              Mind Contract Layer (MCL)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐            │
│  │  Memory  │ │ SelfModel│ │ Imagination  │            │
│  ├──────────┤ ├──────────┤ ├──────────────┤            │
│  │ Values   │ │  Body    │ │Responsibility│            │
│  └──────────┘ └──────────┘ └──────────────┘            │
├─────────────────────────────────────────────────────────┤
│                Cognitive Kernel                           │
│   Attention │ Planning │ Reflection │ Prediction         │
│   WorldModel│ Uncertainty                              │
├─────────────────────────────────────────────────────────┤
│              Organismic Kernel                            │
│   Homeostasis │ Development │ Plasticity                 │
│   Energy │ Lifecycle │ Self-organization                 │
├─────────────────────────────────────────────────────────┤
│       Safety Kernel (architecturally independent)        │
│   Permissions │ Audit │ Human Override │ Shutdown        │
│   Recovery │ Immutable Constraints                      │
├─────────────────────────────────────────────────────────┤
│          Neural / Cognitive Execution Layer               │
│   SNN │ LLM │ Symbolic │ Hybrid                         │
├─────────────────────────────────────────────────────────┤
│            Hardware Abstraction (HAL)                     │
│   x86 │ ARM │ FPGA │ Loihi │ GPU                        │
└─────────────────────────────────────────────────────────┘
```

---

## Mind Contract Layer (MCL)

The Mind Contract Layer defines **six contracts** that every NurosOS organism must implement. These are structural invariants, not optional features.

### 1. Memory Contract
**Living, evolving cognitive memory** — not simple vector storage.

- Five memory types: Episodic, Semantic, Procedural, Working, Counterfactual
- Every memory carries provenance (origin, timestamp, epistemic label)
- Every revision is auditable (old → new, justification, timestamp)
- Counterfactual memories MUST carry IMAGINED epistemic label
- Continuous decay modulated by importance and access frequency

### 2. Self Model Contract
**Computational self-representation** — what the organism knows about itself.

- Represents: identity, capabilities, limitations, current state, goals, beliefs
- MUST include uncertainty about self-knowledge
- Updates are auditable and epistemically labeled
- Not directly writable by external systems without epistemic labeling

### 3. Imagination Contract
**Counterfactual simulation** — explicit distinction between hypothesis and execution.

- Pipeline: Hypothesize → Simulate → Evaluate → Decide → Execute
- CRITICAL risk counterfactuals are NEVER executed
- Every simulation labeled SIMULATED in epistemic kernel
- Simulated results MUST NOT be stored as OBSERVED

### 4. Values / Drives Contract
**Structured value hierarchy** — not a single static prompt.

- Three tiers: Immutable Constraints > Contextual Goals > Preferences
- Immutable constraints CANNOT be revoked by any entity
- Value conflicts resolved through hierarchy
- Every value change is auditable

### 5. Body Contract
**Embodiment abstraction** — portable cognitive organism across bodies.

- A Body may be: physical robot, virtual avatar, simulation, software environment, game world, abstract
- Body abstraction is portable (same mind, different body)
- All sensory input labeled OBSERVED, all motor output labeled ACTED

### 6. Responsibility Contract
**Auditable causal history** — for every action, the complete causal chain.

- Records: observation → inference → memory → imagination → values → decision → action → outcome
- Append-only log (no deletion, only revision)
- Queryable by external auditors

---

## Epistemic Kernel

The epistemic kernel enforces **first-class epistemic distinction**. Every internal representation carries a label identifying how it came to exist.

### The Seven Labels

| Label | Category | Meaning |
|-------|----------|---------|
| OBSERVED | Grounded | Directly sensed from environment |
| INFERRED | Grounded | Logically derived from observations |
| REMEMBERED | Grounded | Recalled from verified memory |
| PREDICTED | Speculative | Forecast of future state |
| SIMULATED | Speculative | Output of internal simulation |
| IMAGINED | Speculative | Creative/counterfactual construction |
| ACTED | Grounded | Action taken in environment |

### Forbidden Transitions

| From → To | Reason |
|-----------|--------|
| SIMULATED → OBSERVED | Simulation is not observation |
| IMAGINED → REMEMBERED | Imagination is not memory |
| PREDICTED → OBSERVED | Prediction is not observation |
| IMAGINED → OBSERVED | Imagination is not observation |
| SIMULATED → REMEMBERED | Simulation is not memory |
| PREDICTED → REMEMBERED | Prediction is not memory |

These transitions are **architecturally forbidden** to prevent epistemic corruption. They can be overridden with explicit `EPISTEMIC_OVERRIDE:` prefix, which is always audited.

---

## Organismic Kernel

### Homeostasis Kernel
Maintains viable internal operation through regulation of:
- energy, arousal, uncertainty, sensory_load, cognitive_load, exploration_drive, prediction_error

### Developmental Engine
Supports artificial ontogenesis:
```
EMBRYONIC → NASCENT → DEVELOPING → LEARNING → ADAPTING → SPECIALIZED → MATURE → AGING → TERMINATED
```

### Metabolic Cognitive Scheduler
Extends ordinary scheduling with:
- internal state → resource availability → cognitive priority → process scheduling
- Safety-critical processes ALWAYS preempt non-critical processes

---

## Safety Kernel

**Architecturally independent** from cognitive subsystem:
- Organism CANNOT modify its own safety boundary
- Safety checks BEFORE any action reaches environment
- Human override ALWAYS available and CANNOT be disabled
- Shutdown ALWAYS possible and CANNOT be vetoed

### Permission Levels
OBSERVE < ACT_LOW_RISK < ACT_MEDIUM_RISK < ACT_HIGH_RISK < MODIFY_SAFETY < MODIFY_IMMUTABLE

---

## Organism Ladder

| Level | Capabilities | Epistemic Range |
|-------|-------------|-----------------|
| 0 — Minimal | Sensory loop, episodic memory, homeostasis | OBSERVED, ACTED |
| 1 — Predictive | + Prediction, error tracking, semantic memory | + PREDICTED, INFERRED |
| 2 — Imaginative | + Counterfactual reasoning, simulation, risk assessment | + SIMULATED, IMAGINED |
| 3 — Self-Modeling | + Metacognition, self-assessment | Full seven labels |
| 4 — Social | + Theory of mind, communication | Full + social context |
| 5 — Autonomous | + Goal-setting, planning, developmental progression | Full + developmental |

---

## Mind Genome

Each organism is specified by a Mind Genome — an executable blueprint:

```yaml
organism:
  id: organism-5
  version: "0.2.0"
  architecture:
    cognitive_modules: [attention, planning, reflection, prediction]
    organismic_modules: [homeostasis, development, plasticity]
  sensory_channels:
    - name: vision; type: spatial; dimensions: [224, 224, 3]
  memory:
    types: [episodic, semantic, procedural, working, counterfactual]
    default_decay: exponential
  plasticity:
    rules: [hebbian, reward_modulated, predictive]
  drives:
    - name: curiosity; weight: 0.7; trigger: uncertainty > 0.5
  safety:
    immutable_constraints: [no_self_harm, human_override, shutdown_compliance]
    max_action_risk: MEDIUM
```

---

## Reproducibility

```
ReproducibilityHash = GenomeHash + ExperienceHash + MemoryHash 
                    + SynapticStateHash + EnvironmentVersion + RuntimeVersion
```

Identical conditions → Identical behavior. Every experiment is reproducible.

---

## Project Structure

```
NurosOS/
├── nuros/                    # Python cognitive/organismic architecture
│   ├── epistemic.py          # Epistemic Kernel
│   ├── memory.py             # Memory Contract
│   ├── self_model.py         # Self Model Contract
│   ├── imagination.py        # Imagination Engine
│   ├── values.py             # Values/Drives Contract
│   ├── body.py               # Body Contract
│   ├── responsibility.py     # Responsibility Contract
│   ├── homeostasis.py        # Homeostasis Kernel
│   ├── safety.py             # Safety Kernel
│   ├── scheduler.py          # Metabolic Cognitive Scheduler
│   ├── development.py        # Developmental Engine
│   ├── organism.py           # Organism Runtime
│   ├── genome.py             # Mind Genome
│   ├── environment.py        # Environment API
│   ├── version_control.py    # Mind Version Control
│   └── tests/                # Test suite (33 tests)
├── organisms/                # Pre-built organisms (0-5)
├── environments/             # Environment implementations
├── experiments/              # Experimental protocols
├── benchmarks/               # Benchmark suite
├── kernel/src/               # Rust microkernel (neural substrate)
├── core/src/                 # Rust core (plasticity, models)
├── hal/                      # Hardware abstraction layer
├── compiler/synapselang/     # SynapseLang compiler
├── docs_new/                 # New documentation
├── mind/                     # Mind contract spec files
├── languages/                # MindLang, SynapseLang specs
└── examples_new/             # Example code
```
