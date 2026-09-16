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

### Phase 11 — CounterfactualSelf 📋 (Proposed)
- [ ] `CounterfactualSelf` module for evaluating alternative developmental histories
- [ ] "What if environment E2 had occurred?" simulations
- [ ] Counterfactual simulations marked SIMULATED + COUNTERFACTUAL in epistemic system
- [ ] Never automatically execute counterfactual actions in the real environment

### Phase 12 — Cognitive/Epistemic Metabolism 📋 (Proposed)
- [ ] Resource accounting: attention_budget, inference_budget, memory_budget,
      exploration_budget, uncertainty_budget, risk_budget, energy_budget
- [ ] `CognitiveMetabolism` module with per-operation cost model
- [ ] Scheduler uses metabolic values
- [ ] Experiments around "Is this information worth the cognitive cost?"

### Phase 13 — Artificial Aging 📋 (Proposed)
- [ ] `AgingModel` with configurable aging dimensions
- [ ] Memory degradation, plasticity changes, processing constraints,
      experience accumulation, structural consolidation
- [ ] Investigate: How does accumulated computational history affect future cognition?

### Phase 14 — Artificial Evolution 📋 (Proposed)
- [ ] `ArtificialEvolution` operating on `DevelopmentalGenome`
- [ ] Mutation, selection, variation, inheritance, evaluation
- [ ] Minimal experimental population engine
- [ ] Only after deterministic developmental experiments are functional

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
