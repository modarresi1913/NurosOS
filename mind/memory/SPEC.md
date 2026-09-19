# Memory Contract Specification

> **PHASE 2 update (HippoCore integration):** This contract is now backed
> by the `MemoryEngine` ABC (`nuros/memory_engine.py`). The historical
> `MemoryContract` class is now a *deprecated alias* for
> `DefaultMemoryContract` (`nuros/memory.py`) — the reference impl of
> `MemoryEngine`. The ABC adds four first-class operations
> (`consolidate`, `checkpoint`, `restore`, `inspect`) and an
> `iter_all()` public iterator. `forget()` is now SOFT-delete by
> default (`hard=False`) — closes audit Appendix B.1 spec violation.
> See `docs/HIPPOCORE_INTEGRATION_AUDIT.md` §11 for the full
> MemoryEngine API and migration rationale.
>
> The v0.3.0-alpha developmental substrate (`nuros-dev` Rust crate)
> builds on top of these contracts.


## Interface (PHASE 2)

```python
# nuros/memory_engine.py — the ABC
class MemoryEngine(ABC):
    def encode(content, memory_type=None, origin="", provenance="",
               confidence=1.0, importance=0.5, context=None, tags=None,
               epistemic_label=None) -> MemoryEntry
    def retrieve(query=None, memory_type=None, min_confidence=0.0,
                 min_importance=0.0, tags=None, limit=10) -> List[MemoryEntry]
    def retrieve_by_id(memory_id) -> Optional[MemoryEntry]
    def associate(memory_id_a, memory_id_b, relation_type="semantic",
                  strength=1.0, bidirectional=True) -> bool
    def reconsolidate(memory_id, reward=0.0,
                      prediction_error=None) -> Optional[MemoryEntry]
    def replay(memory_type=None, tags=None, time_range=None,
               n=None, generative=False) -> List[MemoryEntry]
    def consolidate(source_type=EPISODIC, target_type=SEMANTIC,
                    batch_size=50, similarity_threshold=0.85) -> int
    def forget(memory_id, justification="", hard=False) -> bool
    def checkpoint() -> dict[str, Any]
    def restore(payload: dict[str, Any]) -> None
    def inspect(memory_id) -> Optional[dict[str, Any]]
    def iter_all() -> List[MemoryEntry]
    # Properties: memory_count, operation_log
    # Working memory: working_set(key, value), working_get(key)
    # Summary: summary() -> dict[str, Any]

# nuros/memory.py — the reference impl
class DefaultMemoryContract(MemoryEngine): ...
class MemoryContract(DefaultMemoryContract):  # deprecated alias, warns on construction
    ...
```

## Memory Types

| Type | Epistemic Default | Purpose |
|------|------------------|---------|
| EPISODIC | OBSERVED | Event sequences with temporal context |
| SEMANTIC | INFERRED | Generalized knowledge and facts |
| PROCEDURAL | ACTED | Skill and habit storage |
| WORKING | OBSERVED | Temporary active state |
| COUNTERFACTUAL | IMAGINED | What-if scenarios |

## Invariants

1. Every memory has provenance (origin, timestamp, epistemic label).
2. Every revision is auditable (old → new, justification, timestamp).
3. Counterfactual memories MUST carry IMAGINED epistemic label.
4. Decay is continuous; importance modulates decay rate.
5. `forget(hard=False)` (default) SOFT-forgets — entry stays in store,
   marked `forgotten=True`, `importance=0`,
   `consolidation_status="FORGOTTEN"`, epistemic label downgraded
   (REMEMBERED → INFERRED). Invisible to `retrieve()` but visible
   via `iter_all()`. Satisfies the historical invariant
   "No memory is permanently deleted".
6. `forget(hard=True)` permanently deletes (legacy behaviour).
7. Association graph is bidirectional.
8. `MemoryEntry` carries a `consolidation_status` field
   (ACTIVE / WEAKENING / CONSOLIDATED / RECONSOLIDATED / ARCHIVED /
   FORGOTTEN) tracking the conceptual forgetting lifecycle
   (audit §17).
9. `checkpoint()` payload MUST round-trip via `restore()` and be
   idempotent (audit §11.1). `MindCheckpoint.memory_state` (PHASE 7)
   carries this payload through the Rust substrate.
10. `reconsolidate()` accepts an optional `prediction_error` argument
    (audit §11.1 NEW field usage) — when provided, the error is
    recorded on `MemoryEntry.prediction_error` and modulates the
    reward magnitude.
