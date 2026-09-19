# Metrics

> Master prompt §26: "Do NOT create one universal intelligence score.
> Create a multidimensional profile."

The HippoCore integration exposes the following multidimensional
profile. Every metric is clearly defined with units + measurement
protocol.

---

## Adaptation

**Definition**: How well the organism adjusts its behavior when the
environment changes.

**Measurement**: Counterfactual replay from a checkpoint in an
alternative environment (benchmark 09, master prompt §13).
`n_cf_only_memories` — the number of memories unique to the
counterfactual trajectory.

**Units**: integer (memory count).

---

## Memory Retention

**Definition**: Fraction of memories still retrievable after a
subsequent learning task.

**Measurement**: Benchmark 03 (`benchmarks/memory/__init__.py:bench_03_catastrophic_forgetting`)
— encodes 10 task-A memories, then 10 task-B memories, then measures
`retention_<condition> = (n task-A memories still retrievable) / 10`.

**Units**: ratio in [0, 1].

**Known limitation**: PHASE 6 design does not overwrite episodic
memories, so `retention = 1.0` across all conditions. See BENCHMARKS.md
benchmark 03 entry.

---

## Environmental Robustness

**Definition**: How stable the organism's behavior is across
environmental perturbations.

**Measurement**: Benchmark 08 (`bench_08_same_genome_different_world`)
— two organisms with the same genome in different environments;
`behavioral_divergence` is the count of action differences.

**Units**: integer (action count).

---

## Developmental Plasticity

**Definition**: How much the developmental state changes over time.

**Measurement**: `DevelopmentalState` distance between consecutive
`TrajectoryPoint`s (Rust side, `nuros-dev/src/trajectory.rs:163-187`).
Not yet exposed in the PHASE 9 Python benchmarks; will land in PHASE 10+
when Rust PyO3 is rebuilt.

**Units**: float (L1 distance).

---

## Replay Fidelity

**Definition**: How faithfully a replayed memory matches its source.

**Measurement**: Benchmark 10 (`bench_10_checkpoint_reproducibility`)
— `hash_match` is 1.0 iff the restored memory count matches the
original; `content_match` is 1.0 iff the sorted content lists match.

**Units**: ratio in [0, 1] (1.0 = exact reproduction).

---

## Causal Traceability

**Definition**: Whether the developmental causal graph can trace an
outcome back to its originating experience.

**Measurement**: PHASE 8 `PythonCausalGraph.trace_outcome_to_experience(outcome_id)`
— returns the full chain `Outcome → Action → Decision → Memory →
Experience` for a given outcome event ID.

**Units**: integer (length of the trace; 0 if the chain is broken).

---

## Resource Efficiency

**Definition**: How much compute + memory the engine consumes per
operation.

**Measurement**: All PHASE 9 benchmarks report `latency_ms` per
operation. `HippoCoreMemory.last_replay_selection` and
`last_consolidation_result` carry elapsed time telemetry.

**Units**: milliseconds.

---

## Recovery

**Definition**: How quickly the engine returns to a usable state after
a checkpoint/restore.

**Measurement**: Benchmark 10 `latency_ms` — restore wall-clock time.

**Units**: milliseconds.

---

## Generalization

**Definition**: How well the consolidated semantic memories summarize
their episodic sources.

**Measurement**: Benchmark 05 (`bench_05_consolidation`) —
`target_importance_mean` is the mean importance of the newly-created
semantic memories (= mean of source importances, preserving signal).

**Units**: float (mean importance in [0, 1]).

---

## Behavioral Stability

**Definition**: How consistent the organism's behavior is across runs
with the same seed.

**Measurement**: PHASE 5 benchmark 04 (`bench_04_replay`) — `n_unique_*`
per policy. Different policies should produce different selections
(non-degeneracy); same policy + same seed should produce identical
selections (determinism).

**Units**: integer (memory count).

---

## Status matrix

| Metric | Phase | Benchmark | Status |
|--------|-------|-----------|--------|
| Adaptation | PHASE 9 | 09 counterfactual | `[IMPLEMENTED]` |
| Memory Retention | PHASE 9 | 03 catastrophic forgetting | `[IMPLEMENTED]` (caveat: retention=1.0 by design) |
| Environmental Robustness | PHASE 9 | 08 same genome | `[IMPLEMENTED]` |
| Developmental Plasticity | (Rust side) | — | `[PROPOSED]` (needs PyO3 rebuild) |
| Replay Fidelity | PHASE 9 | 10 checkpoint reproducibility | `[IMPLEMENTED]` |
| Causal Traceability | PHASE 8 | (PythonCausalGraph.trace) | `[IMPLEMENTED]` (Python side; Rust side `[PROPOSED]`) |
| Resource Efficiency | PHASE 9 | all benchmarks (latency_ms) | `[IMPLEMENTED]` |
| Recovery | PHASE 9 | 10 checkpoint reproducibility | `[IMPLEMENTED]` |
| Generalization | PHASE 9 | 05 consolidation | `[IMPLEMENTED]` |
| Behavioral Stability | PHASE 9 | 04 replay | `[IMPLEMENTED]` |
