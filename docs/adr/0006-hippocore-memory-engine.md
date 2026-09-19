# ADR 0006: HippoCore Memory Engine Integration

**Date**: 2026-09-19
**Status**: ACCEPTED (PHASES 1-10 implemented on `feature/hippocore-integration-audit` branch)

## Context

The master prompt mandates a deep architectural integration of
NurosOS with HippoCore (an episodic memory & continual-learning
engine). The audit (Phase 1, commit `254875c`, `docs/HIPPOCORE_
INTEGRATION_AUDIT.md`) identified three parallel, non-unified memory
subsystems in NurosOS:

1. Python `MemoryContract` (`nuros/memory.py:118`) — the documented
   Mind Contract Layer Contract 1.
2. Rust `MemoryRecord` (`nuros-dev/src/organism.rs:30`) — the
   developmental substrate's memory.
3. Rust kernel `Ams` (`kernel/src/mem.rs:54`) — the "no-filesystem"
   content-addressable store, never used by the developmental substrate.

The audit also identified critical gaps:
- `MindCheckpoint` (`nuros-dev/src/checkpoint.rs:29`) does NOT capture
  Python-side memory state — restoring a checkpoint would NOT restore
  memories.
- `EventKind::MemoryUpdate` (`nuros-dev/src/causality.rs:33`) is
  defined but never produced.
- 10 pre-existing bugs catalogued in Appendix B (forget() hard-delete
  spec violation, decay_experiment.py `_store` AttributeError,
  MemoryRecord.access_count dead field, Organism.state_hash() not
  including memory contents, OrganismConfig missing description field,
  etc.).

## Decision

Introduce a `MemoryEngine` ABC that unifies the three subsystems
behind a single pluggable contract. Provide two implementations:

1. **`DefaultMemoryContract`** (`nuros/memory.py`): the historical
   `MemoryContract` behaviour, retained for full backward
   compatibility. `MemoryContract` is kept as a deprecated alias.
2. **`HippoCoreMemory`** (`nuros/hippocore/memory_engine.py`): a new
   implementation that delivers genuine hippocampal-inspired
   computational mechanisms (episodic encoding + structured
   provenance + 5 replay policies + fast→slow consolidation +
   memory event emission + causal graph integration).

The selector knob is `OrganismConfig.memory_engine = "default" |
"hippocore"` (default `"default"` for backward compatibility).

## Consequences

### Positive

- **Unification**: three memory subsystems → one ABC with two impls.
- **Pluggability**: future memory engines (e.g. a Rust trait impl
  backed by the kernel `Ams`) can be added without touching the ABC
  or any caller.
- **Backward compatibility**: `MemoryContract` is kept as a deprecated
  alias. All existing callers (`Organism`, `Organism0..5`,
  `benchmark_suite`, `decay_experiment`) continue to work unchanged.
- **Determinism**: every HippoCore operation is deterministic given
  a fixed seed (PHASE 9 benchmark suite verifies this with multi-seed
  runs).
- **No LLM dependency**: the HippoCore package is fully local and
  deterministic (master prompt §23).
- **Honest scientific status**: every claim is labeled `[IMPLEMENTED]`
  / `[PROPOSED]` / `[NOT VALIDATED]` (master prompt §27). No
  "biological equivalence" or "consciousness" or "AGI" overclaims.

### Negative

- **Schema migration**: extending `MemoryEntry` with PHASE 4 fields
  requires existing checkpoint JSON files to use `#[serde(default)]`
  for the new fields. Backward-compatible per the PHASE 2 + PHASE 4
  implementation.
- **Rust-side wiring is deferred**: PHASES 7+8 land the Python side;
  the Rust side needs PyO3 callback integration to consume
  `MemoryEventEmitter` events. Requires `maturin build --release`
  (not available in the PHASE 10 authoring environment). Flagged as
  known technical debt.
- **Memory-dependent behavior is deferred**: `Organism.tick()` does
  not yet consult `MemoryEngine.retrieve()` during action selection
  (audit §36 stage 5). Flagged as the highest-priority PHASE 10+
  item.

### Neutral

- The audit's existing Rust `Ams` (`kernel/src/mem.rs:54`) remains
  unused by the developmental substrate. It is documented as a
  candidate pattern-separation backend for PHASE 10+.
- The Rust `MemoryRecord` (`nuros-dev/src/organism.rs:30`) remains
  a simple `Vec<MemoryRecord>`. PHASE 10+ should make it a
  `DefaultMemory` impl of a Rust `MemoryEngine` trait (audit §11.2).

## Alternatives considered

1. **Copy HippoCore into NurosOS as a fourth memory subsystem**:
   rejected — would create a 4-way divergence (audit §20 architectural
   risk).
2. **Replace MemoryContract entirely with HippoCore**: rejected —
   would break backward compat with all existing callers and tests.
3. **Defer integration until the Rust extension is rebuilt**: rejected
   — the Python side is sufficient for the audit's PHASES 1-10
   scope (the Rust side is documented as PHASE 10+ follow-up).

## Implementation timeline

| Phase | Commit | Description |
|-------|--------|-------------|
| 1 | `254875c` | Audit |
| 2 | `f29a768` | Memory Contract stabilization |
| 3 | `5c58859` | HippoCore adapter scaffold |
| 4 | `b5dcc6e` | Episodic encoding + provenance |
| 5 | `3e60a63` | Replay policies |
| 6 | `f5dc734` | Consolidation pipeline |
| 7 | `b3e97cf` | Memory event emission |
| 8 | `74fb2da` | Causal graph integration (Python side) |
| 9 | `bc411cf` | 10-benchmark suite |
| 10 | (this commit) | Documentation + release |

## References

- Audit: `docs/HIPPOCORE_INTEGRATION_AUDIT.md` (1051 lines, 24 sections + 2 appendices)
- Integration guide: `docs/HIPPOCORE_INTEGRATION.md`
- Memory architecture: `docs/MEMORY_ARCHITECTURE.md`
- Developmental memory: `docs/DEVELOPMENTAL_MEMORY.md`
- Benchmarks: `docs/BENCHMARKS.md`
- Metrics: `docs/METRICS.md`
- Reproducibility: `docs/REPRODUCIBILITY.md`
- Experiments: `docs/EXPERIMENTS.md`
- Final report: `docs/HIPPOCORE_INTEGRATION_REPORT.md`
- Master prompt sections: 0-37 (master prompt).
