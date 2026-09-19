# NurosOS Roadmap

> **Identity shift (v0.3.0-alpha):** NurosOS has evolved from "A Runtime for
> Synthetic Minds" into "The Experimental Substrate for Synthetic Development".
> The fundamental object is no longer `MODEL` but `TRAJECTORY`; no longer
> `AGENT` but `DEVELOPING ORGANISM`. See [DEVELOPMENTAL_SUBSTRATE.md](DEVELOPMENTAL_SUBSTRATE.md)
> for the full architectural specification.

## Version 0.1.0 — Neural Substrate ✅ (Complete)
- [x] Rust microkernel (sched, mem, neuron, synapse, region, connectome, ipc, hal)
- [x] Core library (plasticity, models, delays)
- [x] SynapseLang compiler (lexer, parser, codegen, stdlib)
- [x] Hardware abstraction (x86, ARM, FPGA, Loihi)
- [x] Basic tests and benchmarks

## Version 0.2.0-alpha — Cognitive Architecture ✅ (Complete)
- [x] Epistemic Kernel (7 labels, forbidden transitions, override mechanism)
- [x] Memory Contract (5 types, provenance, decay, audit)
- [x] Self Model Contract (queries, updates, uncertainty)
- [x] Imagination Engine (hypothesize → simulate → decide)
- [x] Values/Drives Contract (3-tier hierarchy, immutable constraints)
- [x] Body Contract (embodiment abstraction)
- [x] Responsibility Contract (causal history, audit)
- [x] Homeostasis Kernel (regulation, drives)
- [x] Safety Kernel (permissions, audit, shutdown, override)
- [x] Metabolic Cognitive Scheduler
- [x] Developmental Engine (artificial ontogenesis)
- [x] Organism Runtime (lifecycle, fork, snapshot)
- [x] Mind Genome (YAML spec, hash)
- [x] Environment API
- [x] Mind Version Control
- [x] Organism Ladder (Organism-0 through Organism-5)
- [x] Benchmark Suite
- [x] 33 passing tests

## Version 0.3.0-alpha — Developmental Substrate 🔄 (Current)

The developmental substrate (`nuros-dev` crate) turns NurosOS from a runtime
into an experimental platform for synthetic development.

### Phase 1 — Repository Audit ✅
- [x] Audit existing modules against the new developmental-substrate thesis
- [x] Identify claim/code gaps in Mind Genome, Mind Version Control, Development Engine
- [x] Document the central inversion (Model → Trajectory, Agent → Developing Organism)

### Phase 2 — DevelopmentalState ✅
- [x] `DevelopmentalState` vector with 14 scalar fields + capability map
- [x] L1 distance metric between states
- [x] Canonical hash for provenance

### Phase 3 — DevelopmentalGenome ✅
- [x] `DevelopmentalGenome` with architecture, initial_memory, initial_capabilities,
      plasticity_rules, biases, maturation_schedule, homeostasis, energy_model,
      mutation_parameters
- [x] Canonical SHA-256 hash (single source of truth via `hash::hash()`)
- [x] JSON round-trip preserves hash

### Phase 4 — ArtificialOntogenesis ✅
- [x] `DevelopmentalTrajectory` with ordered `TrajectoryPoint` records
- [x] `DevelopmentalEvent` records (stage transitions, capability emergence)
- [x] `LifecycleMachine` with auditable transitions

### Phase 5 — Checkpoint + Replay ✅
- [x] `MindCheckpoint` captures full organism + environment state
- [x] `replay_from_checkpoint()` with explicit fidelity classification
- [x] `ReplayFidelity::{Exact, Approximate, NonReproducible}`

### Phase 6 — MindDiff ✅
- [x] Structured `MindDiff` across memory, self-model, values, capabilities,
      prediction, behavior, developmental state
- [x] Machine-readable JSON + human-readable rendering
- [x] Exposed to Python via `mind_diff()` function

### Phase 7 — DevelopmentalTelemetry ✅
- [x] Per-step `TelemetryRecord` with 24 fields
- [x] JSONL export (one JSON object per line)
- [x] CSV export (flat table)

### Phase 8 — DevelopmentalCausalityGraph ✅
- [x] Provenance DAG with `CausalEvent` records
- [x] 11 event kinds (EnvironmentEvent → SensoryObservation → ... → DevelopmentalChange)
- [x] Causal trace walks (transitive closure of `depends_on`)
- [x] JSONL export for offline analysis

### Phase 9 — Same Genome / Different World Experiment ✅
- [x] `experiments/same_genome_different_world.py` flagship experiment runner
- [x] 13 output artifacts (genome, trajectories, telemetry, checkpoints, divergence,
      mind diff, manifests, report, summary)
- [x] `ReproducibilityManifest` for each organism
- [x] Demonstrates Computational Developmental Divergence with non-zero metrics
- [x] 75 tests passing (57 Rust + 18 Python)

### Phase 10 — Mind Observatory ✅ (Complete)
- [x] `nuros/observatory.py` — observability layer with text renderers + PNG plots
- [x] `experiments/observatory.py` — CLI with 16 commands (summary, timeline,
      mind-diff, causal-trace, env-events, checkpoints, manifests, divergence,
      8 plot commands, render-all)
- [x] Text renderers: timeline replay, mind diff, causal trace, environment
      events, checkpoints overview, manifests, divergence summary
- [x] PNG plots: developmental trajectory, prediction error + reward,
      memory changes + cumulative reward, state transitions, resource
      consumption, mind diff, per-step divergence, divergence comparison
- [x] `nuros/tests/test_observatory.py` — 21 tests (loaders + text renderers + plots + render-all)
- [x] Built as an experimental instrument, not a decorative dashboard

### Phase 11 — CounterfactualSelf + PossibleSelfSpace ✅ (Complete)
- [x] `nuros-dev/src/counterfactual.rs` — `CounterfactualTrajectory`, `CounterfactualSelf`, `PossibleSelfSpace`
- [x] `MinimumOrganism::tick_with_action` — forced-action replay for counterfactuals
- [x] `what_if_environment()` — replay from checkpoint in alternative environment
- [x] `what_if_actions()` — replay from checkpoint with forced action sequence
- [x] `compare_to_actual()` — divergence between counterfactual and actual trajectory
- [x] `PossibleSelfSpace` — current self + possible futures + counterfactual past, with coverage metric
- [x] All counterfactual trajectories marked `["SIMULATED", "COUNTERFACTUAL"]`
- [x] `executed_in_real_environment: false` invariant enforced and auditable
- [x] PyO3 bindings: `run_counterfactual_environment()`, `run_possible_self_space()`
- [x] `experiments/counterfactual_demo.py` — demo with 3 alternative futures
- [x] `nuros/tests/test_counterfactual.py` — 15 Python integration tests
- [x] 9 Rust unit tests in counterfactual.rs
- [x] Interpretation caveat: PossibleSelfSpace does NOT represent phenomenological identity

### Phase 12 — Cognitive/Epistemic Metabolism ✅ (Complete)
- [x] `nuros-dev/src/metabolism.rs` — `CognitiveMetabolism`, `CognitiveBudget`, `CognitiveCostModel`
- [x] 7 budgets: attention, inference, memory, exploration, uncertainty, risk, energy
- [x] 9 cognitive operations: Perceive, Predict, Memorize, Plan, Simulate, Act, Explore, ReduceUncertainty, TakeRisk
- [x] Per-operation cost model + spending tracker + refusal counter
- [x] `can_afford()` + `spend()` + `is_worth_it()` (value-of-information decision rule)
- [x] `remaining_fractions()` for telemetry
- [x] `reset_tick()` for per-tick budget reset + `total_spending` for cumulative tracking
- [x] PyO3 bindings: `run_metabolism_sweep()`, `evaluate_value_of_information()`
- [x] `experiments/metabolism_demo.py` — budget sweep + VoI table
- [x] `nuros/tests/test_metabolism.py` — 12 Python integration tests
- [x] 11 Rust unit tests in metabolism.rs
- [x] Interpretation caveat: computational abstraction, NOT biological metabolism

### Phase 13 — Artificial Aging ✅ (Complete)
- [x] `nuros-dev/src/aging.rs` — `AgingModel` + `AgingEffect`
- [x] 5 aging dimensions: memory degradation, plasticity changes, processing constraints, experience accumulation, structural consolidation
- [x] Configurable rates + onsets + floors + ceilings
- [x] `AgingModel::no_aging()` + `AgingModel::rapid_aging()` presets
- [x] `apply(&mut DevelopmentalState)` — applies one tick of aging
- [x] PyO3 binding: `run_aging_comparison(aging_model_json, n_steps)`
- [x] `experiments/aging_demo.py` — comparison with 3 presets (none/gentle/rapid)
- [x] `nuros/tests/test_aging.py` — 11 Python integration tests
- [x] 14 Rust unit tests in aging.rs
- [x] Interpretation caveat: Aging is configurable. Do not impose biological aging assumptions without evidence.

### Phase 14 — Artificial Evolution 📋 (Proposed)
- [ ] `ArtificialEvolution` operating on `DevelopmentalGenome`
- [ ] Mutation, selection, variation, inheritance, evaluation
- [ ] Minimal experimental population engine
- [ ] Only after deterministic developmental experiments are functional

### Phase 15 — HippoCore Integration ✅ (Implemented on `feature/hippocore-integration-audit`)

The HippoCore integration transforms NurosOS from a runtime for
artificial cognitive organisms into a developmental intelligence
substrate where memory is a first-class computational mechanism.

Ten phases shipped on the `feature/hippocore-integration-audit` branch:

| Sub-phase | Commit | Description | Tests |
|-----------|--------|-------------|-------|
| 15.1 — Audit | `254875c` | 1051-line audit (24 sections + 2 appendices) anchored to file:line evidence | — |
| 15.2 — Memory Contract stabilization | `f29a768` | `MemoryEngine` ABC + `DefaultMemoryContract` refactor; soft-delete fix; checkpoint/restore; 6 bug-fixes from audit Appendix B | 83 |
| 15.3 — HippoCore adapter scaffold | `5c58859` | `HippoCoreMemory(MemoryEngine)` thin wrapper; 25 golden-file equivalence tests | 108 |
| 15.4 — Episodic encoding + provenance | `b5dcc6e` | `MemoryProvenance` dataclass; `MemoryEntry` schema extension (organism_id, action, outcome, prediction, environment_state, causal_metadata, structured_provenance); `encode_episode()` full-schema entry point | 128 |
| 15.5 — Replay policies | `3e60a63` | 5 policies (recent / importance_weighted / novelty_weighted / prediction_error_weighted / random); all deterministic when seeded | 169 |
| 15.6 — Consolidation pipeline | `f5dc734` | 2 strategies (tag_jaccard / content_prefix); real fast→slow pipeline; sources marked CONSOLIDATED + importance lowered; sources↔target associations | 201 |
| 15.7 — Memory event emission | `b3e97cf` | 6 `MemoryEventKind`s; `MemoryEventEmitter` event bus; `set_step()` for trajectory alignment | 220 |
| 15.8 — Causal graph integration (Python side) | `74fb2da` | 17 `EventKind` variants (11 original Rust + 6 PHASE 8 memory kinds); `PythonCausalGraph`; `trace_outcome_to_experience()` walk | 247 |
| 15.9 — Benchmark suite | `bc411cf` | 10 benchmarks in `benchmarks/memory/`; multi-seed runner with JSON/CSV/Markdown export; all deterministic | — (benchmarks ARE tests) |
| 15.10 — Documentation and release | (this phase) | 9 new docs + ADR 0006 + final report | — |

**Total**: 247 tests passing (Python side). Rust-side tests (57) still
pass per README quickstart when `maturin build --release` is run.

**Status**: [IMPLEMENTED] PHASES 1-10 (Python side).
            [PROPOSED]    Rust-side wiring for PHASES 7+8 (needs
                          maturin build) + memory-dependent behavior
                          (Organism.tick consults MemoryEngine during
                          action selection — audit §36 stage 5).

**LLM dependency**: NONE (master prompt §23 satisfied).

**Branch**: `feature/hippocore-integration-audit`. Pull-request
comparison: https://github.com/modarresi1913/NurosOS/compare/main...feature/hippocore-integration-audit

See:
- `docs/HIPPOCORE_INTEGRATION_AUDIT.md` (Phase 1 audit, 1051 lines)
- `docs/HIPPOCORE_INTEGRATION.md` (integration guide)
- `docs/MEMORY_ARCHITECTURE.md` (memory architecture)
- `docs/DEVELOPMENTAL_MEMORY.md` (developmental memory)
- `docs/BENCHMARKS.md` (benchmark guide)
- `docs/METRICS.md` (multidimensional metric profile)
- `docs/REPRODUCIBILITY.md` (reproducibility invariants)
- `docs/EXPERIMENTS.md` (experiment guide)
- `docs/HIPPOCORE_INTEGRATION_REPORT.md` (final report)
- `docs/adr/0006-hippocore-memory-engine.md` (ADR)

## Version 0.4.0 — Neural-Cognitive Bridge
- [ ] Bridge Rust SNN substrate to Python cognitive kernel
- [ ] FFI bindings for real-time neural simulation
- [ ] Synaptic state export/import for memory persistence
- [ ] Spike-timing-dependent plasticity integration
- [ ] Connectome-preserving organism migration

## Version 0.5.0 — Language Layer
- [ ] MindLang v1: declarative organism specification language
- [ ] MindLang compiler: genome → running organism
- [ ] SynapseLang v2: cognitive circuit specification
- [ ] REPL for interactive organism development
- [ ] Visual connectome editor

## Version 0.5.0 — Development & Learning
- [ ] Full developmental trajectory implementation
- [ ] Stage transition criteria and verification
- [ ] Artificial dreaming (offline generative replay)
- [ ] Sleep states (AWAKE, SLEEP, DREAM, CONSOLIDATE, RECOVER)
- [ ] Curriculum learning environments
- [ ] Transfer learning between organism levels

## Version 0.6.0 — Multi-Organism Systems
- [ ] Organism communication protocol
- [ ] Shared environment support
- [ ] Theory of mind implementation
- [ ] Cooperative task solving
- [ ] Competitive games
- [ ] Ecosystem simulation framework

## Version 0.7.0 — Self-Modification
- [ ] Safe self-modification framework
- [ ] Plasticity rule discovery
- [ ] Architecture search within safety bounds
- [ ] Developmental milestone verification
- [ ] Self-improvement audit trail

## Version 0.8.0 — Reproducibility & Science
- [ ] Full reproducibility guarantee
- [ ] Experiment versioning
- [ ] Statistical analysis framework
- [ ] Paper-ready experiment pipelines
- [ ] Result comparison tools

## Version 0.9.0 — Observability & Tools
- [ ] Real-time organism dashboard
- [ ] Cognitive state visualization
- [ ] Epistemic flow diagrams
- [ ] Memory landscape visualization
- [ ] Developmental trajectory plots
- [ ] Safety audit browser

## Version 1.0.0 — Stable Release
- [ ] API stability guarantees
- [ ] Comprehensive documentation
- [ ] Performance benchmarks vs baselines
- [ ] Security audit
- [ ] Community contribution guidelines
- [ ] Long-term support commitment
