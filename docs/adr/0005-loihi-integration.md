# ADR 0005: Loihi integration plan (proposed)

## Status
Proposed

## Context
The v0.3.0 milestone requires a **1000× power reduction** for pattern
recognition vs. traditional GPUs. This target cannot be met on x86
emulation — it requires real neuromorphic silicon. Intel Loihi 2 is the
most mature commercially-available neuromorphic research chip.

## Decision
NurosOS will integrate with the **Intel Loihi 2 SDK** (Lava) as the
primary neuromorphic backend. The integration will live in
`hal/drivers/loihi/`.

### Integration plan

1. **v0.2.0:** Implement a Loihi *simulator* backend (runs Lava in
   software) to validate the API without hardware.
2. **v0.3.0 (RC):** Deploy on real Loihi 2 hardware at Intel Neuromorphic
   Research Community (INRC) partner sites.
3. **v0.3.0+:** Add a `--target=loihi` flag to `nuros-cli start` that
   selects the Loihi HAL driver instead of x86 emulation.

### Translation layer

NurosOS NIR bytecode → Lava process model:
- `Neuron` (LIF) → `LoihiLIF` process
- `Synapse` → `Connection` process
- `SparseSpec(density=0.05)` → Loihi's native sparse fan-out
- `StdpRule` → Loihi's on-chip learning rule (with constraints — Loihi's
  STDP is a fixed-function unit, so some SynapseLang parameters will
  need to be quantized)

## Consequences
- **Pro:** Hits the 1000× power reduction target.
- **Pro:** Validates the HAL abstraction — if Loihi integration works,
  the same pattern applies to other neuromorphic chips (TrueNorth,
  SpiNNaker, BrainScaleS).
- **Con:** Adds a hard dependency on Intel's Lava SDK (Python, GPL-ish
  license — needs legal review).
- **Con:** Loihi's on-chip learning is less flexible than SynapseLang's
  STDP. Some SynapseLang programs will not be expressible on Loihi and
  will need to fall back to off-chip learning + weight upload.
- **Con:** Hardware access is gated by Intel (INRC membership required).

## Open questions
- Can we implement dopamine-modulated plasticity (PlasticityRule::DopamineModulated)
  on Loihi? Or do we need to fall back to CPU-side modulation?
- How do we map the 5% sparsity cap to Loihi's hardware? Loihi has no
  global sparsity constraint — we'd need to enforce it in software.

## References
- WHITEPAPER.md §5 (performance projections)
- hal/drivers/loihi/src/lib.rs (stub)
- Intel Lava SDK: https://github.com/intel-ai/lava
