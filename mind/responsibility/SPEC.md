# Responsibility Contract Specification

## Purpose

For every externally relevant action, maintain the complete causal chain:
observation → inference → memory → imagination → values → decision → action → outcome

## Interface

```python
class ResponsibilityContract:
    def record_action(action, cause, epistemic_label) -> ResponsibilityEntry
    def query(filters) -> List[ResponsibilityEntry]
    def get_causal_chain(action_id) -> List[ResponsibilityEntry]
    def summary() -> Dict
```

## Invariants

1. Every action has a complete causal chain
2. Responsibility log is append-only (no deletion)
3. Responsibility log is queryable by external auditors
4. All entries carry epistemic labels
