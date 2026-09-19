"""
PHASE 5 tests — replay policies.

Verifies the new PHASE 5 surface:
  - ReplayPolicy ABC + 5 concrete policies
  - HippoCoreMemoryConfig(replay_policy=...) knob
  - HippoCoreMemory.replay(n=N) delegates to the configured policy
  - Deterministic when seeded (reproducibility)
  - All policies produce sensible selections given edge-case inputs
    (empty buffer, n > buffer_size, all-zero importances, etc.)

Master prompt §9: "Do not assume one policy is superior. Benchmark them."
These tests do NOT compare policies for "superiority" — they only verify
each policy's contract. The actual benchmark comparison happens in
PHASE 9 (benchmarks/memory/04_replay).
"""

from __future__ import annotations

import unittest
from typing import Any

from nuros.hippocore import (
    HippoCoreMemory,
    HippoCoreMemoryConfig,
    ImportanceWeightedReplayPolicy,
    NoveltyWeightedReplayPolicy,
    POLICIES,
    PredictionErrorWeightedReplayPolicy,
    RandomReplayPolicy,
    RecentReplayPolicy,
    ReplayPolicy,
    ReplaySelection,
    make_policy,
)
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType


# ============================================================================
# Test utilities
# ============================================================================

def make_test_buffer(n: int = 10, base_importance: float = 0.5) -> list[MemoryEntry]:
    """Build a deterministic test buffer of N MemoryEntry instances with
    varied importance, access_count, and prediction_error."""
    entries: list[MemoryEntry] = []
    for i in range(n):
        e = MemoryEntry(
            content=f"entry-{i:02d}",
            memory_type=MemoryType.EPISODIC,
            importance=min(1.0, base_importance + (i % 5) * 0.1),
            prediction_error=(i - n / 2) * 0.01,  # varied PPE
        )
        # Vary access_count — entries 0-3 accessed more (less novel).
        for _ in range(i % 4):
            e.record_access(MemoryOperation := __import__("nuros.memory", fromlist=["MemoryOperation"]).MemoryOperation.RETRIEVE)
        entries.append(e)
    return entries


# ============================================================================
# ReplayPolicy ABC + registry
# ============================================================================


class TestReplayPolicyABC(unittest.TestCase):
    def test_abc_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ReplayPolicy()  # type: ignore[abstract]

    def test_all_5_policies_registered(self):
        self.assertEqual(
            set(POLICIES.keys()),
            {
                "recent", "importance_weighted", "novelty_weighted",
                "prediction_error_weighted", "random",
            },
        )

    def test_make_policy_returns_correct_class(self):
        self.assertIsInstance(make_policy("recent"), RecentReplayPolicy)
        self.assertIsInstance(make_policy("importance_weighted"), ImportanceWeightedReplayPolicy)
        self.assertIsInstance(make_policy("novelty_weighted"), NoveltyWeightedReplayPolicy)
        self.assertIsInstance(make_policy("prediction_error_weighted"), PredictionErrorWeightedReplayPolicy)
        self.assertIsInstance(make_policy("random"), RandomReplayPolicy)

    def test_make_policy_rejects_unknown(self):
        with self.assertRaises(ValueError):
            make_policy("nonexistent")


# ============================================================================
# RecentReplayPolicy
# ============================================================================


class TestRecentReplayPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RecentReplayPolicy()
        self.buffer = make_test_buffer(n=10)

    def test_name(self):
        self.assertEqual(self.policy.name, "recent")

    def test_selects_most_recent_n(self):
        # Sort by timestamp desc; first n returned should be the n most recent.
        sorted_desc = sorted(self.buffer, key=lambda e: e.timestamp, reverse=True)
        sel = self.policy.select(self.buffer, n=5, seed=42)
        self.assertEqual(len(sel.entries), 5)
        for i, entry in enumerate(sel.entries):
            self.assertEqual(entry.memory_id, sorted_desc[i].memory_id)

    def test_selects_all_when_n_exceeds_buffer(self):
        sel = self.policy.select(self.buffer, n=100, seed=42)
        self.assertEqual(len(sel.entries), 10)

    def test_returns_empty_for_empty_buffer(self):
        sel = self.policy.select([], n=5, seed=42)
        self.assertEqual(len(sel.entries), 0)
        self.assertEqual(sel.n_available, 0)

    def test_no_weights_since_deterministic_sort(self):
        sel = self.policy.select(self.buffer, n=5, seed=42)
        self.assertIsNone(sel.selection_weights)


# ============================================================================
# ImportanceWeightedReplayPolicy
# ============================================================================


class TestImportanceWeightedReplayPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = ImportanceWeightedReplayPolicy()
        self.buffer = make_test_buffer(n=10)

    def test_name(self):
        self.assertEqual(self.policy.name, "importance_weighted")

    def test_returns_correct_count(self):
        sel = self.policy.select(self.buffer, n=5, seed=42)
        self.assertEqual(len(sel.entries), 5)
        self.assertEqual(sel.n_requested, 5)
        self.assertEqual(sel.n_available, 10)
        self.assertEqual(sel.n_selected, 5)

    def test_weights_proportional_to_importance_squared(self):
        sel = self.policy.select(self.buffer, n=5, seed=42)
        # Weights should be normalized (sum to 1).
        self.assertAlmostEqual(sum(sel.selection_weights), 1.0, places=6)
        # Higher-importance entries should have higher weights.
        sorted_pairs = sorted(
            zip(self.buffer, sel.selection_weights),
            key=lambda p: p[0].importance,
        )
        # Lowest-importance should have lowest weight; highest should have highest.
        self.assertLessEqual(
            sorted_pairs[0][1],
            sorted_pairs[-1][1],
        )

    def test_deterministic_with_seed(self):
        sel1 = self.policy.select(self.buffer, n=5, seed=42)
        sel2 = self.policy.select(self.buffer, n=5, seed=42)
        self.assertEqual(
            [e.memory_id for e in sel1.entries],
            [e.memory_id for e in sel2.entries],
        )

    def test_different_seeds_produce_different_selections(self):
        # Probabilistic — should differ at least sometimes.
        sel1 = self.policy.select(self.buffer, n=5, seed=1)
        sel2 = self.policy.select(self.buffer, n=5, seed=2)
        # Not a strict assertion (random can coincide), but with 5/10 picks
        # and varied importances, they should differ.
        ids1 = {e.memory_id for e in sel1.entries}
        ids2 = {e.memory_id for e in sel2.entries}
        # At least one should differ — sanity check.
        # NOTE: extremely unlikely to coincide; if it ever does, increase n.
        self.assertNotEqual(ids1, ids2)

    def test_handles_zero_importances_uniformly(self):
        zero_buffer = [
            MemoryEntry(content=f"zero-{i}", importance=0.0)
            for i in range(5)
        ]
        sel = self.policy.select(zero_buffer, n=3, seed=42)
        self.assertEqual(len(sel.entries), 3)
        # All weights should be equal (uniform fallback).
        w = sel.selection_weights
        self.assertAlmostEqual(w[0], w[1])
        self.assertAlmostEqual(w[1], w[2])

    def test_empty_buffer(self):
        sel = self.policy.select([], n=5, seed=42)
        self.assertEqual(len(sel.entries), 0)


# ============================================================================
# NoveltyWeightedReplayPolicy
# ============================================================================


class TestNoveltyWeightedReplayPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = NoveltyWeightedReplayPolicy()
        self.buffer = make_test_buffer(n=10)

    def test_name(self):
        self.assertEqual(self.policy.name, "novelty_weighted")

    def test_weights_proportional_to_inverse_access_count(self):
        sel = self.policy.select(self.buffer, n=5, seed=42)
        # Find the entry with the most accesses — should have lowest weight.
        sorted_pairs = sorted(
            zip(self.buffer, sel.selection_weights),
            key=lambda p: p[0].access_count,
        )
        self.assertLessEqual(
            sorted_pairs[-1][1],  # highest access_count -> lowest weight
            sorted_pairs[0][1],   # lowest access_count -> highest weight
        )

    def test_deterministic_with_seed(self):
        sel1 = self.policy.select(self.buffer, n=5, seed=42)
        sel2 = self.policy.select(self.buffer, n=5, seed=42)
        self.assertEqual(
            [e.memory_id for e in sel1.entries],
            [e.memory_id for e in sel2.entries],
        )

    def test_handles_all_zero_access_counts(self):
        # All entries never accessed — novelty weights uniform.
        fresh_buffer = [MemoryEntry(content=f"f-{i}") for i in range(5)]
        sel = self.policy.select(fresh_buffer, n=3, seed=42)
        # All weights should be equal (1 / (1+0) = 1 for all).
        w = sel.selection_weights
        self.assertAlmostEqual(w[0], w[1])
        self.assertAlmostEqual(w[1], w[2])


# ============================================================================
# PredictionErrorWeightedReplayPolicy
# ============================================================================


class TestPredictionErrorWeightedReplayPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = PredictionErrorWeightedReplayPolicy()
        self.buffer = make_test_buffer(n=10)

    def test_name(self):
        self.assertEqual(self.policy.name, "prediction_error_weighted")

    def test_weights_proportional_to_abs_prediction_error(self):
        sel = self.policy.select(self.buffer, n=5, seed=42)
        sorted_pairs = sorted(
            zip(self.buffer, sel.selection_weights),
            key=lambda p: abs(p[0].prediction_error),
        )
        self.assertLessEqual(
            sorted_pairs[0][1],
            sorted_pairs[-1][1],
        )

    def test_deterministic_with_seed(self):
        sel1 = self.policy.select(self.buffer, n=5, seed=42)
        sel2 = self.policy.select(self.buffer, n=5, seed=42)
        self.assertEqual(
            [e.memory_id for e in sel1.entries],
            [e.memory_id for e in sel2.entries],
        )

    def test_handles_all_zero_prediction_errors(self):
        # All entries have prediction_error=0 — fallback to uniform.
        zero_pe_buffer = [MemoryEntry(content=f"z-{i}", prediction_error=0.0) for i in range(5)]
        sel = self.policy.select(zero_pe_buffer, n=3, seed=42)
        self.assertEqual(len(sel.entries), 3)
        w = sel.selection_weights
        self.assertAlmostEqual(w[0], w[1])


# ============================================================================
# RandomReplayPolicy
# ============================================================================


class TestRandomReplayPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RandomReplayPolicy()
        self.buffer = make_test_buffer(n=10)

    def test_name(self):
        self.assertEqual(self.policy.name, "random")

    def test_uniform_weights(self):
        sel = self.policy.select(self.buffer, n=5, seed=42)
        w = sel.selection_weights
        self.assertAlmostEqual(w[0], 1.0 / 10)
        self.assertAlmostEqual(w[0], w[-1])

    def test_deterministic_with_seed(self):
        sel1 = self.policy.select(self.buffer, n=5, seed=42)
        sel2 = self.policy.select(self.buffer, n=5, seed=42)
        self.assertEqual(
            [e.memory_id for e in sel1.entries],
            [e.memory_id for e in sel2.entries],
        )

    def test_different_seeds_produce_different_selections(self):
        sel1 = self.policy.select(self.buffer, n=5, seed=1)
        sel2 = self.policy.select(self.buffer, n=5, seed=999)
        self.assertNotEqual(
            {e.memory_id for e in sel1.entries},
            {e.memory_id for e in sel2.entries},
        )

    def test_no_seed_still_works(self):
        # seed=None — non-deterministic but should not crash.
        sel = self.policy.select(self.buffer, n=5, seed=None)
        self.assertEqual(len(sel.entries), 5)


# ============================================================================
# HippoCoreMemoryConfig + HippoCoreMemory.replay(n=N) integration
# ============================================================================


class TestHippoCoreConfigWithReplayPolicy(unittest.TestCase):
    def test_default_config_is_recent_policy(self):
        cfg = HippoCoreMemoryConfig()
        self.assertEqual(cfg.replay_policy, "recent")
        self.assertIsNone(cfg.replay_seed)

    def test_config_accepts_all_5_policies(self):
        for name in POLICIES:
            cfg = HippoCoreMemoryConfig(replay_policy=name)
            self.assertEqual(cfg.replay_policy, name)

    def test_config_rejects_unknown_policy(self):
        with self.assertRaises(ValueError):
            HippoCoreMemoryConfig(replay_policy="nonexistent")

    def test_config_to_dict_includes_knobs(self):
        cfg = HippoCoreMemoryConfig(replay_policy="novelty_weighted", replay_seed=42)
        d = cfg.to_dict()
        self.assertEqual(d["knobs"]["replay_policy"], "novelty_weighted")
        self.assertEqual(d["knobs"]["replay_seed"], 42)


class TestHippoCoreReplayDelegatesToPolicy(unittest.TestCase):
    def setUp(self):
        # Build a buffer of 10 entries on a HippoCoreMemory.
        self.hcm = HippoCoreMemory(
            HippoCoreMemoryConfig(replay_policy="recent", replay_seed=42),
        )
        for i in range(10):
            self.hcm.encode_episode(
                content=f"ep-{i:02d}", action=f"a-{i}",
                importance=0.3 + (i % 5) * 0.15,  # 0.3-0.9
                prediction_error=(i - 5) * 0.02,  # varied
            )

    def test_replay_with_n_uses_policy(self):
        results = self.hcm.replay(n=5)
        self.assertEqual(len(results), 5)
        # Recent policy: most recent 5 by timestamp.
        all_entries = self.hcm.iter_all()
        sorted_desc = sorted(all_entries, key=lambda e: e.timestamp, reverse=True)
        for i, entry in enumerate(results):
            self.assertEqual(entry.memory_id, sorted_desc[i].memory_id)

    def test_replay_without_n_falls_back_to_default(self):
        # No n specified — should return all entries sorted by timestamp asc.
        results = self.hcm.replay()
        self.assertEqual(len(results), 10)
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i].timestamp, results[i + 1].timestamp)

    def test_last_replay_selection_telemetry_set(self):
        self.hcm.replay(n=5)
        sel = self.hcm.last_replay_selection
        self.assertIsNotNone(sel)
        self.assertEqual(sel.policy_name, "recent")
        self.assertEqual(sel.n_requested, 5)
        self.assertEqual(sel.n_selected, 5)

    def test_set_replay_policy_swaps_at_runtime(self):
        # Default is recent.
        self.assertIsInstance(self.hcm.replay_policy, RecentReplayPolicy)
        # Swap to importance_weighted.
        self.hcm.set_replay_policy(ImportanceWeightedReplayPolicy())
        self.assertIsInstance(self.hcm.replay_policy, ImportanceWeightedReplayPolicy)
        # Telemetry reset.
        self.assertIsNone(self.hcm.last_replay_selection)
        # New replay uses the new policy.
        self.hcm.replay(n=5)
        self.assertEqual(self.hcm.last_replay_selection.policy_name, "importance_weighted")

    def test_replay_filters_by_memory_type(self):
        # Encode a semantic memory — should be excluded from episodic replay.
        self.hcm.encode("fact", memory_type=MemoryType.SEMANTIC, importance=0.9)
        results = self.hcm.replay(memory_type=MemoryType.EPISODIC, n=5)
        self.assertEqual(len(results), 5)
        for entry in results:
            self.assertEqual(entry.memory_type, MemoryType.EPISODIC)

    def test_replay_excludes_forgotten(self):
        first_entry = self.hcm.iter_all()[0]
        self.hcm.forget(first_entry.memory_id)
        results = self.hcm.replay(n=100)  # request all
        self.assertEqual(len(results), 9)  # one forgotten, excluded
        for entry in results:
            self.assertFalse(entry.forgotten)

    def test_replay_with_n_larger_than_buffer_returns_all(self):
        # Buffer has 10; request 100.
        results = self.hcm.replay(n=100)
        self.assertEqual(len(results), 10)


class TestHippoCorePolicyComparison(unittest.TestCase):
    """Sanity-check that the 5 policies produce DIFFERENT selections on
    the same input buffer — confirming they are not all degenerate.

    Master prompt §9: "Do not assume one policy is superior. Benchmark
    them." — this test does NOT compare for superiority, only for
    non-degeneracy. The actual quality comparison is in PHASE 9
    benchmarks/memory/04_replay.
    """

    def test_policies_produce_different_selections(self):
        buffer = make_test_buffer(n=20)
        # Use distinct seeds for each policy.
        selections: dict[str, set[str]] = {}
        for name in POLICIES:
            policy = make_policy(name)
            sel = policy.select(buffer, n=10, seed=42)
            selections[name] = {e.memory_id for e in sel.entries}
        # At least 2 distinct selections among the 5 policies.
        distinct = len(set(frozenset(s) for s in selections.values()))
        self.assertGreaterEqual(distinct, 2,
            "Policies should not all collapse to the same selection "
            "(would indicate a bug in the policy implementations).")


if __name__ == "__main__":
    unittest.main()
