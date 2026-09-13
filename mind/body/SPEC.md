# Body Contract Specification

## Body Types

- PHYSICAL: Robot with real sensors and actuators
- VIRTUAL: Avatar in simulated environment
- SOFTWARE: API-connected software environment
- SIMULATION: Sandboxed simulation
- GAME: Game world
- ABSTRACT: No physical presence

## Interface

```python
class BodyContract:
    def sense(channel: str) -> Observation
    def act(action: Dict) -> Result
    def available_channels() -> List[Channel]
    def body_type() -> BodyType
    def attach(organism) -> None
    def detach() -> None
```

## Invariants

1. Body abstraction is portable (same mind, different body)
2. All sensory input labeled OBSERVED
3. All motor output labeled ACTED
4. Body can be changed without modifying mind
