"""
PHASE 4 tests — episodic encoding with structured provenance.

Verifies the new PHASE 4 surface introduced by HippoCoreMemory:
  - ``encode_episode()`` — HippoCore-specific entry point for full
    episodic encoding (master prompt §6).
  - ``MemoryProvenance`` — structured provenance answering
    WHERE/WHEN/WHAT/WHO/WHAT-ENV/WHAT-INTERNAL/WHAT-ACTION/WHAT-OUTCOME
    (master prompt §7).
  - ``MemoryEntry`` PHASE 4 fields: organism_id, action, outcome,
    prediction, environment_state, causal_metadata, structured_provenance.
  - Cross-engine compatibility: DefaultMemoryContract leaves the PHASE 4
    fields None (it does not populate provenance); HippoCoreMemory
    populates them. Checkpoint/restore round-trips both.

These tests document the FIRST INTENTIONAL DIVERGENCE between
HippoCoreMemory and DefaultMemoryContract — audit §11.1 golden-file
equivalence tests deliberately do NOT assert on the PHASE 4 fields,
so they continue to pass.
"""

from __future__ import annotations

import unittest
from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.hippocore.memory_engine import HippoCoreMemory, HippoCoreMemoryConfig
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType
from nuros.memory_engine import MemoryEngine
from nuros.memory_provenance import MemoryProvenance


class TestMemoryProvenance(unittest.TestCase):
    """The MemoryProvenance dataclass — master prompt §7."""

    def test_default_provenance(self):
        p = MemoryProvenance()
        self.assertEqual(p.origin, "")
        self.assertGreater(p.encoded_at, 0)
        self.assertIsNone(p.experience_id)
        self.assertIsNone(p.organism_id)
        self.assertIsNone(p.environment_hash)
        self.assertIsNone(p.environment_state)
        self.assertIsNone(p.internal_state)
        self.assertIsNone(p.action)
        self.assertIsNone(p.outcome)
        self.assertIsNone(p.prediction)
        self.assertIsNone(p.prediction_error)
        self.assertEqual(p.causal_metadata, {})
        self.assertEqual(p.encoder, "unknown")
        self.assertGreater(len(p.provenance_id), 0)

    def test_populated_provenance(self):
        p = MemoryProvenance(
            origin="sensory_observation",
            organism_id="org-001",
            environment_hash="env-hash-abc",
            environment_state={"agent_pos": [3, 4], "visible_resources": 5},
            internal_state={"energy": 0.7, "uncertainty": 0.3},
            action="MoveRight",
            outcome={"reward": 0.5, "new_pos": [4, 4]},
            prediction={"predicted_reward": 0.4},
            prediction_error=0.1,
            experience_id="exp-step-42",
            encoder="hippocore_phase4",
        )
        self.assertEqual(p.origin, "sensory_observation")
        self.assertEqual(p.organism_id, "org-001")
        self.assertEqual(p.environment_hash, "env-hash-abc")
        self.assertEqual(p.environment_state, {"agent_pos": [3, 4], "visible_resources": 5})
        self.assertEqual(p.internal_state, {"energy": 0.7, "uncertainty": 0.3})
        self.assertEqual(p.action, "MoveRight")
        self.assertEqual(p.outcome, {"reward": 0.5, "new_pos": [4, 4]})
        self.assertEqual(p.prediction, {"predicted_reward": 0.4})
        self.assertEqual(p.prediction_error, 0.1)
        self.assertEqual(p.experience_id, "exp-step-42")
        self.assertEqual(p.encoder, "hippocore_phase4")

    def test_to_dict_round_trips_via_from_dict(self):
        p1 = MemoryProvenance(
            origin="x", organism_id="o", environment_hash="h",
            environment_state={"k": 1}, internal_state={"i": 2},
            action="a", outcome="o", prediction="p", prediction_error=0.5,
            experience_id="e", encoder="hippocore_phase4",
            causal_metadata={"k": "v"},
        )
        d = p1.to_dict()
        p2 = MemoryProvenance.from_dict(d)
        self.assertEqual(p1.origin, p2.origin)
        self.assertEqual(p1.encoded_at, p2.encoded_at)
        self.assertEqual(p1.experience_id, p2.experience_id)
        self.assertEqual(p1.organism_id, p2.organism_id)
        self.assertEqual(p1.environment_hash, p2.environment_hash)
        self.assertEqual(p1.environment_state, p2.environment_state)
        self.assertEqual(p1.internal_state, p2.internal_state)
        self.assertEqual(p1.action, p2.action)
        self.assertEqual(p1.outcome, p2.outcome)
        self.assertEqual(p1.prediction, p2.prediction)
        self.assertEqual(p1.prediction_error, p2.prediction_error)
        self.assertEqual(p1.causal_metadata, p2.causal_metadata)
        self.assertEqual(p1.encoder, p2.encoder)

    def test_answer_where_when_what_returns_all_fields(self):
        """Convenience method per master prompt §7 — must return a dict
        with keys for each 'WHERE/WHEN/WHAT/WHO' question."""
        p = MemoryProvenance(origin="o", organism_id="oid", action="a", outcome="o")
        d = p.answer_where_when_what()
        for key in (
            "where", "when", "what_experience", "what_organism",
            "what_environment", "what_internal_state",
            "what_action", "what_outcome", "what_prediction",
            "what_prediction_error", "what_later_modifications", "encoder",
        ):
            self.assertIn(key, d, f"answer_where_when_what() must include {key}")


class TestHippoCoreEncodeEpisode(unittest.TestCase):
    """HippoCoreMemory.encode_episode() — the full episodic encoding entry
    point (master prompt §6)."""

    def setUp(self):
        self.hcm = HippoCoreMemory(
            organism_id="org-001",
            environment_hash="env-abc",
        )

    def test_encode_episode_populates_all_phase4_fields(self):
        entry = self.hcm.encode_episode(
            content="observation at step 5",
            action="MoveRight",
            prediction={"predicted_reward": 0.4},
            outcome={"reward": 0.5, "new_pos": [4, 4]},
            prediction_error=0.1,
            environment_state={"agent_pos": [3, 4], "visible_resources": 5},
            internal_state={"energy": 0.7, "uncertainty": 0.3},
            experience_id="exp-step-5",
            importance=0.8,
            origin="episodic_observation",
        )
        # All PHASE 4 fields populated.
        self.assertEqual(entry.organism_id, "org-001")
        self.assertEqual(entry.action, "MoveRight")
        self.assertEqual(entry.prediction, {"predicted_reward": 0.4})
        self.assertEqual(entry.outcome, {"reward": 0.5, "new_pos": [4, 4]})
        self.assertEqual(entry.prediction_error, 0.1)
        self.assertEqual(entry.environment_state,
                         {"agent_pos": [3, 4], "visible_resources": 5})
        self.assertEqual(entry.memory_type, MemoryType.EPISODIC)
        self.assertEqual(entry.importance, 0.8)
        self.assertEqual(entry.origin, "episodic_observation")

        # structured_provenance populated.
        self.assertIsNotNone(entry.structured_provenance)
        sp = entry.structured_provenance
        self.assertEqual(sp.organism_id, "org-001")
        self.assertEqual(sp.environment_hash, "env-abc")
        self.assertEqual(sp.environment_state,
                         {"agent_pos": [3, 4], "visible_resources": 5})
        self.assertEqual(sp.internal_state,
                         {"energy": 0.7, "uncertainty": 0.3})
        self.assertEqual(sp.action, "MoveRight")
        self.assertEqual(sp.outcome, {"reward": 0.5, "new_pos": [4, 4]})
        self.assertEqual(sp.prediction, {"predicted_reward": 0.4})
        self.assertEqual(sp.prediction_error, 0.1)
        self.assertEqual(sp.experience_id, "exp-step-5")
        self.assertEqual(sp.encoder, "hippocore_phase4")

    def test_encode_episode_seeds_causal_metadata(self):
        """audit §15: encode_episode seeds causal_metadata with organism_id +
        environment_hash for downstream PHASE 8 causal graph integration."""
        entry = self.hcm.encode_episode(
            content="x", action="a",
            environment_state={"k": 1}, internal_state={"i": 2},
            experience_id="exp-step-1",
        )
        self.assertIn("organism_id", entry.causal_metadata)
        self.assertEqual(entry.causal_metadata["organism_id"], "org-001")
        self.assertIn("environment_hash", entry.causal_metadata)
        self.assertEqual(entry.causal_metadata["environment_hash"], "env-abc")
        self.assertIn("experience_id", entry.causal_metadata)
        self.assertIn("internal_state", entry.causal_metadata)

    def test_encode_episode_without_encoding_context(self):
        """When no encoding context is set, encode_episode still works —
        organism_id and environment_hash will be None in the entry."""
        hcm = HippoCoreMemory()  # no organism_id / environment_hash
        entry = hcm.encode_episode(content="x", action="a")
        self.assertIsNone(entry.organism_id)
        self.assertIsNone(entry.structured_provenance.environment_hash)
        # No causal_metadata seeded (because both organism_id and
        # environment_hash are None).
        self.assertEqual(entry.causal_metadata, {})
        # structured_provenance still populated (with None values).
        self.assertIsNotNone(entry.structured_provenance)
        self.assertIsNone(entry.structured_provenance.organism_id)
        self.assertEqual(entry.structured_provenance.encoder, "hippocore_phase4")

    def test_encode_episode_outcome_optional_at_encode_time(self):
        """audit §11.1: outcome may be None at encode time, filled in
        via revise() after the environment responds."""
        entry = self.hcm.encode_episode(
            content="predict", action="MoveRight",
            prediction={"predicted_reward": 0.4},  # outcome=None
        )
        self.assertIsNone(entry.outcome)
        # Caller can fill in outcome later via revise.
        self.hcm.revise(entry.memory_id, "outcome",
                        {"reward": 0.6, "new_pos": [4, 4]},
                        justification="environment responded")

    def test_set_encoding_context_after_construction(self):
        """set_encoding_context() updates organism_id + environment_hash
        for subsequent encode() / encode_episode() calls."""
        hcm = HippoCoreMemory()
        # Initially no context.
        entry1 = hcm.encode_episode(content="x", action="a")
        self.assertIsNone(entry1.organism_id)
        # Set context.
        hcm.set_encoding_context(organism_id="org-2", environment_hash="env-2")
        entry2 = hcm.encode_episode(content="y", action="b")
        self.assertEqual(entry2.organism_id, "org-2")
        self.assertEqual(entry2.structured_provenance.environment_hash, "env-2")
        # Clear context.
        hcm.set_encoding_context(organism_id=None, environment_hash=None)
        entry3 = hcm.encode_episode(content="z", action="c")
        self.assertIsNone(entry3.organism_id)


class TestHippoCoreEncodeEnrichesProvenance(unittest.TestCase):
    """The plain encode() path (not encode_episode) also attaches
    structured_provenance, but with action/outcome/prediction left None
    (the caller can fill them in later)."""

    def test_encode_attaches_structured_provenance(self):
        hcm = HippoCoreMemory(organism_id="org-1", environment_hash="env-1")
        entry = hcm.encode(
            content="hello", importance=0.5, tags={"test"},
        )
        # PHASE 4 fields populated where possible.
        self.assertEqual(entry.organism_id, "org-1")
        self.assertIsNone(entry.action)
        self.assertIsNone(entry.outcome)
        self.assertIsNone(entry.prediction)
        self.assertIsNone(entry.environment_state)
        # structured_provenance populated with encoder='hippocore_phase4'.
        self.assertIsNotNone(entry.structured_provenance)
        self.assertEqual(entry.structured_provenance.encoder, "hippocore_phase4")
        self.assertEqual(entry.structured_provenance.organism_id, "org-1")
        self.assertEqual(entry.structured_provenance.environment_hash, "env-1")

    def test_encode_causal_metadata_seeded_when_context_set(self):
        hcm = HippoCoreMemory(organism_id="org-1", environment_hash="env-1")
        entry = hcm.encode(content="hello")
        self.assertEqual(entry.causal_metadata.get("organism_id"), "org-1")
        self.assertEqual(entry.causal_metadata.get("environment_hash"), "env-1")


class TestPhase4CheckpointRestoreRoundTrip(unittest.TestCase):
    """checkpoint/restore must round-trip the PHASE 4 fields."""

    def test_hippocore_checkpoint_carries_phase4_fields(self):
        hcm = HippoCoreMemory(organism_id="org-1", environment_hash="env-1")
        hcm.encode_episode(
            content="ep1", action="a1", outcome={"r": 0.5},
            prediction={"pr": 0.4}, prediction_error=0.1,
            environment_state={"pos": [1, 2]},
            internal_state={"energy": 0.8},
            experience_id="exp-1", importance=0.7,
        )
        payload = hcm.checkpoint()
        self.assertEqual(payload["engine"], "hippocore")
        self.assertEqual(payload["engine_phase"], 3)  # PHASE 3 schema_version bump
        # But the entry should carry PHASE 4 fields.
        entries = payload["entries"]
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["organism_id"], "org-1")
        self.assertEqual(e["action"], "a1")
        self.assertEqual(e["outcome"], {"r": 0.5})
        self.assertEqual(e["prediction"], {"pr": 0.4})
        self.assertEqual(e["prediction_error"], 0.1)
        self.assertEqual(e["environment_state"], {"pos": [1, 2]})
        self.assertIn("structured_provenance", e)
        self.assertEqual(e["structured_provenance"]["organism_id"], "org-1")
        self.assertEqual(e["structured_provenance"]["environment_hash"], "env-1")
        self.assertEqual(e["structured_provenance"]["experience_id"], "exp-1")
        self.assertEqual(e["structured_provenance"]["action"], "a1")
        self.assertEqual(e["structured_provenance"]["outcome"], {"r": 0.5})
        self.assertEqual(e["structured_provenance"]["encoder"], "hippocore_phase4")

    def test_hippocore_restore_round_trips_phase4_fields(self):
        hcm = HippoCoreMemory(organism_id="org-1", environment_hash="env-1")
        hcm.encode_episode(
            content="ep1", action="a1", outcome={"r": 0.5},
            prediction={"pr": 0.4}, prediction_error=0.1,
            environment_state={"pos": [1, 2]},
            internal_state={"energy": 0.8},
            experience_id="exp-1", importance=0.7,
        )
        payload = hcm.checkpoint()

        hcm2 = HippoCoreMemory()  # no encoding context
        hcm2.restore(payload)
        self.assertEqual(hcm2.memory_count, 1)
        entry = hcm2.iter_all()[0]
        # All PHASE 4 fields round-tripped.
        self.assertEqual(entry.organism_id, "org-1")
        self.assertEqual(entry.action, "a1")
        self.assertEqual(entry.outcome, {"r": 0.5})
        self.assertEqual(entry.prediction, {"pr": 0.4})
        self.assertEqual(entry.prediction_error, 0.1)
        self.assertEqual(entry.environment_state, {"pos": [1, 2]})
        self.assertIsNotNone(entry.structured_provenance)
        self.assertEqual(entry.structured_provenance.organism_id, "org-1")
        self.assertEqual(entry.structured_provenance.environment_hash, "env-1")
        self.assertEqual(entry.structured_provenance.experience_id, "exp-1")
        self.assertEqual(entry.structured_provenance.action, "a1")
        self.assertEqual(entry.structured_provenance.outcome, {"r": 0.5})
        self.assertEqual(entry.structured_provenance.encoder, "hippocore_phase4")

    def test_default_checkpoint_omits_phase4_fields_when_none(self):
        """DefaultMemoryContract leaves PHASE 4 fields None — checkpoint
        payload must NOT include them (clean serialization)."""
        dmc = DefaultMemoryContract()
        dmc.encode("hello", importance=0.5)
        payload = dmc.checkpoint()
        e = payload["entries"][0]
        # No PHASE 4 keys should be present.
        self.assertNotIn("organism_id", e)
        self.assertNotIn("action", e)
        self.assertNotIn("outcome", e)
        self.assertNotIn("prediction", e)
        self.assertNotIn("environment_state", e)
        self.assertNotIn("causal_metadata", e)
        self.assertNotIn("structured_provenance", e)

    def test_cross_engine_restore_preserves_phase4_fields(self):
        """DefaultMemoryContract can restore a HippoCoreMemory-produced
        checkpoint and the PHASE 4 fields survive."""
        hcm = HippoCoreMemory(organism_id="org-1", environment_hash="env-1")
        hcm.encode_episode(content="ep", action="a", outcome="o", importance=0.5)
        payload = hcm.checkpoint()

        dmc = DefaultMemoryContract()
        dmc.restore(payload)
        self.assertEqual(dmc.memory_count, 1)
        entry = dmc.iter_all()[0]
        self.assertEqual(entry.organism_id, "org-1")
        self.assertEqual(entry.action, "a")
        self.assertEqual(entry.outcome, "o")
        self.assertIsNotNone(entry.structured_provenance)
        self.assertEqual(entry.structured_provenance.organism_id, "org-1")


class TestHippoCoreInspectShowsProvenance(unittest.TestCase):
    """inspect() must include the PHASE 4 provenance fields when present."""

    def test_inspect_default_engine_omits_phase4_fields(self):
        dmc = DefaultMemoryContract()
        e = dmc.encode("hello", importance=0.5)
        meta = dmc.inspect(e.memory_id)
        # PHASE 4 fields are present but with None / empty values.
        self.assertFalse(meta["has_structured_provenance"])
        self.assertIsNone(meta["organism_id"])
        self.assertIsNone(meta["action"])
        self.assertIsNone(meta["outcome"])
        self.assertIsNone(meta["prediction"])
        self.assertFalse(meta["has_environment_state"])
        self.assertEqual(meta["causal_metadata_keys"], [])

    def test_inspect_hippocore_engine_includes_provenance(self):
        hcm = HippoCoreMemory(organism_id="org-1", environment_hash="env-1")
        entry = hcm.encode_episode(
            content="ep", action="a", outcome="o",
            prediction="p", prediction_error=0.1,
            environment_state={"k": 1}, importance=0.5,
            experience_id="exp-1", internal_state={"energy": 0.8},
        )
        meta = hcm.inspect(entry.memory_id)
        # engine marker from HippoCoreMemory.
        self.assertEqual(meta["engine"], "hippocore")
        # PHASE 4 fields surfaced.
        self.assertTrue(meta["has_structured_provenance"])
        self.assertEqual(meta["organism_id"], "org-1")
        self.assertEqual(meta["action"], "a")
        self.assertEqual(meta["outcome"], "o")
        self.assertEqual(meta["prediction"], "p")
        self.assertTrue(meta["has_environment_state"])
        self.assertIn("experience_id", meta["causal_metadata_keys"])
        self.assertIn("internal_state", meta["causal_metadata_keys"])
        # provenance sub-dict answers WHERE/WHEN/WHAT.
        self.assertIn("provenance", meta)
        prov = meta["provenance"]
        self.assertEqual(prov["what_organism"], "org-1")
        self.assertEqual(prov["what_action"], "a")
        self.assertEqual(prov["what_outcome"], "o")
        self.assertEqual(prov["what_prediction"], "p")
        self.assertEqual(prov["what_prediction_error"], 0.1)


class TestHippoCoreSchemaVersionBump(unittest.TestCase):
    """PHASE 4 bump: HippoCoreMemory.checkpoint() now reports a v1.phase4
    schema_version (was v1.phase3 in PHASE 3)."""

    def test_schema_version_is_phase4(self):
        hcm = HippoCoreMemory()
        self.assertEqual(hcm.SCHEMA_VERSION, "nuros.hippocore.HippoCoreMemory.v1.phase4")
        payload = hcm.checkpoint()
        self.assertEqual(payload["schema_version"], hcm.SCHEMA_VERSION)
        # engine_phase stays 3 (the PHASE 3 wrapper layer); the encode()
        # override adds PHASE 4 fields but doesn't bump engine_phase.

    def test_hippocore_restores_phase3_payload(self):
        """Backward-compat: HippoCoreMemory can restore a payload with
        schema_version 'v1.phase3' (e.g. produced by an earlier
        HippoCoreMemory before PHASE 4)."""
        hcm = HippoCoreMemory()
        # Synthesize a PHASE 3 payload (no PHASE 4 fields).
        payload = {
            "schema_version": "nuros.hippocore.HippoCoreMemory.v1.phase3",
            "entries": [
                {
                    "memory_id": "test-id",
                    "content": "legacy content",
                    "memory_type": "episodic",
                    "epistemic_label": "REMEMBERED",
                    "importance": 0.5,
                    "confidence": 1.0,
                    "forgotten": False,
                    "consolidation_status": "ACTIVE",
                    "tags": [],
                }
            ],
            "working_memory": {},
            "working_memory_capacity": 7,
            "operation_log": [],
        }
        hcm.restore(payload)
        self.assertEqual(hcm.memory_count, 1)
        entry = hcm.iter_all()[0]
        self.assertEqual(entry.content, "legacy content")
        # PHASE 4 fields are None (since the PHASE 3 payload didn't carry them).
        self.assertIsNone(entry.organism_id)
        self.assertIsNone(entry.action)
        self.assertIsNone(entry.structured_provenance)


class TestPhase3EquivalenceStillHoldsForBasicEncode(unittest.TestCase):
    """The PHASE 3 golden-file equivalence tests in
    test_hippocore_smoke.py::TestHippoCorePhase3Equivalence deliberately
    do NOT assert on the PHASE 4 fields. This test confirms that
    adding the PHASE 4 fields does NOT break the equivalence on the
    fields the equivalence tests DO assert on (content, type,
    importance, confidence, epistemic_label, forgotten,
    consolidation_status, tags)."""

    def test_basic_encode_equivalence_preserved(self):
        dmc = DefaultMemoryContract()
        hcm = HippoCoreMemory()  # no encoding context
        d_entry = dmc.encode("hello", importance=0.7, tags={"test"})
        h_entry = hcm.encode("hello", importance=0.7, tags={"test"})
        # PHASE 3 equivalence assertions (the golden-file tests).
        self.assertEqual(d_entry.content, h_entry.content)
        self.assertEqual(d_entry.memory_type, h_entry.memory_type)
        self.assertEqual(d_entry.importance, h_entry.importance)
        self.assertEqual(d_entry.confidence, h_entry.confidence)
        self.assertEqual(d_entry.epistemic_label, h_entry.epistemic_label)
        self.assertEqual(d_entry.forgotten, h_entry.forgotten)
        self.assertEqual(d_entry.consolidation_status, h_entry.consolidation_status)
        self.assertEqual(d_entry.tags, h_entry.tags)

        # PHASE 4 divergence (intentional):
        # - d_entry has structured_provenance=None
        # - h_entry has structured_provenance populated
        self.assertIsNone(d_entry.structured_provenance)
        self.assertIsNotNone(h_entry.structured_provenance)


if __name__ == "__main__":
    unittest.main()
