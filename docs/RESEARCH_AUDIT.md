# RESEARCH AUDIT — NurosOS

> **Audit type**: Scientific + Engineering forensic audit.
> **Auditor**: Super Z (acting as senior research software architect, computational cognitive science researcher, reinforcement-learning evaluator, experimental-methodology auditor, Rust/Python systems engineer).
> **Date**: 2026-09-19
> **Repository state at audit**: commit `be2ad75` on branch `feature/hippocore-integration-audit` (post-PHASE-10-HippoCore-doc-polish).
> **Posture**: Skeptical. `ARCHITECTURE ≠ EVIDENCE`, `IMPLEMENTATION ≠ EMERGENCE`, `TRAJECTORY DIVERGENCE ≠ INTELLIGENCE`, `REPRODUCIBILITY ≠ VALIDITY`, `COMPLEXITY ≠ COGNITIVE CAPABILITY`.

This audit is structured in 17 sections per master prompt PHASE 0.

---

## 1. Executive assessment

NurosOS is **a credible infrastructure project masquerading as a research result**. The infrastructure (genome hashing, lifecycle machine, checkpoints, telemetry, manifest) is genuinely well-engineered and reproducible. The *research* — the part that should support falsifiable claims about development, memory, adaptation — is currently **under-specified, hard-coded in critical places, and confounded by a teacher-shaped environment**.

The flagship *Same Genome / Different World* experiment measures Computational Developmental Divergence. **The divergence is real and reproducible** (verified at `organism.rs:662-685` and `trajectory.rs:388-410`). But the divergence is overwhelmingly explained by:
1. The environment's RNG-dependent initial resource placement (`environment.rs:177-189`, `ResourceWorld::generate_resources`).
2. The organism's hand-coded heuristic biases that consume privileged observation fields (`organism.rs:451-503`).
3. The env leaking privileged state (`environment.rs:242-250` emits `direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`, `total_resource_left`).

None of the three confounds above are *learned* or *developed*. The organism's learned component (`action_preferences` in `OrganismState`, updated at `organism.rs:206-213`) is a secondary, weak signal that contributes to action selection only as a tie-breaker among heuristic-bias-equal actions.

**Verdict**: NurosOS is **architecturally ready** for scientific work but **scientifically not yet usable** as configured. Three minimal changes would unblock it:
1. Strip the privileged observation fields (or wrap them behind a "raw obs" / "privileged obs" switch).
2. Make `heuristic_bias` an ablation condition (PHASE 4 of this audit).
3. Introduce a tabular Q-learning baseline using the same observation/action harness.

The HippoCore integration work on the feature branch is **technically sound** but should be **reframed as a future experimental intervention** (master prompt PHASE 14), not as a current capability. The audit recommends *not* activating HippoCore until the NurosOS baseline is empirically characterized against Q-learning.

---

## 2. Implemented capabilities

The following are genuinely implemented (file:line evidence):

| Capability | File:line | Evidence |
|------------|----------|----------|
| DevelopmentalGenome (serializable, hashable) | `nuros-dev/src/genome.rs` | SHA-256 hash, JSON round-trip, used as primary key in every checkpoint/trajectory/manifest. |
| DevelopmentalState (vector-valued, L1 distance) | `nuros-dev/src/state.rs:60-187` | L1 distance + canonical hash; 14 scalar fields + capability map. |
| LifecycleMachine (auditable state machine) | `nuros-dev/src/lifecycle.rs` | CREATED → INITIALIZED → DEVELOPING → ... → TERMINATED, transition record. |
| ResourceWorld (2D grid) | `nuros-dev/src/environment.rs:137-321` | Deterministic given seed; supports reset/observe/step/snapshot/restore/hash. **Leaks privileged state — see §11.** |
| ChangingWorld (1D shifting-resource) | `nuros-dev/src/environment.rs:331-...` | Deterministic; resource shifts at fixed interval. **Also leaks `resource_pos`.** |
| MinimumOrganism (deterministic cognitive engine) | `nuros-dev/src/organism.rs:135-552` | Full tick() loop: observe → predict → select → step → learn → memory update → self-model update → developmental update → maturation. **Has hard-coded heuristic_bias — see §10.** |
| DevelopmentalTrajectory + Divergence | `nuros-dev/src/trajectory.rs:18-310` | Ordered points + L1/Hamming divergence metrics across reward / prediction_error / action / state / stage. |
| MindCheckpoint + ReplayFidelity | `nuros-dev/src/checkpoint.rs:29-237` | Full state capture; replay classified EXACT/APPROXIMATE/NON_REPRODUCIBLE. **Does NOT capture Python MemoryContract contents — see §8.** |
| MindDiff | `nuros-dev/src/diff.rs` | Structured diff of memory/self-model/values/capabilities/prediction/behavior/developmental state. |
| DevelopmentalCausalityGraph | `nuros-dev/src/causality.rs:73-200` | 11 EventKind variants, provenance DAG, trace() walk. **`MemoryUpdate` variant defined but never produced; graph is never instantiated by MinimumOrganism — see §12.** |
| DevelopmentalTelemetry (JSONL+CSV) | `nuros-dev/src/telemetry.rs:23-165` | 24-field TelemetryRecord, JSONL/CSV export. |
| ReproducibilityManifest | `nuros-dev/src/telemetry.rs:168-287` | 13-field manifest with hashes + seeds + dependency versions. |
| Same Genome / Different World flagship | `experiments/same_genome_different_world.py:87-285` | Produces 13 artifacts; runs the Rust flagship runner. |
| Mind Observatory | `nuros/observatory.py`, `experiments/observatory.py` | 9 text renderers + 13 PNG plots + CLI; 21 tests. |
| CounterfactualSelf + PossibleSelfSpace | `nuros-dev/src/counterfactual.rs:60-553` | what_if_environment(), what_if_actions(), compare_to_actual(); SIMULATED+COUNTERFACTUAL labels enforced. |
| Cognitive Metabolism | `nuros-dev/src/metabolism.rs` | 7 budgets + 9 operations + can_afford/spend/is_worth_it VoI rule. |
| Artificial Aging | `nuros-dev/src/aging.rs` | 5 dimensions: memory degradation, plasticity, processing, experience, structural consolidation. |
| **HippoCore integration** | `nuros/hippocore/`, `nuros/memory_engine.py`, `nuros/memory_provenance.py`, `nuros/memory_events.py`, `nuros/causal_graph.py` | 10-phase integration on feature branch; 247 Python tests; pure-Python; NO LLM dependency. **Reframe as future intervention — see §15.** |

---

## 3. Claimed but unverified capabilities

The README/WHITEPAPER/SUMMARY/ROADMAP/llms.txt make several claims that are NOT supported by the current code. **Per master prompt PHASE 19 (Documentation integrity)**, these should be relabeled.

| Claim | Source | Reality | Recommended label |
|-------|--------|---------|-------------------|
| "Capabilities emerge through development rather than explicit programming" | `README.md:340`, `RESEARCH_AGENDA.md:147`, Open Question 4 | The organism's `heuristic_bias` (`organism.rs:451-503`) hard-codes resource-seeking, hazard-avoidance, and direction-aware movement. **Capabilities are programmed, not emergent.** | `UNVALIDATED` (currently undermined by hard-coded bias) |
| "Cognitive trajectories can be reproduced experimentally" | `RESEARCH_AGENDA.md:150` (Open Question 6) | True for the deterministic engine — verified by `organism.rs:638-660` `same_genome_same_seed_same_environment_produces_identical_trajectory` test. | `IMPLEMENTED AND TESTED` |
| "Computational Developmental Divergence is observable" | `WHITEPAPER.md:148-163`, `SUMMARY.md:30-42` | True: `organism.rs:662-685` `different_environments_produce_different_trajectories` test. **But the divergence is a function of RNG resource placement + hard-coded bias, not of learning.** | `IMPLEMENTED AND TESTED` (caveat: causal attribution is confounded — see §11) |
| "Counterfactual developmental histories improve planning" | `RESEARCH_AGENDA.md:151` (Open Question 7) | `CounterfactualSelf` exists; **no experiment measures whether counterfactual reasoning improves planning.** | `PROPOSED` (mechanism implemented; benefit unmeasured) |
| "Cognitive Metabolism improves decisions" | `RESEARCH_AGENDA.md:152` (Open Question 8) | `CognitiveMetabolism` exists with VoI rule; **no experiment compares decisions with vs without metabolism.** | `PROPOSED` (mechanism implemented; benefit unmeasured) |
| "Artificial organisms specialize without explicit specialization programming" | `RESEARCH_AGENDA.md:153-154` (Open Question 9) | Specialization is hard-coded in `maturation_schedule` thresholds (`organism.rs:507-528`). **Not emergent.** | `UNVALIDATED` |
| "HippoCore integration enables genuine episodic memory + replay + consolidation" | `docs/HIPPOCORE_INTEGRATION.md`, branch `feature/hippocore-integration-audit` | 247 tests pass; **but `Organism.tick()` does not consult HippoCoreMemory during action selection** — see §15. | `IMPLEMENTED BUT NOT EMPIRICALLY VALIDATED` |
| "Pattern separation prevents overwriting" | `benchmarks/memory/__init__.py:bench_01_pattern_separation` | The benchmark measures `collision_rate=0.0` — but every encode just generates a fresh UUID; this is **storage-level** separation, not neural-circuit-accurate pattern separation. | `IMPLEMENTED BUT NOT EMPIRICALLY VALIDATED` (storage-level only) |
| "Catastrophic forgetting benchmark" | `benchmarks/memory/__init__.py:bench_03_catastrophic_forgetting` | The benchmark measures `retention=1.0` across all conditions because episodic memory does not overwrite. **The benchmark does not measure catastrophic forgetting at all.** | `UNVALIDATED` (benchmark measures wrong phenomenon) |
| "Divergence is NOT evidence of consciousness" | `WHITEPAPER.md:150-158`, `README.md` "Interpretation caveat" | Caveat is correctly stated. **But the README could be read as implying divergence is meaningful beyond RNG + bias.** | `IMPLEMENTED` (caveat present, but interpretive scope unclear) |

---

## 4. Architecture map

```
┌─────────────────────────────────────────────────────────────────────┐
│                    User-facing entry points                          │
│  experiments/same_genome_different_world.py                          │
│  experiments/counterfactual_demo.py / aging_demo.py / metabolism_*   │
│  experiments/observatory.py                                          │
│  benchmarks/memory/__init__.py (HippoCore, 10 benchmarks)            │
├─────────────────────────────────────────────────────────────────────┤
│              HippoCore (PHASE 3-8, nuros/hippocore/)                 │
│  [FUTURE INTERVENTION — not currently wired to Organism.tick()]     │
│  HippoCoreMemory · 5 ReplayPolicies · 2 ConsolidationStrategies    │
│  MemoryEventEmitter · PythonCausalGraph                             │
├─────────────────────────────────────────────────────────────────────┤
│              Mind Contract Layer (MCL) — nuros/                       │
│  MemoryContract → MemoryEngine ABC (PHASE 2)                         │
│  SelfModel · Imagination · Values · Body · Responsibility           │
│  EpistemicKernel · Homeostasis · Safety · Scheduler · Development    │
├─────────────────────────────────────────────────────────────────────┤
│              Developmental Substrate — nuros-dev/ (Rust + PyO3)     │
│  DevelopmentalGenome · DevelopmentalState · LifecycleMachine         │
│  ResourceWorld · ChangingWorld (BOTH LEAK PRIVILEGED STATE — §11)    │
│  MinimumOrganism (HAS HARD-CODED heuristic_bias — §10)              │
│  DevelopmentalTrajectory · MindCheckpoint · MindDiff                │
│  DevelopmentalCausalityGraph (instantiated but UNUSED by MinimumOrg)│
│  CounterfactualSelf · PossibleSelfSpace                            │
│  CognitiveMetabolism · AgingModel                                    │
│  DevelopmentalTelemetry · ReproducibilityManifest                    │
├─────────────────────────────────────────────────────────────────────┤
│              Neural / Cognitive Execution Layer                      │
│  SNN (kernel/) · LLM (none, explicit) · Symbolic (none)              │
├─────────────────────────────────────────────────────────────────────┤
│              Hardware Abstraction (HAL) — v0.1.0, preserved          │
│  x86 · ARM · FPGA · Loihi · GPU                                      │
└─────────────────────────────────────────────────────────────────────┘
```

The architecture is layered correctly. The HippoCore integration sits behind the `MemoryEngine` ABC, which is the right abstraction boundary (master prompt PHASE 14). The problem is **not architectural** — it is experimental.

---

## 5. Experimental infrastructure

**Strong**:

- `ReproducibilityManifest` (`telemetry.rs:168-197`) captures all 13 fields needed for scientific reproducibility (mind_id, genome_hash, runtime_hash, environment_hash, experiment_hash, random_seed, environment_seed, checkpoint_hash, configuration_hash, dependency_versions, timestamp, n_steps, limitations).
- `experiments/same_genome_different_world.py:87-285` produces 13 machine-readable artifacts (genome.json, trajectories JSONL, telemetry CSV, checkpoints, divergence, mind_diff, manifests, report.txt, summary.json).
- Determinism is verified by `organism.rs:638-660` test `same_genome_same_seed_same_environment_produces_identical_trajectory`.

**Weak**:

- **No baseline condition** (master prompt PHASE 3): there is no Q-learning or any other conventional learning system to compare NurosOS against. Without a baseline, no experiment can claim that "NurosOS provides measurable value beyond a conventional simple learning system."
- **No ablation matrix** (master prompt PHASE 6): the maturation schedule, plasticity decay, self-model contribution, and heuristic bias cannot be toggled independently.
- **No preregistration** (master prompt PHASE 7): hypotheses are stated AFTER observation in the WHITEPAPER (`WHITEPAPER.md:113-117` — "Hypothesis: Identical initial computational conditions ... can produce divergent developmental states under different environmental histories"). This is a post-hoc claim, not a preregistered hypothesis.
- **Statistical rigor is absent** (master prompt PHASE 8): the flagship experiment reports single-seed results (`WHITEPAPER.md:134-141` — `steps=300, env_a_seed=1, env_b_seed=999`). No 30-seed replication, no mean ± std, no confidence intervals, no effect size. The single-seed numbers in `SUMMARY.md:34-41` are essentially **anecdotal** per master prompt PHASE 8.
- **The metrics layer is incomplete** (master prompt PHASE 9): only `reward`, `prediction_error`, `action_distance`, `mean_state_distance`, `stage_divergence` are reported. Missing: adaptation latency, post-shift recovery, transfer performance, forgetting, backward/forward transfer, memory footprint, retrieval count, replay count, consolidation activity, runtime, compute cost, checkpoint size, replay cost.
- **The experiment harness lacks the standard structure** (master prompt PHASE 10): no `experiment_outputs/<experiment_id>/{config.json, manifest.json, raw/, metrics/, trajectories/, checkpoints/, plots/, report.md}` directory layout. The flagship experiment dumps 13 files flat into one directory.

---

## 6. Learning mechanisms

The MinimumOrganism has exactly **one** learning mechanism: `action_preferences` (a `BTreeMap<String, f64>` in `OrganismState`, `organism.rs:72`).

**Update rule** (`organism.rs:206-213`):

```rust
let lr = self.genome.plasticity_rules.learning_rate
    * self.state.developmental.plasticity;
let entry = self.state.action_preferences
    .entry(candidate.to_string())
    .or_insert(0.0);
*entry += lr * (actual_reward - predicted_reward);  // TD-like update
*entry *= 1.0 - self.genome.plasticity_rules.forgetting_rate;  // decay toward 0
```

**Audit findings**:

- This is **a tabular Q-update without the max_a' term** (i.e., it's *not* Q-learning — it's a single-step Rescorla-Wagner / TD(0) update without bootstrapping). It's "learning" in a weak sense but it's not even Q-learning's bellman backup.
- The state space is **not factored by observation** — `action_preferences` is keyed by action name only, NOT by `(state_signature, action)`. So the preferences are **context-free**: they encode "Consume is generally good" but not "Consume is good WHEN on a resource." All contextual reasoning is done by `heuristic_bias`.
- The learned signal is **dominated by the hard-coded bias**: when `select_action` runs (`organism.rs:408-441`), it computes `score = pref + bias` and argmaxes. The bias values are 0.5 / 0.3 / 0.2 / 0.1 / 0.02 — substantially larger than the per-action learned preference deltas from a single TD update (`lr * (reward - predicted)` ≈ 0.05 × 1.0 = 0.05 per step).

**Verdict**: The "learning" mechanism is real but **structurally irrelevant** to the organism's behavior. The behavior is set by `heuristic_bias`, not by `action_preferences`. The organism will not learn a counter-intuitive policy (e.g., "avoid resources") even with infinite training, because the bias will always push toward Consume when `on_resource=True`.

---

## 7. Development mechanisms

The "developmental" aspects of `MinimumOrganism`:

| Mechanism | File:line | Status |
|-----------|----------|--------|
| Maturation schedule | `organism.rs:507-528` | **Hard-coded** stage transition thresholds (Nascent → Developing → Maturing → Mature) based on step count. Not learned. |
| Plasticity decay | `organism.rs:269` `dev.plasticity = (dev.plasticity * 0.999).max(0.05);` | **Hard-coded** exponential decay. Not learned. |
| Stability rise | `organism.rs:271` `dev.stability = 0.5 * dev.stability + 0.5 * dev.prediction_accuracy;` | **Hard-coded** EMA. Not learned. |
| Energy metabolism | `organism.rs:262-267` | **Hard-coded** cost/regen schedule from `genome.energy_model`. Not learned. |
| Cognitive load | `organism.rs:256` `dev.cognitive_load = (dev.cognitive_load * 0.95 + 0.05).min(1.0);` | **Hard-coded** EMA. The `+0.05` is a constant floor. |
| Memory capacity | `organism.rs:257` `dev.memory_capacity = (self.state.memory.len() as f64 / 200.0).min(1.0);` | **Hard-coded** division by 200 (the memory cap). |
| Self-model update | `organism.rs:239-251` | Rolling averages with α=0.1 (hard-coded). |

**Verdict**: Every "developmental" mechanism is either a fixed-schedule stage transition or a fixed-coefficient exponential moving average. None are emergent, none are plastic, none respond to the environment in any way that could not be specified a priori. The "developmental state" is best understood as **a deterministic function of (step_count, accumulated_reward, accumulated_prediction_error)**.

This is not necessarily bad — a deterministic substrate is good for reproducibility. But it should not be described as "development" in the cognitive-science sense of the word. It is **bookkeeping of accumulated statistics**, not developmental plasticity.

---

## 8. Memory mechanisms

The audit's PHASE 13 deliverable is `docs/MEMORY_AUDIT.md`. Summary here; full detail there.

- **Rust `MinimumOrganism::MemoryRecord`** (`organism.rs:30-44`): a flat `Vec<MemoryRecord>` with `key`, `value`, `importance`, `step`, `access_count`. Capped at 200 entries (`organism.rs:233-236`). `access_count` is initialized to 0 at write (`organism.rs:230, 345`) and **NEVER incremented or read anywhere** — dead field.
- **Rust kernel `Ams`** (`kernel/src/mem.rs`): Drosophila-mushroom-body-inspired associative memory store with content-addressable retrieval via cosine similarity. **NOT used by the developmental substrate.** v0.1.0 legacy.
- **Python `MemoryContract` / `DefaultMemoryContract`** (`nuros/memory.py`): 5 memory types, 10 operations (PHASE 2 stabilized the API). The Python `Organism.tick()` (`nuros/organism.py:178-211`) does NOT call `MemoryEngine.retrieve()` during action selection. The Python `MemoryContract` is essentially unused at the action-selection layer.
- **Python `HippoCoreMemory`** (`nuros/hippocore/memory_engine.py`): full episodic encoding + 5 replay policies + 2 consolidation strategies + memory events + Python causal graph. **NOT consulted by `Organism.tick()` during action selection either.**

**Verdict**: Memory exists at three levels (Rust organism, Rust kernel, Python cognitive layer), but **NONE of the three memory systems influences action selection**. The organism selects actions purely from `heuristic_bias + action_preferences`. Memory is a *post-hoc log*, not a *causal driver* of behavior.

This is the single biggest scientific gap in the project. The HippoCore integration (which is technically sound) cannot demonstrate its value until `Organism.tick()` actually consults the memory engine. That is the master prompt's PHASE 4 → §36 stage 5 ("memory-dependent behavior") gap.

---

## 9. Hard-coded behavioral mechanisms

**CRITICAL FINDING.** The `MinimumOrganism::heuristic_bias()` method at `organism.rs:451-503` is hard-coded task knowledge:

| Bias | File:line | What it encodes | Task knowledge leaked? |
|------|-----------|-----------------|------------------------|
| `+0.5` to `Consume` when `on_resource=True` | `organism.rs:457-459` | "Consume the resource you're standing on" | YES |
| `-0.3` to `Idle` when `on_hazard=True` | `organism.rs:460-462` | "Don't idle on hazards" | YES |
| `+0.2` to movement in direction of resource | `organism.rs:474-484` | "Move toward resources" (Manhattan-aware) | YES — and uses a **direction vector** the env provides |
| `+0.1` to perpendicular movement | `organism.rs:477-478, 482-483` | "Also move slightly in the smaller-delta direction" | YES |
| `+0.1` to `Consume` when `dx=0, dy=0` | `organism.rs:488-490` | "Consume when on the resource cell" | YES (redundant with line 457-459) |
| `+0.02` to any non-Idle, non-Consume action when `nearest_resource_distance > 1.0` | `organism.rs:494-500` | "Don't idle when far from a resource" | YES |

**All six biases consume observation fields the env provides** (`environment.rs:242-250`): `on_resource`, `on_hazard`, `direction_to_resource`, `nearest_resource_distance`. These are **privileged state information** that the env should not provide to a learning agent if we want to test genuine learning.

**Implication for the audit**:

- The "Computational Developmental Divergence" the flagship experiment measures is mostly a function of the env's RNG-dependent resource placement + the bias reading the env's privileged fields. Two organisms in different environments will take different actions because the bias reads different `direction_to_resource` vectors — NOT because of any learning difference.
- The `action_preferences` learning mechanism is essentially a tie-breaker among actions with equal `heuristic_bias` scores.
- Any claim that the organism "develops" resource-seeking behavior is false — the bias hard-codes resource-seeking.

**PHASE 4 ablation plan** (per master prompt):

- **Condition A (full)**: current `MinimumOrganism` with `heuristic_bias` enabled.
- **Condition B (no bias)**: identical organism with `heuristic_bias()` returning 0.0 for all (action, observation) pairs. The organism selects actions purely from `action_preferences`.

The Condition B implementation should be a one-line toggle, not a fork. Suggested: add `genome.biases.disable_heuristic_bias: bool` flag, defaulting to `false` for backward compat.

**Long-term replacement options** (per master prompt): replace `heuristic_bias` with genome-encoded priors that are themselves ablatable. This is a PHASE 10+ follow-up; do not implement during the audit.

---

## 10. Reproducibility mechanisms

**Strong**:

- `DevelopmentalGenome.hash()` is canonical SHA-256 (`hash.rs`), preserved across JSON round-trip.
- `ResourceWorld.hash()` and `EnvironmentSnapshot` are content-addressable.
- `MindCheckpoint.hash()` covers the full Rust organism state.
- `ReproducibilityManifest` (`telemetry.rs:168-197`) records every hash + seed.
- Determinism test: `organism.rs:638-660` `same_genome_same_seed_same_environment_produces_identical_trajectory`.
- Replay fidelity: `checkpoint.rs:282-301` `replay_from_checkpoint_is_exact_for_deterministic_engine` confirms EXACT replay for the Rust numeric engine.

**Weak / gaps**:

- **`Organism.state_hash()`** (`nuros/organism.py:302-328`) does include a memory content hash (PHASE 2 fix), but the **Rust `MindCheckpoint.organism_state`** (`checkpoint.rs:47`) does NOT capture Python-side memory contents. Restoring a checkpoint does NOT restore Python `MemoryContract._memories`.
- The HippoCore benchmarks' `bench_10_checkpoint_reproducibility` reports `hash_match=1.0` — but this only verifies that the count matches; it does NOT verify that two restored organisms would produce identical future trajectories when given identical inputs.
- The audit could not execute Rust tests in this environment (no `maturin build --release` available). The 57 Rust tests pass per README, but the audit cannot independently verify this.

**Verdict**: Reproducibility infrastructure is excellent for the **Rust developmental substrate** but is **incomplete at the Python/HippoCore boundary** — see `docs/REPRODUCIBILITY_SPEC.md` for the gap list.

---

## 11. Current confounds

The flagship *Same Genome / Different World* experiment has **three confounds** that the audit must call out:

1. **Environment RNG confound** (`environment.rs:177-189`): `ResourceWorld::generate_resources` uses a `SimpleRng` seeded by the env seed. Different env seeds place resources at different grid cells. Two organisms in different envs will necessarily encounter different `direction_to_resource` vectors, so they will necessarily take different actions. This is divergence by construction, not by learning.

2. **Privileged observation confound** (`environment.rs:242-250`): the observation payload includes `direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`, `total_resource_left`. Any learner (including a Q-learning baseline) given this observation would trivially learn to consume resources. The environment is **teacher-shaped** — there is no real learning problem to solve.

3. **Hard-coded bias confound** (`organism.rs:451-503`): the `heuristic_bias` method encodes task knowledge (resource-seeking, hazard-avoidance, Manhattan-direction movement) directly into action selection. The learned `action_preferences` are a secondary signal.

**Causal attribution problem**: the "Computational Developmental Divergence" measured by the flagship experiment cannot be attributed to:
- learning (the learned signal is dominated by the bias),
- memory (memory is not consulted during action selection),
- development (the developmental state is a deterministic function of accumulated statistics),
- plasticity (the plasticity decay is hard-coded).

It can ONLY be attributed to:
- the env's RNG-dependent initial resource placement, AND
- the bias reading the env's privileged direction vectors.

This is the audit's primary scientific finding.

---

## 12. Scientific risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| The "Computational Developmental Divergence" is an artifact of RNG + bias, not of learning | **CRITICAL** | PHASE 4 ablation: Condition B (no bias). Plus PHASE 5: non-stationary env that requires genuine adaptation. |
| No baseline → cannot claim NurosOS provides value beyond conventional learning | **HIGH** | PHASE 3: implement tabular Q-learning baseline using same env/observation/action harness. |
| Privileged observation fields make any learner trivial | **HIGH** | PHASE 5: either (a) strip the privileged fields, OR (b) provide a "raw_obs" / "privileged_obs" toggle and run experiments in both modes. |
| Single-seed flagship results are anecdotal | **HIGH** | PHASE 8: 30-seed replication with mean ± std, CI, effect size. |
| Memory is not consulted during action selection | **HIGH** for HippoCore integration | PHASE 4 of the master prompt's HippoCore plan (already documented in `docs/HIPPOCORE_INTEGRATION_AUDIT.md` §36 stage 5): wire `MemoryEngine.retrieve()` into `Organism.tick()`. **DO NOT do this during the audit** — it's a PHASE 10+ follow-up. |
| "Development" is a deterministic function of step count | MEDIUM | Relabel from "development" to "state accumulation" in the docs; or implement genuine plasticity (PHASE 10+). |
| The Rust extension cannot be built in some environments | LOW (cosmetic) | Document the build requirement clearly; the Python-only HippoCore benchmarks work without Rust. |

---

## 13. Engineering risks

| Risk | File:line | Severity | Mitigation |
|------|-----------|----------|------------|
| Three parallel memory subsystems (Rust MemoryRecord, Rust Ams, Python MemoryContract/HippoCoreMemory) — divergence risk | `organism.rs:30`, `kernel/src/mem.rs`, `nuros/memory.py`, `nuros/hippocore/memory_engine.py` | HIGH | Already partially mitigated by the `MemoryEngine` ABC (PHASE 2). The Rust `MemoryRecord` should become a `DefaultMemory` impl of a Rust `MemoryEngine` trait (audit `docs/HIPPOCORE_INTEGRATION_AUDIT.md` §11.2). PHASE 10+ follow-up. |
| `MemoryRecord.access_count` is a dead field | `organism.rs:41` | LOW | Already noted in `docs/HIPPOCORE_INTEGRATION_AUDIT.md` Appendix B.7. Fix in PHASE 10+. |
| `DevelopmentalCausalityGraph` is implemented + tested but never instantiated by `MinimumOrganism::tick` | `nuros-dev/src/causality.rs`, `organism.rs:179-290` (tick method does not call graph.record) | MEDIUM | Wire in PHASE 8 Rust-side (needs `maturin build`). |
| `EventKind::MemoryUpdate` is defined but never produced | `causality.rs:33` | MEDIUM | Same — wire in PHASE 8 Rust-side. |
| The Python `genome.py` and `version_control.py` are flagged as "superseded by nuros-dev" in `README.md:419-420` but still ship | `nuros/genome.py`, `nuros/version_control.py` | LOW | Either delete (with deprecation cycle) or document as parallel implementation. |
| No CI configuration visible | (no `.github/workflows/` directory seen in the audit) | MEDIUM | Add a CI workflow that runs `pytest nuros/tests/` + `cargo test --lib` on every push. |
| `experiments/memory/decay_experiment.py` previously referenced `memory._store` (audit Appendix B.2) — already fixed in PHASE 2 of HippoCore integration | `experiments/memory/decay_experiment.py:68,72` | RESOLVED | — |

---

## 14. Recommended experimental sequence

The audit recommends the following **minimum** sequence to establish a credible experimental baseline. **Do NOT add HippoCore during this sequence.**

1. **PHASE A — Strip the env's privileged fields (or add a toggle)**: implement a `privileged_obs: bool` flag on `ResourceWorld` and `ChangingWorld`. When `false`, the observation only contains `agent_pos` and the reward signal — no `direction_to_resource`, no `nearest_resource_distance`, no `on_resource`, no `on_hazard`. The organism must learn everything from reward.

2. **PHASE B — Ablate the heuristic_bias**: implement Condition B (no bias). The organism selects actions purely from `action_preferences`.

3. **PHASE C — Implement Q-learning baseline**: `benchmarks/baselines/q_learning/` with a tabular Q-learner using the same env/observation/action harness. **No access to NurosOS-specific privileged info.**

4. **PHASE D — Non-stationary environment**: implement a minimal non-stationary benchmark (PHASE A → PHASE B → PHASE C regime transitions) that requires genuine adaptation. The current `ResourceWorld` saturates too quickly.

5. **PHASE E — Preregister the flagship experiment**: `experiments/EXPERIMENTS.md` BEFORE running. Hypothesis, null hypothesis, primary/secondary outcomes, exclusion criteria, statistical analysis plan, stopping rules.

6. **PHASE F — 30-seed replication**: run the flagship experiment with 30 independent seeds per condition. Report mean ± std, 95% CI, effect size.

7. **PHASE G — Ablation matrix**: conditions A through F per master prompt PHASE 6. Run all of them.

8. **PHASE H — Re-evaluate the divergence claim**: with privileged fields stripped + bias ablated + Q-learning baseline, is the "Computational Developmental Divergence" still observable? If yes — interesting. If no — the original claim was an artifact.

Only **after** PHASE A-H is complete and the NurosOS baseline is empirically characterized should HippoCore be activated as Condition "NurosOS + HippoCore" per master prompt PHASE 15.

---

## 15. HippoCore integration readiness

**Question**: Is the current Memory Contract ready for HippoCore?

**Answer**: The Memory Contract is **architecturally ready** (the `MemoryEngine` ABC from PHASE 2 is the right abstraction boundary). But HippoCore is **scientifically premature**:

- The NurosOS baseline (without HippoCore) has not been empirically characterized. There is no baseline condition against which HippoCore's value can be measured.
- The privileged observation confound (§11) means any HippoCore benefit could be attributed to the env being teacher-shaped rather than to episodic memory.
- The hard-coded bias confound (§9) means HippoCore's retrieval would have to compete with (or be diluted by) the bias — the experiment would be confounded.
- `Organism.tick()` does not consult `MemoryEngine.retrieve()` during action selection. HippoCore's episodic encoding + replay + consolidation are technically implemented but **not wired into behavior**.

**Recommended action**: **DO NOT activate HippoCore as a default.** Keep it on the feature branch (`feature/hippocore-integration-audit`) as a future intervention candidate. Run the audit's recommended experimental sequence (§14) first.

The HippoCore code itself is **technically sound** (247 Python tests pass; pure Python; NO LLM dependency; deterministic when seeded). It just shouldn't be the focus of the next experimental phase.

---

## 16. Critical blockers

Items that **MUST** be resolved before any scientific claim can be made:

1. **BL-1**: Strip the env's privileged observation fields (or add a toggle). Without this, any learner (Q-learning included) will trivially solve the env.
2. **BL-2**: Implement the PHASE 4 ablation condition (no heuristic bias). Without this, learned vs. hard-coded contributions cannot be separated.
3. **BL-3**: Implement a tabular Q-learning baseline. Without this, "NurosOS provides value" cannot be falsified.
4. **BL-4**: Preregister the flagship experiment (hypothesis + null hypothesis + analysis plan BEFORE running). Without this, the post-hoc claim in the WHITEPAPER is anecdotal.
5. **BL-5**: 30-seed replication of the flagship experiment. Single-seed results are anecdotal.

Items that should NOT be done during the audit:

- DO NOT add new HippoCore features.
- DO NOT add an LLM.
- DO NOT add a neural network.
- DO NOT refactor the Rust architecture.
- DO NOT delete legacy code without migration documentation.

---

## 17. Non-blocking improvements

Items that would improve the project but are not critical for scientific credibility:

- NB-1: Add a CI workflow (`.github/workflows/test.yml`) that runs `pytest nuros/tests/` + `cargo test --lib` on every push.
- NB-2: Migrate the Python `genome.py` and `version_control.py` to either delete or formally deprecate.
- NB-3: Wire `DevelopmentalCausalityGraph` into `MinimumOrganism::tick` (Rust side; needs `maturin build`).
- NB-4: Add the experiment harness directory structure (`experiment_outputs/<experiment_id>/{config.json, manifest.json, raw/, metrics/, trajectories/, checkpoints/, plots/, report.md}`) per master prompt PHASE 10.
- NB-5: Replace the ad-hoc `deterministic_random` FNV-1a hash (`organism.rs:573-584`) with a proper xorshift128+ or PCG — the current implementation is sufficient but non-standard.
- NB-6: Wire `Organism.tick()` (Python) to consult `MemoryEngine.retrieve()` during action selection — this is the master prompt's PHASE 4 → §36 stage 5 gap. **PHASE 10+ follow-up, not during the audit.**
- NB-7: Add statistical significance testing infrastructure (bootstrap CIs, permutation tests).
- NB-8: Add an effect-size calculator (Cohen's d, Hedges' g).

---

## End of RESEARCH_AUDIT.md

**Next**: see `docs/ARCHITECTURE_AUDIT.md`, `docs/MEMORY_AUDIT.md`, `experiments/EXPERIMENTS.md`, `experiments/ABLATION_MATRIX.md`, `docs/EXPERIMENTAL_ROADMAP.md`, `docs/HIPPOCORE_INTEGRATION_PLAN.md`, `docs/SCIENTIFIC_RISKS.md`, `docs/BASELINE_SPEC.md`, `docs/REPRODUCIBILITY_SPEC.md`, `docs/METRICS_SPEC.md`.
