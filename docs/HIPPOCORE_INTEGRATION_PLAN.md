# HIPPOCORE INTEGRATION PLAN — Future Intervention

> **Master prompt PHASE 14**: HippoCore must remain a LATER intervention.
> **Master prompt PHASE 15**: Design (but do not necessarily execute) the future comparison.
> **Status**: PLAN ONLY — do not execute until the NurosOS baseline is empirically characterized.
> **Current branch state**: HippoCore code exists on `feature/hippocore-integration-audit` (247 Python tests, 10 phases). This document reframes that work as a **future experimental intervention** rather than a current capability.

---

## 1. Why HippoCore is premature (per RESEARCH_AUDIT.md §15)

The Memory Contract (PHASE 2 `MemoryEngine` ABC) is **architecturally ready** for HippoCore. But HippoCore is **scientifically premature** for three reasons:

1. **No baseline condition**: the NurosOS baseline (without HippoCore) has not been empirically characterized. There is no Q-learning baseline or NurosOS-only baseline against which HippoCore's value can be measured.
2. **Privileged observation confound** (RESEARCH_AUDIT.md §11): the env emits `direction_to_resource` + `nearest_resource_distance` + `on_resource` + `on_hazard`. Any HippoCore benefit could be attributed to the env being teacher-shaped rather than to episodic memory.
3. **Hard-coded bias confound** (RESEARCH_AUDIT.md §9): `MinimumOrganism::heuristic_bias` hard-codes resource-seeking. HippoCore's retrieval would have to compete with (or be diluted by) the bias — the experiment would be confounded.
4. **Memory is not consulted during action selection** (MEMORY_AUDIT.md "Memory → Behavior coupling audit"): `Organism.tick()` does not call `MemoryEngine.retrieve()` during action selection. HippoCore's episodic encoding + replay + consolidation are technically implemented but **not wired into behavior**.

**Recommended action**: do NOT activate HippoCore as a default. Run the audit's recommended experimental sequence (EXPERIMENTAL_ROADMAP.md Phases A-H) first.

---

## 2. The Memory Contract as abstraction boundary (master prompt PHASE 14)

The architecture must preserve:

```
NurosOS = developmental substrate
HippoCore = memory implementation / intervention
```

The PHASE 2 `MemoryEngine` ABC is the abstraction boundary. The selector is `OrganismConfig.memory_engine = "default" | "hippocore"` (default `"default"`). The HippoCore integration must NOT:

- Hard-code the entire organism around HippoCore internals.
- Create a competing memory system (must implement the same `MemoryEngine` ABC).
- Be wired into behavior until the NurosOS baseline is empirically characterized.

The HippoCore package (`nuros/hippocore/`) currently satisfies all three architectural constraints. The 247 Python tests pass; NO LLM dependency; deterministic when seeded.

---

## 3. The future HippoCore experiment (master prompt PHASE 15)

After the audit's recommended Phases A-H are complete, the following comparison can be run. **Design only — do not execute until baseline is established.**

### Conditions

| ID | Condition | heuristic_bias | Memory engine | Memory budget | Replay policy | Consolidation strategy | Pattern separation |
|----|-----------|-----------------|---------------|---------------|----------------|------------------------|---------------------|
| A | Q-learning baseline | N/A | N/A (tabular Q) | 200 entries | N/A | N/A | N/A |
| B | NurosOS baseline (no HippoCore) | ENABLED | `DefaultMemoryContract` (or no memory at all, since memory is not consulted) | 200 entries | N/A | N/A | N/A |
| C | NurosOS + HippoCore (full) | ENABLED | `HippoCoreMemory` | 200 entries | configurable | configurable | storage-level (current) |
| D | HippoCore − replay | ENABLED | `HippoCoreMemory` with `replay_policy = "recent"` and `replay(n=0)` (effectively disabled) | 200 | DISABLED | configurable | storage-level |
| E | HippoCore − pattern separation | ENABLED | `HippoCoreMemory` (currently storage-level only; would need an actual PS mechanism to ablate) | 200 | configurable | configurable | DISABLED (PHASE 10+ follow-up — no real PS mechanism exists yet) |
| F | HippoCore − consolidation | ENABLED | `HippoCoreMemory` with `consolidate()` returning 0 (no-op) | 200 | configurable | DISABLED | storage-level |

### Same across all conditions

- Genome (the same `DevelopmentalGenome` instance)
- Environment (the same non-stationary 3-regime env from `experiments/EXPERIMENTS.md` §7)
- Seed set (30 seeds: 42..71)
- Compute budget (300 steps per run)
- Memory budget (200 entries)
- Evaluation protocol (per `experiments/EXPERIMENTS.md`)

### Primary future question

> **Does structured episodic memory (HippoCore) improve adaptation under environmental change and constrained memory budget?**

This is the master prompt's preferred candidate question (PHASE 2). The audit accepts this question as the primary future HippoCore research question, contingent on:

- The NurosOS baseline (condition B) being empirically characterized against condition A (Q-learning) first.
- The env privileged-obs toggle being implemented (Phase A of EXPERIMENTAL_ROADMAP.md).
- The heuristic-bias ablation flag being implemented (Phase B).
- The non-stationary env being implemented (Phase D).
- `Organism.tick()` being wired to consult `MemoryEngine.retrieve()` during action selection (PHASE 10+ follow-up — see §5 below).

### Operationalization

| Element | Definition |
|---------|-----------|
| **Independent variable** | Memory engine implementation (`default` vs `hippocore` vs `hippocore` ablations) |
| **Dependent variables** | Primary: cumulative reward over 300 steps × 30 seeds. Secondary: adaptation latency, post-shift recovery, transfer performance, forgetting, backward transfer, memory footprint, retrieval count, replay count, consolidation activity, runtime, checkpoint size. |
| **Controlled variables** | genome, env (non-stationary 3-regime), seed set, compute budget (300 steps), memory budget (200 entries), evaluation protocol. |
| **Confounders** | (a) privileged env observation fields (mitigated by raw-mode runs); (b) hard-coded heuristic_bias (mitigated by ablation condition F of the audit's matrix); (c) memory not being consulted by action selection (mitigated by the §5 follow-up). |
| **Null hypothesis (H0)** | HippoCore provides no measurable behavioral value over `DefaultMemoryContract` on the non-stationary env with 200-entry memory budget. |
| **Alternative hypothesis (H1)** | HippoCore provides a statistically significant (α = 0.05, two-tailed, Bonferroni-adjusted) and practically significant (Cohen's d > 0.3) improvement over `DefaultMemoryContract` on the primary outcome. |
| **Prediction** | If episodic memory + replay + consolidation provide adaptation value under non-stationarity, condition C should outperform condition B, especially on Regime C (novel env) where memory of past regimes could aid transfer. |
| **Falsification condition** | H1 is falsified if effect size (Cohen's d) between C and B < 0.3 OR if the 95% CI on the mean difference (C - B) includes 0 OR if after Bonferroni correction no comparison is significant at α ≈ 0.0042. |

---

## 4. Memory budget comparison (master prompt PHASE 16)

Per master prompt: "A memory architecture must not receive unlimited capacity while the baseline is constrained."

The audit's plan: run the future HippoCore experiment at **three memory budgets**:

| Budget | Entries |
|--------|---------|
| Small | 50 |
| Medium | 200 (default) |
| Large | 1000 |

All conditions (A-F above) run at all three budgets. The Q-learning baseline also gets a budget-constrained variant (e.g., tabular Q with a 50-state LRU cache for the "Small" condition).

This ensures that any HippoCore benefit is NOT simply because HippoCore has more memory.

---

## 5. Critical PHASE 10+ follow-up: wire memory into action selection

The single biggest scientific gap is that `Organism.tick()` (Python) and `MinimumOrganism::tick` (Rust) **do not consult `MemoryEngine.retrieve()` during action selection** (MEMORY_AUDIT.md "Memory → Behavior coupling audit").

Before the future HippoCore experiment can produce meaningful results, the following wiring must be done:

### Python side

- `Organism.tick()` (`nuros/organism.py:178-211`) must call `self._memory.retrieve(query=obs_signature, limit=5)` to fetch similar past memories.
- The retrieved memories' actions (and their outcomes) must be combined with the learned `action_preferences` to produce the final action selection.

### Rust side

- `MinimumOrganism::select_action` (`organism.rs:408-441`) must consult `self.state.memory` (the `Vec<MemoryRecord>`) — e.g., look up the most-similar past MemoryRecord by `key` (the observation signature) and bias toward its action if it was rewarded.
- The `MemoryRecord.access_count` dead field (`organism.rs:41`) should be incremented on each retrieval (audit Appendix B.7 fix).

### Why this is PHASE 10+ and not during the audit

Per master prompt PHASE 21 (Change Control): "Do not perform broad refactoring before completing the audit." The memory → action-selection wiring is a non-trivial refactor that would confound the audit's baseline measurement. It should be done AFTER the audit's Phases A-H (baseline characterization) are complete.

The HippoCore integration code itself is technically sound — it implements the full `MemoryEngine` ABC with episodic encoding + 5 replay policies + 2 consolidation strategies + memory events + causal graph. The 247 Python tests pass. The only missing piece is the wiring to behavior.

---

## 6. Branch strategy

The HippoCore integration currently lives on `feature/hippocore-integration-audit`. Recommended branch strategy:

- Keep `feature/hippocore-integration-audit` as the HippoCore code home.
- Do NOT merge to `main` until:
  - The audit's recommended Phases A-H are complete (baseline characterized).
  - The memory → action-selection wiring is done (§5 above).
  - The future HippoCore experiment (§3) is run and produces a non-anecdotal result.
- A PR from `feature/hippocore-integration-audit` to `main` should include:
  - The audit documents (`docs/RESEARCH_AUDIT.md`, `docs/ARCHITECTURE_AUDIT.md`, `docs/MEMORY_AUDIT.md`, etc.).
  - The Q-learning baseline (`benchmarks/baselines/q_learning/`).
  - The non-stationary env (`environments/nonstationary.py`).
  - The experiment harness (`experiments/harness.py`).
  - The analysis + report (`experiments/analyze.py` + `experiments/report.md`).
  - The HippoCore code (`nuros/hippocore/` — already present).
  - The memory → action-selection wiring (PHASE 10+ follow-up).

---

## 7. What should NOT be done (per master prompt PHASE 21)

- DO NOT add new HippoCore features during the audit.
- DO NOT add an LLM to HippoCore (master prompt §23 of the original HippoCore master prompt).
- DO NOT add a neural network to HippoCore.
- DO NOT claim "HippoCore prevents catastrophic forgetting" — the audit's `bench_03_catastrophic_forgetting` benchmark currently measures `retention=1.0` because episodic memory does not overwrite; this is NOT the same as preventing catastrophic forgetting in a continual-learning weight-overwrite sense.
- DO NOT claim "biological equivalence to hippocampus" — the audit's HippoCore uses computational proxies (tag-Jaccard, content-prefix), not neural-circuit-accurate mechanisms.

**End of HIPPOCORE_INTEGRATION_PLAN.md.**
