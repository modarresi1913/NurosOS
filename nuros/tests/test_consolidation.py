"""
PHASE 6 tests — fast→slow consolidation pipeline.

Verifies:
  - ConsolidationStrategy ABC + 2 concrete strategies (TagJaccard,
    ContentPrefix).
  - HippoCoreMemoryConfig consolidation knobs (strategy, batch_size,
    similarity_threshold, max_episodes, max_memory_bytes).
  - HippoCoreMemory.consolidate() runs the real pipeline:
    * Selects only ACTIVE sources.
    * Clusters by similarity.
    * Derives SEMANTIC target memories from clusters of size >= 2.
    * Marks sources as CONSOLIDATED + lowers importance.
    * Associates sources ↔ target via 'consolidated_into' edges.
    * Returns the count of target memories created.
  - last_consolidation_result telemetry.
  - Determinism: same inputs + same params → same clusters.
  - Memory budget knobs (max_episodes, max_memory_bytes).

Master prompt §10 measures: retention, forgetting, retrieval accuracy,
adaptation, interference. Those measurements are in PHASE 9 benchmarks/
memory/05_consolidation.
"""

from __future__ import annotations

import unittest
from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.hippocore import HippoCoreMemory, HippoCoreMemoryConfig
from nuros.hippocore.consolidation import (
    ConsolidationResult,
    ConsolidationStrategy,
    ContentPrefixConsolidation,
    STRATEGIES,
    TagJaccardConsolidation,
    make_strategy,
)
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType


class TestConsolidationStrategyABC(unittest.TestCase):
    def test_abc_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ConsolidationStrategy()  # type: ignore[abstract]

    def test_both_strategies_registered(self):
        self.assertEqual(set(STRATEGIES.keys()), {"tag_jaccard", "content_prefix"})

    def test_make_strategy_returns_correct_class(self):
        self.assertIsInstance(make_strategy("tag_jaccard"), TagJaccardConsolidation)
        self.assertIsInstance(make_strategy("content_prefix"), ContentPrefixConsolidation)

    def test_make_strategy_rejects_unknown(self):
        with self.assertRaises(ValueError):
            make_strategy("nonexistent")


class TestTagJaccardStrategy(unittest.TestCase):
    def setUp(self):
        self.s = TagJaccardConsolidation()

    def test_name(self):
        self.assertEqual(self.s.name, "tag_jaccard")

    def test_similarity_zero_disjoint_tags(self):
        a = MemoryEntry(content="a", tags={"x"})
        b = MemoryEntry(content="b", tags={"y"})
        self.assertEqual(self.s.similarity(a, b), 0.0)

    def test_similarity_one_identical_tags(self):
        a = MemoryEntry(content="a", tags={"x", "y"})
        b = MemoryEntry(content="b", tags={"x", "y"})
        self.assertEqual(self.s.similarity(a, b), 1.0)

    def test_similarity_half_shared_tags(self):
        a = MemoryEntry(content="a", tags={"x", "y"})
        b = MemoryEntry(content="b", tags={"y", "z"})
        # Jaccard = 1/3 (only 'y' shared, union is {x,y,z}).
        self.assertAlmostEqual(self.s.similarity(a, b), 1.0 / 3.0)

    def test_similarity_empty_tags_returns_zero(self):
        a = MemoryEntry(content="a", tags=set())
        b = MemoryEntry(content="b", tags=set())
        self.assertEqual(self.s.similarity(a, b), 0.0)

    def test_cluster_groups_similar_entries(self):
        # 4 entries: 3 share tag 'food', 1 shares tag 'water'.
        e1 = MemoryEntry(content="apple", tags={"food", "fruit"})
        e2 = MemoryEntry(content="bread", tags={"food", "grain"})
        e3 = MemoryEntry(content="cheese", tags={"food", "dairy"})
        e4 = MemoryEntry(content="water", tags={"drink"})
        # Threshold 0.3 → e1-e2-e3 share 'food' → Jaccard ~0.33-0.5.
        clusters = self.s.cluster([e1, e2, e3, e4], similarity_threshold=0.3)
        # Should be 2 clusters: {e1,e2,e3} and {e4}.
        self.assertEqual(len(clusters), 2)
        # The big cluster has 3 members.
        sizes = sorted(len(c) for c in clusters)
        self.assertEqual(sizes, [1, 3])

    def test_cluster_returns_singletons_when_no_similarity(self):
        e1 = MemoryEntry(content="a", tags={"x"})
        e2 = MemoryEntry(content="b", tags={"y"})
        clusters = self.s.cluster([e1, e2], similarity_threshold=0.5)
        self.assertEqual(len(clusters), 2)
        self.assertEqual(len(clusters[0]), 1)
        self.assertEqual(len(clusters[1]), 1)

    def test_cluster_deterministic(self):
        # Order of inputs affects cluster assignment, but the SAME inputs
        # always produce the same clusters.
        e1 = MemoryEntry(content="a", tags={"x"})
        e2 = MemoryEntry(content="b", tags={"x", "y"})
        e3 = MemoryEntry(content="c", tags={"x", "y", "z"})
        clusters1 = self.s.cluster([e1, e2, e3], 0.3)
        clusters2 = self.s.cluster([e1, e2, e3], 0.3)
        self.assertEqual(len(clusters1), len(clusters2))


class TestContentPrefixStrategy(unittest.TestCase):
    def setUp(self):
        self.s = ContentPrefixConsolidation(min_prefix_chars=5)

    def test_name(self):
        self.assertEqual(self.s.name, "content_prefix")

    def test_similarity_zero_for_disjoint_content(self):
        a = MemoryEntry(content="hello world")
        b = MemoryEntry(content="goodbye moon")
        self.assertEqual(self.s.similarity(a, b), 0.0)

    def test_similarity_positive_for_shared_prefix(self):
        a = MemoryEntry(content="resource at (3,4)")
        b = MemoryEntry(content="resource at (3,5)")
        # Common prefix is "resource at (3,"  — 15 chars >= 5.
        self.assertGreater(self.s.similarity(a, b), 0.0)

    def test_cluster_groups_shared_prefix(self):
        e1 = MemoryEntry(content="resource at (3,4)")
        e2 = MemoryEntry(content="resource at (3,5)")
        e3 = MemoryEntry(content="resource at (4,1)")
        e4 = MemoryEntry(content="hazard at (5,5)")
        clusters = self.s.cluster([e1, e2, e3, e4], similarity_threshold=0.4)
        # 'resource at' is a common prefix for e1-e3.
        # 'hazard at' differs from 'resource' immediately → separate cluster.
        self.assertEqual(len(clusters), 2)
        sizes = sorted(len(c) for c in clusters)
        self.assertEqual(sizes, [1, 3])


class TestHippoCoreConfigConsolidationKnobs(unittest.TestCase):
    def test_default_config_has_tag_jaccard_strategy(self):
        cfg = HippoCoreMemoryConfig()
        self.assertEqual(cfg.consolidation_strategy, "tag_jaccard")
        self.assertEqual(cfg.consolidation_batch_size, 50)
        self.assertAlmostEqual(cfg.consolidation_similarity_threshold, 0.5)

    def test_config_accepts_content_prefix(self):
        cfg = HippoCoreMemoryConfig(consolidation_strategy="content_prefix")
        self.assertEqual(cfg.consolidation_strategy, "content_prefix")

    def test_config_rejects_unknown_strategy(self):
        with self.assertRaises(ValueError):
            HippoCoreMemoryConfig(consolidation_strategy="nonexistent")

    def test_config_max_episodes_and_bytes(self):
        cfg = HippoCoreMemoryConfig(max_episodes=100, max_memory_bytes=10_000_000)
        self.assertEqual(cfg.max_episodes, 100)
        self.assertEqual(cfg.max_memory_bytes, 10_000_000)


class TestHippoCoreConsolidatePipeline(unittest.TestCase):
    """End-to-end tests for HippoCoreMemory.consolidate()."""

    def setUp(self):
        # Use tag_jaccard at threshold 0.3 — easy to satisfy.
        self.hcm = HippoCoreMemory(
            HippoCoreMemoryConfig(
                consolidation_strategy="tag_jaccard",
                consolidation_similarity_threshold=0.3,
                consolidation_batch_size=100,
            ),
        )
        # Encode 4 episodes with shared tags (food) — should cluster.
        # Plus 1 unrelated episode (water).
        self.e1 = self.hcm.encode_episode(
            content="apple", action="eat", tags={"food", "fruit"},
        )
        self.e2 = self.hcm.encode_episode(
            content="bread", action="eat", tags={"food", "grain"},
        )
        self.e3 = self.hcm.encode_episode(
            content="cheese", action="eat", tags={"food", "dairy"},
        )
        self.e4 = self.hcm.encode_episode(
            content="water", action="drink", tags={"drink"},
        )

    def test_consolidate_creates_one_target_per_cluster(self):
        n = self.hcm.consolidate()
        # e1+e2+e3 form one cluster (shared 'food' tag). e4 is singleton.
        self.assertEqual(n, 1)

    def test_consolidate_marks_sources_as_consolidated(self):
        self.hcm.consolidate()
        # e1, e2, e3 should now be CONSOLIDATED.
        self.assertEqual(self.e1.consolidation_status, "CONSOLIDATED")
        self.assertEqual(self.e2.consolidation_status, "CONSOLIDATED")
        self.assertEqual(self.e3.consolidation_status, "CONSOLIDATED")
        # e4 was a singleton — stays ACTIVE.
        self.assertEqual(self.e4.consolidation_status, "ACTIVE")

    def test_consolidate_lowers_source_importance_by_half(self):
        # Set known importances.
        for e, imp in [(self.e1, 0.8), (self.e2, 0.6), (self.e3, 0.4)]:
            e.importance = imp
        self.hcm.consolidate()
        # Each should be halved.
        self.assertAlmostEqual(self.e1.importance, 0.4)
        self.assertAlmostEqual(self.e2.importance, 0.3)
        self.assertAlmostEqual(self.e3.importance, 0.2)
        # e4 stays at its original importance.
        self.assertNotEqual(self.e4.importance, 0.0)

    def test_consolidate_creates_target_with_semantic_type(self):
        self.hcm.consolidate()
        # Find the target — it's the SEMANTIC memory not in {e1,e2,e3,e4}.
        all_entries = self.hcm.iter_all()
        targets = [e for e in all_entries if e.memory_type == MemoryType.SEMANTIC]
        self.assertEqual(len(targets), 1)
        target = targets[0]
        self.assertEqual(target.consolidation_status, "CONSOLIDATED")
        self.assertEqual(target.epistemic_label, EpistemicLabel.INFERRED)
        # Target content is the derived summary.
        self.assertIsInstance(target.content, dict)
        self.assertIn("summary", target.content)
        self.assertEqual(target.content["summary"], "consolidated from 3 memories")
        # Target tags = union of source tags.
        self.assertEqual(target.tags, {"food", "fruit", "grain", "dairy"})

    def test_consolidate_associates_sources_to_target(self):
        self.hcm.consolidate()
        # Each source should have a 'consolidated_into' relationship to the target.
        all_entries = self.hcm.iter_all()
        target = next(e for e in all_entries
                      if e.memory_type == MemoryType.SEMANTIC)
        for src in [self.e1, self.e2, self.e3]:
            # Find the relationship pointing to target.
            rels_to_target = [r for r in src.relationships
                              if r.target_id == target.memory_id]
            self.assertEqual(len(rels_to_target), 1)
            self.assertEqual(rels_to_target[0].relation_type, "consolidated_into")
            self.assertTrue(rels_to_target[0].bidirectional)
        # Target should have back-edges to each source.
        target_rels_to_sources = [r for r in target.relationships
                                   if r.relation_type == "consolidated_into"]
        self.assertEqual(len(target_rels_to_sources), 3)

    def test_consolidate_skips_already_consolidated_sources(self):
        # First pass — consolidates e1+e2+e3.
        n1 = self.hcm.consolidate()
        self.assertEqual(n1, 1)
        # Second pass — e4 is the only ACTIVE episodic source (singleton) → 0.
        n2 = self.hcm.consolidate()
        self.assertEqual(n2, 0)

    def test_consolidate_returns_zero_for_empty_buffer(self):
        empty_hcm = HippoCoreMemory(HippoCoreMemoryConfig(
            consolidation_strategy="tag_jaccard",
            consolidation_similarity_threshold=0.3,
        ))
        self.assertEqual(empty_hcm.consolidate(), 0)

    def test_consolidate_respects_batch_size(self):
        # Batch size 2 → only 2 sources considered per pass.
        # With 3 sources in the food cluster, batch_size=2 → 2 sources →
        # 1 cluster of size 2 (both food) → 1 target. e3 stays ACTIVE.
        hcm = HippoCoreMemory(HippoCoreMemoryConfig(
            consolidation_strategy="tag_jaccard",
            consolidation_similarity_threshold=0.3,
            consolidation_batch_size=2,
        ))
        hcm.encode_episode(content="a", action="x", tags={"food"})
        hcm.encode_episode(content="b", action="x", tags={"food"})
        hcm.encode_episode(content="c", action="x", tags={"food"})
        n = hcm.consolidate()
        self.assertEqual(n, 1)  # 1 target created from the 2-source cluster.

    def test_consolidate_telemetry_in_last_consolidation_result(self):
        self.hcm.consolidate()
        result = self.hcm.last_consolidation_result
        self.assertIsNotNone(result)
        self.assertEqual(result.strategy_name, "tag_jaccard")
        self.assertEqual(result.n_target_created, 1)
        self.assertEqual(len(result.source_ids), 3)  # e1, e2, e3
        self.assertEqual(len(result.target_ids), 1)
        self.assertGreaterEqual(result.elapsed_seconds, 0.0)

    def test_set_consolidation_strategy_at_runtime(self):
        # Default is tag_jaccard.
        self.assertIsInstance(self.hcm.consolidation_strategy, TagJaccardConsolidation)
        # Swap to content_prefix.
        self.hcm.set_consolidation_strategy(ContentPrefixConsolidation())
        self.assertIsInstance(self.hcm.consolidation_strategy, ContentPrefixConsolidation)
        # Telemetry reset.
        self.assertIsNone(self.hcm.last_consolidation_result)


class TestHippoCoreConsolidateDeterminism(unittest.TestCase):
    """Master prompt §36: replay fidelity + consolidation must be
    deterministic given same inputs."""

    def _build_hcm_with_same_buffer(self, seed: int = 42):
        hcm = HippoCoreMemory(HippoCoreMemoryConfig(
            consolidation_strategy="tag_jaccard",
            consolidation_similarity_threshold=0.3,
            replay_seed=seed,
        ))
        # Use deterministic content + tags.
        for i in range(5):
            hcm.encode_episode(
                content=f"resource-{i}", action="consume",
                tags={"food"} if i < 3 else {"drink"},
            )
        return hcm

    def test_consolidate_is_deterministic_across_runs(self):
        hcm1 = self._build_hcm_with_same_buffer()
        n1 = hcm1.consolidate()

        hcm2 = self._build_hcm_with_same_buffer()
        n2 = hcm2.consolidate()

        self.assertEqual(n1, n2)
        # The target contents should match.
        targets1 = [e for e in hcm1.iter_all()
                    if e.memory_type == MemoryType.SEMANTIC]
        targets2 = [e for e in hcm2.iter_all()
                    if e.memory_type == MemoryType.SEMANTIC]
        self.assertEqual(len(targets1), len(targets2))
        for t1, t2 in zip(targets1, targets2):
            self.assertEqual(t1.content, t2.content)
            self.assertEqual(t1.tags, t2.tags)


class TestConsolidateWithContentPrefixStrategy(unittest.TestCase):
    """Switch strategy to content_prefix — verify same pipeline works."""

    def test_content_prefix_consolidation(self):
        hcm = HippoCoreMemory(HippoCoreMemoryConfig(
            consolidation_strategy="content_prefix",
            consolidation_similarity_threshold=0.4,
        ))
        # 3 memories with shared prefix "resource at (".
        hcm.encode_episode(content="resource at (1,1)", action="consume")
        hcm.encode_episode(content="resource at (2,2)", action="consume")
        hcm.encode_episode(content="resource at (3,3)", action="consume")
        # 1 unrelated.
        hcm.encode_episode(content="hazard nearby", action="avoid")

        n = hcm.consolidate()
        self.assertEqual(n, 1)  # 1 cluster of size 3 → 1 target.


if __name__ == "__main__":
    unittest.main()
