# Epistemic Kernel Specification

> **Note (v0.3.0-alpha):** This document describes the v0.2.0 cognitive
> architecture. NurosOS has since evolved into "The Experimental Substrate
> for Synthetic Development". For the current v0.3.0+ architecture (with
> the new Developmental Substrate layer), see
> [`ARCHITECTURE.md`](../ARCHITECTURE.md) and
> [`DEVELOPMENTAL_SUBSTRATE.md`](../DEVELOPMENTAL_SUBSTRATE.md).
>
> The v0.2.0 cognitive layer described here is still implemented in the
> `nuros/` Python package and is the foundation on which the v0.3.0
> developmental substrate builds.


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
