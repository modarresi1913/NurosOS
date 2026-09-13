# Imagination Contract Specification

## Interface

```python
class ImaginationEngine:
    def hypothesize(state, actions) -> List[Counterfactual]
    def simulate(counterfactual) -> Counterfactual
    def evaluate(counterfactual) -> float
    def decide(counterfactuals) -> Decision
```

## Pipeline

1. Hypothesize: Generate candidate what-if scenarios
2. Simulate: Run internal simulation for each scenario
3. Evaluate: Score outcomes against values and goals
4. Decide: Choose best action (or none if all too risky)

## Risk Levels

- LOW: Proceed with execution
- MEDIUM: Execute with monitoring
- HIGH: Block execution, log warning
- CRITICAL: NEVER execute, always block

## Invariants

1. CRITICAL risk counterfactuals are NEVER executed
2. Every simulation is labeled SIMULATED
3. Simulated results MUST NOT be stored as OBSERVED
4. Imagination MUST check safety kernel before execution
