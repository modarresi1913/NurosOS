# METRICS SPEC

> **Master prompt PHASE 9**: implement a reproducible metrics layer.
> **Companion to**: `experiments/EXPERIMENTS.md` §4-5 (primary + secondary outcomes).
> **Status**: SPECIFICATION.

This document specifies the metrics the audit recommends for the NurosOS
experiments. Every metric has a formal definition, source data, computation
procedure, serialization format, and unit test.

Per master prompt: "Do not use reward as the only metric."

---

## 1. PRIMARY metrics

### M-1. Cumulative reward

**Formal definition**: `total_reward = Σ_{t=1..N} r_t` where `r_t` is the reward signal returned by `env.step(action_t)` at step `t`, and `N` is the total number of steps (default 300).

**Source data**: `experiment_outputs/<experiment_id>/raw/per_step.jsonl` — the `reward` field of each per-step record.

**Computation procedure**: sum the per-step rewards. One number per seed. Aggregate as mean ± std across 30 seeds. Report 95% CI + effect size.

**Serialization format**: 
```json
{
  "seed": <int>,
  "total_reward": <float>
}
```
per seed; aggregate:
```json
{
  "mean": <float>,
  "std": <float>,
  "median": <float>,
  "ci_95": [<float>, <float>],
  "min": <float>,
  "max": <float>,
  "n": <int>,
  "per_seed": [<float>, ...]
}
```

**Unit**: dimensionless (reward is in [-1, 1] per step per `environment.rs`).

**Unit test**: `tests/test_metrics.py::test_cumulative_reward` — given a known per-step reward sequence, assert the cumulative sum is correct.

---

### M-2. Adaptation latency

**Formal definition**: number of steps from a regime transition (e.g., step 100, the A→B boundary) to the first step where the rolling 10-step mean reward recovers to within 90% of the pre-transition 10-step mean reward.

**Source data**: per-step reward + regime boundary step from env config.

**Computation procedure**:
1. Compute the rolling 10-step mean reward: `R_t = mean(r_{t-9..t})`.
2. Identify the pre-transition baseline: `R_pre = R_{transition_step - 1}`.
3. Find the smallest `t > transition_step` such that `R_t >= 0.9 * R_pre`.
4. `adaptation_latency = t - transition_step`.
5. If no such `t` exists within the regime, `adaptation_latency = regime_length` (did not adapt).

**Serialization format**: `{ "adaptation_latency": <int>, "regime": "A_to_B" | "B_to_C" }` per transition per seed.

**Unit**: steps (integer).

**Unit test**: `tests/test_metrics.py::test_adaptation_latency` — given a synthetic reward sequence with a known recovery point, assert the latency is correct.

---

### M-3. Post-shift recovery

**Formal definition**: cumulative reward in the 30 steps following a regime transition, normalized by the pre-transition 30-step cumulative reward.

**Formal**: `post_shift_recovery = sum(r_{transition+1..transition+30}) / sum(r_{transition-29..transition})`.

**Source data**: per-step reward.

**Computation procedure**: slice the reward sequence at the transition; compute the ratio.

**Serialization format**: `{ "post_shift_recovery": <float>, "transition": "A_to_B" | "B_to_C" }` per transition per seed.

**Unit**: ratio (dimensionless). > 1.0 means recovery exceeded pre-shift; < 1.0 means recovery was worse.

**Unit test**: `tests/test_metrics.py::test_post_shift_recovery`.

---

### M-4. Transfer performance (forward)

**Formal definition**: mean reward in the first 30 steps of Regime B (steps 100-129), relative to the last 30 steps of Regime A (steps 70-99).

**Formal**: `forward_transfer = mean(r_{100..129}) / mean(r_{70..99})`.

**Source data**: per-step reward.

**Unit**: ratio (dimensionless). > 1.0 means forward transfer (knowledge from A helps in B); < 1.0 means negative transfer.

**Unit test**: `tests/test_metrics.py::test_forward_transfer`.

---

## 2. CONTINUAL LEARNING metrics

### M-5. Forgetting

**Formal definition**: decrease in performance on Regime A's task after training on Regime B.

**Formal**: `forgetting = mean(r_{70..99}) - mean(r_{170..199})` if Regime C revisits Regime A's task (else `forgetting = NaN`).

**Source data**: per-step reward + regime task identity.

**Unit**: dimensionless reward difference. Positive = forgetting; negative = improvement (backward transfer).

**Unit test**: `tests/test_metrics.py::test_forgetting`.

---

### M-6. Backward transfer

**Formal definition**: mean reward in Regime A when revisited in Regime C (if Regime C revisits A's task), relative to original Regime A performance.

**Formal**: `backward_transfer = mean(r_{C_revisit_A_window}) / mean(r_{70..99})`.

**Source data**: per-step reward.

**Unit**: ratio. > 1.0 means backward transfer (training on B improved A's performance when revisited); < 1.0 means forgetting.

**Unit test**: `tests/test_metrics.py::test_backward_transfer`.

---

### M-7. Forward transfer (full)

**Formal definition**: same as M-4 but generalized: mean reward in the first 30 steps of any new regime, relative to the last 30 steps of the previous regime.

**Unit**: ratio.

---

## 3. DEVELOPMENT metrics

### M-8. Trajectory divergence

**Formal definition**: `DevelopmentalDivergence.mean_state_distance` between two organisms from the same genome in differently-seeded envs.

**Source data**: `nuros-dev/src/trajectory.rs:DevelopmentalDivergence::between` (Rust).

**Computation procedure**: instantiate two organisms from the same `DevelopmentalGenome`, place each in a `ResourceWorld(seed=env_seed_a)` and `ResourceWorld(seed=env_seed_b)` respectively, develop both for N steps, call `DevelopmentalDivergence::between(traj_a, traj_b)`.

**Serialization format**: `{ "mean_state_distance": <float>, "reward_distance": <float>, "prediction_error_distance": <float>, "action_distance": <float>, "stage_divergence": <bool> }` per seed pair.

**Unit**: L1 distance (dimensionless scalar vector distance).

**Unit test**: `nuros-dev/src/trajectory.rs:tests::divergence_between_different_worlds_is_positive`.

---

### M-9. Developmental-state divergence

**Formal definition**: L1 distance between the final `DevelopmentalState` of two organisms from the same genome in different envs.

**Source data**: `nuros-dev/src/state.rs:DevelopmentalState::distance` (Rust, `state.rs:162-187`).

**Unit**: L1 distance.

---

### M-10. Capability changes

**Formal definition**: change in `DevelopmentalState.capabilities` (a `BTreeMap<String, f64>` of capability name → proficiency) from step 0 to step N.

**Source data**: `DevelopmentalState.capabilities` at start and end of run.

**Serialization format**: `{ "capability": <string>, "start": <float>, "end": <float>, "delta": <float> }` per capability.

**Unit**: proficiency in [0, 1].

---

## 4. MEMORY metrics

### M-11. Memory footprint

**Formal definition**: number of stored memory entries at end of run.

**Source data**: `MemoryEngine.memory_count` (Python) / `OrganismState.memory.len()` (Rust).

**Unit**: integer (count of entries).

---

### M-12. Retrieval count

**Formal definition**: number of `MemoryEngine.retrieve()` calls during the run.

**Source data**: `MemoryEngine.operation_log` filtered by `MemoryOperation.RETRIEVE`.

**Unit**: integer.

---

### M-13. Replay count

**Formal definition**: number of `MemoryEngine.replay()` calls during the run.

**Source data**: `MemoryEngine.operation_log` filtered by `MemoryOperation.REPLAY`.

**Unit**: integer.

---

### M-14. Consolidation activity

**Formal definition**: number of `MemoryEngine.consolidate()` calls + number of target memories created during the run.

**Source data**: `MemoryEngine.operation_log` filtered by `MemoryOperation.CONSOLIDATE` + `HippoCoreMemory.last_consolidation_result.n_target_created`.

**Unit**: integer (calls) + integer (memories created).

---

### M-15. Forgetting activity

**Formal definition**: number of `MemoryEngine.forget()` calls during the run.

**Source data**: `MemoryEngine.operation_log` filtered by `MemoryOperation.FORGET`.

**Unit**: integer.

---

## 5. SYSTEM metrics

### M-16. Runtime

**Formal definition**: wall-clock seconds for the full 300-step run.

**Source data**: `time.perf_counter()` at start/end of `run_experiment`.

**Unit**: seconds (float).

---

### M-17. Compute cost

**Formal definition**: total CPU time consumed by the run (user + sys).

**Source data**: `resource.getrusage(resource.RUSAGE_SELF)` before/after the run.

**Unit**: seconds (float).

---

### M-18. Checkpoint size

**Formal definition**: bytes of the serialized `MindCheckpoint` at end of run.

**Source data**: `len(MindCheckpoint.to_json().encode())`.

**Unit**: bytes (integer).

---

### M-19. Replay cost

**Formal definition**: wall-clock seconds consumed by all `replay()` calls during the run.

**Source data**: `time.perf_counter()` before/after each `replay()` call; sum across the run.

**Unit**: seconds (float).

---

## 6. Serialization format (per-condition aggregate)

Each condition (A-F in the ablation matrix) produces, per observation mode:

```json
{
  "condition": "B",
  "observation_mode": "raw",
  "n_seeds": 30,
  "metrics": {
    "cumulative_reward": { "mean": ..., "std": ..., "ci_95": [...], "per_seed": [...] },
    "adaptation_latency": { ... },
    "post_shift_recovery": { ... },
    "forward_transfer": { ... },
    "forgetting": { ... },
    "backward_transfer": { ... },
    "trajectory_divergence": { ... },
    "developmental_state_divergence": { ... },
    "memory_footprint": { ... },
    "retrieval_count": { ... },
    "replay_count": { ... },
    "consolidation_activity": { ... },
    "forgetting_activity": { ... },
    "runtime_seconds": { ... },
    "compute_cost_seconds": { ... },
    "checkpoint_size_bytes": { ... },
    "replay_cost_seconds": { ... }
  },
  "effect_size_vs_B": {
    "cumulative_reward_cohens_d": <float>,
    "p_value": <float>,
    "significant_at_alpha_0_0042": <bool>
  }
}
```

The `effect_size_vs_B` field is only present for conditions A, C, D, E, F (not B itself, which is the reference).

---

## 7. Unit test plan

`tests/test_metrics.py` (new) verifies each metric's computation on synthetic data with known answers. Every metric M-1 through M-19 has at least one test case.

**End of METRICS_SPEC.md.**
