# Contributing to NurosOS

> **Identity note (v0.3.0+):** NurosOS has two parallel contribution tracks:
>
> 1. **The developmental substrate** (`nuros-dev/` crate + `experiments/` + `nuros/` Python package) — the v0.3.0+ track. Contributions here extend the experimental substrate for synthetic development.
> 2. **The neuromorphic kernel** (`kernel/`, `core/`, `hal/` Rust crates) — the v0.1.0 track. Contributions here extend the SNN execution backend.
>
> Both tracks are welcome. The developmental substrate is the active research direction; the neuromorphic kernel is preserved as a future execution backend.

---

## 0. Build & Test (Developmental Substrate)

```bash
# Prerequisites: Rust 1.75+, Python 3.10+, maturin
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
pip install maturin

# Build and install the Rust developmental substrate
cd nuros-dev
maturin build --release
pip install --force-reinstall target/wheels/nuros_dev-*.whl
# Copy the .so into the local nuros/ package for in-tree imports
cp $(python -c "import nuros._dev, os; print(os.path.dirname(nuros._dev.__file__))")/_dev*.so ../nuros/
cd ..

# Run the test suite (75 tests)
cd nuros-dev && cargo test --lib && cd ..
python -m pytest nuros/tests/test_developmental_substrate.py -v

# Run the flagship experiment
python experiments/same_genome_different_world.py --steps 300
```

---

## 1. Code of Conduct

Be excellent to each other. We are building infrastructure for the next century of computing — there is no room for ego. Disagreements are settled by **data** (benchmarks, behavioral assays, developmental trajectories), not by reputation.

---

## 2. The Cardinal Rules

### Rule 1: Scientific Honesty

Every PR must label its claims with one of: `[IMPLEMENTED]`, `[EXPERIMENTAL]`, `[PROPOSED]`, `[SPECULATIVE]`. Documentation must never imply that an unimplemented concept already exists. Avoid phrases such as "creates consciousness", "creates life", "solves cognition", "achieves sentience" unless explicitly discussing them as open hypotheses.

### Rule 2: Reproducibility

Every experiment must produce a `ReproducibilityManifest`. Every claim must ship with a runnable experiment. Two runs with the same manifest values must produce identical trajectories (within documented tolerance).

### Rule 3: Pass the Test Suite

All PRs to `main` must pass:
- 57 Rust unit tests (`cd nuros-dev && cargo test --lib`)
- 18 Python integration tests (`pytest nuros/tests/test_developmental_substrate.py`)
- 33 existing cognitive-layer tests (`pytest nuros/tests/test_core.py`)

If your change degrades any test, your PR will be rejected unless you can demonstrate that the new behavior is **more correct** than the old one (in which case, update the tests too).

### Rule 4: Biological Plausibility (for kernel/ PRs)

For PRs to the neuromorphic kernel (`kernel/`, `core/`, `hal/`), every change must include a **biological justification**. If you are adding a new neuron model, cite the cell type it models and the paper that characterizes it. If you are optimizing an existing one, show that the optimization does not degrade the Fly Benchmark score.

> ❌ *Bad commit message:* `"Optimized STDP update by 30%"`
> ✅ *Good commit message:* `"Optimized STDP update by 30% by batching eligibility traces. Fly Benchmark score unchanged (0.87 → 0.87)."`

### Rule 5: Pass the Fly Benchmark (for kernel/ PRs)

All PRs to `main` that touch the neuromorphic kernel must pass the [Fly Benchmark](../tests/README.md) suite. This is a set of behavioral tests that check whether the system's emergent behavior matches actual *Drosophila* responses (e.g., obstacle avoidance, phototaxis, courtship song production).

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
