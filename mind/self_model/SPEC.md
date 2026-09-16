# Self Model Contract Specification

> **Note (v0.3.0-alpha):** This contract is implemented in the `nuros/`
> Python package (v0.2.0 cognitive layer). The v0.3.0 developmental
> substrate (`nuros-dev` Rust crate) builds on top of these contracts.
> See [`DEVELOPMENTAL_SUBSTRATE.md`](../../DEVELOPMENTAL_SUBSTRATE.md).


## Interface

```python
class SelfModel:
    def query(query_type: SelfModelQuery) -> Dict
    def update_state(assessment: Dict) -> None
    def update_capability(name, value, confidence) -> None
    def update_limitation(name, value, confidence) -> None
    def update_belief(belief, confidence, evidence) -> None
    def summary() -> Dict
```

## Query Types

- CAPABILITIES: What can I do?
- LIMITATIONS: What can't I do?
- BELIEFS: What do I believe about the world?
- IDENTITY: Who am I?
- CURRENT_STATE: What is my current state?
- UNCERTAINTY: What am I uncertain about?

## Invariants

1. Self-model MUST include uncertainty about self-knowledge
2. Self-model updates MUST be auditable
3. Self-model MUST NOT be directly writable by external systems
4. Capability claims MUST carry confidence values
