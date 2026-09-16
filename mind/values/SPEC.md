# Values/Drives Contract Specification

> **Note (v0.3.0-alpha):** This contract is implemented in the `nuros/`
> Python package (v0.2.0 cognitive layer). The v0.3.0 developmental
> substrate (`nuros-dev` Rust crate) builds on top of these contracts.
> See [`DEVELOPMENTAL_SUBSTRATE.md`](../../DEVELOPMENTAL_SUBSTRATE.md).


## Three-Tier Hierarchy

1. **Immutable Constraints** — Cannot be revoked
   - human_override, no_self_harm, epistemic_integrity, audit_trail, shutdown_compliance

2. **Contextual Goals** — Can be added/revoked with justification
   - Task-specific objectives

3. **Preferences** — Can be freely adjusted
   - Behavioral tendencies, style preferences

## Interface

```python
class ValuesContract:
    def add_constraint(name, description) -> (bool, str)
    def add_goal(name, description, priority) -> (bool, str)
    def add_preference(name, value) -> (bool, str)
    def revoke(name) -> (bool, str)
    def evaluate_action(action, context) -> (bool, str)
    def get_active_values() -> List[Value]
    def summary() -> Dict
```

## Invariants

1. Immutable constraints CANNOT be revoked
2. Value conflicts resolved through hierarchy (constraints > goals > preferences)
3. Every value change is auditable
