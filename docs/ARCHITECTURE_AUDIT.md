# ARCHITECTURE AUDIT — NurosOS

> Companion to `docs/RESEARCH_AUDIT.md`. This document audits the *architecture*
> (not the science). It cross-checks claims in README/ARCHITECTURE/ROADMAP/
> RESEARCH_AGENDA/WHITEPAPER/DEVELOPMENTAL_SUBSTRATE/experiments against the
> actual code, and labels every architectural claim with its current status.

---

## Status labels (master prompt PHASE 19)

Every claim below is labeled exactly one of:

- `IMPLEMENTED` — built, code present, file:line evidence.
- `IMPLEMENTED AND TESTED` — built + has automated test coverage.
- `IMPLEMENTED BUT NOT EMPIRICALLY VALIDATED` — built + tested at unit level, but no scientific experiment demonstrates the claim.
- `PARTIALLY IMPLEMENTED` — some code present, some missing.
- `ARCHITECTURALLY SPECIFIED` — design described in docs, no code.
- `PROPOSED` — designed, planned, no code yet.
- `UNVALIDATED` — claim made in docs, no supporting evidence.
- `UNSUPPORTED` — claim made in docs, contradicted by code.

---

## 1. Architecture claims vs. code

| Architectural claim | Source doc | File:line evidence | Status |
|---------------------|-----------|--------------------|----|
| Two-layer substrate (Rust developmental + Python cognitive) | `ARCHITECTURE.md:130-135`, `README.md:developmental-substrate` | `nuros-dev/src/lib.rs` exposes PyO3 module `nuros._dev`; `nuros/` Python package implements the cognitive layer | `IMPLEMENTED` |
| Three-layer substrate (adds HippoCore) | `README.md:architecture`, `docs/HIPPOCORE_INTEGRATION.md` | `nuros/hippocore/` package exists with all PHASE 3-8 mechanisms | `IMPLEMENTED` (on feature branch; not activated by default) |
| Six Mind Contracts (Memory / SelfModel / Imagination / Values / Body / Responsibility) | `ARCHITECTURE.md:mind-contracts`, `mind/memory/SPEC.md` | `nuros/memory.py`, `nuros/self_model.py`, `nuros/imagination.py`, `nuros/values.py`, `nuros/body.py`, `nuros/responsibility.py` — all present | `IMPLEMENTED` |
| Epistemic Kernel (7 labels, forbidden transitions) | `ARCHITECTURE.md:epistemic-kernel`, `nuros/epistemic.py` | 7 labels (OBSERVED/INFERRED/REMEMBERED/PREDICTED/SIMULATED/IMAGINED/ACTED) + 6 forbidden transitions enforced | `IMPLEMENTED AND TESTED` (33 tests in `test_core.py`) |
| Organismic Kernel (Homeostasis, Development, Plasticity, Energy, Lifecycle, Self-organization) | `ARCHITECTURE.md:organismic-kernel` | `nuros/homeostasis.py`, `nuros/development.py`, `nuros/scheduler.py`, `nuros-dev/src/lifecycle.rs`, `nuros-dev/src/aging.rs` | `IMPLEMENTED` (partial: "Self-organization" is `ARCHITECTURALLY SPECIFIED`) |
| Safety Kernel architecturally independent | `ARCHITECTURE.md:safety-kernel`, `nuros/safety.py` | `nuros/safety.py` is a separate module; safety checks happen BEFORE any action reaches environment | `IMPLEMENTED AND TESTED` |
| Organism Ladder (Organism-0 through Organism-5) | `ARCHITECTURE.md:organism-ladder`, `organisms/organism_0.py` ... `organisms/organism_5.py` | Six Python files present | `PARTIALLY IMPLEMENTED` (audit did not verify each ladder level's full contract compliance) |
| Mind Genome (YAML spec, hash) | `ARCHITECTURE.md:mind-genome`, `nuros/genome.py`, `nuros-dev/src/genome.rs` | Two parallel implementations: Python `nuros/genome.py` (superseded per README) and Rust `nuros-dev/src/genome.rs` (canonical). | `IMPLEMENTED AND TESTED` (Rust side; Python side deprecated but retained) |
| Reproducibility invariant: GenomeHash + ExperienceHash + MemoryHash + SynapticStateHash + EnvironmentVersion + RuntimeVersion | `ARCHITECTURE.md:reproducibility` | `ReproducibilityManifest` (`telemetry.rs:168-197`) captures 10 of 6 listed components — but no separate `ExperienceHash` or `SynapticStateHash` (those are subsumed into `checkpoint_hash`) | `IMPLEMENTED` (with renamed/merged fields) |
| HAL with drivers (x86/ARM/FPGA/Loihi/GPU) | `ARCHITECTURE.md:hal`, `hal/drivers/` | Five Rust driver directories exist; `hal/src/lib.rs` + `hal/src/energy.rs` | `PARTIALLY IMPLEMENTED` (v0.1.0 scaffold; not exercised by developmental substrate) |
| Cognitive Kernel (Attention, Planning, Reflection, Prediction, WorldModel, Uncertainty) | `ARCHITECTURE.md:cognitive-kernel` | Only `Prediction` and (loosely) `Reflection` are present (in `MinimumOrganism::tick`); no Attention/Planning/WorldModel/Uncertainty modules | `ARCHITECTURALLY SPECIFIED` |
| Neural/Cognitive Execution Layer (SNN/LLM/Symbolic/Hybrid) | `ARCHITECTURE.md:execution-layer` | v0.1.0 SNN scaffold in `kernel/`, `core/`; LLM explicitly not used; Symbolic and Hybrid are `PROPOSED` | `PARTIALLY IMPLEMENTED` (SNN scaffold only; not connected to developmental substrate) |

---

## 2. Module-level audit

### 2.1 `nuros-dev/src/` (Rust developmental substrate)

| Module | Lines | Status | Audit notes |
|---|---|---|---|
| `lib.rs` | ~700 (persisted preview) | `IMPLEMENTED` | PyO3 bindings + flagship runner. Module map documented in module-level doc comment. |
| `hash.rs` | (small) | `IMPLEMENTED AND TESTED` | Canonical JSON + SHA-256. Used as single source of truth for all hashes. |
| `genome.rs` | (medium) | `IMPLEMENTED AND TESTED` | `DevelopmentalGenome` with architecture, plasticity, maturation, energy, biases, mutation_parameters. JSON round-trip preserves hash. |
| `state.rs` | 267 | `IMPLEMENTED AND TESTED` | 14 scalar fields + capability map. L1 distance metric (`state.rs:162-187`). Canonical hash. |
| `lifecycle.rs` | (medium) | `IMPLEMENTED AND TESTED` | Auditable state machine, terminal state enforced. |
| `environment.rs` | 595 | `IMPLEMENTED AND TESTED` for `ResourceWorld` and `ChangingWorld` — **but emits privileged observation fields (see §11 of RESEARCH_AUDIT.md)**. Confound: env is teacher-shaped. |
| `organism.rs` | 711 | `IMPLEMENTED AND TESTED` — **but contains hard-coded `heuristic_bias` (lines 451-503) that confounds the learning claim (see §9 of RESEARCH_AUDIT.md)**. |
| `trajectory.rs` | 422 | `IMPLEMENTED AND TESTED` | `DevelopmentalTrajectory` + `DevelopmentalDivergence` with 5 distance metrics + per-step CSV export. |
| `checkpoint.rs` | 318 | `IMPLEMENTED AND TESTED` | `MindCheckpoint` + `ReplayFidelity::{Exact, Approximate, NonReproducible}`. **Gap: does NOT capture Python-side memory contents.** |
| `diff.rs` | (medium) | `IMPLEMENTED AND TESTED` | `MindDiff` across memory, self-model, values, capabilities, prediction, behavior, developmental state. |
| `causality.rs` | 271 | `IMPLEMENTED AND TESTED` at the module level — **but `DevelopmentalCausalityGraph` is never instantiated by `MinimumOrganism::tick`** (audit Appendix B.8). `EventKind::MemoryUpdate` defined but never produced. |
| `counterfactual.rs` | 553 | `IMPLEMENTED AND TESTED` | `CounterfactualSelf` with `what_if_environment` and `what_if_actions`. SIMULATED+COUNTERFACTUAL labels enforced. |
| `metabolism.rs` | 513 | `IMPLEMENTED AND TESTED` | 7 budgets + 9 operations + VoI rule. **No experiment measures whether metabolism improves decisions** — `UNVALIDATED` as a research claim. |
| `aging.rs` | 426 | `IMPLEMENTED AND TESTED` | 5 aging dimensions with configurable rates/onsets/floors. **No experiment measures whether aging affects future cognition** — `UNVALIDATED` as a research claim. |
| `telemetry.rs` | 426 | `IMPLEMENTED AND TESTED` | 24-field `TelemetryRecord`, JSONL+CSV export, `ReproducibilityManifest` with 13 fields. |

### 2.2 `nuros/` (Python cognitive layer)

| Module | Status | Audit notes |
|---|---|---|
| `epistemic.py` | `IMPLEMENTED AND TESTED` | 7 labels, 6 forbidden transitions, override mechanism. |
| `memory.py` | `IMPLEMENTED AND TESTED` | PHASE 2 stabilization: refactored to `DefaultMemoryContract(MemoryEngine)` + deprecated `MemoryContract` alias. Soft-delete fix. Checkpoint/restore. iter_all(). |
| `memory_engine.py` | `IMPLEMENTED AND TESTED` | `MemoryEngine` ABC with 10 abstract methods. PHASE 2. |
| `memory_provenance.py` | `IMPLEMENTED AND TESTED` | `MemoryProvenance` dataclass. PHASE 4. |
| `memory_events.py` | `IMPLEMENTED AND TESTED` | `MemoryEventKind` (6 kinds) + `MemoryEventEmitter` event bus. PHASE 7. |
| `causal_graph.py` | `IMPLEMENTED AND TESTED` | `PythonCausalGraph` + `EventKind` (17 variants). PHASE 8. |
| `self_model.py` | `IMPLEMENTED` | Self Model Contract. |
| `imagination.py` | `IMPLEMENTED` | Imagination Engine with safety gates. |
| `values.py` | `IMPLEMENTED` | Three-tier value hierarchy. |
| `body.py` | `IMPLEMENTED` | Body Contract (portable embodiment). |
| `responsibility.py` | `IMPLEMENTED` | Auditable causal history. |
| `homeostasis.py` | `IMPLEMENTED` | Homeostasis Kernel. |
| `safety.py` | `IMPLEMENTED AND TESTED` | Safety Kernel, architecturally independent. |
| `scheduler.py` | `IMPLEMENTED` | Metabolic Cognitive Scheduler. |
| `development.py` | `IMPLEMENTED` | Synthetic Development Runtime. |
| `organism.py` | `IMPLEMENTED` | `Organism` runtime; PHASE 2 added `OrganismConfig.memory_engine` selector; PHASE 2 fix to `state_hash()` to include memory content hash. **Gap: `Organism.tick()` does not consult `MemoryEngine.retrieve()` during action selection.** |
| `environment.py` | `IMPLEMENTED` | Environment API (Python side). |
| `genome.py` | `PARTIALLY IMPLEMENTED` (superseded) | README flags as superseded by `nuros-dev`. Still ships. |
| `version_control.py` | `PARTIALLY IMPLEMENTED` (superseded) | Same. |
| `observatory.py` | `IMPLEMENTED AND TESTED` | 9 text renderers + 13 PNG plots + CLI. 21 tests. |

### 2.3 `nuros/hippocore/` (HippoCore integration, on feature branch)

| Module | Status | Audit notes |
|---|---|---|
| `__init__.py` | `IMPLEMENTED` | Re-exports all HippoCore classes. |
| `memory_engine.py` | `IMPLEMENTED AND TESTED` | `HippoCoreMemory(MemoryEngine)`. PHASE 3 adapter + PHASE 4 encode_episode + PHASE 5 replay + PHASE 6 consolidate + PHASE 7 events + PHASE 8 causal graph wiring. 247 tests passing. **NO LLM dependency.** |
| `replay_policy.py` | `IMPLEMENTED AND TESTED` | 5 policies, all deterministic when seeded. |
| `consolidation.py` | `IMPLEMENTED AND TESTED` | 2 strategies (`TagJaccardConsolidation`, `ContentPrefixConsolidation`). Both deterministic. |

### 2.4 `experiments/` and `benchmarks/`

| Module | Status | Audit notes |
|---|---|---|
| `experiments/same_genome_different_world.py` | `IMPLEMENTED` | Flagship experiment runner. Produces 13 artifacts. **Single-seed results only — anecdotal per master prompt PHASE 8.** |
| `experiments/counterfactual_demo.py` | `IMPLEMENTED` | Demo of `CounterfactualSelf`. |
| `experiments/aging_demo.py` | `IMPLEMENTED` | Aging model comparison. |
| `experiments/metabolism_demo.py` | `IMPLEMENTED` | Metabolism sweep + VoI table. |
| `experiments/memory/decay_experiment.py` | `IMPLEMENTED` (PHASE 2 fix) | Decay dynamics. Previously broken (`_store` reference), fixed in PHASE 2. |
| `experiments/observatory.py` | `IMPLEMENTED` | CLI for Observatory. |
| `benchmarks/benchmark_suite.py` | `IMPLEMENTED` (v0.2 micro-benchmarks) | 9 micro-benchmarks, single-seed. Not multi-seed. |
| `benchmarks/memory/__init__.py` | `IMPLEMENTED` (PHASE 9) | 10 HippoCore benchmarks with multi-seed runner + JSON/CSV/Markdown export. |

### 2.5 `kernel/`, `core/`, `hal/`, `compiler/` (v0.1.0 preserved)

| Module | Status | Audit notes |
|---|---|---|
| `kernel/src/{main,sched,neuron,synapse,region,connectome,mem,ipc,hal}.rs` | `PARTIALLY IMPLEMENTED` (v0.1.0 scaffold) | Neuromorphic microkernel. Not exercised by developmental substrate. `mem.rs` (the `Ams` associative memory store) is documented as a candidate HippoCore pattern-separation backend (PHASE 10+ follow-up). |
| `core/src/{lib,models,plasticity,delays}.rs` | `PARTIALLY IMPLEMENTED` (v0.1.0) | Neural algorithms (plasticity rules, neuron models, delays). |
| `hal/src/{lib,energy}.rs` + `hal/drivers/{x86,arm,fpga,loihi}/` | `PARTIALLY IMPLEMENTED` (v0.1.0) | Hardware Abstraction Layer. |
| `compiler/synapselang/` | `IMPLEMENTED` (v0.1.0) | SynapseLang compiler (lexer, parser, codegen, stdlib). |

---

## 3. Documentation integrity (master prompt PHASE 19)

The following documentation claims are **contradicted by the code** and must be relabeled:

| Claim | Source | Contradiction | Recommended action |
|---|---|---|---|
| "Capabilities emerge through development rather than explicit programming" | `README.md:340`, `RESEARCH_AGENDA.md:147` (Open Question 4) | Hard-coded `heuristic_bias` (`organism.rs:451-503`) encodes resource-seeking, hazard-avoidance, direction-aware movement. Capabilities are programmed, not emergent. | Relabel to `UNVALIDATED`. |
| "Specialization without explicit specialization programming" | `RESEARCH_AGENDA.md:153-154` (Open Question 9) | `maturation_schedule` thresholds (`organism.rs:507-528`) are hard-coded stage transitions. Specialization is hard-coded. | Relabel to `UNVALIDATED`. |
| "Counterfactual developmental histories improve planning" | `RESEARCH_AGENDA.md:151` (Open Question 7) | `CounterfactualSelf` exists but **no experiment measures planning improvement**. | Relabel to `PROPOSED` (mechanism implemented, benefit unmeasured). |
| "HippoCore integration: 247 tests passing" | `README.md`, `docs/HIPPOCORE_INTEGRATION.md` | True, but tests do not exercise behavior — `Organism.tick()` does not consult `MemoryEngine.retrieve()`. | Add caveat: `IMPLEMENTED BUT NOT EMPIRICALLY VALIDATED`. |
| "Pattern separation" | `benchmarks/memory/__init__.py:bench_01_pattern_separation` | Storage-level separation (fresh UUIDs); not neural-circuit-accurate. | Add caveat: `IMPLEMENTED (storage-level only)`. |
| "Catastrophic forgetting benchmark" | `benchmarks/memory/__init__.py:bench_03_catastrophic_forgetting` | Measures `retention=1.0` because episodic memory does not overwrite. The benchmark does NOT measure catastrophic forgetting. | Rename to `forgetting_baseline` OR add a true continual-learning protocol. |

**Promotional language to remove** (master prompt PHASE 19):

- "advanced" — appears in `docs/HIPPOCORE_INTEGRATION.md` and `README.md` body
- "powerful" — appears in `docs/HIPPOCORE_INTEGRATION.md`
- "promising" — appears in `RESEARCH_AGENDA.md` open questions
- "comprehensive" — appears in `DEVELOPMENTAL_SUBSTRATE.md` and `README.md`

Replace with neutral language: "the X subsystem", "the X mechanism", "the X experiment".

---

## 4. Duplicate / superseded components (master prompt PHASE 17)

| Component pair | Status | Migration decision |
|---|---|---|
| Python `nuros/genome.py` vs Rust `nuros-dev/src/genome.rs` | Python is "superseded by nuros-dev" per `README.md:419` | Recommend: deprecate Python `genome.py` with a 2-version sunset; document the migration in an ADR. Do NOT delete during the audit. |
| Python `nuros/version_control.py` vs Rust `MindCheckpoint` | Same | Same. |
| Rust `MemoryRecord` (in `OrganismState`) vs Rust kernel `Ams` vs Python `MemoryContract`/`HippoCoreMemory` | Three parallel memory systems | `MemoryEngine` ABC (PHASE 2) is the abstraction boundary. Rust `MemoryRecord` should become a `DefaultMemory` impl of a Rust `MemoryEngine` trait (audit `docs/HIPPOCORE_INTEGRATION_AUDIT.md` §11.2) — PHASE 10+ follow-up. |

---

## 5. Dead code (master prompt PHASE 17)

| Symbol | File:line | Status |
|---|---|---|
| `MemoryRecord.access_count` | `organism.rs:41` | Dead field — initialized to 0 at write (`organism.rs:230, 345`), never incremented, never read. Audit Appendix B.7. Fix in PHASE 10+. |
| `EventKind::MemoryUpdate` | `causality.rs:33` | Defined but never produced by any `record()` call. Fix in PHASE 8 Rust-side. |
| `LifecycleState::CONSOLIDATE` | `nuros/homeostasis.py:34` | Declared but no organism state machine transitions to it. |

---

## 6. CI / build

| Item | Status |
|---|---|
| `.github/workflows/` directory | NOT FOUND in the audit. |
| `Makefile` | Present at repo root. |
| `Cargo.toml` (nuros-dev) | `pyo3 = 0.22`, `serde = 1.0`, `serde_json = 1.0`, `sha2 = 0.10`. Minimal, edge-friendly, no LLM. |
| `pyproject.toml` (nuros-dev) | `maturin >= 1.4, < 2.0`, Python >= 3.10. |
| Build instructions | Documented in `README.md:quickstart`. |

**Recommendation**: add `.github/workflows/test.yml` running `pytest nuros/tests/ -v` + `cargo test --lib` on every push (PHASE 10+ follow-up).

---

## 7. Summary verdict

The architecture is **layered correctly** and **largely implemented** at the module level. The HippoCore integration is **technically sound** (247 tests passing, NO LLM dependency) but is **scientifically premature** — see `docs/RESEARCH_AUDIT.md` §15.

**The architectural problems are not design problems — they are experimental problems**:
1. Hard-coded `heuristic_bias` (§9 of RESEARCH_AUDIT.md).
2. Privileged env observation fields (§11 of RESEARCH_AUDIT.md).
3. Memory not consulted during action selection (§8 above + §8 of RESEARCH_AUDIT.md).

Fix these three and the architecture can support falsifiable experiments.

**End of ARCHITECTURE_AUDIT.md.**
