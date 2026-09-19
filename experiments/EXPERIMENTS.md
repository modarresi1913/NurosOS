# EXPERIMENTS — Preregistration

> **Master prompt PHASE 7**: This file is the **preregistration** of the flagship
> NurosOS experiment. It MUST be committed BEFORE any large-scale experimental
> runs. Per master prompt: "Do not modify the hypothesis after observing results.
> If implementation problems require changes, create a new version of the
> preregistration."
>
> **Status**: PREREGISTRATION v1.0 — committed before the experiments described herein are run.
> **Date**: 2026-09-19
> **Auditor**: Super Z (acting as senior research software architect + RL evaluator + experimental-methodology auditor).

---

## 1. Research question

**Primary research question**: Does the NurosOS developmental substrate provide measurable behavioral value beyond a conventional tabular Q-learning baseline, under (a) a non-stationary environment and (b) a constrained memory budget?

This is the master prompt PHASE 2 "preferred candidate" question, operationalized.

**Subordinate questions** (secondary, exploratory):

- SQ1: Does removing the hard-coded `heuristic_bias` (PHASE 4 ablation condition F) reduce cumulative reward?
- SQ2: Does removing the maturation schedule (condition C) alter developmental-state trajectory shape?
- SQ3: Does removing the plasticity decay (condition D) alter retention on the second regime?
- SQ4: Does removing the self-model contribution (condition E) alter prediction accuracy?

---

## 2. Hypothesis (H1)

**Primary hypothesis (H1)**: Under a non-stationary 3-regime environment (Regime A → Regime B → Regime C-novel) with a constrained memory budget, the NurosOS baseline organism achieves higher cumulative reward and faster post-shift recovery than a tabular Q-learning baseline with the same observation/action harness, the same memory budget, and the same seed set.

**Operational form**: H1 predicts a positive effect size (Cohen's d > 0.3) on the primary outcome (cumulative reward over 300 steps × 30 seeds) when comparing NurosOS-baseline (condition B) vs Q-learning-baseline (condition A).

## 3. Null hypothesis (H0)

**Null hypothesis (H0)**: There is no statistically significant difference in cumulative reward between the NurosOS baseline (condition B) and the tabular Q-learning baseline (condition A) under the same environment, memory budget, and seed set.

H0 is the "NurosOS provides no measurable value" hypothesis. We will reject H0 only if the effect is statistically significant (two-sample t-test, α = 0.05, two-tailed) AND practically significant (Cohen's d > 0.3).

## 4. Primary outcome

**Cumulative reward** over 300 steps, averaged across 30 seeds.

- Formal definition: `total_reward = Σ_{t=1..300} r_t` where `r_t` is the reward signal returned by `env.step(action)` at step `t`.
- Source data: `experiment_outputs/<experiment_id>/trajectories/trajectory.jsonl` (per-step `reward` field).
- Computation procedure: sum the per-step rewards; one number per seed; aggregate as mean ± std across 30 seeds.
- Serialization format: JSON `{"seed": <int>, "total_reward": <float>}` per seed; aggregate `{"mean": <float>, "std": <float>, "ci_95": [<float>, <float>], "effect_size": <float>}` per condition.

## 5. Secondary outcomes

| Outcome | Definition | Source data |
|---------|------------|-------------|
| Adaptation latency | Number of steps from a regime transition to recover to within 90% of the pre-transition mean reward. | Per-step reward; per-regime boundary step from env config. |
| Post-shift recovery | Cumulative reward in the 30 steps following a regime transition, normalized by pre-transition mean. | Same. |
| Transfer performance (forward) | Mean reward in the first 30 steps of Regime B (relative to the last 30 steps of Regime A). | Same. |
| Backward transfer | Mean reward in Regime A when revisited in Regime C (relative to original Regime A performance). | Same. |
| Forgetting | Decrease in performance on Regime A's task after training on Regime B. | Same. |
| Trajectory divergence | `DevelopmentalDivergence.mean_state_distance` between two organisms from the same genome in differently-seeded envs. | `nuros-dev/src/trajectory.rs:DevelopmentalDivergence::between`. |
| Memory footprint | Number of stored memory entries at end of run. | `MemoryEngine.memory_count` (Python) / `OrganismState.memory.len()` (Rust). |
| Retrieval count | Number of `MemoryEngine.retrieve()` calls during the run. | `MemoryEngine.operation_log` filtered by `MemoryOperation.RETRIEVE`. |
| Replay count | Number of `MemoryEngine.replay()` calls during the run. | Same, filtered by `MemoryOperation.REPLAY`. |
| Consolidation activity | Number of `MemoryEngine.consolidate()` calls + number of memories created. | Same, filtered by `MemoryOperation.CONSOLIDATE`. |
| Runtime | Wall-clock seconds for the full 300-step run. | `time.perf_counter()` at start/end of `run_experiment`. |
| Checkpoint size | Bytes of the serialized `MindCheckpoint` at end of run. | `len(checkpoint.to_json())`. |

## 6. Experimental conditions

| Condition | Implementation | Memory budget | heuristic_bias | maturation schedule | plasticity decay | self-model contribution |
|-----------|----------------|---------------|----------------|---------------------|------------------|--------------------------|
| A. Q-learning baseline | `benchmarks/baselines/q_learning/` (new) | 200 entries (matches Rust cap) | N/A (no bias in Q-learner) | N/A | N/A | N/A |
| B. NurosOS baseline | `MinimumOrganism` (current) | 200 entries (`organism.rs:233`) | ENABLED (current default) | ENABLED | ENABLED | ENABLED |
| C. NurosOS without maturation | Same, with maturation thresholds set to ∞ | 200 | ENABLED | DISABLED | ENABLED | ENABLED |
| D. NurosOS without plasticity decay | Same, with `plasticity *= 1.0` (no decay) | 200 | ENABLED | ENABLED | DISABLED | ENABLED |
| E. NurosOS without self-model | Same, with `self_model_*` fields zeroed in action selection | 200 | ENABLED | ENABLED | ENABLED | DISABLED |
| F. NurosOS without heuristic bias | Same, with `heuristic_bias()` returning 0.0 | 200 | **DISABLED** | ENABLED | ENABLED | ENABLED |

**Causal purpose of each condition**:

- **A** (Q-learning): establishes whether NurosOS provides measurable value beyond a conventional learning system. **Critical for falsifiability.**
- **B** (NurosOS baseline): the reference condition.
- **C** (no maturation): isolates the contribution of the developmental stage transitions.
- **D** (no plasticity decay): isolates the contribution of plasticity decay to retention/forgetting.
- **E** (no self-model): isolates the contribution of the rolling-average self-model to prediction accuracy.
- **F** (no heuristic bias): **CRITICAL** — isolates the contribution of the hard-coded task knowledge (audit §9 of RESEARCH_AUDIT.md).

**Conditions NOT run** (per master prompt PHASE 6: "Do not run all conditions automatically if some are not scientifically justified"):

- NurosOS with intrinsic motivation: NOT RUN. No intrinsic-motivation mechanism exists in the current codebase (would require implementation).
- HippoCore conditions (PHASE 15 of master prompt): NOT RUN during this preregistration. HippoCore is a future intervention (audit §15 of RESEARCH_AUDIT.md).

## 7. Environment definition

**Non-stationary 3-regime environment** (master prompt PHASE 5):

- **Regime A** (steps 0-99): `ResourceWorld(width=8, height=8, seed=env_seed, n_resources=5, n_hazards=2)`. Standard regime.
- **Regime B** (steps 100-199): `ResourceWorld(width=8, height=8, seed=env_seed + 1000, n_resources=3, n_hazards=4)`. Harder regime — fewer resources, more hazards, different RNG placement.
- **Regime C** (steps 200-299): `ChangingWorld(size=10, shift_interval=20, seed=env_seed + 2000)`. **Novel environment** — completely different env type. Tests transfer.

The env is **constructed in Python** to wrap the Rust envs and orchestrate the regime transitions. It must:

- Have **explicit regime transitions** (deterministic).
- Have **deterministic seed control** (env_seed for Regime A; env_seed + 1000 for B; env_seed + 2000 for C — ensures different placements but reproducible across runs with the same env_seed).
- Have **known ground truth** (regime transitions happen at fixed steps).
- Have **no hidden privileged information** — see PHASE 5 ablation below.
- Be **reproducible** (same env_seed + same organism_seed + same condition → same trajectory).

**PHASE 5 ablation**: the env's `observe()` payload is run in **two modes**:

1. **Privileged mode** (default): emits `direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`, `total_resource_left` (current Rust behavior, `environment.rs:242-250`).
2. **Raw mode**: emits only `agent_pos` and the reward signal. No privileged fields.

Conditions A-F are run in **both modes** (12 sub-conditions total). The privileged-mode results are the audit's "confounded" baseline; the raw-mode results are the audit's "fair" comparison.

## 8. Seed policy

- **30 independent seeds per condition** (master prompt PHASE 8). Seeds are integers `42, 43, 44, ..., 71` (30 values).
- The seed controls the env's initial state (resource/hazard placement) AND the organism's deterministic RNG (`deterministic_random` in `organism.rs:573-584`).
- Each seed produces a unique (env_state, organism_pseudo_rng_state) pair.
- **No seed selection based on performance.** Per master prompt PHASE 8: "Never select seeds based on performance."

## 9. Number of runs

- 30 seeds × 6 conditions (A-F) × 2 observation modes (privileged + raw) = **360 runs total**.
- Each run is 300 steps. Estimated wall-clock: ~1 second per run × 360 runs ≈ 6 minutes total compute. Tractable.

## 10. Hyperparameters

| Hyperparameter | Value | Source |
|----------------|-------|--------|
| `genome.plasticity_rules.learning_rate` | 0.1 | `nuros-dev/src/genome.rs` default |
| `genome.plasticity_rules.forgetting_rate` | 0.01 | same |
| `genome.biases.exploration_bias` | 0.3 | same |
| `genome.biases.risk_sensitivity` | 0.5 | same |
| `genome.energy_model.perceive_cost` | 0.01 | same |
| `genome.energy_model.predict_cost` | 0.01 | same |
| `genome.energy_model.act_cost` | 0.02 | same |
| `genome.energy_model.idle_regen` | 0.03 | same |
| `genome.maturation_schedule.nascent_to_developing` | 10 | same |
| `genome.maturation_schedule.developing_to_maturing` | 100 | same |
| `genome.maturation_schedule.maturing_to_mature` | 500 | same |
| Q-learning hyperparameters | α=0.1, γ=0.95, ε=0.1 | `benchmarks/baselines/q_learning/config.json` (to be created) |
| Total steps per run | 300 | this preregistration |
| Memory budget | 200 entries | matches Rust `organism.rs:233` cap |

## 11. Exclusion criteria

Per master prompt PHASE 8: "Never delete inconvenient runs without a preregistered exclusion rule."

A run is **excluded** if and only if:

1. The organism terminates mid-run (lifecycle transitions to `Terminated` before step 300) due to an implementation bug (not a designed safety shutdown). Documented as `exclusion_reason="premature_termination"` in the manifest.
2. The env raises an exception during the run. Documented as `exclusion_reason="env_exception"`.
3. The trajectory fails to deserialize after a checkpoint/restore. Documented as `exclusion_reason="restore_failure"`.

Excluded runs are **kept in the raw output** but excluded from the aggregated metrics. The exclusion count per condition is reported alongside the metrics.

**Exclusion is NOT permitted for**:
- Poor performance (low reward).
- Divergent behavior.
- "The result looks wrong."

## 12. Statistical analysis plan

**Primary outcome analysis**:

- Two-sample t-test (Welch's) comparing condition B vs condition A on cumulative reward, per observation mode.
- Significance threshold: α = 0.05 (two-tailed).
- Multiple-comparison correction: Bonferroni for 6 conditions × 2 modes = 12 comparisons; adjusted α = 0.05/12 ≈ 0.0042.
- Effect size: Cohen's d (pooled std).
- 95% confidence interval on the mean difference.
- Report: per-condition mean ± std + median (if distribution is non-normal) + 95% CI + effect size + p-value.

**Secondary outcome analysis**:

- Same statistical treatment as primary, applied to each secondary outcome.
- Adaptation latency + post-shift recovery: per-regime analysis (ANOVA across 3 regimes × 6 conditions).

**Distribution checks**:

- Shapiro-Wilk test for normality on each condition's seed distribution.
- If non-normal: report median + IQR instead of mean ± std, use Mann-Whitney U instead of t-test.
- Per-seed raw values are always reported (no aggregation hides the distribution).

**Prefer statistical methods appropriate to the actual experimental design rather than automatically applying a single test.**

## 13. Expected failure modes

| Failure mode | What it would mean | What we would report |
|--------------|---------------------|----------------------|
| H1 fails (no significant difference between B and A) | NurosOS provides no measurable value over Q-learning on this env | "We failed to reject H0; the NurosOS developmental substrate does not provide measurable behavioral value over tabular Q-learning on this non-stationary env with this memory budget." |
| B is significantly WORSE than A | NurosOS is actively harmful (likely due to the hard-coded bias overfitting to Regime A's resource geometry) | "The NurosOS baseline underperforms Q-learning; we attribute this to the hard-coded heuristic_bias overfitting to Regime A." |
| Condition F (no bias) is significantly better than B | The bias is harmful | "Removing the heuristic bias improves performance; we recommend the bias be made into an ablatable condition by default." |
| Condition F is significantly worse than B | The bias carries the performance; the learned signal is too weak | "The bias carries the performance; the learned component is too weak without it. The 'capabilities emerge through development' claim is unsupported on this env." |
| Raw mode shows no difference between conditions | The env is so easy that any learner trivially solves it | "The env is teacher-shaped; the privileged observation fields trivialize the learning problem. A more challenging env is needed." |

## 14. Falsification criteria

H1 is **falsified** if any of the following hold:

1. Effect size (Cohen's d) between B and A on primary outcome < 0.3, even if p < 0.05.
2. The 95% CI on the mean difference (B - A) includes 0.
3. After Bonferroni correction, no comparison is significant at α = 0.0042.

If H1 is falsified, the audit's recommended conclusion is:

> "We identified a developmental substrate architecture, measured its behavioral contribution against a conventional baseline, and found no measurable value under the specified conditions. The architecture is reproducible but does not provide scientific evidence for the developmental thesis on this env."

## 15. Stopping rules

- **Run all 360 trials** regardless of intermediate results. No early stopping based on observed performance.
- If a condition produces a runtime exception that affects > 50% of its 30 seeds, halt that condition, document the failure, and mark its results as `INCONCLUSIVE` in the report. Do NOT silently drop the condition.
- After all 360 trials complete, run the statistical analysis. If H0 cannot be rejected, the experiment is **complete and the negative result is reported**.

---

## Versioning

- v1.0 (this file) — committed before any large-scale experimental run.
- If implementation problems require changes (e.g., a condition cannot be implemented as specified), create v1.1 with the changes documented. Do NOT silently modify v1.0 after observing results.

**End of EXPERIMENTS.md (preregistration v1.0).**
