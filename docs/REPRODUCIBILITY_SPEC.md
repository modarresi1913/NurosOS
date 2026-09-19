# REPRODUCIBILITY SPEC

> **Master prompt PHASE 11**: verify same seed + same commit + same configuration = same initial state and reproducible result.
> **Companion to**: `docs/RESEARCH_AUDIT.md` §10 (Reproducibility mechanisms).
> **Status**: SPECIFICATION.

This document specifies the reproducibility invariants the audit verifies
(or recommends verifying) for NurosOS.

---

## 1. Reproducibility invariants

### INV-1: Determinism given a fixed seed

**Invariant**: For a given (genome, env_seed, organism_seed, condition, observation_mode), the trajectory MUST be byte-for-byte identical across runs.

**Mechanism**: the Rust `MinimumOrganism` uses `deterministic_random` (`organism.rs:573-584`) — an FNV-1a hash on (step, salt) — for ε-greedy action selection. The env uses `SimpleRng` seeded by `env_seed`. Both are pure functions of their inputs.

**Verification**: `nuros-dev/src/organism.rs:638-660` test `same_genome_same_seed_same_environment_produces_identical_trajectory` confirms this for the Rust engine.

**Gap**: the Python `Organism.tick()` uses `uuid.uuid4()` for memory IDs (`nuros/memory.py:78`) — this is NOT deterministic across runs. The audit's PHASE 2 fix to `Organism.state_hash()` (`nuros/organism.py:302-328`) includes a memory content hash that's stable across runs (because it hashes the contents, not the UUIDs), so the state_hash is reproducible even if the individual memory_ids are not. But the trajectory's `memory_id` fields will differ across runs.

**Recommendation**: PHASE 10+ follow-up — switch memory IDs to a deterministic counter (e.g., `f"mem-{self._next_id}"` with `self._next_id += 1` per encode) so the full trajectory is byte-for-byte reproducible.

---

### INV-2: Checkpoint restoration

**Invariant**: `MindCheckpoint.take()` + `replay_from_checkpoint()` MUST reproduce the same trajectory as a fresh run from the checkpointed step.

**Mechanism**: `nuros-dev/src/checkpoint.rs:29-105` (`MindCheckpoint` captures organism_state + environment_snapshot + genome + seeds + runtime_version); `checkpoint.rs:174-237` (`replay_from_checkpoint` restores + steps + compares).

**Verification**: `nuros-dev/src/checkpoint.rs:282-301` test `replay_from_checkpoint_is_exact_for_deterministic_engine` confirms EXACT replay for the Rust numeric engine.

**Gap**: `MindCheckpoint.organism_state` is the Rust `OrganismState` (numeric vector). It does **NOT** capture Python `MemoryContract._memories`. Restoring a Rust checkpoint does NOT restore Python-side memory contents. (Audit `docs/HIPPOCORE_INTEGRATION_AUDIT.md` §14.) The PHASE 2 Python `MemoryEngine.checkpoint()`/`restore()` exists but is not yet wired to the Rust `MindCheckpoint`.

**Recommendation**: PHASE 10+ follow-up — extend `MindCheckpoint` with `memory_state: serde_json::Value` that carries the Python `MemoryEngine.checkpoint()` payload. The HippoCore integration's PHASE 7 spec already recommends this.

---

### INV-3: Trajectory replay

**Invariant**: a `DevelopmentalTrajectory` recorded at run-time MUST be replayable step-by-step against the env, producing the same `(action, reward, prediction_error, state_hash)` at each step.

**Mechanism**: `nuros-dev/src/trajectory.rs:DevelopmentalTrajectory` records ordered `TrajectoryPoint`s; `nuros-dev/src/checkpoint.rs:replay_from_checkpoint` replays from a checkpoint and compares each step to the original trajectory.

**Verification**: same test as INV-2.

---

### INV-4: Environment determinism

**Invariant**: a `ResourceWorld` or `ChangingWorld` constructed with a fixed seed, reset to its initial state, MUST produce identical observation/reward sequences when given identical action sequences.

**Mechanism**: `nuros-dev/src/environment.rs:16-19` documents the determinism contract; `ResourceWorld::reset` (`environment.rs:216-221`) restores initial state.

**Verification**: `nuros-dev/src/environment.rs:tests::environment_determinism` (mentioned at line 19).

---

### INV-5: Genome hash stability

**Invariant**: `DevelopmentalGenome.hash()` MUST be canonical SHA-256 — the same logical genome always produces the same hash, regardless of field declaration order in the JSON.

**Mechanism**: `nuros-dev/src/hash.rs` (canonical JSON + SHA-256).

**Verification**: `nuros-dev/src/genome.rs` tests confirm JSON round-trip preserves the hash.

---

### INV-6: Configuration hash stability

**Invariant**: the experiment configuration hash MUST be stable across runs with the same configuration.

**Mechanism**: `ReproducibilityManifest.configuration_hash` (`telemetry.rs:186`) is computed via `crate::hash::hash(&configuration)`.

**Verification**: `nuros-dev/src/telemetry.rs:tests::manifest_round_trips_through_json`.

---

### INV-7: Dependency version pinning

**Invariant**: the experiment's dependency versions (Rust crate versions, Python package versions) MUST be recorded in the manifest.

**Mechanism**: `ReproducibilityManifest.dependency_versions` (`telemetry.rs:189`) — currently records `nuros-dev` version + `rustc` version. **Does NOT record Python package versions.**

**Gap**: Python-side dependency versions (e.g., `pytest`, `maturin`) are not in the manifest.

**Recommendation**: PHASE 10+ follow-up — extend `ReproducibilityManifest` to record Python-side `pip freeze` output.

---

## 2. Where exact replay is impossible

The audit identifies the following cases where exact replay is NOT possible:

### Case 1: Python memory_id UUIDs

The Python `MemoryContract._memories` uses `uuid.uuid4()` for memory_ids. These are non-deterministic across runs. The state_hash is stable (because it hashes contents, not IDs) but the individual `memory_id` fields are not.

**Mitigation**: switch to deterministic counters (INV-1 recommendation).

### Case 2: Wall-clock timestamps in telemetry

`MemoryAccess.timestamp`, `MemoryRevision.timestamp`, `MemoryEntry.timestamp` use `time.time()` — wall-clock seconds. These are non-deterministic.

**Mitigation**: for trajectory replay, ignore these fields (or replace with a `tick_count` derived timestamp).

### Case 3: SystemTime in ReproducibilityManifest

`ReproducibilityManifest.timestamp` (`telemetry.rs:240-243`) uses `SystemTime::now()`. Non-deterministic.

**Mitigation**: this is correct behavior for a manifest (it records WHEN the experiment was run, not a deterministic value). Document this clearly.

---

## 3. Reproducibility vs. validity (master prompt: "Do not confuse reproducibility with scientific validity.")

A reproducible experiment can still be:

- **Confounded** (e.g., the env privileged-obs confound — see RESEARCH_AUDIT.md §11).
- **Anecdotal** (e.g., single-seed results — see RESEARCH_AUDIT.md §5).
- **Unfalsifiable** (e.g., a hypothesis that cannot produce a negative result).

The audit's reproducibility invariants (INV-1 through INV-7) verify that **the same inputs produce the same outputs**. They do NOT verify that **the outputs support the scientific claim**. For scientific validity, see `experiments/EXPERIMENTS.md` (preregistration) and `experiments/ABLATION_MATRIX.md` (matrix).

---

## 4. Reproducibility test plan

The audit recommends the following tests (PHASE 10+ follow-up):

1. `test_deterministic_trajectory_replay`: given a fixed (genome, env_seed, organism_seed), run 100 steps, checkpoint, restore, run 100 more steps, compare to a fresh 200-step run. Assert byte-for-byte identical.
2. `test_checkpoint_round_trip`: take a checkpoint, serialize to JSON, deserialize, take a new checkpoint, assert both checkpoints have the same hash.
3. `test_env_determinism`: construct a `ResourceWorld(seed=42)`, reset, take 50 random actions, record (action, reward) sequence. Construct another `ResourceWorld(seed=42)`, reset, take the same 50 actions, assert identical (action, reward) sequence.
4. `test_genome_hash_stability`: serialize a `DevelopmentalGenome` to JSON, deserialize, re-serialize, assert canonical JSON is byte-identical (modulo field order, which canonical JSON sorts).
5. `test_manifest_completeness`: build a `ReproducibilityManifest` for a 10-step run, assert all 13 fields are populated and non-empty.
6. `test_python_memory_reproducibility` (PHASE 10+): take a `MemoryEngine.checkpoint()`, restore it into a fresh `MemoryEngine` instance, assert `memory_count` matches and the sorted content lists match.

---

## 5. Reproducibility manifest gap audit

| Manifest field | Populated? | Stable? | Audit notes |
|----------------|-----------|---------|-------------|
| `mind_id` | YES | YES (deterministic UUID from genome) | — |
| `genome_hash` | YES | YES (canonical SHA-256) | — |
| `runtime_hash` | YES | YES (Cargo version + rustc version) | — |
| `environment_hash` | YES | YES (env content hash) | — |
| `experiment_hash` | YES | YES (configuration hash) | — |
| `random_seed` | YES | YES | — |
| `environment_seed` | YES | YES | — |
| `checkpoint_hash` | YES | YES | — |
| `configuration_hash` | YES | YES | — |
| `dependency_versions` | PARTIAL | YES | Records `nuros-dev` + `rustc` only; NOT Python packages. **Gap.** |
| `timestamp` | YES | NO (wall-clock) | Acceptable for manifest. |
| `n_steps` | YES | YES | — |
| `limitations` | YES (optional) | YES | Caller-controlled. |
| **`memory_state_hash` (NEW)** | NO | — | **Recommended addition**: hash of `MemoryEngine.checkpoint()` payload. PHASE 10+ follow-up. |

---

## 6. Recommended minimum reproducibility deliverable

Before any flagship experiment is run, the following must be true:

1. All 7 invariants (INV-1 through INV-7) are verified by automated tests.
2. The `ReproducibilityManifest` is complete for every run (13 fields + the recommended `memory_state_hash` addition).
3. The experiment outputs follow the `experiment_outputs/<experiment_id>/{config.json, manifest.json, raw/, metrics/, trajectories/, checkpoints/, plots/, report.md}` layout per master prompt PHASE 10.
4. Per-seed raw results are kept (no aggregation hides the distribution).

**End of REPRODUCIBILITY_SPEC.md.**
