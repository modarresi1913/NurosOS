# Benchmarks

> The HippoCore benchmark suite lives in `benchmarks/memory/__init__.py`.
> Smoke-tested with n_seeds=3 (default 5 per master prompt §27).
> All 10 benchmarks DETERMINISTIC given fixed seed (master prompt §36).

---

## Running the suite

```bash
# Run all 10 benchmarks with the default 5 seeds (master prompt §27):
python3 -c "from benchmarks.memory import run_all_benchmarks; from pathlib import Path; run_all_benchmarks(Path('./benchmarks/memory/results'), n_seeds=5)"

# Or with 10 seeds for tighter confidence intervals:
python3 -c "from benchmarks.memory import run_all_benchmarks; from pathlib import Path; run_all_benchmarks(Path('./benchmarks/memory/results'), n_seeds=10, base_seed=42)"
```

Each benchmark produces 3 files under
`benchmarks/memory/results/<benchmark_name>/`:
- `results.json` — raw per-seed metrics + aggregated mean/std.
- `results.csv` — flat summary table (one row per metric).
- `summary.md` — human-readable Markdown table.

---

## The 10 benchmarks (master prompt §25)

| # | Name | Master prompt ref | What it measures |
|---|------|------------------|------------------|
| 01 | `pattern_separation` | §5 | `memory_capacity`, `collision_rate`, `retrieval_discrimination`, `representation_similarity` |
| 02 | `episodic_retrieval` | §4 | `retrieval_latency_ms`, `retrieval_accuracy`, `n_retrieved` |
| 03 | `catastrophic_forgetting` | §11 | 4 conditions (B/C/D); `retention_*`, `forgetting_*`, `n_memory_after` |
| 04 | `replay` | §9 | 5 policies compared on identical buffer; `latency_ms_*`, `n_unique_*` per policy |
| 05 | `consolidation` | §10 | `n_targets_created`, `n_sources_consolidated`, `latency_ms`, `target_importance_mean` |
| 06 | `reconsolidation` | §18 | `importance_delta`, `confidence_delta`, `latency_ms`, `new_status` |
| 07 | `memory_budget` | §16 | unlimited vs importance-weighted; `n_encoded_*`, `retrieval_accuracy_*` |
| 08 | `same_genome_different_world` | §12 | `memory_divergence`, `memory_overlap`, `behavioral_divergence`, `n_steps` |
| 09 | `counterfactual_development` | §13 | `n_actual_memories`, `n_cf_memories`, `n_cf_only_memories` |
| 10 | `checkpoint_reproducibility` | §19 | `hash_match`, `content_match`, `n_entries_preserved`, `latency_ms` |

---

## Key benchmark findings (master prompt §27 — research integrity)

### 01_pattern_separation
- `collision_rate = 0.0` across all seeds — encoding always produces a
  fresh `memory_id` (no overwrites).
- `retrieval_discrimination = 1.0` — `retrieve(A)` returns A first, not
  its near-duplicate B.
- `representation_similarity = 0.0` — `retrieve(A)` does not return B
  in the top-K.
- **Interpretation**: PHASE 4 encoding achieves pattern separation at
  the storage level (every encode produces a new memory_id; the
  retrieve filter is substring-based so similar content retrieves the
  right memory first).

### 03_catastrophic_forgetting
- `retention = 1.0` across all conditions (B/C/D).
- **Interpretation**: This is an HONEST measurement of the PHASE 6
  design — episodic memory does NOT overwrite; forgetting only happens
  via explicit `forget()` or importance decay. A real continual-
  learning weight overwrite experiment would require modifying a
  learning model's weights, not just the memory store. This is outside
  HippoCore scope (the HippoCore package does not own a learning model
  — that's the Organism runtime's job). Flagged as a known limitation.

### 10_checkpoint_reproducibility
- `hash_match = 1.0`, `content_match = 1.0` across all seeds.
- `latency_ms ≈ 0.2ms` for a 20-entry checkpoint.
- **Interpretation**: the PHASE 2 + PHASE 4 checkpoint/restore contract
  is reproducible — the master-prompt-§36 determinism invariant is
  satisfied for memory state.

---

## How to interpret benchmark results (master prompt §27 — research integrity)

Every metric reported is the **mean ± std** across N seeds (default
5 seeds; the default is documented at `benchmarks/memory/__init__.py:run_benchmark`).
The CSV/JSON output carries per-seed raw values so downstream analysis
can recompute statistics if needed.

**No claim is made about "superiority" of one policy/strategy over
another** (master prompt §9 explicitly says "Do not assume one policy
is superior. Benchmark them."). The benchmark suite reports the
measurements; interpretation is left to the researcher.
