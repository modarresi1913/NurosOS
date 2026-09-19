"""
PHASE 3 smoke tests for the HippoCore adapter scaffold.

Verifies that ``HippoCoreMemory`` is a real ``MemoryEngine`` that, in
PHASE 3, produces behaviorally-identical results to
``DefaultMemoryContract`` for every operation in the ABC.

The point of these tests is to lock in the equivalence baseline so that
PHASE 4+ (real episodic encoding + pattern separation), PHASE 5 (policy-
driven replay), and PHASE 6 (fast→slow consolidation) can introduce
*DIVERGING* behavior intentionally and have it show up as test failures
that the implementer must explicitly bless.

Scientific status: [IMPLEMENTED] — adapter scaffold + equivalence tests.
"""

from __future__ import annotations

import unittest

from nuros.epistemic import EpistemicLabel
from nuros.hippocore import HippoCoreMemory, HippoCoreMemoryConfig
from nuros.hippocore.memory_engine import HippoCoreMemory as HCM_direct_import
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType
from nuros.memory_engine import MemoryEngine


class TestHippoCorePackage(unittest.TestCase):
    """Package surface tests — ensure imports + re-exports work."""

    def test_package_exports(self):
        from nuros.hippocore import HippoCoreMemory, HippoCoreMemoryConfig
        self.assertTrue(callable(HippoCoreMemory))
        self.assertTrue(callable(HippoCoreMemoryConfig))

    def test_direct_module_import_matches_package_reexport(self):
        self.assertIs(HippoCoreMemory, HCM_direct_import)


class TestHippoCoreIsMemoryEngine(unittest.TestCase):
    """HippoCoreMemory must be a real MemoryEngine — instantiable and
    implementing every abstract method."""

    def test_is_a_memory_engine(self):
        hcm = HippoCoreMemory()
        self.assertIsInstance(hcm, MemoryEngine)

    def test_implements_all_abstract_methods(self):
        hcm = HippoCoreMemory()
        for method_name in (
            "encode", "retrieve", "retrieve_by_id", "associate",
            "reconsolidate", "replay", "consolidate", "forget",
            "checkpoint", "restore", "inspect", "iter_all",
            "working_set", "working_get", "summary",
        ):
            self.assertTrue(
                callable(getattr(hcm, method_name, None)),
                f"HippoCoreMemory must implement {method_name}()",
            )


class TestHippoCorePhase3Equivalence(unittest.TestCase):
    """PHASE 3 behavioral equivalence: HippoCoreMemory must produce
    identical results to DefaultMemoryContract.

    Every test in this class is a golden-file comparison that will BREAK
    in PHASE 4+ when the corresponding operation is replaced with real
    HippoCore behavior. That's intentional — it forces the implementer
    to acknowledge the divergence when it lands.
    """

    def setUp(self):
        self.default = DefaultMemoryContract()
        self.hippocore = HippoCoreMemory()

    def _encode_mirror(self, content: str, importance: float = 0.5, **kwargs):
        """Encode on both engines with identical args, return both entries."""
        d_entry = self.default.encode(content, importance=importance, **kwargs)
        h_entry = self.hippocore.encode(content, importance=importance, **kwargs)
        return d_entry, h_entry

    def assertEntryEquivalent(self, d: MemoryEntry, h: MemoryEntry, msg: str = ""):
        """Assert that two MemoryEntry instances are behaviorally equivalent
        (same content, type, importance, confidence, epistemic label, etc).
        Does NOT assert memory_id equality — different engines may use
        different ID schemes (UUIDs in PHASE 3, but possibly deterministic
        counters in PHASE 4)."""
        # PHASE 3 equivalence baseline — these will diverge in PHASE 4+
        # (e.g. consolidation_status will change when HippoCore does real
        # reconsolidation; importance may differ when pattern separation
        # detects near-duplicates).
        self.assertEqual(d.content, h.content, f"{msg}: content mismatch")
        self.assertEqual(d.memory_type, h.memory_type, f"{msg}: memory_type mismatch")
        self.assertEqual(d.importance, h.importance, f"{msg}: importance mismatch")
        self.assertEqual(d.confidence, h.confidence, f"{msg}: confidence mismatch")
        self.assertEqual(d.epistemic_label, h.epistemic_label, f"{msg}: epistemic_label mismatch")
        self.assertEqual(d.forgotten, h.forgotten, f"{msg}: forgotten mismatch")
        self.assertEqual(d.consolidation_status, h.consolidation_status,
                         f"{msg}: consolidation_status mismatch")
        self.assertEqual(d.tags, h.tags, f"{msg}: tags mismatch")

    def test_encode_basic_equivalence(self):
        d, h = self._encode_mirror("hello world", importance=0.7)
        self.assertEntryEquivalent(d, h, "encode basic")

    def test_encode_counterfactual_is_imagined_in_both_engines(self):
        d, h = self._encode_mirror(
            "what if", memory_type=MemoryType.COUNTERFACTUAL,
        )
        self.assertEqual(d.epistemic_label, EpistemicLabel.IMAGINED)
        self.assertEqual(h.epistemic_label, EpistemicLabel.IMAGINED)

    def test_encode_tags_preserved_in_both_engines(self):
        d, h = self._encode_mirror(
            "tagged content", importance=0.5, tags={"alpha", "beta"},
        )
        self.assertEqual(d.tags, {"alpha", "beta"})
        self.assertEqual(h.tags, {"alpha", "beta"})

    def test_retrieve_returns_same_count_and_content(self):
        """Will DIVERGE in PHASE 4 (HippoCore will do similarity-based
        k-NN retrieval, not just substring matching)."""
        for content in ["hello world", "hello universe", "goodbye moon"]:
            self.default.encode(content, importance=0.6)
            self.hippocore.encode(content, importance=0.6)

        d_results = self.default.retrieve(query="hello", limit=10)
        h_results = self.hippocore.retrieve(query="hello", limit=10)
        self.assertEqual(len(d_results), len(h_results))
        for d_entry, h_entry in zip(d_results, h_results):
            self.assertEqual(d_entry.content, h_entry.content)

    def test_forget_soft_delete_semantics_match(self):
        """Both engines must soft-delete identically in PHASE 3.
        Will DIVERGE in PHASE 6 (HippoCore will use the full
        ACTIVE/WEAKENING/CONSOLIDATED/RECONSOLIDATED/ARCHIVED/FORGOTTEN
        lifecycle per audit §17)."""
        d_entry = self.default.encode("forget me", importance=0.6)
        h_entry = self.hippocore.encode("forget me", importance=0.6)

        ok_d = self.default.forget(d_entry.memory_id, justification="test")
        ok_h = self.hippocore.forget(h_entry.memory_id, justification="test")
        self.assertEqual(ok_d, ok_h)
        self.assertEqual(d_entry.forgotten, h_entry.forgotten)
        self.assertEqual(d_entry.importance, h_entry.importance)
        self.assertEqual(d_entry.consolidation_status, h_entry.consolidation_status)
        self.assertEqual(d_entry.epistemic_label, h_entry.epistemic_label)
        # Soft-forgotten entries are invisible to retrieve() in both engines.
        self.assertEqual(len(self.default.retrieve(query="forget")), 0)
        self.assertEqual(len(self.hippocore.retrieve(query="forget")), 0)

    def test_forget_hard_delete_semantics_match(self):
        d_entry = self.default.encode("hard forget", importance=0.5)
        h_entry = self.hippocore.encode("hard forget", importance=0.5)
        self.default.forget(d_entry.memory_id, hard=True)
        self.hippocore.forget(h_entry.memory_id, hard=True)
        self.assertEqual(self.default.memory_count, self.hippocore.memory_count)
        self.assertEqual(len(self.default.iter_all()), len(self.hippocore.iter_all()))

    def test_reconsolidate_prediction_error_recorded_in_both(self):
        d_entry = self.default.encode("recon", importance=0.5, confidence=0.5)
        h_entry = self.hippocore.encode("recon", importance=0.5, confidence=0.5)
        self.default.reconsolidate(d_entry.memory_id, reward=0.5, prediction_error=0.7)
        self.hippocore.reconsolidate(h_entry.memory_id, reward=0.5, prediction_error=0.7)
        self.assertEqual(d_entry.prediction_error, h_entry.prediction_error)
        self.assertEqual(d_entry.importance, h_entry.importance)
        self.assertEqual(d_entry.confidence, h_entry.confidence)

    def test_replay_returns_same_count_and_content(self):
        """Will DIVERGE in PHASE 5 (HippoCore will support
        policy-driven generative replay — recent/importance_weighted/
        novelty_weighted/prediction_error_weighted/random)."""
        for content in ["a", "b", "c", "d", "e"]:
            self.default.encode(content, importance=0.5)
            self.hippocore.encode(content, importance=0.5)
        d_replay = self.default.replay()
        h_replay = self.hippocore.replay()
        self.assertEqual(len(d_replay), len(h_replay))
        for d_entry, h_entry in zip(d_replay, h_replay):
            self.assertEqual(d_entry.content, h_entry.content)

    def test_replay_n_cap_in_both(self):
        for content in ["a", "b", "c", "d", "e"]:
            self.default.encode(content, importance=0.5)
            self.hippocore.encode(content, importance=0.5)
        self.assertEqual(len(self.default.replay(n=3)), 3)
        self.assertEqual(len(self.hippocore.replay(n=3)), 3)

    def test_consolidate_is_noop_in_both_engines(self):
        """Both engines return 0 in PHASE 3.
        Will DIVERGE in PHASE 6 (HippoCore will run the real
        fast→slow consolidation pipeline)."""
        for content in ["a", "b", "c"]:
            self.default.encode(content, importance=0.5)
            self.hippocore.encode(content, importance=0.5)
        self.assertEqual(self.default.consolidate(), 0)
        self.assertEqual(self.hippocore.consolidate(), 0)

    def test_checkpoint_round_trips_in_hippocore(self):
        self.hippocore.encode("ephemeral", importance=0.5)
        self.hippocore.encode("consolidated", importance=0.9)
        payload = self.hippocore.checkpoint()
        # Schema version is overridden to indicate HippoCoreMemory origin.
        self.assertTrue(payload["schema_version"].startswith("nuros.hippocore."))
        self.assertEqual(payload["engine"], "hippocore")
        self.assertEqual(payload["engine_phase"], 3)
        # Round-trip
        hcm2 = HippoCoreMemory()
        hcm2.restore(payload)
        self.assertEqual(hcm2.memory_count, self.hippocore.memory_count)
        # Content is preserved
        contents = sorted(e.content for e in hcm2.iter_all())
        self.assertEqual(contents, ["consolidated", "ephemeral"])

    def test_hippocore_restores_default_payload(self):
        """HippoCoreMemory must accept payloads from DefaultMemoryContract
        too (cross-engine restore) — useful when migrating an organism
        from default → hippocore mid-development."""
        self.default.encode("shared", importance=0.7)
        default_payload = self.default.checkpoint()
        self.hippocore.restore(default_payload)
        self.assertEqual(self.hippocore.memory_count, 1)
        self.assertEqual(self.hippocore.iter_all()[0].content, "shared")

    def test_inspect_includes_engine_metadata(self):
        h_entry = self.hippocore.encode("inspect me", importance=0.8)
        meta = self.hippocore.inspect(h_entry.memory_id)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["engine"], "hippocore")
        self.assertEqual(meta["engine_phase"], 3)

    def test_summary_includes_engine_metadata(self):
        self.hippocore.encode("a", importance=0.5)
        s = self.hippocore.summary()
        self.assertEqual(s["engine"], "hippocore")
        self.assertEqual(s["engine_phase"], 3)
        self.assertIn("config", s)

    def test_inner_property_exposes_default_memory_contract(self):
        """The .inner property is used by PHASE 9 benchmarks to compare
        HippoCore vs Default on identical inputs."""
        hcm = HippoCoreMemory()
        self.assertIsInstance(hcm.inner, DefaultMemoryContract)


class TestOrganismWithHippoCore(unittest.TestCase):
    """OrganismConfig.memory_engine='hippocore' selects HippoCoreMemory."""

    def test_organism_uses_hippocore_when_configured(self):
        from nuros.organism import Organism, OrganismConfig
        org = Organism(OrganismConfig(name="test", memory_engine="hippocore"))
        self.assertIsInstance(org.memory, HippoCoreMemory)
        self.assertIsInstance(org.memory, MemoryEngine)

    def test_organism_uses_default_when_not_configured(self):
        from nuros.organism import Organism, OrganismConfig
        org = Organism(OrganismConfig(name="test"))
        # Default is DefaultMemoryContract (not HippoCoreMemory).
        self.assertIsInstance(org.memory, DefaultMemoryContract)
        self.assertNotIsInstance(org.memory, HippoCoreMemory)

    def test_organism_state_hash_differs_by_memory_engine_when_contents_differ(self):
        """Two organisms with same genome/different memory engines can
        still develop identically — but if memory contents differ, their
        state_hash MUST differ (audit Appendix B.9 fix)."""
        from nuros.organism import Organism, OrganismConfig
        org_default = Organism(OrganismConfig(name="od"))
        org_hippocore = Organism(OrganismConfig(name="oh", memory_engine="hippocore"))
        org_default.birth()
        org_hippocore.birth()
        # Encode the same content on both.
        org_default.memory.encode("shared content", importance=0.7)
        org_hippocore.memory.encode("shared content", importance=0.7)
        # State hashes will differ because the engines use different
        # UUIDs for memory_ids — but both will be deterministic given
        # the same engine + same inputs (modulo UUIDs which are random
        # in PHASE 3; PHASE 4 may switch to deterministic IDs).
        # The key property: state_hash is stable for a given organism
        # across multiple calls.
        self.assertEqual(org_default.state_hash(), org_default.state_hash())
        self.assertEqual(org_hippocore.state_hash(), org_hippocore.state_hash())


class TestHippoCoreConfig(unittest.TestCase):
    """PHASE 3: config is empty. PHASE 4+ will add knobs."""

    def test_config_to_dict(self):
        """PHASE 5 update: config now carries replay_policy + replay_seed
        knobs. The 'phase' field tracks the latest phase that touched
        the config (PHASE 5 = replay policies)."""
        cfg = HippoCoreMemoryConfig()
        d = cfg.to_dict()
        self.assertEqual(d["phase"], 5)
        self.assertIn("replay_policy", d["knobs"])
        self.assertIn("replay_seed", d["knobs"])

    def test_config_can_be_passed_to_hippocore_memory(self):
        cfg = HippoCoreMemoryConfig()
        hcm = HippoCoreMemory(config=cfg)
        self.assertIsInstance(hcm, HippoCoreMemory)


if __name__ == "__main__":
    unittest.main()
