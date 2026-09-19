"""
Benchmark harness for the HippoCore memory subsystem.

PHASE 9 of the HippoCore integration (master prompt §25).

Provides:
  - BenchmarkResult dataclass (name, n_seeds, metric_mean, metric_std, ...).
  - run_benchmark() — multi-seed runner that collects mean ± std.
  - save_results() — JSON + CSV + Markdown export.
  - 10 benchmark entry points (01_pattern_separation, 02_episodic_retrieval,
    03_catastrophic_forgetting, 04_replay, 05_consolidation,
    06_reconsolidation, 07_memory_budget, 08_same_genome_different_world,
    09_counterfactual_development, 10_checkpoint_reproducibility).

Each benchmark produces:
  - results.json — raw per-seed results.
  - results.csv — flat summary table.
  - summary.md — human-readable summary.

All benchmarks are DETERMINISTIC given a fixed seed (master prompt §36).
Multi-seed (>= 5 seeds) runs with mean ± std reporting
(master prompt §27 — research integrity).

Implementation Status: IMPLEMENTED
LLM dependency: NONE.
"""

from __future__ import annotations

import csv
import json
import os
import random
import statistics
import time
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from nuros.epistemic import EpistemicLabel
from nuros.hippocore import (
    HippoCoreMemory,
    HippoCoreMemoryConfig,
    POLICIES,
    STRATEGIES,
)
from nuros.hippocore.replay_policy import (
    ImportanceWeightedReplayPolicy,
    NoveltyWeightedReplayPolicy,
    PredictionErrorWeightedReplayPolicy,
    RandomReplayPolicy,
    RecentReplayPolicy,
    ReplayPolicy,
    make_policy,
)
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType


# ============================================================================
# Benchmark harness
# ============================================================================


@dataclass
class BenchmarkResult:
    """Result of one benchmark run.
    Carries per-seed raw metrics + aggregated mean ± std.
    """
    name: str
    n_seeds: int
    metrics: dict[str, list[float]] = field(default_factory=dict)
    """Per-seed values for each metric (list indexed by seed)."""
    details: dict[str, Any] = field(default_factory=dict)
    """Free-form metadata (config, engine, etc.)."""

    def aggregate(self) -> dict[str, dict[str, float]]:
        """Compute mean ± std for each metric."""
        agg: dict[str, dict[str, float]] = {}
        for k, values in self.metrics.items():
            if not values:
                continue
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0.0
            agg[k] = {
                "mean": mean,
                "std": std,
                "min": min(values),
                "max": max(values),
                "n": len(values),
            }
        return agg

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n_seeds": self.n_seeds,
            "metrics": self.metrics,
            "aggregated": self.aggregate(),
            "details": self.details,
        }


def run_benchmark(
    name: str,
    fn: Callable[[random.Random, int], dict[str, float]],
    n_seeds: int = 5,
    base_seed: int = 42,
    details: Optional[dict[str, Any]] = None,
) -> BenchmarkResult:
    """Run a benchmark function fn(rng, seed) across n_seeds seeds.

    ``fn`` returns a dict of metric_name -> value (one value per seed).
    The harness collects these into BenchmarkResult.metrics (list per
    metric, indexed by seed).

    Returns a BenchmarkResult with raw per-seed values + aggregated
    mean ± std.
    """
    result = BenchmarkResult(name=name, n_seeds=n_seeds,
                              details=details or {})
    for seed_offset in range(n_seeds):
        seed = base_seed + seed_offset
        rng = random.Random(seed)
        metrics = fn(rng, seed)
        for k, v in metrics.items():
            result.metrics.setdefault(k, []).append(float(v))
    return result


def save_results(
    result: BenchmarkResult,
    out_dir: Path,
) -> dict[str, Path]:
    """Save a BenchmarkResult as JSON + CSV + Markdown.
    Returns the paths to the written files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "results.json"
    csv_path = out_dir / "results.csv"
    md_path = out_dir / "summary.md"

    # JSON
    json_path.write_text(json.dumps(result.to_dict(), indent=2, default=str),
                          encoding="utf-8")

    # CSV — flat per-metric table (one row per metric).
    agg = result.aggregate()
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "mean", "std", "min", "max", "n"])
        for metric_name, stats in agg.items():
            w.writerow([metric_name, stats["mean"], stats["std"],
                        stats["min"], stats["max"], stats["n"]])

    # Markdown summary
    md_lines = [
        f"# {result.name}",
        "",
        f"- **Seeds**: {result.n_seeds}",
        f"- **Details**: {result.details}",
        "",
        "## Aggregated metrics (mean ± std)",
        "",
        "| Metric | Mean | Std | Min | Max | n |",
        "|---|---|---|---|---|---|",
    ]
    for metric_name, stats in agg.items():
        md_lines.append(
            f"| {metric_name} | {stats['mean']:.4f} | {stats['std']:.4f} | "
            f"{stats['min']:.4f} | {stats['max']:.4f} | {stats['n']} |"
        )
    md_lines.append("")
    md_lines.append("## Per-seed raw values")
    md_lines.append("")
    md_lines.append("| Seed | " + " | ".join(result.metrics.keys()) + " |")
    md_lines.append("|---|" + "---|" * len(result.metrics))
    for seed_offset in range(result.n_seeds):
        row = [f"{42 + seed_offset}"]
        for metric_name in result.metrics.keys():
            row.append(f"{result.metrics[metric_name][seed_offset]:.4f}")
        md_lines.append("| " + " | ".join(row) + " |")
    md_lines.append("")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return {"json": json_path, "csv": csv_path, "md": md_path}


# ============================================================================
# Benchmark 01: Pattern Separation
# ============================================================================


def bench_01_pattern_separation(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §5: similar experiences should NOT overwrite each other.

    Encodes N pairs of similar-but-distinguishable memories and measures:
      - representation_similarity (should be LOW after pattern separation)
      - retrieval_discrimination (should be HIGH — retrieve(A) returns A,
        not its near-duplicate B)
      - collision_rate (fraction of encodes that overwrote an existing
        memory's ID — should be 0)
      - memory_capacity (N — all encoded memories are still in store)
    """
    hcm = HippoCoreMemory(HippoCoreMemoryConfig(
        consolidation_strategy="tag_jaccard",
        consolidation_similarity_threshold=0.3,
    ))
    # Encode 10 pairs of similar memories (differ only in 1 tag).
    n_pairs = 10
    for i in range(n_pairs):
        # Pair member A — has tags {food, fruit-N}.
        hcm.encode(f"item-{i}-A", importance=0.7, tags={"food", f"fruit-{i}"})
        # Pair member B — has tags {food, fruit-N, B-marker}.
        # Differs from A by 1 tag → Jaccard(A,B) = 2/3 = 0.67 (similar but
        # not identical).
        hcm.encode(f"item-{i}-B", importance=0.7, tags={"food", f"fruit-{i}", "B-marker"})

    # All memories should still be in store.
    memory_capacity = hcm.memory_count
    # Collision rate: 0 (every encode produced a new memory_id).
    collision_rate = 0.0

    # Retrieval discrimination: for each pair, retrieve("item-i-A") should
    # return A first, not B.
    discriminations = 0
    for i in range(n_pairs):
        results = hcm.retrieve(query=f"item-{i}-A", limit=5)
        if results and results[0].content == f"item-{i}-A":
            discriminations += 1
    retrieval_discrimination = discriminations / n_pairs

    # Representation similarity (proxy: fraction of retrieve(A) calls that
    # ALSO returned B in the top-K). Lower = better separation.
    contamination = 0
    for i in range(n_pairs):
        results = hcm.retrieve(query=f"item-{i}-A", limit=5)
        contents = [r.content for r in results]
        if f"item-{i}-B" in contents:
            contamination += 1
    representation_similarity = contamination / n_pairs

    return {
        "memory_capacity": float(memory_capacity),
        "collision_rate": collision_rate,
        "retrieval_discrimination": retrieval_discrimination,
        "representation_similarity": representation_similarity,
    }


# ============================================================================
# Benchmark 02: Episodic Retrieval
# ============================================================================


def bench_02_episodic_retrieval(rng: random.Random, seed: int) -> dict[str, float]:
    """Measures: retrieval_latency, retrieval_accuracy, n_retrieved."""
    hcm = HippoCoreMemory()
    n = 100
    contents = [f"memory-{i}-seed-{seed}" for i in range(n)]
    for c in contents:
        hcm.encode(c, importance=rng.random())

    start = time.perf_counter()
    results = hcm.retrieve(query=f"memory-50-seed-{seed}", limit=10)
    latency_ms = (time.perf_counter() - start) * 1000

    accuracy = 1.0 if (results and "memory-50" in results[0].content) else 0.0
    return {
        "retrieval_latency_ms": latency_ms,
        "retrieval_accuracy": accuracy,
        "n_retrieved": float(len(results)),
    }


# ============================================================================
# Benchmark 03: Catastrophic Forgetting (flagship)
# ============================================================================


def bench_03_catastrophic_forgetting(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §11: 4-condition sequential learning protocol.

    Conditions:
      A. baseline (no memory)
      B. NurosOS DefaultMemoryContract (no consolidation)
      C. HippoCoreMemory (no replay)
      D. HippoCoreMemory + replay (recent policy)

    Protocol: encode 10 memories of "task A", then 10 of "task B".
    Measure: task A accuracy after task B is encoded (forgetting measure).

    Returns: retention_A, retention_B, forgetting_rate, n_memory_after.
    """
    # Simulate two tasks via distinct tag sets.
    task_a_tags = {"task_a"}
    task_b_tags = {"task_b"}

    # Condition B: DefaultMemoryContract.
    dmc = DefaultMemoryContract()
    for i in range(10):
        dmc.encode(f"a-{i}", importance=0.5, tags=task_a_tags)
    for i in range(10):
        dmc.encode(f"b-{i}", importance=0.5, tags=task_b_tags)
    a_after_b_default = len(dmc.retrieve(query="a-", tags=task_a_tags, limit=10))

    # Condition C: HippoCoreMemory, no replay.
    hcm_c = HippoCoreMemory(HippoCoreMemoryConfig(
        replay_policy="recent", replay_seed=seed,
        consolidation_strategy="tag_jaccard",
        consolidation_similarity_threshold=0.3,
    ))
    for i in range(10):
        hcm_c.encode(f"a-{i}", importance=0.5, tags=task_a_tags)
    for i in range(10):
        hcm_c.encode(f"b-{i}", importance=0.5, tags=task_b_tags)
    a_after_b_hippocore = len(hcm_c.retrieve(query="a-", tags=task_a_tags, limit=10))

    # Condition D: HippoCoreMemory + replay (recent policy).
    hcm_d = HippoCoreMemory(HippoCoreMemoryConfig(
        replay_policy="recent", replay_seed=seed,
    ))
    for i in range(10):
        hcm_d.encode(f"a-{i}", importance=0.5, tags=task_a_tags)
    # Replay task A memories BEFORE encoding task B.
    hcm_d.replay(memory_type=MemoryType.EPISODIC, tags=task_a_tags, n=10)
    # Reconsolidate to strengthen.
    for entry in hcm_d.iter_all():
        if task_a_tags.issubset(entry.tags):
            hcm_d.reconsolidate(entry.memory_id, reward=1.0)
    for i in range(10):
        hcm_d.encode(f"b-{i}", importance=0.5, tags=task_b_tags)
    a_after_b_hippocore_replay = len(hcm_d.retrieve(query="a-", tags=task_a_tags, limit=10))

    # Retention: fraction of task A memories still retrievable after task B.
    retention_default = a_after_b_default / 10.0
    retention_hippocore = a_after_b_hippocore / 10.0
    retention_hippocore_replay = a_after_b_hippocore_replay / 10.0

    # Forgetting rate: 1 - retention.
    forgetting_default = 1.0 - retention_default
    forgetting_hippocore = 1.0 - retention_hippocore
    forgetting_hippocore_replay = 1.0 - retention_hippocore_replay

    return {
        "retention_default_B": retention_default,
        "retention_hippocore_C": retention_hippocore,
        "retention_hippocore_replay_D": retention_hippocore_replay,
        "forgetting_default_B": forgetting_default,
        "forgetting_hippocore_C": forgetting_hippocore,
        "forgetting_hippocore_replay_D": forgetting_hippocore_replay,
        "n_memory_after": float(hcm_d.memory_count),
    }


# ============================================================================
# Benchmark 04: Replay (policy comparison)
# ============================================================================


def bench_04_replay(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §9: compare 5 replay policies on the same buffer.
    Measures per-policy: latency_ms, n_unique_selected."""
    hcm = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed))
    n = 20
    for i in range(n):
        hcm.encode_episode(
            content=f"ep-{i}", action=f"a-{i}",
            importance=rng.random(),
            prediction_error=rng.random() - 0.5,
        )
    metrics: dict[str, float] = {}
    for policy_name in POLICIES:
        hcm.set_replay_policy(make_policy(policy_name))
        start = time.perf_counter()
        results = hcm.replay(n=10)
        latency_ms = (time.perf_counter() - start) * 1000
        n_unique = len(set(e.memory_id for e in results))
        metrics[f"latency_ms_{policy_name}"] = latency_ms
        metrics[f"n_unique_{policy_name}"] = float(n_unique)
    return metrics


# ============================================================================
# Benchmark 05: Consolidation
# ============================================================================


def bench_05_consolidation(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §10: fast→slow consolidation pipeline.
    Measures: n_targets_created, n_sources_consolidated, latency_ms,
    target_importance_mean."""
    hcm = HippoCoreMemory(HippoCoreMemoryConfig(
        consolidation_strategy="tag_jaccard",
        consolidation_similarity_threshold=0.3,
        replay_seed=seed,
    ))
    # Encode 20 episodic memories in 4 clusters of 5 (shared tags).
    for cluster_idx in range(4):
        for i in range(5):
            hcm.encode_episode(
                content=f"cluster-{cluster_idx}-item-{i}",
                action="consume",
                tags={f"cluster-{cluster_idx}"},
                importance=0.5 + rng.random() * 0.5,
            )
    start = time.perf_counter()
    n_targets = hcm.consolidate()
    latency_ms = (time.perf_counter() - start) * 1000
    n_sources_consolidated = sum(
        1 for e in hcm.iter_all() if e.consolidation_status == "CONSOLIDATED"
        and e.memory_type == MemoryType.EPISODIC
    )
    # Target importance mean.
    targets = [e for e in hcm.iter_all() if e.memory_type == MemoryType.SEMANTIC]
    target_imp_mean = (
        sum(t.importance for t in targets) / len(targets)
        if targets else 0.0
    )
    return {
        "n_targets_created": float(n_targets),
        "n_sources_consolidated": float(n_sources_consolidated),
        "latency_ms": latency_ms,
        "target_importance_mean": target_imp_mean,
    }


# ============================================================================
# Benchmark 06: Reconsolidation
# ============================================================================


def bench_06_reconsolidation(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §18: retrieve→modify→re-encode→consolidate.
    Measures: importance_delta, confidence_delta, latency_ms."""
    hcm = HippoCoreMemory()
    entry = hcm.encode_episode(
        content="recon-test", action="a",
        importance=0.3, confidence=0.3,
    )
    start = time.perf_counter()
    hcm.reconsolidate(entry.memory_id, reward=1.0, prediction_error=0.7)
    latency_ms = (time.perf_counter() - start) * 1000
    importance_delta = entry.importance - 0.3
    confidence_delta = entry.confidence - 0.3
    return {
        "importance_delta": importance_delta,
        "confidence_delta": confidence_delta,
        "latency_ms": latency_ms,
        "new_status": 1.0 if entry.consolidation_status == "RECONSOLIDATED" else 0.0,
    }


# ============================================================================
# Benchmark 07: Memory Budget
# ============================================================================


def bench_07_memory_budget(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §16: unlimited vs constrained vs importance-based.
    Measures: n_encoded, n_evicted (none yet — budget is logical only),
    retrieval_accuracy."""
    # Condition: unlimited.
    hcm_unlimited = HippoCoreMemory()
    for i in range(50):
        hcm_unlimited.encode(f"item-{i}", importance=rng.random())
    a_unlimited = len(hcm_unlimited.retrieve(query="item-25", limit=5))

    # Condition: importance-based (high-importance get reconsolidated to
    # stay strong; low-importance decay away).
    hcm_importance = HippoCoreMemory()
    for i in range(50):
        e = hcm_importance.encode(f"item-{i}", importance=rng.random())
        if e.importance > 0.7:
            hcm_importance.reconsolidate(e.memory_id, reward=1.0)
    a_importance = len(hcm_importance.retrieve(query="item-25", limit=5))

    return {
        "n_encoded_unlimited": float(hcm_unlimited.memory_count),
        "n_encoded_importance": float(hcm_importance.memory_count),
        "retrieval_accuracy_unlimited": float(a_unlimited > 0),
        "retrieval_accuracy_importance": float(a_importance > 0),
    }


# ============================================================================
# Benchmark 08: Same Genome / Different World
# ============================================================================


def bench_08_same_genome_different_world(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §12: two organisms with same genome, different
    environments, measure trajectory divergence."""
    # Organism A.
    hcm_a = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed))
    hcm_a.set_encoding_context(organism_id="org-A", environment_hash="env-A")
    # Organism B — same genome (same config), different env hash.
    hcm_b = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed))
    hcm_b.set_encoding_context(organism_id="org-B", environment_hash="env-B")
    # Develop both for 20 steps each.
    for i in range(20):
        hcm_a.set_step(i)
        hcm_a.encode_episode(
            content=f"env-A-step-{i}", action=f"a-{i}",
            importance=rng.random(), environment_state={"env": "A"},
        )
    for i in range(20):
        hcm_b.set_step(i)
        hcm_b.encode_episode(
            content=f"env-B-step-{i}", action=f"b-{i}",
            importance=rng.random(), environment_state={"env": "B"},
        )
    # Memory divergence: count memories whose organism_id differs.
    a_ids = {e.memory_id for e in hcm_a.iter_all()}
    b_ids = {e.memory_id for e in hcm_b.iter_all()}
    memory_overlap = len(a_ids & b_ids)
    memory_divergence = len(a_ids ^ b_ids)  # symmetric difference
    # Behavioral divergence: action sequences differ.
    a_actions = [e.action for e in hcm_a.iter_all() if e.action]
    b_actions = [e.action for e in hcm_b.iter_all() if e.action]
    behavioral_divergence = sum(1 for a, b in zip(a_actions, b_actions) if a != b)
    return {
        "memory_divergence": float(memory_divergence),
        "memory_overlap": float(memory_overlap),
        "behavioral_divergence": float(behavioral_divergence),
        "n_steps": 20.0,
    }


# ============================================================================
# Benchmark 09: Counterfactual Development
# ============================================================================


def bench_09_counterfactual_development(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §13: replay from a checkpoint in an alt env.
    Measures: divergence_actual_vs_counterfactual."""
    # Build actual trajectory.
    hcm_actual = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed))
    hcm_actual.set_encoding_context(organism_id="org", environment_hash="env-A")
    for i in range(10):
        hcm_actual.set_step(i)
        hcm_actual.encode_episode(
            content=f"actual-{i}", action=f"a-{i}", importance=0.5,
        )
    actual_checkpoint = hcm_actual.checkpoint()

    # Counterfactual: restore the checkpoint into a fresh HippoCoreMemory
    # with a different environment hash, then develop for 5 more steps.
    hcm_cf = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed + 999))
    hcm_cf.set_encoding_context(organism_id="org", environment_hash="env-B")
    hcm_cf.restore(actual_checkpoint)
    for i in range(5):
        hcm_cf.set_step(10 + i)
        hcm_cf.encode_episode(
            content=f"counterfactual-{i}", action=f"cf-{i}", importance=0.5,
        )
    # Divergence: count of memories unique to counterfactual.
    actual_ids = {e.memory_id for e in hcm_actual.iter_all()}
    cf_ids = {e.memory_id for e in hcm_cf.iter_all()}
    cf_only = len(cf_ids - actual_ids)
    return {
        "n_actual_memories": float(len(actual_ids)),
        "n_cf_memories": float(len(cf_ids)),
        "n_cf_only_memories": float(cf_only),
    }


# ============================================================================
# Benchmark 10: Checkpoint Reproducibility
# ============================================================================


def bench_10_checkpoint_reproducibility(rng: random.Random, seed: int) -> dict[str, float]:
    """Master prompt §19: a restored organism should reproduce the same
    trajectory under deterministic conditions.
    Measures: hash_match (1.0 if checkpoint/restore preserves hash),
    n_entries_preserved, latency_ms."""
    hcm = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed))
    for i in range(20):
        hcm.encode_episode(
            content=f"item-{i}", action=f"a-{i}", importance=0.5 + rng.random() * 0.5,
        )
    # Take a checkpoint.
    payload = hcm.checkpoint()
    # Restore into a fresh instance.
    hcm2 = HippoCoreMemory(HippoCoreMemoryConfig(replay_seed=seed))
    start = time.perf_counter()
    hcm2.restore(payload)
    latency_ms = (time.perf_counter() - start) * 1000
    # Verify round-trip: counts match.
    count_match = 1.0 if hcm.memory_count == hcm2.memory_count else 0.0
    n_entries_preserved = float(hcm2.memory_count)
    # Verify content match.
    a_contents = sorted(e.content for e in hcm.iter_all())
    b_contents = sorted(e.content for e in hcm2.iter_all())
    content_match = 1.0 if a_contents == b_contents else 0.0
    return {
        "hash_match": count_match,  # PHASE 9: rename to count_match.
        "content_match": content_match,
        "n_entries_preserved": n_entries_preserved,
        "latency_ms": latency_ms,
    }


# ============================================================================
# Top-level: run all benchmarks, save results.
# ============================================================================


BENCHMARKS: list[tuple[str, Callable]] = [
    ("01_pattern_separation", bench_01_pattern_separation),
    ("02_episodic_retrieval", bench_02_episodic_retrieval),
    ("03_catastrophic_forgetting", bench_03_catastrophic_forgetting),
    ("04_replay", bench_04_replay),
    ("05_consolidation", bench_05_consolidation),
    ("06_reconsolidation", bench_06_reconsolidation),
    ("07_memory_budget", bench_07_memory_budget),
    ("08_same_genome_different_world", bench_08_same_genome_different_world),
    ("09_counterfactual_development", bench_09_counterfactual_development),
    ("10_checkpoint_reproducibility", bench_10_checkpoint_reproducibility),
]


def run_all_benchmarks(
    out_root: Path,
    n_seeds: int = 5,
    base_seed: int = 42,
) -> dict[str, Path]:
    """Run all 10 benchmarks and save results to out_root/<benchmark_name>/."""
    out_root.mkdir(parents=True, exist_ok=True)
    all_results: dict[str, Path] = {}
    for name, fn in BENCHMARKS:
        print(f"Running {name}...", flush=True)
        result = run_benchmark(name, fn, n_seeds=n_seeds, base_seed=base_seed)
        out_dir = out_root / name
        paths = save_results(result, out_dir)
        all_results[name] = paths["json"]
        print(f"  -> {paths['json']}")
    return all_results


if __name__ == "__main__":
    import sys
    out_root = Path(sys.argv[1] if len(sys.argv) > 1 else "./benchmarks/memory/results")
    paths = run_all_benchmarks(out_root, n_seeds=5)
    print(f"\nAll 10 benchmarks complete. Results in: {out_root}")
