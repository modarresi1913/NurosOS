# SCIENTIFIC RISKS

> **Companion to**: `docs/RESEARCH_AUDIT.md` (§12 Scientific risks + §11 Confounds).
> **Master prompt ref**: PHASE 21 (Change Control) + the audit's overall skeptical posture.
> **Status**: SPECIFICATION.

This document lists the scientific risks that could undermine the audit's
experimental results, and the mitigation for each.

---

## Critical risks (severity CRITICAL)

### S-1. The flagship "Computational Developmental Divergence" is an artifact

**Risk**: the divergence measured by the *Same Genome / Different World* experiment is overwhelmingly explained by (a) the env's RNG-dependent initial resource placement + (b) the organism's hard-coded `heuristic_bias` reading the env's privileged `direction_to_resource` vector. It is NOT explained by learning, memory, development, or plasticity.

**Evidence**: `nuros-dev/src/environment.rs:177-189` (`ResourceWorld::generate_resources` uses `SimpleRng` seeded by the env seed); `nuros-dev/src/organism.rs:451-503` (`heuristic_bias` consumes `direction_to_resource`); `nuros-dev/src/environment.rs:242-250` (env emits privileged fields).

**Mitigation**: 
- Phase A of `docs/EXPERIMENTAL_ROADMAP.md` (env privileged-obs toggle — raw mode strips the privileged fields).
- Phase B (heuristic-bias ablation flag — condition F in the ablation matrix).
- If, in raw mode + no bias, the divergence disappears, the original claim was an artifact. Report this honestly.

**If unmitigated**: any conclusion drawn from the flagship experiment is confounded.

---

### S-2. No baseline condition

**Risk**: without a Q-learning baseline, no experiment can claim that "NurosOS provides measurable value beyond a conventional simple learning system."

**Evidence**: no `benchmarks/baselines/` directory exists.

**Mitigation**: Phase C of `docs/EXPERIMENTAL_ROADMAP.md` (implement `benchmarks/baselines/q_learning/`).

**If unmitigated**: NurosOS remains "architecturally interesting" but scientifically untested.

---

### S-3. Memory is not consulted during action selection

**Risk**: the entire HippoCore integration (10 phases, 247 tests) is technically sound but **scientifically inert** because `Organism.tick()` does not call `MemoryEngine.retrieve()` during action selection. No experiment can demonstrate that HippoCore's episodic memory + replay + consolidation provide behavioral value.

**Evidence**: `nuros/organism.py:178-211` (`tick()` does not call `_memory.retrieve()`); `nuros-dev/src/organism.rs:408-441` (`select_action` reads only `action_preferences` + `heuristic_bias`).

**Mitigation**: PHASE 10+ follow-up (wire memory into action selection). See `docs/HIPPOCORE_INTEGRATION_PLAN.md` §5.

**If unmitigated**: HippoCore remains a complete-but-unused subsystem.

---

## High-severity risks

### S-4. Environment is teacher-shaped (privileged observation)

**Risk**: the env emits `direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`, `total_resource_left`. Any learner (Q-learning included) trivially solves the env. The env does not present a real learning problem.

**Evidence**: `nuros-dev/src/environment.rs:242-250` (`ResourceWorld::observe()`); `nuros-dev/src/environment.rs:393-399` (`ChangingWorld::observe()` leaks `resource_pos` — the goal itself).

**Mitigation**: Phase A (env privileged-obs toggle). Run all conditions in both privileged and raw modes. The raw-mode results are the audit's "fair" comparison.

**If unmitigated**: results are confounded by the env being too easy.

---

### S-5. Single-seed flagship results are anecdotal

**Risk**: the WHITEPAPER reports `steps=300, env_a_seed=1, env_b_seed=999` — single-seed results. Per master prompt PHASE 8: "a 4-condition comparison without multiple seeds is anecdotal, not scientific."

**Evidence**: `WHITEPAPER.md:134-141`; `SUMMARY.md:34-41`.

**Mitigation**: Phase F of `docs/EXPERIMENTAL_ROADMAP.md` (30-seed replication across all ablation matrix cells).

**If unmitigated**: the flagship numbers are not statistically interpretable.

---

### S-6. Hard-coded bias confounds the learning claim

**Risk**: `MinimumOrganism::heuristic_bias` (`organism.rs:451-503`) encodes task knowledge (resource-seeking, hazard-avoidance, direction-aware movement). The learned `action_preferences` are a secondary signal. Any "learning" or "development" claim is confounded.

**Evidence**: `nuros-dev/src/organism.rs:434` (`score = pref + bias`); `nuros-dev/src/organism.rs:451-503` (six hard-coded bias rules consuming privileged observation fields).

**Mitigation**: Phase B (heuristic-bias ablation flag — condition F in the ablation matrix).

**If unmitigated**: the "capabilities emerge through development" claim is unsupported.

---

### S-7. HippoCore claims "pattern separation" but only implements storage-level UUIDs

**Risk**: the HippoCore `bench_01_pattern_separation` benchmark reports `collision_rate=0.0` — but every encode just generates a fresh UUID. This is **storage-level** separation, not neural-circuit-accurate pattern separation.

**Evidence**: `benchmarks/memory/__init__.py:bench_01_pattern_separation`; `nuros/memory.py:139` (`memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))`).

**Mitigation**: relabel "pattern separation" to "storage-level pattern separation" in docs. PHASE 10+ follow-up: explore using the Rust kernel `Ams` (`kernel/src/mem.rs:54`) as a similarity-based pattern-separation backend.

**If unmitigated**: any "pattern separation" claim is overstated.

---

### S-8. Catastrophic forgetting benchmark does not measure catastrophic forgetting

**Risk**: the HippoCore `bench_03_catastrophic_forgetting` benchmark measures `retention=1.0` across all conditions because episodic memory does not overwrite. The benchmark measures the wrong phenomenon.

**Evidence**: `benchmarks/memory/__init__.py:bench_03_catastrophic_forgetting`.

**Mitigation**: rename to `forgetting_baseline` OR add a true continual-learning protocol (e.g., encode N1 memories of "task A", then N2 of "task B", measure the retrieval accuracy of task A memories after task B encoding — but with an actual memory budget cap that forces eviction). The non-stationary 3-regime env (Phase D) will provide this protocol.

**If unmitigated**: the benchmark reports a misleading 100% retention.

---

## Medium-severity risks

### S-9. "Development" is a deterministic function of step count

**Risk**: every "developmental" mechanism in `MinimumOrganism` is either a fixed-schedule stage transition or a fixed-coefficient exponential moving average. None are emergent. The "developmental state" is a deterministic function of (step_count, accumulated_reward, accumulated_prediction_error).

**Evidence**: `nuros-dev/src/organism.rs:507-528` (maturation schedule); `nuros-dev/src/organism.rs:269` (`dev.plasticity *= 0.999`); `nuros-dev/src/organism.rs:271` (`dev.stability = 0.5 * dev.stability + 0.5 * dev.prediction_accuracy`); `nuros-dev/src/organism.rs:256` (`dev.cognitive_load = (dev.cognitive_load * 0.95 + 0.05)`).

**Mitigation**: relabel "development" to "state accumulation" in docs. PHASE 10+ follow-up: implement genuine plasticity (e.g., plasticity that responds to prediction error rather than decaying by a fixed schedule).

**If unmitigated**: the "developmental" framing overstates what the system does.

---

### S-10. Memory budget enforcement is config-only

**Risk**: `HippoCoreMemoryConfig.max_episodes` and `max_memory_bytes` knobs exist but are never consulted to evict memories. A PHASE 10+ follow-up is needed.

**Evidence**: `nuros/hippocore/memory_engine.py:HippoCoreMemoryConfig` (the fields are stored but `HippoCoreMemory` does not consult them).

**Mitigation**: PHASE 10+ follow-up (implement an importance/age-based eviction policy when the budget is reached).

**If unmitigated**: HippoCore has effectively unlimited memory, which is an unfair advantage over a constrained Q-learning baseline.

---

### S-11. The Rust extension cannot be built in some environments

**Risk**: the audit cannot run the 57 Rust tests + 18 integration tests because `maturin build --release` is not available in this environment. The README claims 322 tests passing, but the audit can only independently verify 247 Python tests.

**Evidence**: `maturin build --release` requires Rust toolchain + Python dev headers; not available in the audit environment.

**Mitigation**: the README quickstart documents the build requirement. The audit's deliverables are documentation + Python-only Q-learning baseline.

**If unmitigated**: the audit's independent verification of the Rust-side claims is incomplete.

---

## Low-severity risks

### S-12. Documentation uses promotional language

**Risk**: "advanced", "powerful", "promising", "comprehensive" appear in docs. Per master prompt PHASE 19, these should be removed.

**Mitigation**: Phase H of `docs/EXPERIMENTAL_ROADMAP.md` (documentation integrity).

### S-13. No CI workflow

**Risk**: no `.github/workflows/` directory.

**Mitigation**: add `.github/workflows/test.yml` running `pytest nuros/tests/` + `cargo test --lib` on every push.

### S-14. Dead code (audit Appendix B)

**Risk**: `MemoryRecord.access_count` (`organism.rs:41`) is a dead field; `EventKind::MemoryUpdate` (`causality.rs:33`) is defined but never produced; `LifecycleState::CONSOLIDATE` (`nuros/homeostasis.py:34`) is declared but unused.

**Mitigation**: PHASE 10+ follow-up.

---

## Risk matrix summary

| Risk | Severity | Mitigation phase | Blocker? |
|------|----------|------------------|----------|
| S-1 (divergence artifact) | CRITICAL | Phase A+B (env toggle + bias ablation) | YES |
| S-2 (no baseline) | CRITICAL | Phase C (Q-learning) | YES |
| S-3 (memory not consulted) | CRITICAL | PHASE 10+ follow-up | YES (for HippoCore experiments) |
| S-4 (env teacher-shaped) | HIGH | Phase A | YES |
| S-5 (single-seed anecdote) | HIGH | Phase F (30-seed runs) | YES |
| S-6 (hard-coded bias confound) | HIGH | Phase B | YES |
| S-7 (pattern separation overstated) | HIGH | Phase H (relabel) | NO (labeling fix) |
| S-8 (catastrophic forgetting benchmark wrong) | HIGH | Phase D (non-stationary env) | NO (benchmark rename) |
| S-9 (development is bookkeeping) | MEDIUM | Phase H (relabel) | NO |
| S-10 (memory budget enforcement missing) | MEDIUM | PHASE 10+ follow-up | NO (for HippoCore experiments) |
| S-11 (Rust build unavailable) | LOW | (document the build requirement) | NO |
| S-12 (promotional language) | LOW | Phase H | NO |
| S-13 (no CI) | LOW | add `.github/workflows/test.yml` | NO |
| S-14 (dead code) | LOW | PHASE 10+ follow-up | NO |

**End of SCIENTIFIC_RISKS.md.**
