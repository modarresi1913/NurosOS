# Epistemic Kernel Specification

## The Seven Epistemic Labels

| Label | Value | Category | Meaning |
|-------|-------|----------|---------|
| OBSERVED | 1 | Grounded | Directly sensed from environment |
| INFERRED | 2 | Grounded | Logically derived from observations |
| REMEMBERED | 3 | Grounded | Recalled from verified memory |
| PREDICTED | 4 | Speculative | Forecast of future state |
| SIMULATED | 5 | Speculative | Output of internal simulation |
| IMAGINED | 6 | Speculative | Creative/counterfactual construction |
| ACTED | 7 | Grounded | Action taken in environment |

## Forbidden Transitions

These transitions are **architecturally forbidden** to prevent epistemic corruption:

| From | To | Reason |
|------|----|--------|
| SIMULATED | OBSERVED | Simulation is not observation |
| IMAGINED | REMEMBERED | Imagination is not memory |
| PREDICTED | OBSERVED | Prediction is not observation |
| IMAGINED | OBSERVED | Imagination is not observation |
| SIMULATED | REMEMBERED | Simulation is not memory |
| PREDICTED | REMEMBERED | Prediction is not memory |

## Override Mechanism

Forbidden transitions CAN be performed with explicit `EPISTEMIC_OVERRIDE:` prefix in the justification. This is:
- Audited (logged with timestamp)
- Rare (should only happen for verified transitions)
- Traceable (can be found in audit log)

## Confidence

Every epistemic representation carries a confidence ∈ [0.0, 1.0]:
- Grounded labels typically start at high confidence
- Speculative labels typically start at lower confidence
- Confidence can be updated through Bayesian updating
- Confidence bounds are enforced (ValueError on out-of-range)

## Provenance

Every representation maintains a provenance chain:
- Who/what created it
- What it was derived from
- When it was created
- What transformations have been applied

This enables full traceability from any belief back to its origin.
