# Memory Architecture

> **Scope**: This document describes the memory architecture of NurosOS
> after the HippoCore integration (PHASES 1-10). For the historical
> Memory Contract spec (pre-PHASE 2), see `mind/memory/SPEC.md`.

---

## Central Thesis

Memory is **not merely storage**; it is part of the developmental process.
The organism changes because of what it experiences, remembers, replays,
consolidates, and forgets. This is the HippoCore thesis (master prompt
§1) realized in NurosOS's computational substrate.

---

## Three Memory Subsystems → One Engine (audit §1)

Before the HippoCore integration, NurosOS had **three parallel,
non-unified memory subsystems**:

1. **Python `MemoryContract`** (`nuros/memory.py:118`) — the documented
   Mind Contract Layer Contract 1. 5 memory types (episodic, semantic,
   procedural, working, counterfactual), 8 operations.
2. **Rust `MemoryRecord`** (`nuros-dev/src/organism.rs:30`) — the
   developmental substrate's memory. A simple `Vec<MemoryRecord>` with
   key→value + importance + access_count (the latter was a dead field
   per audit Appendix B.7).
3. **Rust kernel `Ams`** (`kernel/src/mem.rs:54`) — the "no-filesystem"
   Associative Memory Store (Drosophila mushroom-body-inspired content-
   addressed storage, never used by the developmental substrate).

They did not reference each other. The HippoCore integration **unifies
them behind a single `MemoryEngine` ABC** (PHASE 2) and adds a new
`HippoCoreMemory` implementation (PHASE 3+) that delivers genuine
hippocampal-inspired computational mechanisms.

### Current architecture (post-PHASE 10)

```
MemoryEngine ABC (nuros/memory_engine.py — PHASE 2)
    ├── DefaultMemoryContract (nuros/memory.py — the historical impl)
    │   - retains all historical MemoryContract behaviour
    │   - soft-delete by default (audit Appendix B.1 fix)
    │   - checkpoint/restore (audit §7 fix)
    │   - inspect() (audit Appendix B.3 fix)
    │   - iter_all() public iterator (audit Appendix B.2 fix)
    │
    └── HippoCoreMemory (nuros/hippocore/memory_engine.py — PHASE 3+)
        - episodic encoding with MemoryProvenance (PHASE 4)
        - policy-driven replay (PHASE 5)
        - fast→slow consolidation (PHASE 6)
        - memory event emission (PHASE 7)
        - causal graph integration (PHASE 8)

OrganismConfig.memory_engine = "default" | "hippocore"  (PHASE 2 selector)
```

### Future: Rust-side wiring (PHASE 10+ follow-up)

The Rust `MemoryRecord` should become a `DefaultMemory` impl of a Rust
`MemoryEngine` trait (audit §11.2). The Rust `Ams` (`kernel/src/mem.rs:54`)
could be a HippoCore pattern-separation backend, accessed via a thin
adapter, only when `DevelopmentalGenome.architecture.kernel_memory = true`
(audit §20). These are flagged as known technical debt.

---

## Memory Engine Contract (master prompt §3)

The `MemoryEngine` ABC (PHASE 2) exposes 10 first-class operations:

```python
class MemoryEngine(ABC):
    def encode(content, memory_type=None, ...) -> MemoryEntry
    def retrieve(query=None, memory_type=None, ..., limit=10) -> list[MemoryEntry]
    def retrieve_by_id(memory_id) -> Optional[MemoryEntry]
    def associate(memory_id_a, memory_id_b, relation_type="semantic", ...) -> bool
    def reconsolidate(memory_id, reward=0.0, prediction_error=None) -> Optional[MemoryEntry]
    def replay(memory_type=None, tags=None, time_range=None, n=None, generative=False) -> list[MemoryEntry]
    def consolidate(source_type=EPISODIC, target_type=SEMANTIC, ...) -> int
    def forget(memory_id, justification="", hard=False) -> bool
    def checkpoint() -> dict[str, Any]
    def restore(payload: dict[str, Any]) -> None
    def inspect(memory_id) -> Optional[dict[str, Any]]
    def iter_all() -> list[MemoryEntry]
    # Properties: memory_count, operation_log
    # Working memory: working_set(key, value), working_get(key)
    # Summary: summary() -> dict[str, Any]
```

---

## Episodic Encoding Schema (master prompt §6)

A `MemoryEntry` carries the following fields after PHASE 4:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `memory_id` | str | UUID | Unique ID |
| `content` | Any | None | Sensory/context representation |
| `memory_type` | `MemoryType` | EPISODIC | One of EPISODIC / SEMANTIC / PROCEDURAL / WORKING / COUNTERFACTUAL |
| `origin` | str | "" | Source label |
| `timestamp` | float | now() | Wall-clock time |
| `provenance` | str | "" | Legacy free-form provenance string (PHASE 2 compat) |
| `confidence` | float | 1.0 | In [0, 1] |
| `context` | dict | {} | Free-form context dict |
| `importance` | float | 0.5 | In [0, 1] |
| `prediction_error` | float | 0.0 | Signed prediction error (PHASE 5 weight) |
| `epistemic_label` | `EpistemicLabel` | REMEMBERED | One of 7 labels (OBSERVED / INFERRED / REMEMBERED / PREDICTED / SIMULATED / IMAGINED / ACTED) |
| `decay_rate` | float | 0.001 | Exponential decay rate |
| `access_history` | list | [] | Audit trail of accesses |
| `relationships` | list | [] | Bidirectional association edges |
| `revision_history` | dict | {} | Auditable revisions (old → new, justification) |
| `tags` | set | {} | Free-form tag set |
| `forgotten` | bool | False | PHASE 2 soft-delete marker |
| `consolidation_status` | str | "ACTIVE" | PHASE 2 lifecycle state (ACTIVE / WEAKENING / CONSOLIDATED / RECONSOLIDATED / ARCHIVED / FORGOTTEN) |
| `organism_id` | Optional[str] | None | PHASE 4 — ID of encoding organism |
| `action` | Any | None | PHASE 4 — action at encode time |
| `outcome` | Any | None | PHASE 4 — outcome that followed |
| `prediction` | Any | None | PHASE 4 — organism's prediction |
| `environment_state` | dict | None | PHASE 4 — environment snapshot |
| `causal_metadata` | dict | {} | PHASE 4 — PHASE 8 causal graph links |
| `structured_provenance` | Optional[MemoryProvenance] | None | PHASE 4 — full WHERE/WHEN/WHAT provenance |

---

## MemoryProvenance (master prompt §7)

A structured provenance record answering:

- WHERE: `origin` (e.g. "sensory_observation")
- WHEN: `encoded_at` (Unix epoch seconds)
- WHAT experience: `experience_id` (matches CausalEvent.id or TrajectoryPoint.step)
- WHAT organism: `organism_id` (matches DevelopmentalTrajectory.organism_id)
- WHAT environment: `environment_hash` + `environment_state`
- WHAT internal state: `internal_state`
- WHAT action: `action`
- WHAT outcome: `outcome`
- WHAT prediction: `prediction`
- WHAT prediction error: `prediction_error`
- WHAT later modifications: `causal_metadata` (carries PHASE 8 CausalEvent IDs)

---

## Replay Policies (master prompt §9, PHASE 5)

5 pluggable `ReplayPolicy` implementations, all deterministic when seeded:

| Policy | Selection rule |
|--------|----------------|
| `RecentReplayPolicy` | Most recent N memories by timestamp descending |
| `ImportanceWeightedReplayPolicy` | Weighted sampling with probability ∝ importance² |
| `NoveltyWeightedReplayPolicy` | Weighted by 1 / (1 + access_count) — less-accessed is more novel |
| `PredictionErrorWeightedReplayPolicy` | Weighted by |prediction_error| — surprise signal |
| `RandomReplayPolicy` | Uniform random sampling (baseline) |

Configuration via `HippoCoreMemoryConfig(replay_policy="...", replay_seed=...)`.

Runtime swapping via `hcm.set_replay_policy(make_policy("..."))` (used by
PHASE 9 benchmark 04 to compare policies on identical input sets).

---

## Consolidation Strategies (master prompt §10, PHASE 6)

2 pluggable `ConsolidationStrategy` implementations, both deterministic:

| Strategy | Similarity metric |
|----------|-------------------|
| `TagJaccardConsolidation` | Jaccard similarity on `tags` sets |
| `ContentPrefixConsolidation` | Common-prefix length on `content` strings |

The pipeline (master prompt §10):
1. Select up to `batch_size` ACTIVE sources of `source_type` (default EPISODIC).
2. Cluster via the configured strategy.
3. For each cluster of size ≥ 2, derive one `target_type` (default SEMANTIC) memory with unioned tags + summarized content.
4. Mark sources as `CONSOLIDATED` + lower importance by 50%.
5. Associate sources ↔ target via bidirectional `consolidated_into` edges.

---

## Memory Events (master prompt §8, PHASE 7)

6 event kinds emitted by `HippoCoreMemory` for every operation:

| Kind | Triggered by |
|------|--------------|
| `MEMORY_ENCODED` | `encode()` / `encode_episode()` |
| `MEMORY_RETRIEVED` | `retrieve()` / `retrieve_by_id()` |
| `MEMORY_REPLAYED` | `replay()` (per selected memory) |
| `MEMORY_RECONSOLIDATED` | `reconsolidate()` |
| `MEMORY_CONSOLIDATED` | `consolidate()` (per source) |
| `MEMORY_FORGOTTEN` | `forget()` |

Events are emitted via `MemoryEventEmitter` (a synchronous event bus with
`on/off/emit/clear`). Callback exceptions are swallowed so a buggy
consumer cannot break the engine's main operation.

The `events` property exposes the emitter for external consumers
(Organism, DevelopmentalTrajectory adapter, PHASE 9 benchmarks):

```python
hcm.events.on(lambda ev: trajectory.record(ev))
```

`set_step(n)` lets the Organism runtime tag events with a developmental
step number for trajectory alignment.

---

## Causal Graph (master prompt §20, PHASE 8)

`PythonCausalGraph` (pure-Python; mirrors the API of the Rust
`DevelopmentalCausalityGraph` at `nuros-dev/src/causality.rs:73`):

- 17 `EventKind` variants: 11 original Rust + 6 PHASE 8 memory-specific
  (MEMORY_ENCODE / RETRIEVE / REPLAY / RECONSOLIDATE / CONSOLIDATE / FORGET).
- `record()` / `get()` / `events_of_kind()` / `trace()` /
  `trace_outcome_to_experience()` / `to_jsonl()`.

When a `PythonCausalGraph` is attached to `HippoCoreMemory` (via the
`causal_graph` constructor parameter or `attach_causal_graph()` post-
construction), every memory event becomes a `CausalEvent` in the graph
with `depends_on` edges chaining events within the same developmental
step.

This enables the master-prompt-§20 walk:
```
Outcome → Action → Decision → MemoryEncode → SensoryObservation
```

---

## Checkpoint / Restore (master prompt §19, PHASE 2 + PHASE 4)

`MemoryEngine.checkpoint()` returns a JSON-native dict payload with:

- `schema_version`: e.g. `nuros.hippocore.HippoCoreMemory.v1.phase8`
- `entries`: list of MemoryEntry dicts (including PHASE 4 fields when
  populated: organism_id, action, outcome, prediction, environment_state,
  causal_metadata, structured_provenance).
- `working_memory`: dict[str, Any]
- `working_memory_capacity`: int
- `operation_log`: list of {operation, target, timestamp} dicts

`MemoryEngine.restore(payload)` is idempotent: restoring twice yields
the same state as restoring once (PHASE 2 + audit §11.1).

Cross-engine restore is supported: a `DefaultMemoryContract` can
restore a `HippoCoreMemory`-produced checkpoint (the layout is
identical in PHASE 3-8). This enables organism migration from `default`
to `hippocore` mid-development.

---

## Known Limitations (audit §35 item 11)

1. **Memory-dependent behavior**: `Organism.tick()` does not yet
   consult `MemoryEngine.retrieve()` during action selection. The
   Rust `MinimumOrganism::tick` similarly does not consult memory.
   This is the master-prompt-§36 stage 5 gap — flagged as the
   highest-priority PHASE 10+ item.
2. **Rust-side wiring**: PHASES 7+8 land the Python side. The Rust
   `DevelopmentalCausalityGraph` and `DevelopmentalTrajectory` need
   updating to consume the Python events via PyO3 callbacks. Requires
   `maturin build --release`.
3. **Pattern separation via embedding model**: PHASE 6 uses tag-Jaccard
   and content-prefix similarity, not learned embeddings. The Rust `Ams`
   at `kernel/src/mem.rs:54` is a candidate backend (currently unused).
4. **Generative replay (PHASE 5 `generative=True`)**: Currently a no-op
   (returns raw stored memories). PHASE 6+ would reconstruct from
   compressed traces.
5. **Memory budget enforcement**: PHASE 6 `max_episodes` and
   `max_memory_bytes` are configuration-only — no eviction logic.
   PHASE 6+ would add an importance/age-based eviction policy.
6. **Catastrophic forgetting measurement**: PHASE 9 benchmark 03 shows
   retention=1.0 across all conditions because episodic memory does not
   overwrite. A real continual-learning weight overwrite experiment
   requires modifying a learning model's weights, outside HippoCore
   scope.
