# Developmental Memory

> The HippoCore thesis: **memory is part of the developmental process**.
> The organism changes because of what it experiences, remembers, replays,
> consolidates, and forgets.

---

## Why memory is central to development (master prompt §8)

Memory is **not an external storage layer** for the developmental
organism. It is a first-class computational mechanism that drives
developmental change. The HippoCore integration makes this explicit:

1. Every memory operation emits a `MemoryEvent` (PHASE 7) that the
   developmental trajectory can record. Memory events are part of the
   trajectory, not separate from it.
2. The `PythonCausalGraph` (PHASE 8) records every memory event with
   `depends_on` edges, enabling the master-prompt-§20 walk:
   `Outcome → Action → Decision → Memory → Experience`. Memory is a
   node in the developmental causal graph.
3. Replay (PHASE 5) is not a debugging feature — it is a developmental
   mechanism. The replayed memories shape the next tick's prediction
   and decision. (PHASE 10+ follow-up: wire `replay()` into the
   `Organism.tick()` loop.)
4. Consolidation (PHASE 6) is not just storage — it promotes fast
   episodic memories into slow consolidated knowledge, which is the
   computational analog of biological memory consolidation. The
   promoted semantic memories are tagged `CONSOLIDATED` and persist
   longer than their episodic sources (which are importance-lowered
   after consolidation).

---

## Why episodic memory matters (master prompt §4 + §6)

Episodic memory is the **fast learning system** — it records specific
experiences with full provenance (WHERE/WHEN/WHAT/WHO/WHAT-ENV/WHAT-
INTERNAL/WHAT-ACTION/WHAT-OUTCOME). Without it:

- The organism cannot answer "what did I do last step?" except by
  re-running the trajectory.
- The organism cannot perform counterfactual reasoning ("what if I had
  taken the other path?") because the original experience is lost.
- The organism cannot consolidate (because consolidation needs source
  memories to cluster).

The PHASE 4 `MemoryEntry` schema carries all the fields master
prompt §6 lists. The PHASE 4 `encode_episode()` entry point is the
HippoCore-specific entry point for full episodic encoding.

The PHASE 6 consolidation pipeline promotes episodic memories to
semantic memories — the slow consolidated store. This is the
computational analog of the hippocampus→neocortex consolidation
hypothesis (we make NO biological-equivalence claim — see "Scientific
Status" below).

---

## How HippoCore integrates with NurosOS (master prompt §2)

The integration architecture (master prompt §2):

```
MemoryContract (historical, deprecated alias)
        ↓ (PHASE 2 stabilization)
MemoryEngine ABC (nuros/memory_engine.py)
        ├── DefaultMemoryContract (nuros/memory.py)
        │   full backward compat with historical MemoryContract API
        └── HippoCoreMemory (nuros/hippocore/memory_engine.py)
            PHASE 3: adapter scaffold
            PHASE 4: episodic encoding + structured provenance
            PHASE 5: policy-driven replay (5 policies)
            PHASE 6: fast→slow consolidation pipeline (2 strategies)
            PHASE 7: memory event emission for trajectory
            PHASE 8: causal graph integration (Python side)
```

The selector knob is `OrganismConfig.memory_engine = "default" | "hippocore"`.
Default is `"default"` for full backward compatibility.

The architecture is **layered**: HippoCore is a subsystem that NurosOS
reaches through the `MemoryEngine` ABC. HippoCore never dominates the
organism (master prompt §22). Developmental decisions stay in
`Organism.tick()`; memory dynamics stay in `HippoCoreMemory`.

---

## What is actually implemented (master prompt §27 — research integrity)

| Feature | Status | Phase |
|---------|--------|-------|
| `MemoryEngine` ABC + `DefaultMemoryContract` refactor | `[IMPLEMENTED]` | 2 |
| Soft-delete by default + `forget(hard=True)` legacy path | `[IMPLEMENTED]` | 2 |
| `checkpoint()` / `restore()` round-trip + idempotency | `[IMPLEMENTED]` | 2 |
| `inspect()` + `iter_all()` public iterators | `[IMPLEMENTED]` | 2 |
| `MemoryContract` deprecated alias (warns on construction) | `[IMPLEMENTED]` | 2 |
| `OrganismConfig.description` field (audit Appendix B.6) | `[IMPLEMENTED]` | 2 |
| `Organism.state_hash()` includes memory content hash (B.9) | `[IMPLEMENTED]` | 2 |
| `decay_experiment.py` uses `iter_all()` (B.2) | `[IMPLEMENTED]` | 2 |
| `HippoCoreMemory` adapter scaffold | `[IMPLEMENTED]` | 3 |
| PHASE 3 behavioral equivalence tests (golden-file) | `[IMPLEMENTED]` | 3 |
| `MemoryProvenance` dataclass | `[IMPLEMENTED]` | 4 |
| `MemoryEntry` schema extension (PHASE 4 fields) | `[IMPLEMENTED]` | 4 |
| `HippoCoreMemory.encode_episode()` full-schema entry point | `[IMPLEMENTED]` | 4 |
| `HippoCoreMemory.set_encoding_context()` | `[IMPLEMENTED]` | 4 |
| 5 replay policies (recent / importance / novelty / PE / random) | `[IMPLEMENTED]` | 5 |
| `ReplayPolicy` ABC + `ReplaySelection` telemetry | `[IMPLEMENTED]` | 5 |
| `HippoCoreMemory.replay(n=N)` policy delegation | `[IMPLEMENTED]` | 5 |
| `set_replay_policy()` runtime swap | `[IMPLEMENTED]` | 5 |
| `ConsolidationStrategy` ABC + 2 strategies (Jaccard, prefix) | `[IMPLEMENTED]` | 6 |
| `HippoCoreMemory.consolidate()` real pipeline | `[IMPLEMENTED]` | 6 |
| `last_consolidation_result` telemetry | `[IMPLEMENTED]` | 6 |
| `MemoryEventKind` enum (6 kinds) + `MemoryEvent` + `MemoryEventEmitter` | `[IMPLEMENTED]` | 7 |
| `HippoCoreMemory` emits events on every operation | `[IMPLEMENTED]` | 7 |
| `set_step()` for trajectory alignment | `[IMPLEMENTED]` | 7 |
| `EventKind` enum (17: 11 Rust + 6 PHASE 8) + `PythonCausalGraph` | `[IMPLEMENTED]` | 8 |
| `HippoCoreMemory` wired to optional causal graph | `[IMPLEMENTED]` | 8 |
| `trace_outcome_to_experience()` walk | `[IMPLEMENTED]` | 8 |
| 10-benchmark HippoCore suite (master prompt §25) | `[IMPLEMENTED]` | 9 |
| This documentation | `[IMPLEMENTED]` | 10 |

## What remains experimental / proposed (master prompt §27)

| Feature | Status | Why |
|---------|--------|-----|
| Memory-dependent behavior (Organism.tick consults MemoryEngine) | `[PROPOSED]` | PHASE 10+ follow-up; the audit's PHASE 10 doc flags this as the highest-priority item |
| Rust-side PHASES 7+8 wiring | `[PROPOSED]` | Requires `maturin build --release` (not available in authoring env) |
| Pattern separation via learned embeddings | `[PROPOSED]` | PHASE 6 uses tag-Jaccard + content-prefix (deterministic, NO LLM) — real embeddings are PHASE 10+ |
| Generative replay (`replay(generative=True)`) | `[PROPOSED]` | Currently a no-op; PHASE 6+ would reconstruct from compressed traces |
| Memory budget eviction policy | `[PROPOSED]` | `max_episodes` / `max_memory_bytes` are config-only — no eviction logic yet |
| Rust `MemoryEngine` trait (audit §11.2) | `[PROPOSED]` | Rust-side parallel of the Python ABC; needs PyO3 build |
| Edge Runtime deployment | `[PROPOSED]` | Master prompt §24 target — needs hardware profiling |

---

## Scientific status (master prompt §27)

Every claim in this integration is labeled `[IMPLEMENTED]` (built, tested,
demonstrable) or `[PROPOSED]` (designed, not yet built).

We explicitly avoid claiming:
- "biologically equivalent to hippocampus" — we have no measurement
  comparing to neural data.
- "conscious" — subjective experience is not measured.
- "AGI" — this is research infrastructure, not a deployed system.
- "biologically equivalent to dentate gyrus" for pattern separation —
  we use computational proxies (tag-Jaccard, content-prefix), not
  neural-circuit-accurate sparse distributed representations.

The audit document (`docs/HIPPOCORE_INTEGRATION_AUDIT.md` PHASE 1) sets
the skeptical scientific posture. The HippoCore implementation respects
it throughout.
