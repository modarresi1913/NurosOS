# NurosOS Research Agenda

## Guiding Question

> What happens when we stop programming the final behavior of an artificial
> mind and instead program the conditions under which its cognitive structure
> can develop?

The fundamental object is not `MODEL` but `TRAJECTORY`; not `AGENT` but
`DEVELOPING ORGANISM`. The research agenda is organized around characterizing
how artificial cognitive trajectories emerge, stabilize, adapt, diverge,
and evolve.

---

## Phase 1: Foundations — [IMPLEMENTED] ✅

### R1: Epistemic Integrity Verification
**Status**: [IMPLEMENTED] in `nuros/epistemic.py`
**Question**: Can we formally verify that no epistemic violation goes undetected?
**Deliverable**: 7 labels, forbidden-transition table, override mechanism, 33 tests.

### R2: Developmental Substrate Primitives
**Status**: [IMPLEMENTED] in `nuros-dev` crate (Phases 2-8)
**Question**: Can we build the runtime, interfaces, environments, developmental
mechanisms, observability, and reproducibility infrastructure required to
instantiate, develop, measure, fork, replay, and compare artificial cognitive
systems?
**Deliverable**: `DevelopmentalGenome`, `DevelopmentalState`, `LifecycleMachine`,
`ResourceWorld`, `ChangingWorld`, `MinimumOrganism`, `DevelopmentalTrajectory`,
`MindCheckpoint`, `ReplayFidelity`, `MindDiff`, `DevelopmentalCausalityGraph`,
`DevelopmentalTelemetry`, `ReproducibilityManifest`. 57 Rust tests + 18 Python
integration tests passing.

### R3: Computational Developmental Divergence
**Status**: [IMPLEMENTED] as the flagship experiment
**Question**: Do identical initial computational conditions produce divergent
developmental states under different environmental histories?
**Approach**: Instantiate two organisms from the same genome, place them in
differently-seeded `ResourceWorld`s, develop both, measure divergence.
**Deliverable**: `experiments/same_genome_different_world.py`. Demonstrates
non-zero divergence across reward, prediction-error, action, and state
dimensions.
**Interpretation caveat**: This is NOT evidence of consciousness or biological
individuality. It is an observable computational fact about divergent
developmental trajectories.

---

## Phase 2: Characterization (0-6 months)

### R4: Plasticity vs. Stability Trade-offs
**Status**: [PROPOSED]
**Question**: What measurable trade-offs exist between plasticity and stability?
**Approach**: Sweep the `plasticity_rules.learning_rate` parameter across many
seed pairs; measure how developmental divergence, prediction accuracy, and
stability vary.
**Deliverable**: Trade-off curves, recommended defaults.

### R5: Environmental Complexity and Specialization
**Status**: [PROPOSED]
**Question**: Does environmental complexity accelerate specialization?
**Approach**: Compare developmental trajectories across environments of
varying complexity (ResourceWorld with different hazard/resource densities,
ChangingWorld with different shift intervals).
**Deliverable**: Specialization rate as a function of environmental complexity.

### R6: Memory Capacity and Trajectory Shape
**Status**: [PROPOSED]
**Question**: Does memory capacity alter developmental trajectories?
**Approach**: Vary the memory cap in `MinimumOrganism`; measure trajectory
divergence, prediction accuracy, and capability emergence.
**Deliverable**: Memory-capacity sensitivity analysis.

### R7: Prediction Accuracy and Exploration
**Status**: [PROPOSED]
**Question**: Does prediction accuracy influence exploration?
**Approach**: Measure the correlation between rolling prediction accuracy and
exploration level across many trajectories.
**Deliverable**: Correlation analysis, possible causal model.

---

## Phase 3: Counterfactual & Possible Selves (6-18 months)

### R8: Counterfactual Developmental Histories
**Status**: [PROPOSED] (Phase 11 of the roadmap)
**Question**: Can counterfactual developmental histories improve planning?
**Approach**: Implement `CounterfactualSelf`; let the organism evaluate "What
if environment E2 had occurred?" and measure whether this improves future
decisions.
**Deliverable**: Counterfactual planning benchmark.

### R9: Possible-Self Space
**Status**: [PROPOSED] (Phase 11)
**Question**: Can the organism be represented as a space of reachable
developmental states rather than a single static state?
**Approach**: Extend `CounterfactualSelf` into `PossibleSelfSpace`; sample
alternative futures; measure coverage and stability.
**Deliverable**: Possible-self space visualization and metrics.

---

## Phase 4: Metabolism & Aging (18-36 months)

### R10: Cognitive Metabolism
**Status**: [PROPOSED] (Phase 12)
**Question**: How do resource constraints (attention, inference, memory,
exploration, uncertainty, risk, energy budgets) shape developmental
trajectories?
**Approach**: Implement `CognitiveMetabolism`; vary budgets; measure
trade-offs.
**Deliverable**: Metabolic trade-off curves, "Is this information worth the
cognitive cost?" decision rule.

### R11: Artificial Aging
**Status**: [PROPOSED] (Phase 13)
**Question**: How does accumulated computational history affect future
cognition?
**Approach**: Implement `AgingModel` with configurable aging dimensions;
measure how aging alters plasticity, stability, and capability.
**Deliverable**: Aging trajectory characterization.

---

## Phase 5: Evolution (36+ months)

### R12: Artificial Evolution on DevelopmentalGenome
**Status**: [PROPOSED] (Phase 14)
**Question**: Can populations of artificial organisms develop useful behavioral
diversity through evolution on the genome?
**Approach**: Implement `ArtificialEvolution` with mutation, selection,
variation, inheritance, evaluation operating on `DevelopmentalGenome`.
**Deliverable**: Population dynamics, diversity metrics, evolved genomes.
**Constraint**: Only after deterministic developmental experiments are
functional.

---

## Open Questions

These are research questions, not predetermined conclusions:

1. Can developmental trajectories produce stable computational individuality?
2. How does environmental history alter identical initial architectures?
3. What measurable trade-offs exist between plasticity and stability?
4. Can artificial cognitive capabilities emerge through development rather
   than explicit programming? **[UNVALIDATED]** — the `heuristic_bias`
   (`organism.rs:451-503`) hard-codes task knowledge; learned signal is
   secondary. See `docs/RESEARCH_AUDIT.md` §9.
5. How does accumulated experience alter future behavior?
6. Can cognitive trajectories be reproduced experimentally?
   **[IMPLEMENTED]** — verified by 341 tests; see `docs/REPRODUCIBILITY_SPEC.md`.
7. Can counterfactual developmental histories improve planning?
   **[PROPOSED]** — mechanism implemented (`CounterfactualSelf`); benefit
   unmeasured. See `docs/RESEARCH_AUDIT.md` §3.
8. What computational constraints govern artificial cognitive development?
   **[PROPOSED]** — mechanism implemented (`CognitiveMetabolism`); benefit
   unmeasured.
9. Can artificial organisms specialize without explicit specialization
   programming? **[UNVALIDATED]** — `maturation_schedule` transitions are
   hard-coded thresholds (`organism.rs:507-528`). Not emergent.
10. Which properties of cognition are architecture-dependent versus
    development-dependent?

---

## Methodology

Every research item follows these principles:

1. **Reproducible**: Every claim ships with a runnable experiment and a
   `ReproducibilityManifest`.
2. **Epistemically honest**: Results are labeled with their epistemic status
   (`[IMPLEMENTED]`, `[EXPERIMENTAL]`, `[PROPOSED]`, `[SPECULATIVE]`).
3. **Safety-first**: Experiments never compromise safety invariants.
4. **Incremental**: Each result builds on verified foundations.
5. **Open**: All code, data, and analysis are open-source.
6. **Interpretation-cautious**: Divergence is not individuality; simulation
   is not observation; development is not deployment; intelligence is not
   consciousness.
