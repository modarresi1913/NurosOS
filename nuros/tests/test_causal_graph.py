"""
PHASE 8 tests — causal graph integration (Python side).

Verifies:
  - EventKind enum (11 original Rust variants + 6 PHASE 8 memory kinds).
  - memory_event_kind_to_event_kind() translation.
  - PythonCausalGraph.record / get / events_of_kind / trace / to_jsonl.
  - HippoCoreMemory wired to a PythonCausalGraph: every memory operation
    creates a CausalEvent with the right EventKind + depends_on chain.
  - trace_outcome_to_experience() walks the dependency closure.
  - attach_causal_graph() post-construction.
  - causal_event_id is written back to the MemoryEvent (PHASE 7/8 link).

Master prompt §20: the graph should allow tracing
  Outcome → Action → CognitiveState → Memory → Experience.
"""

from __future__ import annotations

import json
import unittest
from typing import Any

from nuros.causal_graph import (
    CausalEvent,
    EventKind,
    PythonCausalGraph,
    memory_event_kind_to_event_kind,
)
from nuros.hippocore import HippoCoreMemory, HippoCoreMemoryConfig
from nuros.memory_events import MemoryEvent, MemoryEventKind


class TestEventKindEnum(unittest.TestCase):
    def test_all_17_kinds_defined(self):
        # 11 original Rust variants + 6 PHASE 8 memory kinds.
        self.assertEqual(len(EventKind), 17)

    def test_original_11_rust_variants_present(self):
        for name in (
            "ENVIRONMENT_EVENT", "SENSORY_OBSERVATION", "PREDICTION",
            "PREDICTION_ERROR", "MEMORY_UPDATE", "BELIEF_REVISION",
            "SELF_MODEL_CHANGE", "DECISION", "ACTION", "OUTCOME",
            "DEVELOPMENTAL_CHANGE",
        ):
            self.assertIn(name, EventKind.__members__)

    def test_phase8_memory_kinds_present(self):
        for name in (
            "MEMORY_ENCODE", "MEMORY_RETRIEVE", "MEMORY_REPLAY",
            "MEMORY_RECONSOLIDATE", "MEMORY_CONSOLIDATE", "MEMORY_FORGET",
        ):
            self.assertIn(name, EventKind.__members__)

    def test_str_returns_value(self):
        self.assertEqual(str(EventKind.MEMORY_ENCODE), "memory_encode")


class TestMemoryEventKindToEventKind(unittest.TestCase):
    def test_all_6_memory_events_translate(self):
        self.assertEqual(
            memory_event_kind_to_event_kind("memory_encoded"),
            EventKind.MEMORY_ENCODE,
        )
        self.assertEqual(
            memory_event_kind_to_event_kind("memory_retrieved"),
            EventKind.MEMORY_RETRIEVE,
        )
        self.assertEqual(
            memory_event_kind_to_event_kind("memory_replayed"),
            EventKind.MEMORY_REPLAY,
        )
        self.assertEqual(
            memory_event_kind_to_event_kind("memory_reconsolidated"),
            EventKind.MEMORY_RECONSOLIDATE,
        )
        self.assertEqual(
            memory_event_kind_to_event_kind("memory_consolidated"),
            EventKind.MEMORY_CONSOLIDATE,
        )
        self.assertEqual(
            memory_event_kind_to_event_kind("memory_forgotten"),
            EventKind.MEMORY_FORGET,
        )

    def test_unknown_falls_back_to_memory_update(self):
        self.assertEqual(
            memory_event_kind_to_event_kind("nonexistent"),
            EventKind.MEMORY_UPDATE,
        )


class TestPythonCausalGraph(unittest.TestCase):
    def setUp(self):
        self.graph = PythonCausalGraph()

    def test_empty_graph(self):
        self.assertEqual(len(self.graph), 0)
        self.assertTrue(self.graph.is_empty())

    def test_record_returns_monotonic_ids(self):
        id1 = self.graph.record(1, EventKind.SENSORY_OBSERVATION, "obs", {}, [])
        id2 = self.graph.record(1, EventKind.PREDICTION, "pred", {}, [id1])
        id3 = self.graph.record(2, EventKind.ACTION, "act", {}, [id2])
        self.assertEqual((id1, id2, id3), (0, 1, 2))

    def test_get_returns_event(self):
        eid = self.graph.record(1, EventKind.ACTION, "act", {"a": 1}, [])
        ev = self.graph.get(eid)
        self.assertIsNotNone(ev)
        self.assertEqual(ev.kind, EventKind.ACTION)
        self.assertEqual(ev.payload, {"a": 1})

    def test_get_unknown_returns_none(self):
        self.assertIsNone(self.graph.get(9999))

    def test_events_of_kind(self):
        self.graph.record(1, EventKind.SENSORY_OBSERVATION, "a", {}, [])
        self.graph.record(1, EventKind.PREDICTION, "b", {}, [])
        self.graph.record(2, EventKind.SENSORY_OBSERVATION, "c", {}, [])
        self.assertEqual(len(self.graph.events_of_kind(EventKind.SENSORY_OBSERVATION)), 2)
        self.assertEqual(len(self.graph.events_of_kind(EventKind.PREDICTION)), 1)
        self.assertEqual(len(self.graph.events_of_kind(EventKind.ACTION)), 0)

    def test_trace_walks_dependency_closure(self):
        id1 = self.graph.record(1, EventKind.SENSORY_OBSERVATION, "obs", {}, [])
        id2 = self.graph.record(1, EventKind.PREDICTION, "pred", {}, [id1])
        id3 = self.graph.record(1, EventKind.DECISION, "dec", {}, [id2])
        id4 = self.graph.record(2, EventKind.ACTION, "act", {}, [id3])
        trace = self.graph.trace(id4)
        ids = [e.id for e in trace]
        self.assertEqual(ids, [0, 1, 2, 3])

    def test_trace_returns_chronological(self):
        id1 = self.graph.record(1, EventKind.SENSORY_OBSERVATION, "obs", {}, [])
        id2 = self.graph.record(1, EventKind.PREDICTION, "pred", {}, [id1])
        trace = self.graph.trace(id2)
        self.assertEqual([e.id for e in trace], [0, 1])

    def test_to_jsonl_round_trips(self):
        id1 = self.graph.record(1, EventKind.SENSORY_OBSERVATION, "obs", {"x": 1}, [])
        id2 = self.graph.record(2, EventKind.ACTION, "act", {}, [id1])
        jsonl = self.graph.to_jsonl()
        lines = jsonl.strip().split("\n")
        self.assertEqual(len(lines), 2)
        e1 = json.loads(lines[0])
        e2 = json.loads(lines[1])
        self.assertEqual(e1["kind"], "sensory_observation")
        self.assertEqual(e2["kind"], "action")
        self.assertEqual(e2["depends_on"], [0])

    def test_to_jsonl_empty_graph_returns_empty(self):
        self.assertEqual(self.graph.to_jsonl(), "")


class TestHippoCoreWiredToCausalGraph(unittest.TestCase):
    """End-to-end: HippoCoreMemory publishes memory events to a
    PythonCausalGraph."""

    def setUp(self):
        self.graph = PythonCausalGraph()
        self.hcm = HippoCoreMemory(
            HippoCoreMemoryConfig(
                replay_policy="recent",
                consolidation_strategy="tag_jaccard",
                consolidation_similarity_threshold=0.3,
                replay_seed=42,
            ),
            organism_id="org-1",
            environment_hash="env-1",
            causal_graph=self.graph,
        )

    def test_encode_creates_causal_event(self):
        self.hcm.set_step(1)
        entry = self.hcm.encode("hello", importance=0.5)
        memory_events = self.graph.events_of_kind(EventKind.MEMORY_ENCODE)
        self.assertEqual(len(memory_events), 1)
        ev = memory_events[0]
        self.assertEqual(ev.step, 1)
        self.assertEqual(ev.payload["memory_id"], entry.memory_id)
        self.assertEqual(ev.payload["engine"], "hippocore")

    def test_encode_episode_creates_causal_event(self):
        self.hcm.set_step(2)
        entry = self.hcm.encode_episode(
            content="ep", action="a", prediction_error=0.1, importance=0.7,
        )
        memory_events = self.graph.events_of_kind(EventKind.MEMORY_ENCODE)
        self.assertEqual(len(memory_events), 1)
        ev = memory_events[0]
        self.assertEqual(ev.payload["memory_id"], entry.memory_id)

    def test_retrieve_creates_causal_events(self):
        self.hcm.set_step(1)
        e1 = self.hcm.encode("hello", importance=0.5)
        e2 = self.hcm.encode("world", importance=0.5)
        self.hcm.set_step(2)
        self.hcm.retrieve(query="hello")
        memory_events = self.graph.events_of_kind(EventKind.MEMORY_RETRIEVE)
        self.assertEqual(len(memory_events), 1)

    def test_replay_creates_causal_events_per_selected(self):
        for i in range(5):
            self.hcm.set_step(i)
            self.hcm.encode_episode(content=f"ep-{i}", action="a", importance=0.5)
        self.hcm.set_step(5)
        results = self.hcm.replay(n=3)
        replay_events = self.graph.events_of_kind(EventKind.MEMORY_REPLAY)
        self.assertEqual(len(replay_events), 3)

    def test_reconsolidate_creates_causal_event(self):
        self.hcm.set_step(1)
        entry = self.hcm.encode_episode(content="recon", action="a",
                                          importance=0.5, confidence=0.5)
        self.hcm.set_step(2)
        self.hcm.reconsolidate(entry.memory_id, reward=1.0, prediction_error=0.3)
        recon_events = self.graph.events_of_kind(EventKind.MEMORY_RECONSOLIDATE)
        self.assertEqual(len(recon_events), 1)

    def test_consolidate_creates_causal_events_per_source(self):
        self.hcm.set_step(1)
        self.hcm.encode_episode(content="apple", action="eat", tags={"food"}, importance=0.5)
        self.hcm.encode_episode(content="bread", action="eat", tags={"food"}, importance=0.5)
        self.hcm.encode_episode(content="cheese", action="eat", tags={"food"}, importance=0.5)
        self.hcm.set_step(2)
        n_targets = self.hcm.consolidate()
        self.assertEqual(n_targets, 1)
        consolidate_events = self.graph.events_of_kind(EventKind.MEMORY_CONSOLIDATE)
        self.assertEqual(len(consolidate_events), 3)  # 1 per source

    def test_forget_creates_causal_event(self):
        self.hcm.set_step(1)
        entry = self.hcm.encode("forget-me", importance=0.5)
        self.hcm.set_step(2)
        self.hcm.forget(entry.memory_id, justification="test")
        forget_events = self.graph.events_of_kind(EventKind.MEMORY_FORGET)
        self.assertEqual(len(forget_events), 1)

    def test_events_in_same_step_chain_via_depends_on(self):
        """PHASE 8: memory events in the same step should chain
        via depends_on so the trace walk returns them in order."""
        self.hcm.set_step(1)
        e1 = self.hcm.encode("first", importance=0.5)
        e2 = self.hcm.encode("second", importance=0.5)
        self.hcm.retrieve(query="first")
        # All 3 events in step 1 — they should chain: encode -> encode -> retrieve.
        all_events = sorted(self.graph._events.values(), key=lambda e: e.id)
        # First event has no depends_on.
        self.assertEqual(all_events[0].depends_on, [])
        # Subsequent events in same step depend on the previous.
        self.assertGreater(len(all_events[1].depends_on), 0)
        self.assertGreater(len(all_events[2].depends_on), 0)

    def test_set_step_resets_depends_on_chain(self):
        """PHASE 8: set_step(n) starts a new depends_on chain — the
        first event in a new step does NOT depend on the last event
        of the previous step."""
        self.hcm.set_step(1)
        self.hcm.encode("step-1-event", importance=0.5)
        self.hcm.set_step(2)
        self.hcm.encode("step-2-event", importance=0.5)
        # Step 2's first event should have empty depends_on.
        step2_events = [e for e in self.graph._events.values() if e.step == 2]
        self.assertGreater(len(step2_events), 0)
        self.assertEqual(step2_events[0].depends_on, [])

    def test_causal_event_id_written_back_to_memory_event(self):
        """PHASE 8: the MemoryEvent.causal_event_id field should be
        populated when a graph is attached, so PHASE 9 benchmarks
        can correlate events across the two systems."""
        captured: list[MemoryEvent] = []
        self.hcm.events.on(lambda ev: captured.append(ev))
        self.hcm.set_step(1)
        self.hcm.encode("hello", importance=0.5)
        self.assertEqual(len(captured), 1)
        # The causal_event_id should be set (non-None) by the PHASE 8
        # callback that ran before this callback (callbacks run in order
        # of registration; the PHASE 8 callback is registered first in
        # __init__ when causal_graph is provided).
        # NOTE: order of callbacks is: PHASE 8 (registered in __init__)
        # THEN this test's callback. So by the time this callback runs,
        # the causal_event_id is set.
        self.assertIsNotNone(captured[0].causal_event_id)


class TestAttachCausalGraphPostConstruction(unittest.TestCase):
    def test_attach_after_construction_starts_publishing(self):
        hcm = HippoCoreMemory()  # no causal_graph
        self.assertIsNone(hcm.causal_graph)
        # Encode something — no graph yet, no events recorded.
        hcm.encode("before-attach", importance=0.5)
        # Attach a graph.
        graph = PythonCausalGraph()
        hcm.attach_causal_graph(graph)
        self.assertIs(hcm.causal_graph, graph)
        # Subsequent operations should publish to the graph.
        hcm.encode("after-attach", importance=0.5)
        memory_events = graph.events_of_kind(EventKind.MEMORY_ENCODE)
        self.assertEqual(len(memory_events), 1)
        # The "before-attach" memory is NOT in the graph.
        descriptions = [e.description for e in memory_events]
        self.assertNotIn("before-attach", " ".join(descriptions))


class TestTraceOutcomeToExperience(unittest.TestCase):
    """Master prompt §20: the graph should support walking
    Outcome → Action → CognitiveState → Memory → Experience."""

    def test_walk_returns_full_chain(self):
        # Simulate: SensoryObservation -> MemoryEncode -> Decision -> Action -> Outcome.
        graph = PythonCausalGraph()
        obs_id = graph.record(
            1, EventKind.SENSORY_OBSERVATION, "obs", {"sensor": 1.0}, [],
        )
        enc_id = graph.record(
            1, EventKind.MEMORY_ENCODE, "encode", {"content": "obs"}, [obs_id],
        )
        dec_id = graph.record(
            1, EventKind.DECISION, "decide", {"action": "MoveRight"}, [enc_id],
        )
        act_id = graph.record(
            1, EventKind.ACTION, "act", {"action": "MoveRight"}, [dec_id],
        )
        out_id = graph.record(
            2, EventKind.OUTCOME, "outcome", {"reward": 0.5}, [act_id],
        )
        trace = graph.trace_outcome_to_experience(out_id)
        kinds = [e.kind for e in trace]
        # All 5 events in the chain.
        self.assertEqual(len(trace), 5)
        self.assertIn(EventKind.OUTCOME, kinds)
        self.assertIn(EventKind.ACTION, kinds)
        self.assertIn(EventKind.MEMORY_ENCODE, kinds)
        self.assertIn(EventKind.SENSORY_OBSERVATION, kinds)
        # Chronological order.
        self.assertEqual(kinds[0], EventKind.SENSORY_OBSERVATION)
        self.assertEqual(kinds[-1], EventKind.OUTCOME)


if __name__ == "__main__":
    unittest.main()
