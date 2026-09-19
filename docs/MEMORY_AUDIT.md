# MEMORY AUDIT — NurosOS

> Companion to `docs/RESEARCH_AUDIT.md`. This document audits the memory
> subsystem (master prompt PHASE 13).

NurosOS has **three parallel, non-unified memory subsystems** (audit §1 of `docs/HIPPOCORE_INTEGRATION_AUDIT.md`):

1. Rust `MinimumOrganism::MemoryRecord` (`organism.rs:30-44`) — the developmental substrate's memory.
2. Rust kernel `Ams` (`kernel/src/mem.rs:54`) — Drosophila-mushroom-body-inspired content-addressable store, **not used by the developmental substrate**.
3. Python `DefaultMemoryContract` / `HippoCoreMemory` (`nuros/memory.py`, `nuros/hippocore/memory_engine.py`) — the Mind Contract Layer implementation.

The HippoCore integration's `MemoryEngine` ABC (PHASE 2) is the **abstraction boundary** that unifies them — but the unification is **partial** (Python side only; Rust side is PHASE 10+ follow-up).

---

## Memory type audit

The Mind Contract (`mind/memory/SPEC.md`) declares 5 memory types:

| Type | Default epistemic label | Status | File:line evidence |
|------|-------------------------|--------|-------------------|
| `EPISODIC` | `OBSERVED` | `IMPLEMENTED` (label only) | `nuros/memory.py:31` |
| `SEMANTIC` | `INFERRED` | `IMPLEMENTED` (label only) | `nuros/memory.py:32` |
| `PROCEDURAL` | `ACTED` | `IMPLEMENTED` (label only) | `nuros/memory.py:33` |
| `WORKING` | `OBSERVED` | `IMPLEMENTED` (with capacity-7 buffer) | `nuros/memory.py:34`, `nuros/memory.py:working_set/working_get` |
| `COUNTERFACTUAL` | `IMAGINED` | `IMPLEMENTED` (label + IMAGINED enforced at encode) | `nuros/memory.py:35`, `nuros/memory.py:encode` (lines 192-200) |

**Audit verdict**: The 5 types are labels on `MemoryEntry.memory_type`. There is **no behavioral difference** between EPISODIC and SEMANTIC memories at the storage level — both are stored in the same `_memories` dict. The difference is purely the `MemoryType` enum value + the auto-assigned `EpistemicLabel`. The PHASE 6 consolidation pipeline (in `HippoCoreMemory.consolidate()`) is what actually creates a SEMANTIC memory from a cluster of EPISODIC sources.

---

## Memory operation audit

The Mind Contract declares 10 operations (post-PHASE 2 stabilization):

| Operation | File:line | Status | Used by action selection? | Audit class |
|-----------|----------|--------|---------------------------|-------------|
| `encode()` | `nuros/memory.py:189-224` (Default) + `nuros/hippocore/memory_engine.py:encode` (PHASE 4 enrichment) | `IMPLEMENTED AND TESTED` | NO — `Organism.tick()` calls `_development.experience()` (`organism.py:178-211`), not `_memory.encode()`. | A (fully implemented) but **D (unused by behavior)** |
| `retrieve()` | `nuros/memory.py:248-286` (Default) + `nuros/hippocore/memory_engine.py:retrieve` (PHASE 7 event emission) | `IMPLEMENTED AND TESTED` | NO — `Organism.tick()` does not call `retrieve()` during action selection. | A (fully implemented) but **D (unused by behavior)** |
| `retrieve_by_id()` | `nuros/memory.py:288-294` | `IMPLEMENTED AND TESTED` | NO | A but D |
| `associate()` | `nuros/memory.py:296-313` | `IMPLEMENTED AND TESTED` | NO — association graph exists but is not consulted during action selection. | A but D |
| `reconsolidate()` | `nuros/memory.py:367-387` (Default) + `nuros/hippocore/memory_engine.py:reconsolidate` (PHASE 7) | `IMPLEMENTED AND TESTED` | NO — only called by `Organism.sleep()` (`organism.py:238-247`) as a stub. | A but D (mostly) |
| `replay()` | `nuros/memory.py:389-439` (Default, PHASE 5 with n + generative) + `nuros/hippocore/memory_engine.py:replay` (PHASE 5 policy delegation) | `IMPLEMENTED AND TESTED` | NO — only called by `Organism.sleep()` (`organism.py:244-247`) as a stub. | A but D (mostly) |
| `consolidate()` | `nuros/memory.py:441-450` (Default, no-op stub) + `nuros/hippocore/memory_engine.py:consolidate` (PHASE 6 real pipeline) | `IMPLEMENTED` (Default = no-op; HippoCore = real) | NO | A but D |
| `forget()` | `nuros/memory.py:452-478` (Default, soft-delete by default since PHASE 2) + `nuros/hippocore/memory_engine.py:forget` (PHASE 7 event) | `IMPLEMENTED AND TESTED` | NO | A but D |
| `checkpoint()` | `nuros/memory.py:480-531` (Default) + `nuros/hippocore/memory_engine.py:checkpoint` (PHASE 4 schema bump) | `IMPLEMENTED AND TESTED` | NO | A but D |
| `restore()` | `nuros/memory.py:533-590` (Default, accepts any `nuros.` prefix) + `nuros/hippocore/memory_engine.py:restore` (delegates) | `IMPLEMENTED AND TESTED` | NO | A but D |
| `inspect()` | `nuros/memory.py:360-391` (Default) + `nuros/hippocore/memory_engine.py:inspect` (engine marker) | `IMPLEMENTED AND TESTED` | NO | A but D |

**Audit classes** (master prompt PHASE 13):
- A = fully implemented
- B = partially implemented
- C = interface-only
- D = unused
- E = not experimentally validated

**Verdict**: Every operation is class A (fully implemented + unit-tested). Every operation is also class D (unused by action selection) AND class E (not experimentally validated as a behavioral driver). The memory subsystem is a **complete but inert log** — it records, retrieves, replays, consolidates, and forgets, but none of these operations influences the organism's behavior.

---

## Per-implementation audit

### 1. Rust `MinimumOrganism::MemoryRecord`

`organism.rs:30-44`:

```rust
pub struct MemoryRecord {
    pub key: String,           // observation signature (canonical JSON, truncated to 64 chars)
    pub value: serde_json::Value,  // {action, reward, prediction_error}
    pub importance: f64,        // in [0, 1]
    pub step: u64,
    pub access_count: u64,     // DEAD FIELD — never incremented, never read
}
```

**Audit findings**:

- Stored as `Vec<MemoryRecord>` in `OrganismState.memory` (`organism.rs:67`).
- Capped at 200 entries (`organism.rs:233-236`); lowest-importance dropped when cap exceeded.
- Records are written in `tick()` (`organism.rs:219-231`) and `tick_with_action()` (`organism.rs:334-346`).
- **Records are never read** by any other code path. `OrganismState.memory` is included in `MindCheckpoint`/`snapshot`/`MindDiff` for inspection, but the records are never consulted during action selection.
- `access_count` field (`organism.rs:41`) is initialized to 0 and never modified — dead field.
- The 200-entry cap is hard-coded; not configurable via `genome`.

**Audit class**: A (fully implemented at the struct level) + D (unused) + E (not validated as a behavioral driver).

### 2. Rust kernel `Ams`

`kernel/src/mem.rs:54-180`:

```rust
pub struct Ams {
    inner: RwLock<HashMap<Handle, Entry>>,
    next_handle: AtomicU64,
}

impl Ams {
    pub fn store(&self, stimulus: Vec<f32>, payload: Vec<u8>) -> Handle;
    pub fn query(&self, partial_stimulus: &[f32], k: usize) -> Vec<(Handle, f32)>;
    pub fn read(&self, h: Handle) -> Option<Vec<u8>>;
    pub fn reinforce(&self, h: Handle, reward: f32);
}
```

**Audit findings**:

- Content-addressable associative memory store inspired by *Drosophila* mushroom body.
- Uses cosine similarity for k-NN retrieval.
- **NOT instantiated by the developmental substrate** — search for `Ams::new()` returns zero hits in `nuros-dev/`. Only the unit test `mem.rs:158-179` instantiates it.
- Documented as a candidate HippoCore pattern-separation backend (`docs/HIPPOCORE_INTEGRATION_AUDIT.md` §20 — PHASE 10+ follow-up).
- The `Entry.reinforcement` field (`mem.rs:46`) IS used — `reinforce()` increments it. But there is no consumer of the incremented reinforcement value (no `recall_by_reinforcement()` method).

**Audit class**: A (fully implemented) + D (unused outside its own unit test) + E (not validated as a developmental mechanism).

### 3. Python `DefaultMemoryContract` (`nuros/memory.py`)

PHASE 2-stabilized reference implementation of `MemoryEngine`.

**Audit findings**:

- 5 memory types, 10 operations (post-PHASE 2).
- Soft-delete by default (`forget(hard=False)`).
- Checkpoint/restore with JSON-native dict payload, idempotent.
- `iter_all()` public iterator (audit Appendix B.2 fix).
- `inspect()` (audit Appendix B.3 spec drift reconciliation).
- `access_count` correctly incremented on every retrieve/retrieve_by_id/inspect (audit Appendix B.7 fix).
- **`Organism.tick()` does NOT consult `MemoryContract.retrieve()` during action selection** — the Python organism is constructed with `MemoryContract` but never uses it for action selection.

**Audit class**: A (fully implemented + 50 tests in `test_memory_engine.py`) + D (unused by action selection) + E (not validated as a behavioral driver).

### 4. Python `HippoCoreMemory` (`nuros/hippocore/memory_engine.py`)

PHASES 3-8 HippoCore integration. Built on top of `MemoryEngine` ABC.

**Audit findings**:

- Adapter scaffold (PHASE 3) + episodic encoding with `MemoryProvenance` (PHASE 4) + 5 replay policies (PHASE 5) + 2 consolidation strategies (PHASE 6) + memory event emission (PHASE 7) + causal graph integration (PHASE 8).
- 247 Python tests passing.
- NO LLM dependency.
- Deterministic when seeded.
- `encode_episode()` full-schema entry point (master prompt §6).
- `set_encoding_context()` for organism attribution.
- `events` property + `set_step()` for trajectory alignment.
- `attach_causal_graph()` post-construction wiring.
- **`Organism.tick()` does NOT consult `HippoCoreMemory.retrieve()` during action selection either.**

**Audit class**: A (fully implemented) + E (not validated as a behavioral driver — the HippoCore integration is **technically sound but scientifically inert** until wired to behavior).

---

## Cross-engine compatibility audit

| Cross-engine operation | Status | Audit notes |
|-------------------------|--------|-------------|
| DefaultMemoryContract → DefaultMemoryContract checkpoint/restore | `IMPLEMENTED AND TESTED` (`test_memory_engine.py:TestCheckpointRestoreRoundTrip`) | Idempotent. |
| HippoCoreMemory → HippoCoreMemory checkpoint/restore | `IMPLEMENTED AND TESTED` (`test_episodic_encoding.py:TestPhase4CheckpointRestoreRoundTrip`) | Idempotent. Preserves PHASE 4 fields. |
| DefaultMemoryContract → HippoCoreMemory restore | `IMPLEMENTED AND TESTED` (`test_memory_engine.py:test_restore_accepts_hippocore_schema_prefix`) | Cross-engine restore works because PHASE 2 made `DefaultMemoryContract.restore()` accept any `nuros.`-prefixed schema_version. |
| HippoCoreMemory → DefaultMemoryContract restore | `IMPLEMENTED AND TESTED` (`test_episodic_encoding.py:test_cross_engine_restore_preserves_phase4_fields`) | PHASE 4 fields preserved when restoring a HippoCore-produced payload into a DefaultMemoryContract. |
| Rust `MindCheckpoint` → Python `MemoryContract` | **GAP** (`docs/HIPPOCORE_INTEGRATION_AUDIT.md` §14) | Rust `MindCheckpoint.organism_state` does NOT capture Python `MemoryContract._memories`. Restoring a Rust checkpoint does not restore Python-side memory contents. **PHASE 10+ follow-up.** |

---

## Memory budget audit (master prompt PHASE 16)

| Implementation | Memory cap | Configurable? | Audit class |
|----------------|-----------|---------------|-------------|
| Rust `MinimumOrganism::MemoryRecord` | 200 entries (`organism.rs:233`) | NO (hard-coded) | A (implemented) + D (unused) |
| Python `DefaultMemoryContract._working_memory` | 7 items (`nuros/memory.py:133`) | NO (hard-coded `_working_memory_capacity = 7`) | A + D (mostly unused) |
| Python `DefaultMemoryContract._memories` | None (unbounded) | NO | A + E (no budget enforcement) |
| Python `HippoCoreMemory` | `max_episodes` and `max_memory_bytes` config knobs in `HippoCoreMemoryConfig` (PHASE 6) | YES (config-only, no eviction logic yet) | A (config-only) + **E (no enforcement)** |

**Audit finding**: The `HippoCoreMemoryConfig.max_episodes` and `max_memory_bytes` knobs are **configuration-only** — they are stored but never consulted to evict memories. A PHASE 10+ follow-up should implement an importance/age-based eviction policy when either budget is reached.

**Scientific implication** (master prompt PHASE 16): "A memory architecture must not receive unlimited capacity while the baseline is constrained." Currently, both NurosOS and HippoCore have effectively unlimited memory. When the Q-learning baseline (PHASE 3) is introduced, the comparison must use EQUAL memory budgets for both systems.

---

## Memory → Behavior coupling audit

The single most important memory-system finding:

**No memory subsystem (Rust MemoryRecord, Rust Ams, Python DefaultMemoryContract, Python HippoCoreMemory) is consulted during action selection.**

Evidence:
- `MinimumOrganism::select_action` (`organism.rs:408-441`) reads only `action_preferences` (the learned Q-values) + `heuristic_bias` (the hard-coded task knowledge). It does NOT read `self.state.memory`.
- `Organism.tick()` (Python, `nuros/organism.py:178-211`) calls `_development.experience(obs)` — but `DevelopmentEngine.experience()` (`nuros/development.py:128`) does NOT call memory.
- `Organism.sleep()` (`nuros/organism.py:238-247`) does call `replay()` + `reconsolidate()` — but `sleep()` is not called automatically by `tick()`; it is a separate method the user must invoke explicitly. Even when invoked, the reconsolidation does not affect action selection on subsequent ticks (it modifies the memory entries' importance/confidence/decay_rate but those are not read by `select_action`).

**Implication**: Memory in NurosOS is **a post-hoc log**, not a **causal driver** of behavior. Until `Organism.tick()` (Python) and `MinimumOrganism::tick` (Rust) consult memory during action selection, no claim about memory's contribution to development can be empirically validated.

This is the **single biggest scientific gap** in the project. It is the master prompt's PHASE 4 → §36 stage 5 ("memory-dependent behavior") gap. **It should NOT be implemented during the audit** (master prompt PHASE 21 — Change Control); it is a PHASE 10+ follow-up.

---

## Recommended minimum changes (do NOT implement during the audit)

1. **PHASE 10+ follow-up**: wire `MemoryEngine.retrieve()` into `Organism.tick()` action selection. This is the master prompt's PHASE 4 → §36 stage 5 gap.
2. **PHASE 10+ follow-up**: extend `MinimumOrganism::select_action` to consult `self.state.memory` (e.g., retrieve the most-similar past MemoryRecord and bias toward its action if it was rewarded).
3. **PHASE 10+ follow-up**: implement the `max_episodes` / `max_memory_bytes` eviction policy in `HippoCoreMemory`.
4. **PHASE 10+ follow-up**: add a `genome.biases.disable_heuristic_bias: bool` flag to enable the PHASE 4 ablation (Condition B = no bias).

**End of MEMORY_AUDIT.md.**
