# NurosOS Tests — The "Fly Benchmark"

This directory contains the **Fly Benchmark** — the suite of tests that
verifies the system's emergent behavior matches actual *Drosophila*
responses. It is the gatekeeper for all PRs to `main`.

## Layout

```
tests/
├── README.md                  ← this file
├── unit/                      ← Rust unit tests for kernel/core/hal
├── integration/               ← End-to-end tests that boot the kernel
├── fly_benchmark/             ← The behavioral benchmark suite
│   ├── behavioral/            ← Python: behavioral scoring scripts
│   ├── obstacle_avoidance/    ← Rust: obstacle avoidance circuit test
│   ├── phototaxis/            ← Rust: light-seeking behavior test
│   ├── courtship_song/        ← Rust: courtship song pattern test
│   └── olfactory_learning/    ← Rust: odor-shock associative memory test
└── benchmarks/                ← Performance benchmarks vs. GPU baseline
```

## The Fly Benchmark

Every PR must pass this suite. The benchmark measures how closely the
emulated behavior matches biological ground truth from published
*Drosophila* studies.

| Sub-suite             | Behavioral assay                              | Score threshold |
|-----------------------|-----------------------------------------------|-----------------|
| `obstacle_avoidance`  | Fly turns away from approaching object        | ≥ 0.85          |
| `phototaxis`          | Fly moves toward light source                 | ≥ 0.90          |
| `courtship_song`      | Male produces species-specific pulse song     | ≥ 0.80          |
| `olfactory_learning`  | Avoids odor paired with shock (within 5 min)  | ≥ 0.75          |

The score is computed by `behavioral/score.py`, which compares emulated
behavioral output to recorded *Drosophila* data.

## Running

```bash
make test                     # Run all tests (unit + integration + Fly Benchmark)
make test-fly-benchmark       # Run only the Fly Benchmark
make bench                    # Run performance benchmarks vs. GPU
```
