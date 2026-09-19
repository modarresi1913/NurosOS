# ABLATION MATRIX

> **Master prompt PHASE 6**: Formal ablation matrix.
> **Companion to**: `experiments/EXPERIMENTS.md` (the preregistration).
> **Status**: SPECIFICATION — matrix is defined here; experimental runs will populate it.

The matrix isolates the causal contribution of each NurosOS subsystem to the
primary outcome (cumulative reward over 300 steps, mean across 30 seeds) on
the non-stationary 3-regime environment.

---

## Conditions

| ID | Condition | heuristic_bias | maturation schedule | plasticity decay | self-model | Memory budget | Note |
|----|-----------|-----------------|---------------------|------------------|-----------|---------------|------|
| **A** | Q-learning baseline | N/A | N/A | N/A | N/A | 200 entries | The falsifier — does NurosOS provide value beyond conventional learning? |
| **B** | NurosOS baseline | ENABLED | ENABLED | ENABLED | ENABLED | 200 entries | The reference. |
| **C** | NurosOS − maturation | ENABLED | DISABLED | ENABLED | ENABLED | 200 entries | Isolates maturation stage transitions. |
| **D** | NurosOS − plasticity decay | ENABLED | ENABLED | DISABLED | ENABLED | 200 entries | Isolates plasticity decay (does decay help or hurt retention?). |
| **E** | NurosOS − self-model | ENABLED | ENABLED | ENABLED | DISABLED | 200 entries | Isolates rolling-average self-model contribution. |
| **F** | NurosOS − heuristic bias | DISABLED | ENABLED | ENABLED | ENABLED | 200 entries | **CRITICAL** — isolates the hard-coded task knowledge (audit §9 of RESEARCH_AUDIT.md). |

**Sub-conditions**: each of A-F runs in **two observation modes**:

- Privileged mode (env emits `direction_to_resource` + `nearest_resource_distance` + `on_resource` + `on_hazard` — current Rust behavior, `environment.rs:242-250`).
- Raw mode (env emits only `agent_pos` + reward signal).

Total sub-conditions: 6 × 2 = 12.

**Conditions NOT run** (per master prompt PHASE 6):

- NurosOS + intrinsic motivation: mechanism does not exist in the codebase; would require implementation.
- NurosOS + HippoCore: HippoCore is a **future intervention** (audit §15 of RESEARCH_AUDIT.md, master prompt PHASE 14). NOT run during this ablation matrix.

---

## Causal purpose of each condition

### A. Q-learning baseline

**Question**: Does the NurosOS developmental substrate provide measurable behavioral value beyond a conventional tabular Q-learning baseline?

**Implementation**: `benchmarks/baselines/q_learning/` — to be created per master prompt PHASE 3 and `docs/BASELINE_SPEC.md`.

**Constraint**: Q-learning must use:
- The same env (the non-stationary 3-regime env from `experiments/EXPERIMENTS.md` §7).
- The same episode structure (300 steps × 30 seeds).
- A comparable action space (the same 6 actions: MoveRight/Left/Up/Down/Idle/Consume).
- The same evaluation seeds (42..71).
- Clearly documented hyperparameters (α=0.1, γ=0.95, ε=0.1 — see `docs/BASELINE_SPEC.md`).
- **No access to NurosOS-specific privileged information** (it uses the same observation payload the NurosOS organism uses, including the privileged fields if the run is in privileged mode; in raw mode, it uses only `agent_pos` + reward).

**Critical interpretation**: the purpose is **NOT** to make Q-learning look weak. The purpose is to establish whether NurosOS provides measurable value. If Q-learning outperforms NurosOS, the result is "NurosOS does not provide value on this env" — that is a valid scientific finding.

### B. NurosOS baseline

**Question**: Reference condition — what does the current NurosOS organism achieve on the non-stationary env?

**Implementation**: `MinimumOrganism` (current, `nuros-dev/src/organism.rs:135-552`).

**Settings**: defaults from `nuros-dev/src/genome.rs`. Memory cap 200 (`organism.rs:233`).

### C. NurosOS − maturation

**Question**: Does the maturation schedule (hard-coded stage transitions at step thresholds) causally affect behavior?

**Implementation**: Same as B, with `genome.maturation_schedule.{nascent_to_developing, developing_to_maturing, maturing_to_mature}` set to `u64::MAX` (so no stage transition ever fires; organism stays in `Nascent` forever).

**Causal interpretation**: If C performs identically to B, the maturation schedule has no behavioral effect on this env — it is bookkeeping, not development. If C differs from B, the stage transitions matter (worth investigating further).

### D. NurosOS − plasticity decay

**Question**: Does the plasticity decay (`dev.plasticity = (dev.plasticity * 0.999).max(0.05);` at `organism.rs:269`) causally affect retention or forgetting?

**Implementation**: Same as B, with the plasticity decay line replaced by `dev.plasticity = dev.plasticity;` (no decay). Requires a one-line toggle — recommend adding `genome.plasticity_rules.disable_decay: bool` flag (PHASE 10+ follow-up; for the audit, the toggle can be a feature flag in a separate Rust branch).

**Causal interpretation**: If D outperforms B on Regime C (novel env), plasticity decay was hurting adaptation — the organism was too rigid. If D underperforms B on Regime A (stable env), plasticity decay was helping stability.

### E. NurosOS − self-model

**Question**: Does the rolling-average self-model (expected_reward, expected_prediction_error at `organism.rs:239-244`) causally affect action selection?

**Implementation**: Same as B, with the self-model fields zeroed in `select_action` (they're not actually consulted there currently — so this ablation may have no effect; document that). The ablation is more meaningful at the developmental-state level (zero `self_model_stability`).

**Causal interpretation**: Likely null result, because the self-model is currently not read by `select_action`. This is itself a finding — it documents that the self-model is currently decorative.

### F. NurosOS − heuristic bias

**Question (CRITICAL)**: Does the hard-coded `heuristic_bias` (`organism.rs:451-503`) carry the organism's performance?

**Implementation**: Same as B, with `heuristic_bias()` modified to return `0.0` for all (action, observation) pairs. The organism selects actions purely from `action_preferences` (the learned signal).

**Causal interpretation**:

- If F performs **identically to or better than B**: the heuristic bias carries no weight; the learned signal is doing the work. **This would be a strong positive result for the developmental thesis.**
- If F performs **significantly worse than B**: the heuristic bias carries the performance; the learned signal is too weak without it. **This falsifies the "capabilities emerge through development" claim on this env.**
- If F is comparable to A (Q-learning): the NurosOS organism without bias is just a tabular learner with extra bookkeeping overhead. **This would suggest NurosOS provides no value beyond Q-learning when the bias is removed.**

This is the audit's **most important ablation condition**.

---

## Matrix layout

```
                       | Privileged obs mode | Raw obs mode      |
                       | cum_reward (mean±std) | cum_reward (mean±std) | effect_size vs B |
-----------------------|--------------------|--------------------|-------------------|
A. Q-learning          |  <to be measured>  |  <to be measured>  |  d_A vs B          |
B. NurosOS baseline    |  <to be measured>  |  <to be measured>  |  —                 |
C. NurosOS − maturation|  <to be measured>  |  <to be measured>  |  d_C vs B          |
D. NurosOS − plasticity| <to be measured>  |  <to be measured>  |  d_D vs B          |
E. NurosOS − self-model|  <to be measured>  |  <to be measured>  |  d_E vs B          |
F. NurosOS − bias      |  <to be measured>  |  <to be measured>  |  d_F vs B          |
```

Each cell will be filled with the mean ± std of the cumulative reward across 30 seeds, plus the effect size (Cohen's d) vs condition B in the same observation mode.

Per-seed raw values are kept in `experiment_outputs/<experiment_id>/raw/` per master prompt PHASE 10.

---

## Statistical analysis plan (recap from `experiments/EXPERIMENTS.md` §12)

- Two-sample t-test (Welch's) for each pair of conditions.
- Significance threshold: α = 0.05 (two-tailed).
- Bonferroni correction for 12 comparisons (6 conditions × 2 modes): adjusted α ≈ 0.0042.
- Effect size: Cohen's d (pooled std).
- 95% CI on the mean difference.
- Shapiro-Wilk for normality; Mann-Whitney U fallback if non-normal.

---

## Pre-registration lock

**This matrix is committed before any of its cells are measured.** Per master prompt PHASE 7: "Do not modify the hypothesis after observing results."

If the matrix needs to change (e.g., a condition cannot be implemented as specified), create v1.1 of this file with the changes documented in a "Changes" section at the end. Do NOT silently modify v1.0 after observing results.

**End of ABLATION_MATRIX.md (v1.0).**
