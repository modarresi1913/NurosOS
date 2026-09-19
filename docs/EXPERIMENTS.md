# Experiments

> The HippoCore integration ships two experiment runners:
> 1. The existing Rust flagship `experiments/same_genome_different_world.py`
>    (requires `maturin build --release`).
> 2. The PHASE 9 Python benchmark suite `benchmarks/memory/__init__.py`
>    (no Rust build required — runs on the Python cognitive layer).

---

## Experiment 1: Same Genome / Different World (master prompt §12, audit §16.1)

The flagship NurosOS × HippoCore experiment. Two organisms instantiated
from the same genome, placed in differently-seeded environments, and
developed for the same number of steps.

### Running

```bash
# Requires the Rust extension to be built (audit §16.1):
cd nuros-dev && maturin build --release && pip install --force-reinstall target/wheels/nuros_dev-*.whl && cd ..

# Run with default 200 steps:
python experiments/same_genome_different_world.py --steps 200 --env-a-seed 1 --env-b-seed 999

# Outputs (in ./experiment_outputs/same_genome_different_world/):
# genome.json
# trajectory_a.jsonl, trajectory_b.jsonl
# telemetry_a.csv, telemetry_b.csv
# checkpoint_a.json, checkpoint_b.json
# divergence.json
# mind_diff.json
# manifest_a.json, manifest_b.json
# report.txt
# summary.json
```

### PHASE 9 benchmark equivalent

For environments without the Rust build, the PHASE 9 benchmark
`08_same_genome_different_world` provides a Python-only equivalent.
It measures:

- `memory_divergence` — symmetric difference of memory IDs between A and B.
- `memory_overlap` — intersection of memory IDs.
- `behavioral_divergence` — count of action differences.
- `n_steps` — number of developmental steps.

```bash
python3 -c "from benchmarks.memory import run_benchmark, save_results, bench_08_same_genome_different_world; from pathlib import Path; r = run_benchmark('08_same_genome_different_world', bench_08_same_genome_different_world, n_seeds=5); save_results(r, Path('./benchmarks/memory/results/08_same_genome_different_world'))"
```

### Known gap (audit §16.1)

The Rust flagship produces 13 artifacts but does NOT currently measure:
- memory divergence (separate from action divergence)
- behavioral divergence as a distinct metric
- capability divergence
- causal graph divergence
- resource consumption divergence

These are the audit's identified gaps for the HippoCore-flagship version.
The PHASE 9 Python benchmark fills some of these gaps at the Python
level; the Rust-side gap remains for PHASE 10+ follow-up.

---

## Experiment 2: Catastrophic Forgetting (master prompt §11, audit §16.2)

Master prompt §11 mandates a 4-condition sequential learning protocol:
- A. baseline learning system
- B. NurosOS without HippoCore (= DefaultMemoryContract)
- C. NurosOS + HippoCore (= HippoCoreMemory, no replay)
- D. NurosOS + HippoCore + replay/consolidation

The PHASE 9 benchmark `03_catastrophic_forgetting` implements conditions
B, C, and D (condition A — "baseline learning system" — is interpreted
as the no-memory condition, which is trivially 0% retention; we report
B/C/D only).

### Running

```bash
python3 -c "from benchmarks.memory import run_benchmark, save_results, bench_03_catastrophic_forgetting; from pathlib import Path; r = run_benchmark('03_catastrophic_forgetting', bench_03_catastrophic_forgetting, n_seeds=5); save_results(r, Path('./benchmarks/memory/results/03_catastrophic_forgetting'))"
```

### Key finding (master prompt §27 — research integrity)

**`retention = 1.0` across all conditions B/C/D.** This is an HONEST
measurement of the PHASE 6 design: episodic memory does NOT overwrite;
forgetting only happens via explicit `forget()` or importance decay.
A real continual-learning weight overwrite experiment would require
modifying a learning model's weights, not just the memory store. This
is outside HippoCore scope (the HippoCore package does not own a
learning model — that's the Organism runtime's job).

This is explicitly NOT claimed as "HippoCore prevents catastrophic
forgetting" — the PHASE 6 design simply does not have overwriting in
its scope. Flagged as a known limitation in BENCHMARKS.md and
REPRODUCIBILITY.md.

---

## Experiment 3: Counterfactual Development (master prompt §13, audit §16.1)

The PHASE 9 benchmark `09_counterfactual_development` exercises the
`what_if_environment()` counterfactual via Python-side checkpoint/
restore. It measures:

- `n_actual_memories` — memories in the actual trajectory.
- `n_cf_memories` — memories in the counterfactual trajectory (after
  restoring the actual checkpoint + developing in an alt env).
- `n_cf_only_memories` — memories unique to the counterfactual
  (the "divergence").

### Running

```bash
python3 -c "from benchmarks.memory import run_benchmark, save_results, bench_09_counterfactual_development; from pathlib import Path; r = run_benchmark('09_counterfactual_development', bench_09_counterfactual_development, n_seeds=5); save_results(r, Path('./benchmarks/memory/results/09_counterfactual_development'))"
```

### Existing Rust counterfactual demo

The Rust extension already ships `experiments/counterfactual_demo.py`
which uses `CounterfactualSelf::what_if_environment()` and
`what_if_actions()` (Rust `nuros-dev/src/counterfactual.rs:130-215`).
This is LLM-free and already marked `["SIMULATED", "COUNTERFACTUAL"]`
with `executed_in_real_environment: false` enforced (audit §13).

The PHASE 9 benchmark adds a Python-side equivalent that exercises the
`HippoCoreMemory` checkpoint/restore path (master prompt §13: "What if
the organism had encountered Environment B instead of Environment A?").

---

## Experiment 4: Pattern Separation (master prompt §5, audit §3)

The PHASE 9 benchmark `01_pattern_separation` exercises similar-but-
distinguishable memory encoding and measures:

- `memory_capacity` — total memories stored (should be 2 × n_pairs).
- `collision_rate` — fraction of encodes that overwrote an existing
  memory's ID (should be 0).
- `retrieval_discrimination` — fraction of `retrieve(A)` calls that
  returned A first (should be 1.0).
- `representation_similarity` — fraction of `retrieve(A)` calls that
  ALSO returned B in the top-K (lower = better separation).

### Running

```bash
python3 -c "from benchmarks.memory import run_benchmark, save_results, bench_01_pattern_separation; from pathlib import Path; r = run_benchmark('01_pattern_separation', bench_01_pattern_separation, n_seeds=5); save_results(r, Path('./benchmarks/memory/results/01_pattern_separation'))"
```

### Key finding

`collision_rate = 0.0` and `retrieval_discrimination = 1.0` across all
seeds — encoding always produces a fresh `memory_id` and `retrieve(A)`
returns A first, not its near-duplicate B.

**Interpretation**: PHASE 4 encoding achieves pattern separation at
the storage level (every encode produces a new `memory_id`; the
retrieve filter is substring-based so similar content retrieves the
right memory first). This is NOT a neural-circuit-accurate pattern
separation mechanism — we use computational proxies (UUIDs + substring
matching), not sparse distributed representations. Flagged as a known
limitation.

---

## Experiment 5: Replay Policy Comparison (master prompt §9)

The PHASE 9 benchmark `04_replay` compares 5 replay policies on an
identical input buffer and reports `latency_ms_<policy>` and
`n_unique_<policy>` per policy.

### Running

```bash
python3 -c "from benchmarks.memory import run_benchmark, save_results, bench_04_replay; from pathlib import Path; r = run_benchmark('04_replay', bench_04_replay, n_seeds=5); save_results(r, Path('./benchmarks/memory/results/04_replay'))"
```

### Interpretation

Master prompt §9: "Do not assume one policy is superior. Benchmark
them." The benchmark reports the measurements; interpretation is left
to the researcher. No claim of "policy X is best" is made.

---

## Other experiments

The PHASE 9 suite also includes:
- `02_episodic_retrieval` — retrieval latency + accuracy on a 100-memory buffer.
- `05_consolidation` — fast→slow consolidation on a 20-memory 4-cluster buffer.
- `06_reconsolidation` — importance/confidence deltas after reconsolidate(reward=1.0).
- `07_memory_budget` — unlimited vs importance-weighted memory budget.
- `10_checkpoint_reproducibility` — checkpoint/restore round-trip fidelity.

All run via the same `run_benchmark()` harness; all produce JSON + CSV
+ Markdown summaries.
