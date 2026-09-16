# Memory Contract Specification

> **Note (v0.3.0-alpha):** This contract is implemented in the `nuros/`
> Python package (v0.2.0 cognitive layer). The v0.3.0 developmental
> substrate (`nuros-dev` Rust crate) builds on top of these contracts.
> See [`DEVELOPMENTAL_SUBSTRATE.md`](../../DEVELOPMENTAL_SUBSTRATE.md).


## Interface

```python
class MemoryContract:
    def remember(content, memory_type, importance, context) -> MemoryEntry
    def retrieve(query, limit, type_filter) -> List[MemoryEntry]
    def retrieve_by_id(memory_id) -> MemoryEntry
    def associate(id_a, id_b, relationship_type) -> bool
    def reflect(query) -> List[MemoryEntry]
    def revise(entry_id, field, new_value, justification) -> MemoryEntry
    def reconsolidate(entry_id, reward) -> MemoryEntry
    def forget(entry_id, justification) -> bool
    def replay(from_tick, to_tick) -> List[MemoryEntry]
    def working_set() -> Dict
    def working_get(key) -> Any
    def summary() -> Dict
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

1. Every memory has provenance (origin, timestamp, epistemic label)
2. Every revision is auditable (old → new, justification, timestamp)
3. Counterfactual memories MUST carry IMAGINED epistemic label
4. Decay is continuous; importance modulates decay rate
5. No memory is permanently deleted — forget() marks as forgotten
6. Association graph is bidirectional
