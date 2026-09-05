# Contributing to NurosOS

> **"Biological Plausibility First, Performance Second."**

Thank you for considering a contribution to NurosOS. This document describes how to add new neuro-synaptic models, fix bugs, and propose architectural changes.

---

## 1. Code of Conduct

Be excellent to each other. We are building infrastructure for the next century of computing — there is no room for ego. Disagreements are settled by **data** (benchmarks, behavioral assays), not by reputation.

---

## 2. The Two Cardinal Rules

### Rule 1: Biological Plausibility First

Every PR must include a **biological justification**. If you are adding a new neuron model, cite the cell type it models and the paper that characterizes it. If you are optimizing an existing one, show that the optimization does not degrade the Fly Benchmark score.

> ❌ *Bad commit message:* `"Optimized STDP update by 30%"`
> ✅ *Good commit message:* `"Optimized STDP update by 30% by batching eligibility traces. Fly Benchmark score unchanged (0.87 → 0.87)."*

### Rule 2: Pass the Fly Benchmark

All PRs to `main` must pass the [Fly Benchmark](../tests/README.md) suite. This is a set of behavioral tests that check whether the system's emergent behavior matches actual *Drosophila* responses (e.g., obstacle avoidance, phototaxis, courtship song production).

If your change degrades the benchmark, your PR will be rejected unless you can demonstrate that the new behavior is **more biologically accurate** than the old one (in which case, update the benchmark too).

---

## 3. Development Workflow

We use **GitFlow**:

```
main              ← protected, always green
├── develop       ← integration branch
├── feature/*     ← new neuro-synaptic models, new HAL drivers
├── bugfix/*      ← fixes
└── release/*     ← release preparation
```

### 3.1 Branch naming

- `feature/stdp-eligibility-trace` — new feature
- `bugfix/hal-loihi-remap-deadlock` — bug fix
- `docs/adr-0005-neuromodulator-scheduler` — documentation only

### 3.2 Commit format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body — biological justification, benchmark numbers>

<footer — issue references>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `bench`, `chore`.

### 3.3 Pull Request requirements

A PR is mergeable when:

1. ✅ It builds cleanly (`make build`).
2. ✅ All tests pass (`make test`).
3. ✅ The Fly Benchmark score does not regress.
4. ✅ It has **2 approving reviews** from maintainers.
5. ✅ CI is green (Rust clippy, Python ruff, Fly Benchmark, formatting).
6. ✅ The PR description includes a **biological justification** section.

---

## 4. Adding a New Neuro-Synaptic Model

This is the most common contribution type. Follow this checklist:

### 4.1 Choose a biological reference

Pick a specific cell type or circuit. Examples:

- αβ Kenyon cells (mushroom body)
- P-FN neurons (central complex, head-direction system)
- AVA interneurons (locomotor rhythm generator — though this is *C. elegans*, we accept cross-species models if justified)

### 4.2 Implement the model in Rust

Create `core/src/models/<your_model>.rs`. The model must implement the `NeuronModel` trait:

```rust
pub trait NeuronModel: Send + Sync {
    /// Update membrane potential given incoming spikes.
    fn step(&mut self, dt: f32, inputs: &[Spike]) -> StepResult;

    /// Return current membrane potential (in mV, biological scale).
    fn potential(&self) -> f32;

    /// Return parameters as a serializable struct (for AMS persistence).
    fn params(&self) -> NeuronParams;
}
```

Every function **must** have a doc comment referencing the biological equivalent:

```rust
/// Lateral inhibition as seen in the Drosophila antennal lobe.
///
/// Each projection neuron (PN) receives feedforward inhibition from
/// local interneurons (LNs) within a 5-neuron radius. This sharpens
/// odor identity coding by suppressing non-principal responses.
///
/// Reference: Hong & Wilson, Nat Neurosci 2015.
fn lateral_inhibit(&mut self, radius: usize, strength: f32) { ... }
```

### 4.3 Register the model

Add an entry to `core/src/models/registry.rs`:

```rust
register_model!("alpha_beta_kenyon", AlphaBetaKenyon::default());
```

### 4.4 Add a SynapseLang binding

In `compiler/synapselang/stdlib.py`, add a constructor:

```python
@dsl_callable
def kenyon_cell(n: int, **params) -> NeuronPopulation:
    """αβ Kenyon cells — sparse, high-dimensional odor coding."""
    return NeuronPopulation("alpha_beta_kenyon", n, params)
```

### 4.5 Write tests

- Unit test in `core/src/models/<your_model>.rs` (under `#[cfg(test)]`).
- Integration test in `tests/fly_benchmark/<behavior>.rs`.
- Update the Fly Benchmark if your model affects a measured behavior.

### 4.6 Update documentation

- Add an entry to `docs/models.md` (create if missing).
- If the model introduces a new architectural pattern, write an ADR in `docs/adr/`.

---

## 5. Adding a New HAL Driver

### 5.1 Implement the `NeuromorphicTarget` trait

See `hal/src/lib.rs` for the trait definition. Your driver lives in `hal/drivers/<target>/`.

### 5.2 Mandatory: dynamic remapping

Every driver **must** implement `remap(failed: NeuronId) -> NeuronId`. If your hardware does not support runtime rerouting, implement it in software by maintaining a shadow routing table.

### 5.3 Mandatory: power instrumentation

Every driver must report energy consumption per tick via the `EnergyReport` struct. This is how we validate the v0.3.0 milestone (1000× power reduction).

---

## 6. Coding Standards

### Rust (kernel, core, hal)

- `cargo fmt` — enforced by CI.
- `cargo clippy -- -D warnings` — zero warnings allowed.
- No `unsafe` in `kernel/` without an ADR justifying it.
- All `pub` items must have doc comments.
- All numeric constants must have units in their name: `SPIKE_THRESHOLD_MV`, not `SPIKE_THRESHOLD`.

### Python (compiler, tools)

- `ruff format` + `ruff check` — enforced by CI.
- Type hints required on all public functions.
- NumPy-style docstrings.

### Comments referencing biology

Every non-trivial function must have at least one comment tying its behavior to a biological equivalent. Examples:

```rust
// Mimics the calcium-activated potassium channel (KCa) that drives
// the afterhyperpolarization in Drosophila projection neurons.
fn after_hyperpolarization(&mut self) { ... }
```

```python
# Implements short-term facilitation at the ORN→PN synapse,
# matching the depression/facilitation dynamics measured by
# Kazama & Wilson (2008).
def facilitate(self, spike_history): ...
```

---

## 7. Issue Reporting

Bugs and feature requests go through GitHub Issues. Use the templates:

- **Bug report:** Include kernel version, HAL target, Fly Benchmark score, minimal reproduction.
- **Feature request:** Include biological justification, proposed API, and at least one cited paper.

Vague issues ("it's slow", "add X") will be closed.

---

## 8. Recognition

Contributors who merge 5+ substantive PRs are invited to join the **Maintainers** team. Maintainers have merge access to `develop` (but not `main` — `main` always requires the founders' sign-off).

Notable contributions are acknowledged in `docs/contributors.md` and in release notes.

---

## 9. License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0, as described in [`LICENSE`](./LICENSE).

---

*Thank you for helping build the substrate for Digital Biology.*
