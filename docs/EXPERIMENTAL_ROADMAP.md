# EXPERIMENTAL ROADMAP

> **Companion to**: `docs/RESEARCH_AUDIT.md` (audit), `experiments/EXPERIMENTS.md` (preregistration), `experiments/ABLATION_MATRIX.md`.
> **Status**: SPECIFICATION — the recommended execution order for the audit's findings.
> **Master prompt ref**: PHASE 14 (HippoCore must remain a later intervention).

This roadmap is the audit's recommended sequence of work to transform NurosOS
from "interesting experimental substrate" into "rigorously testable research
platform."

---

## Phase ordering

The audit recommends the following 8 phases. **Phases 1-7 are pre-HippoCore.** Phase 8 introduces HippoCore as an experimental intervention, NOT as a default feature.

### Phase A — Env privileged-obs toggle (CRITICAL BLOCKER BL-1)

**Scope**: Add a `privileged_obs: bool` flag to `ResourceWorld` and `ChangingWorld` (Rust) + a Python wrapper for the non-stationary 3-regime env.

**Why critical**: Without this toggle, the env emits privileged state (`direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`, `total_resource_left`). Any learner (Q-learning included) trivially solves the env. The audit's claim that the env is "teacher-shaped" (RESEARCH_AUDIT.md §11) cannot be falsified without this toggle.

**File**: `nuros-dev/src/environment.rs` (modify `ResourceWorld::observe()` and `ChangingWorld::observe()` to gate the privileged fields).

**Test**: a unit test that confirms `observe()` in raw mode emits only `agent_pos` (+ reward via `Observation.reward`, which is always present).

**Effect**: enables the raw-mode sub-conditions in the ablation matrix.

**Estimated effort**: ~50 lines of Rust.

### Phase B — Heuristic-bias ablation flag (CRITICAL BLOCKER BL-2)

**Scope**: Add `genome.biases.disable_heuristic_bias: bool` flag (default false). When true, `MinimumOrganism::heuristic_bias()` returns 0.0 for all (action, observation) pairs.

**Why critical**: The hard-coded `heuristic_bias` (`organism.rs:451-503`) is the audit's primary scientific finding (RESEARCH_AUDIT.md §9). Without an ablation toggle, the audit cannot separate learned vs. hard-coded contributions.

**File**: `nuros-dev/src/genome.rs` (add field) + `nuros-dev/src/organism.rs:heuristic_bias` (early-return if flag is set).

**Test**: a unit test that confirms `heuristic_bias()` returns 0.0 for all actions when the flag is set.

**Effect**: enables condition F in the ablation matrix.

**Estimated effort**: ~10 lines of Rust.

### Phase C — Q-learning baseline (CRITICAL BLOCKER BL-3)

**Scope**: `benchmarks/baselines/q_learning/` with implementation + config + tests + deterministic seed support + result serialization.

**Why critical**: Without a baseline, the audit cannot claim that "NurosOS provides measurable value beyond a conventional simple learning system" (master prompt PHASE 3).

**Files**: `benchmarks/baselines/q_learning/{__init__.py, q_learning_agent.py, config.json, README.md, test_q_learning.py}`.

**Constraints**: same env, same episode structure, comparable action space, same seeds, no NurosOS-privileged info.

**See**: `docs/BASELINE_SPEC.md` for the full spec.

**Estimated effort**: ~250 lines of Python (incl. tests).

### Phase D — Non-stationary env (CRITICAL BLOCKER for the flagship)

**Scope**: Implement the 3-regime non-stationary env per `experiments/EXPERIMENTS.md` §7. Regime A (ResourceWorld, 0-99), Regime B (harder ResourceWorld, 100-199), Regime C (ChangingWorld, 200-299).

**Why critical**: The current envs saturate too quickly. A non-stationary env is required to test adaptation, transfer, forgetting, and memory usefulness (master prompt PHASE 5).

**Files**: `environments/nonstationary.py` (new Python wrapper).

**Tests**: a unit test that confirms regime transitions happen at fixed steps + the env is deterministic given a fixed env_seed.

**Estimated effort**: ~150 lines of Python.

### Phase E — Experiment harness (master prompt PHASE 10)

**Scope**: `experiment_outputs/<experiment_id>/{config.json, manifest.json, raw/, metrics/, trajectories/, checkpoints/, plots/, report.md}` directory layout.

**Files**: `experiments/harness.py` (new) — a Python module that wraps the experiment runner and produces the structured output.

**Estimated effort**: ~200 lines of Python.

### Phase F — Preregistration + 30-seed runs (CRITICAL BLOCKER BL-4, BL-5)

**Scope**: Run the full ablation matrix (6 conditions × 2 obs modes × 30 seeds = 360 runs) per `experiments/EXPERIMENTS.md` and `experiments/ABLATION_MATRIX.md`.

**Why critical**: Single-seed results are anecdotal (master prompt PHASE 8). The current WHITEPAPER flagship reports one seed pair (`env_a_seed=1, env_b_seed=999`) — this is anecdotal.

**Estimated wall-clock**: ~6 minutes (360 runs × ~1 second each). Tractable.

**Estimated effort**: ~50 lines of Python runner + ~6 minutes of compute.

### Phase G — Statistical analysis + report

**Scope**: Compute mean ± std + 95% CI + effect size + p-values per cell of the ablation matrix. Produce a final report following master prompt PHASE 22.

**Files**: `experiments/analyze.py` (new) — a Python module that reads `experiment_outputs/*/raw/*.json` and produces `report.md`.

**Estimated effort**: ~150 lines of Python.

### Phase H — Documentation integrity (master prompt PHASE 19)

**Scope**: Relabel claims in README/WHITEPAPER/SUMMARY/ROADMAP/RESEARCH_AGENDA/DEVELOPMENTAL_SUBSTRATE per the audit's findings (RESEARCH_AUDIT.md §3, ARCHITECTURE_AUDIT.md §3). Remove promotional language. Add the audit's caveats to every claim.

**Estimated effort**: documentation-only.

---

## Phase ordering rationale

The phases are ordered to **unblock scientific falsifiability as early as possible**:

1. Phase A (env toggle) + Phase B (bias ablation) — without these, no experiment can isolate causal contributions.
2. Phase C (Q-learning baseline) — without this, no claim of "NurosOS value" can be falsified.
3. Phase D (non-stationary env) — without this, the env saturates too quickly to test adaptation.
4. Phase E (experiment harness) — without this, results are not machine-readable per master prompt PHASE 10.
5. Phase F (30-seed runs) — without this, results are anecdotal.
6. Phase G (statistical analysis) — without this, results are not interpretable.
7. Phase H (documentation integrity) — without this, claims remain unsupported.

**HippoCore intervention** (Phase 8 of the master prompt's HippoCore plan): AFTER Phases A-G are complete and the NurosOS baseline is empirically characterized, the HippoCore integration (already on the feature branch `feature/hippocore-integration-audit`) can be activated as additional ablation conditions per `docs/HIPPOCORE_INTEGRATION_PLAN.md`.

---

## Out-of-scope (per master prompt PHASE 21 — Change Control)

The following are **NOT** in the audit's recommended roadmap:

- DO NOT add new HippoCore features during Phases A-H.
- DO NOT add an LLM.
- DO NOT add a neural network.
- DO NOT refactor the Rust architecture.
- DO NOT delete legacy code without migration documentation (the audit recommends migration decisions in `docs/ARCHITECTURE_AUDIT.md` §4).
- DO NOT wire `MemoryEngine.retrieve()` into `Organism.tick()` during the audit (master prompt PHASE 14 — keep memory as a future intervention).

**End of EXPERIMENTAL_ROADMAP.md.**
