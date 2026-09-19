"""
PHASE 2 tests for the MemoryEngine ABC and DefaultMemoryContract.

These tests verify:
  - The MemoryEngine ABC contract (every abstract method is implemented).
  - The bug fixes from audit Appendix B:
      B.1: forget() soft-delete default
      B.2: decay_experiment.py uses iter_all() instead of _store
      B.3: reflect() spec drift reconciled (delegates to inspect)
      B.4: replay() signature extended (n + generative)
      B.7: MemoryEntry.access_count incremented on access
      B.9: state_hash covers memory contents (separate test in test_core.py)
  - The new operations: encode, consolidate, checkpoint, restore, inspect,
    iter_all, reconsolidate with prediction_error.
  - Backward-compat: MemoryContract deprecated alias still works + warns.

These tests do NOT require the Rust PyO3 extension (nuros._dev) — they
exercise only the Python cognitive layer.
"""

from __future__ import annotations

import json
import unittest
import warnings
from typing import Any

from nuros.epistemic import EpistemicLabel, EpistemicKernel
from nuros.memory import (
    DefaultMemoryContract,
    MemoryContract,
    MemoryEntry,
    MemoryOperation,
    MemoryType,
)
from nuros.memory_engine import MemoryEngine


class TestMemoryEngineABC(unittest.TestCase):
    """The MemoryEngine ABC must be un instantiable, and all its
    abstractmethods must be implemented by DefaultMemoryContract."""

    def test_abc_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            MemoryEngine()  # type: ignore[abstract]

    def test_default_memory_contract_is_a_memory_engine(self):
        dmc = DefaultMemoryContract()
        self.assertIsInstance(dmc, MemoryEngine)

    def test_all_abstract_methods_are_implemented(self):
        """Every abstractmethod declared on MemoryEngine must be overridden
        in DefaultMemoryContract — otherwise Python raises TypeError on
        instantiation."""
        dmc = DefaultMemoryContract()
        # If we got here, all abstract methods are implemented.
        # Spot-check the new surface:
        for method_name in (
            "encode", "retrieve", "retrieve_by_id", "associate",
            "reconsolidate", "replay", "consolidate", "forget",
            "checkpoint", "restore", "inspect", "iter_all",
            "working_set", "working_get", "summary",
        ):
            self.assertTrue(
                callable(getattr(dmc, method_name, None)),
                f"DefaultMemoryContract must implement {method_name}()",
            )

        # Properties
        for prop_name in ("memory_count", "operation_log"):
            self.assertTrue(
                hasattr(type(dmc), prop_name),
                f"DefaultMemoryContract must expose property {prop_name}",
            )


class TestMemoryContractDeprecatedAlias(unittest.TestCase):
    """audit §11.3: MemoryContract name kept as a deprecated alias for
    DefaultMemoryContract for one version."""

    def test_alias_warns_on_construction(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            mc = MemoryContract()
            self.assertEqual(len(ws), 1)
            self.assertTrue(issubclass(ws[0].category, DeprecationWarning))
            self.assertIn("DefaultMemoryContract", str(ws[0].message))

    def test_alias_is_subclass_of_default(self):
        self.assertTrue(issubclass(MemoryContract, DefaultMemoryContract))

    def test_alias_produces_working_memory_engine(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mc = MemoryContract()
            self.assertIsInstance(mc, MemoryEngine)
            entry = mc.encode("hello", importance=0.7)
            self.assertIsInstance(entry, MemoryEntry)
            self.assertEqual(mc.memory_count, 1)


class TestEncodeRetrieve(unittest.TestCase):
    """encode/retrieve/retrieve_by_id — the most-used operations."""

    def setUp(self):
        self.memory = DefaultMemoryContract()

    def test_encode_creates_memory_entry(self):
        entry = self.memory.encode(
            content="the cat sat on the mat",
            importance=0.8,
            tags={"animal", "domestic"},
        )
        self.assertIsInstance(entry, MemoryEntry)
        self.assertEqual(entry.memory_type, MemoryType.EPISODIC)  # default
        self.assertEqual(entry.epistemic_label, EpistemicLabel.REMEMBERED)
        self.assertEqual(entry.importance, 0.8)
        self.assertEqual(entry.tags, {"animal", "domestic"})
        self.assertFalse(entry.forgotten)
        self.assertEqual(entry.consolidation_status, "ACTIVE")

    def test_encode_counterfactual_is_imagined(self):
        entry = self.memory.encode(
            content="what if I had taken the other path",
            memory_type=MemoryType.COUNTERFACTUAL,
        )
        self.assertEqual(entry.epistemic_label, EpistemicLabel.IMAGINED)

    def test_encode_none_memory_type_resolves_to_episodic(self):
        entry = self.memory.encode(content="x", memory_type=None)
        self.assertEqual(entry.memory_type, MemoryType.EPISODIC)

    def test_encode_explicit_epistemic_label_respected(self):
        entry = self.memory.encode(
            content="inferred knowledge",
            memory_type=MemoryType.SEMANTIC,
            epistemic_label=EpistemicLabel.INFERRED,
        )
        self.assertEqual(entry.epistemic_label, EpistemicLabel.INFERRED)

    def test_remember_is_alias_for_encode(self):
        """Historical remember() must still work — audit §11.3 step 1-2."""
        entry = self.memory.remember("legacy call", importance=0.5)
        self.assertIsInstance(entry, MemoryEntry)
        self.assertEqual(self.memory.memory_count, 1)

    def test_retrieve_substring_filter(self):
        self.memory.encode("hello world", importance=0.9)
        self.memory.encode("goodbye world", importance=0.7)
        self.memory.encode("unrelated content", importance=0.5)
        results = self.memory.retrieve(query="world", limit=10)
        self.assertEqual(len(results), 2)
        # Sorted by current_strength descending — higher importance first.
        self.assertGreaterEqual(
            results[0].importance, results[1].importance,
        )

    def test_retrieve_by_id(self):
        entry = self.memory.encode("x", importance=0.5)
        retrieved = self.memory.retrieve_by_id(entry.memory_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.memory_id, entry.memory_id)

    def test_retrieve_by_id_unknown_returns_none(self):
        self.assertIsNone(self.memory.retrieve_by_id("does-not-exist"))

    def test_access_count_incremented_on_retrieve(self):
        """audit Appendix B.7 fix: access_count must be incremented on
        every retrieve/retrieve_by_id/inspect access."""
        entry = self.memory.encode("hot path", importance=0.9)
        # one access from encode (REMEMBER op)
        initial_count = entry.access_count
        self.memory.retrieve(query="hot path")
        self.assertEqual(entry.access_count, initial_count + 1)
        self.memory.retrieve_by_id(entry.memory_id)
        self.assertEqual(entry.access_count, initial_count + 2)
        self.memory.inspect(entry.memory_id)
        self.assertEqual(entry.access_count, initial_count + 3)


class TestForget(unittest.TestCase):
    """forget() — soft-delete default + hard-delete preserved."""

    def setUp(self):
        self.memory = DefaultMemoryContract()
        self.entry = self.memory.encode("forgettable", importance=0.6)

    def test_default_is_soft_delete(self):
        ok = self.memory.forget(self.entry.memory_id, justification="test")
        self.assertTrue(ok)
        # Entry stays in store, marked forgotten.
        self.assertEqual(self.memory.memory_count, 1)
        self.assertTrue(self.entry.forgotten)
        self.assertEqual(self.entry.importance, 0.0)
        self.assertEqual(self.entry.consolidation_status, "FORGOTTEN")

    def test_soft_delete_downgrades_remembered_to_inferred(self):
        """audit §11.1: soft-forget downgrades REMEMBERED → INFERRED
        (no longer first-hand). Other labels (IMAGINED etc.) preserved."""
        self.assertEqual(self.entry.epistemic_label, EpistemicLabel.REMEMBERED)
        self.memory.forget(self.entry.memory_id)
        self.assertEqual(self.entry.epistemic_label, EpistemicLabel.INFERRED)

    def test_soft_delete_preserves_counterfactual_label(self):
        cf = self.memory.encode("what if", memory_type=MemoryType.COUNTERFACTUAL)
        self.assertEqual(cf.epistemic_label, EpistemicLabel.IMAGINED)
        self.memory.forget(cf.memory_id)
        # IMAGINED is preserved (counterfactual stays counterfactual).
        self.assertEqual(cf.epistemic_label, EpistemicLabel.IMAGINED)
        self.assertTrue(cf.forgotten)

    def test_soft_forgotten_invisible_to_retrieve(self):
        self.memory.forget(self.entry.memory_id)
        self.assertEqual(
            len(self.memory.retrieve(query="forgettable")), 0,
        )
        self.assertEqual(
            len(self.memory.retrieve(query="forgettable", min_importance=0.0)), 0,
        )

    def test_soft_forgotten_visible_via_iter_all(self):
        self.memory.forget(self.entry.memory_id)
        all_entries = self.memory.iter_all()
        self.assertEqual(len(all_entries), 1)
        self.assertTrue(all_entries[0].forgotten)

    def test_hard_delete_removes_from_store(self):
        ok = self.memory.forget(self.entry.memory_id, hard=True, justification="hard")
        self.assertTrue(ok)
        self.assertEqual(self.memory.memory_count, 0)
        self.assertEqual(len(self.memory.iter_all()), 0)

    def test_forget_unknown_returns_false(self):
        self.assertFalse(self.memory.forget("nonexistent-id"))

    def test_forget_logs_soft_vs_hard(self):
        self.memory.forget(self.entry.memory_id, soft_log_marker := "soft reason")
        soft_ops = [op for op in self.memory.operation_log if op[0] == MemoryOperation.FORGET]
        self.assertGreaterEqual(len(soft_ops), 1)
        self.assertIn("SOFT", soft_ops[-1][1])

        e2 = self.memory.encode("another", importance=0.5)
        self.memory.forget(e2.memory_id, hard=True, justification="hard reason")
        hard_ops = [op for op in self.memory.operation_log if op[0] == MemoryOperation.FORGET]
        self.assertIn("HARD", hard_ops[-1][1])


class TestReconsolidation(unittest.TestCase):
    """reconsolidate() — extended to accept optional prediction_error."""

    def setUp(self):
        self.memory = DefaultMemoryContract()
        # Use non-default confidence (0.5) so positive reward has room to grow
        # without hitting the 1.0 ceiling.
        self.entry = self.memory.encode("recon test", importance=0.5, confidence=0.5)

    def test_positive_reward_strengthens(self):
        before_importance = self.entry.importance
        before_confidence = self.entry.confidence
        before_decay = self.entry.decay_rate
        self.memory.reconsolidate(self.entry.memory_id, reward=1.0)
        self.assertGreater(self.entry.importance, before_importance)
        self.assertGreater(self.entry.confidence, before_confidence)
        self.assertLess(self.entry.decay_rate, before_decay)
        self.assertEqual(self.entry.consolidation_status, "RECONSOLIDATED")

    def test_negative_reward_weakens(self):
        before_confidence = self.entry.confidence
        before_decay = self.entry.decay_rate
        self.memory.reconsolidate(self.entry.memory_id, reward=-1.0)
        self.assertLess(self.entry.confidence, before_confidence)
        self.assertGreater(self.entry.decay_rate, before_decay)
        self.assertEqual(self.entry.consolidation_status, "WEAKENING")

    def test_prediction_error_recorded_on_entry(self):
        """audit §11.1 NEW field usage: reconsolidate accepts an optional
        prediction_error which is recorded on MemoryEntry.prediction_error."""
        self.assertEqual(self.entry.prediction_error, 0.0)  # default
        self.memory.reconsolidate(
            self.entry.memory_id, reward=0.5, prediction_error=0.8,
        )
        self.assertEqual(self.entry.prediction_error, 0.8)

    def test_prediction_error_modulates_reward_magnitude(self):
        """High prediction error amplifies the reconsolidation update —
        the surprise signal scales the effective reward."""
        e_low_pe = self.memory.encode("low surprise", importance=0.5, confidence=0.5)
        e_high_pe = self.memory.encode("high surprise", importance=0.5, confidence=0.5)
        self.memory.reconsolidate(e_low_pe.memory_id, reward=1.0, prediction_error=0.1)
        self.memory.reconsolidate(e_high_pe.memory_id, reward=1.0, prediction_error=0.9)
        self.assertGreater(e_high_pe.importance, e_low_pe.importance)

    def test_reconsolidate_unknown_returns_none(self):
        self.assertIsNone(self.memory.reconsolidate("nonexistent", reward=1.0))


class TestReplayExtended(unittest.TestCase):
    """replay() — extended with `n` cap and `generative` flag.

    audit Appendix B.4: spec drift on replay() reconciled.
    """

    def setUp(self):
        self.memory = DefaultMemoryContract()
        for i in range(5):
            self.memory.encode(f"entry-{i:02d}", importance=0.5 + i * 0.05)

    def test_replay_returns_all_by_default(self):
        results = self.memory.replay()
        self.assertEqual(len(results), 5)
        # Sorted by timestamp ascending.
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i].timestamp, results[i + 1].timestamp)

    def test_replay_n_cap(self):
        results = self.memory.replay(n=3)
        self.assertEqual(len(results), 3)

    def test_replay_filters_by_type(self):
        self.memory.encode("a fact", memory_type=MemoryType.SEMANTIC)
        episodic = self.memory.replay(memory_type=MemoryType.EPISODIC)
        semantic = self.memory.replay(memory_type=MemoryType.SEMANTIC)
        self.assertEqual(len(episodic), 5)
        self.assertEqual(len(semantic), 1)

    def test_replay_excludes_forgotten(self):
        first_entry = self.memory.iter_all()[0]
        self.memory.forget(first_entry.memory_id)
        results = self.memory.replay()
        self.assertEqual(len(results), 4)

    def test_replay_generative_is_noop_in_default(self):
        """In the Default impl, generative=True returns the same raw stored
        memories as generative=False. HippoCore (PHASE 3+) implements true
        generative replay."""
        non_gen = self.memory.replay()
        gen = self.memory.replay(generative=True)
        self.assertEqual(len(non_gen), len(gen))


class TestCheckpointRestore(unittest.TestCase):
    """checkpoint()/restore() — closes audit §7 / §14 gap."""

    def setUp(self):
        self.memory = DefaultMemoryContract()
        # Diverse memory store
        self.memory.encode("episodic 1", importance=0.8, tags={"t1"})
        self.memory.encode("episodic 2", importance=0.5, tags={"t2"})
        self.memory.encode("semantic fact", memory_type=MemoryType.SEMANTIC, importance=0.9)
        self.memory.encode("counterfactual", memory_type=MemoryType.COUNTERFACTUAL)
        # Soft-forget one entry
        all_entries = self.memory.iter_all()
        self.memory.forget(all_entries[0].memory_id, justification="test")

    def test_checkpoint_returns_dict_with_schema(self):
        payload = self.memory.checkpoint()
        self.assertIsInstance(payload, dict)
        self.assertIn("schema_version", payload)
        self.assertTrue(payload["schema_version"].startswith("nuros.memory."))
        self.assertIn("entries", payload)
        self.assertIn("working_memory", payload)
        self.assertIn("operation_log", payload)
        # 4 entries encoded + 1 forgotten = 4 (forgotten stays in store).
        self.assertEqual(len(payload["entries"]), 4)

    def test_checkpoint_round_trips_through_restore(self):
        payload = self.memory.checkpoint()
        memory2 = DefaultMemoryContract()
        memory2.restore(payload)
        self.assertEqual(memory2.memory_count, self.memory.memory_count)

    def test_restore_preserves_forgotten_state(self):
        payload = self.memory.checkpoint()
        memory2 = DefaultMemoryContract()
        memory2.restore(payload)
        restored_forgotten = [e for e in memory2.iter_all() if e.forgotten]
        self.assertEqual(len(restored_forgotten), 1)
        self.assertEqual(restored_forgotten[0].consolidation_status, "FORGOTTEN")

    def test_restore_preserves_epistemic_labels(self):
        payload = self.memory.checkpoint()
        memory2 = DefaultMemoryContract()
        memory2.restore(payload)
        # Find the counterfactual entry — must be IMAGINED.
        cf_entries = [
            e for e in memory2.iter_all()
            if e.memory_type == MemoryType.COUNTERFACTUAL
        ]
        self.assertEqual(len(cf_entries), 1)
        self.assertEqual(cf_entries[0].epistemic_label, EpistemicLabel.IMAGINED)

    def test_restore_preserves_memory_types(self):
        payload = self.memory.checkpoint()
        memory2 = DefaultMemoryContract()
        memory2.restore(payload)
        # 3 EPISODIC + 1 SEMANTIC + 1 COUNTERFACTUAL = ... wait, we encoded
        # 4 entries total (3 episodic + 1 semantic + 1 counterfactual? let
        # me recheck setUp).
        # setUp: episodic 1, episodic 2, semantic fact, counterfactual = 4 entries.
        # 1 of the episodic ones is soft-forgotten but still in store.
        types = [e.memory_type for e in memory2.iter_all()]
        self.assertEqual(types.count(MemoryType.EPISODIC), 2)
        self.assertEqual(types.count(MemoryType.SEMANTIC), 1)
        self.assertEqual(types.count(MemoryType.COUNTERFACTUAL), 1)

    def test_restore_is_idempotent(self):
        """audit §11.1: 'Implementations MUST be idempotent: restoring
        twice yields the same state as restoring once.'"""
        payload = self.memory.checkpoint()
        memory2 = DefaultMemoryContract()
        memory2.restore(payload)
        count_after_first = memory2.memory_count
        memory2.restore(payload)
        count_after_second = memory2.memory_count
        self.assertEqual(count_after_first, count_after_second)

    def test_restore_rejects_foreign_schema(self):
        memory2 = DefaultMemoryContract()
        with self.assertRaises(ValueError):
            memory2.restore({"schema_version": "foreign.unknown.v1", "entries": []})

    def test_restore_accepts_hippocore_schema_prefix(self):
        """PHASE 3: DefaultMemoryContract.restore() accepts any payload
        with schema_version starting 'nuros.' — this enables cross-engine
        restore (an organism migrating default → hippocore)."""
        memory = DefaultMemoryContract()
        memory.encode("x", importance=0.5)
        payload = memory.checkpoint()
        # Simulate a HippoCoreMemory-produced payload by overriding the
        # schema_version prefix.
        payload["schema_version"] = "nuros.hippocore.HippoCoreMemory.v1.phase3"
        memory2 = DefaultMemoryContract()
        memory2.restore(payload)
        self.assertEqual(memory2.memory_count, 1)
        self.assertEqual(memory2.iter_all()[0].content, "x")

    def test_restore_handles_empty_payload(self):
        memory2 = DefaultMemoryContract()
        memory2.restore({"schema_version": memory2.SCHEMA_VERSION, "entries": []})
        self.assertEqual(memory2.memory_count, 0)


class TestInspect(unittest.TestCase):
    """inspect() — supersedes reflect(). audit §10.2 spec drift fix."""

    def setUp(self):
        self.memory = DefaultMemoryContract()
        self.entry = self.memory.encode("inspect me", importance=0.7)

    def test_inspect_returns_dict_metadata(self):
        meta = self.memory.inspect(self.entry.memory_id)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["memory_id"], self.entry.memory_id)
        self.assertEqual(meta["type"], "episodic")
        self.assertEqual(meta["importance"], 0.7)
        self.assertFalse(meta["forgotten"])
        self.assertEqual(meta["consolidation_status"], "ACTIVE")
        self.assertIn("age_seconds", meta)
        self.assertIn("access_count", meta)

    def test_inspect_unknown_returns_none(self):
        self.assertIsNone(self.memory.inspect("nonexistent"))

    def test_reflect_delegates_to_inspect(self):
        """audit Appendix B.3: reflect() now delegates to inspect().

        We compare only the stable (non-time-dependent) fields because
        both calls advance the access_count and the wall-clock, so
        age_seconds/strength differ between successive calls.
        """
        reflect_meta = self.memory.reflect(self.entry.memory_id)
        inspect_meta = self.memory.inspect(self.entry.memory_id)
        self.assertIsNotNone(reflect_meta)
        self.assertIsNotNone(inspect_meta)
        stable_keys = {
            "memory_id", "type", "confidence", "importance",
            "epistemic_label", "forgotten", "consolidation_status",
            "relationship_count", "revision_count", "prediction_error",
        }
        for k in stable_keys:
            self.assertEqual(
                reflect_meta[k], inspect_meta[k],
                f"reflect().{k!r} differs from inspect().{k!r}",
            )


class TestConsolidateStub(unittest.TestCase):
    """consolidate() — no-op stub in the Default impl (real impl in PHASE 6)."""

    def test_consolidate_returns_zero_in_default_impl(self):
        memory = DefaultMemoryContract()
        memory.encode("a", importance=0.5)
        memory.encode("b", importance=0.5)
        n_created = memory.consolidate()
        self.assertEqual(n_created, 0)

    def test_consolidate_accepts_type_arguments(self):
        memory = DefaultMemoryContract()
        n_created = memory.consolidate(
            source_type=MemoryType.EPISODIC,
            target_type=MemoryType.SEMANTIC,
            batch_size=10,
            similarity_threshold=0.9,
        )
        self.assertEqual(n_created, 0)


class TestIterAll(unittest.TestCase):
    """iter_all() — public iterator for decay_experiment.py + PHASE 9 benchmarks.

    audit Appendix B.2 fix.
    """

    def test_returns_all_entries_including_forgotten(self):
        memory = DefaultMemoryContract()
        e1 = memory.encode("live 1", importance=0.5)
        e2 = memory.encode("live 2", importance=0.5)
        e3 = memory.encode("to forget", importance=0.5)
        memory.forget(e3.memory_id)

        all_entries = memory.iter_all()
        self.assertEqual(len(all_entries), 3)
        forgotten = [e for e in all_entries if e.forgotten]
        self.assertEqual(len(forgotten), 1)
        self.assertEqual(forgotten[0].memory_id, e3.memory_id)

    def test_returns_empty_list_for_empty_store(self):
        memory = DefaultMemoryContract()
        self.assertEqual(memory.iter_all(), [])


class TestSummaryExtended(unittest.TestCase):
    """summary() — extended with consolidation_status breakdown."""

    def test_summary_includes_consolidation_status_counts(self):
        memory = DefaultMemoryContract()
        memory.encode("a", importance=0.5)
        memory.encode("b", importance=0.5)
        e3 = memory.encode("c", importance=0.5)
        memory.reconsolidate(e3.memory_id, reward=1.0)  # → RECONSOLIDATED
        memory.forget(memory.iter_all()[0].memory_id)  # → FORGOTTEN

        s = memory.summary()
        self.assertIn("by_consolidation_status", s)
        self.assertGreater(s["by_consolidation_status"].get("RECONSOLIDATED", 0), 0)
        self.assertGreater(s["by_consolidation_status"].get("FORGOTTEN", 0), 0)
        self.assertEqual(s["forgotten_count"], 1)
        self.assertEqual(s["total_memories"], 3)


if __name__ == "__main__":
    unittest.main()
