# ADR 0003: SPP sparsity threshold is 5%

## Status
Accepted

## Context
The Sparse Propagation Protocol (SPP) requires a *sparsity threshold* —
the maximum fraction of neurons that may be active in a single tick.
Setting this threshold is the single most important parameter in NurosOS:

- Too low → the system is functionally inert (insufficient capacity).
- Too high → energy consumption explodes (defeating the purpose).

Three candidate values were considered: 1%, 5%, 10%.

## Decision
The SPP sparsity threshold is set to **5%** (`SPARSITY_THRESHOLD = 0.05`
in `kernel/src/lib.rs`).

## Rationale
- **1%** is the observed activation rate in *C. elegans* (a much simpler
  organism). For Drosophila it is too sparse — the mushroom body alone
  needs ~5% KC activation to encode odors.
- **5%** matches the observed simultaneous activation rate in the
  *Drosophila* central brain during walking (~4.2%, measured by
  two-photon calcium imaging). It is the biological ground truth.
- **10%** would give more capacity but no longer matches the energy
  budget. Mitochondrial ATP supply caps biological firing at ~5%.

## Consequences
- **Pro:** The 5% figure is empirically defensible — we can point to
  published data and say "this is what the fly does."
- **Pro:** At 5%, the energy model in `WHITEPAPER.md` §5 predicts a
  1000× power reduction on Loihi, hitting the v0.3.0 milestone target.
- **Con:** 5% is global in v0.1.0. Different regions may want different
  caps (the mushroom body is naturally sparser than the antennal lobe).
  This is tracked as open question Q1 in `ARCHITECTURE.md` §8.

## References
- ARCHITECTURE.md §1.2 (Invariant I1), §3 (SPP)
- WHITEPAPER.md §4 (SPP)
- Laughlin & Sejnowski (2003), *Science*
