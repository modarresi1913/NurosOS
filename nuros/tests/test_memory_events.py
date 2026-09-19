"""
PHASE 7 tests — memory event emission.

Verifies that HippoCoreMemory emits MemoryEvent instances for every
memory operation (encode, retrieve, replay, reconsolidate, consolidate,
forget), and that the events carry the right kind + memory_id + details.

Master prompt §8 mandates 6 event kinds:
  MEMORY_ENCODED, MEMORY_RETRIEVED, MEMORY_REPLAYED,
  MEMORY_RECONSOLIDATED, MEMORY_CONSOLIDATED, MEMORY_FORGOTTEN
"""

from __future__ import annotations

import unittest
from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.hippocore import HippoCoreMemory, HippoCoreMemoryConfig
from nuros.memory import MemoryType
from nuros.memory_events import (
    MemoryEvent,
    MemoryEventEmitter,
    MemoryEventKind,
)


class TestMemoryEventKind(unittest.TestCase):
    def test_all_6_kinds_defined(self):
        kinds = {MemoryEventKind.MEMORY_ENCODED,
                 MemoryEventKind.MEMORY_RETRIEVED,
                 MemoryEventKind.MEMORY_REPLAYED,
                 MemoryEventKind.MEMORY_RECONSOLIDATED,
                 MemoryEventKind.MEMORY_CONSOLIDATED,
                 MemoryEventKind.MEMORY_FORGOTTEN}
        self.assertEqual(len(kinds), 6)

    def test_str_returns_value(self):
        self.assertEqual(str(MemoryEventKind.MEMORY_ENCODED), "memory_encoded")


class TestMemoryEvent(unittest.TestCase):
    def test_default_event(self):
        ev = MemoryEvent()
        self.assertEqual(ev.kind, MemoryEventKind.MEMORY_ENCODED)
        self.assertEqual(ev.memory_id, "")
        self.assertGreater(ev.timestamp, 0)
        self.assertIsNone(ev.step)
        self.assertIsNone(ev.organism_id)
        self.assertEqual(ev.engine, "unknown")
        self.assertEqual(ev.details, {})
        self.assertIsNone(ev.causal_event_id)
        self.assertGreater(len(ev.event_id), 0)

    def test_to_dict_round_trips(self):
        ev = MemoryEvent(
            kind=MemoryEventKind.MEMORY_REPLAYED,
            memory_id="mid-1",
            step=42,
            organism_id="org-1",
            engine="hippocore",
            details={"policy": "recent"},
            causal_event_id=99,
        )
        d = ev.to_dict()
        ev2 = MemoryEvent.from_dict(d)
        self.assertEqual(ev.kind, ev2.kind)
        self.assertEqual(ev.memory_id, ev2.memory_id)
        self.assertEqual(ev.step, ev2.step)
        self.assertEqual(ev.organism_id, ev2.organism_id)
        self.assertEqual(ev.engine, ev2.engine)
        self.assertEqual(ev.details, ev2.details)
        self.assertEqual(ev.causal_event_id, ev2.causal_event_id)


class TestMemoryEventEmitter(unittest.TestCase):
    def test_on_off_emit(self):
        emitter = MemoryEventEmitter()
        seen: list[MemoryEvent] = []
        def cb(ev: MemoryEvent) -> None:
            seen.append(ev)
        emitter.on(cb)
        ev = MemoryEvent(kind=MemoryEventKind.MEMORY_ENCODED, memory_id="m1")
        emitter.emit(ev)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].memory_id, "m1")
        emitter.off(cb)
        emitter.emit(ev)
        self.assertEqual(len(seen), 1)

    def test_callback_exception_does_not_propagate(self):
        emitter = MemoryEventEmitter()
        def bad_cb(ev: MemoryEvent) -> None:
            raise RuntimeError("intentional test failure")
        emitter.on(bad_cb)
        # Should not raise.
        emitter.emit(MemoryEvent())
        # Cleanup.
        emitter.clear()

    def test_clear(self):
        emitter = MemoryEventEmitter()
        self.assertEqual(emitter.n_callbacks, 0)
        emitter.on(lambda ev: None)
        emitter.on(lambda ev: None)
        self.assertEqual(emitter.n_callbacks, 2)
        emitter.clear()
        self.assertEqual(emitter.n_callbacks, 0)


class TestHippoCoreEmitsEvents(unittest.TestCase):
    """End-to-end: HippoCoreMemory emits the right MemoryEvent for each
    operation."""

    def setUp(self):
        self.hcm = HippoCoreMemory(
            HippoCoreMemoryConfig(
                replay_policy="recent",
                consolidation_strategy="tag_jaccard",
                consolidation_similarity_threshold=0.3,
                replay_seed=42,
            ),
            organism_id="org-1",
            environment_hash="env-1",
        )
        self.collected: list[MemoryEvent] = []
        self.hcm.events.on(lambda ev: self.collected.append(ev))

    def _events_of_kind(self, kind: MemoryEventKind) -> list[MemoryEvent]:
        return [ev for ev in self.collected if ev.kind == kind]

    def test_encode_emits_memory_encoded(self):
        self.hcm.set_step(1)
        entry = self.hcm.encode("hello", importance=0.5)
        events = self._events_of_kind(MemoryEventKind.MEMORY_ENCODED)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.memory_id, entry.memory_id)
        self.assertEqual(ev.kind, MemoryEventKind.MEMORY_ENCODED)
        self.assertEqual(ev.step, 1)
        self.assertEqual(ev.organism_id, "org-1")
        self.assertEqual(ev.engine, "hippocore")
        self.assertIn("memory_type", ev.details)
        self.assertEqual(ev.details["memory_type"], "episodic")

    def test_encode_episode_emits_memory_encoded_with_episode_details(self):
        self.hcm.set_step(2)
        entry = self.hcm.encode_episode(
            content="ep1", action="MoveRight",
            prediction={"predicted_reward": 0.5},
            prediction_error=0.1, importance=0.7,
        )
        events = self._events_of_kind(MemoryEventKind.MEMORY_ENCODED)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.memory_id, entry.memory_id)
        self.assertIn("action", ev.details)
        self.assertIn("prediction_error", ev.details)
        self.assertEqual(ev.details["prediction_error"], 0.1)

    def test_retrieve_emits_memory_retrieved(self):
        # Encode first.
        e1 = self.hcm.encode("hello world", importance=0.5)
        self.collected.clear()
        # Now retrieve.
        results = self.hcm.retrieve(query="hello")
        events = self._events_of_kind(MemoryEventKind.MEMORY_RETRIEVED)
        self.assertEqual(len(events), len(results))
        for ev in events:
            self.assertEqual(ev.kind, MemoryEventKind.MEMORY_RETRIEVED)
            self.assertEqual(ev.details["query"], "hello")

    def test_retrieve_by_id_emits_memory_retrieved(self):
        e1 = self.hcm.encode("hello", importance=0.5)
        self.collected.clear()
        result = self.hcm.retrieve_by_id(e1.memory_id)
        events = self._events_of_kind(MemoryEventKind.MEMORY_RETRIEVED)
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].details.get("direct"))

    def test_replay_emits_memory_replayed(self):
        # Build a buffer.
        for i in range(5):
            self.hcm.encode_episode(content=f"ep-{i}", action="a",
                                     importance=0.5 + i * 0.1)
        self.collected.clear()
        # Replay 3 memories.
        results = self.hcm.replay(n=3)
        events = self._events_of_kind(MemoryEventKind.MEMORY_REPLAYED)
        self.assertEqual(len(events), len(results))
        for ev in events:
            self.assertEqual(ev.kind, MemoryEventKind.MEMORY_REPLAYED)
            self.assertEqual(ev.details["policy"], "recent")
            self.assertEqual(ev.details["n_selected"], 3)

    def test_reconsolidate_emits_memory_reconsolidated(self):
        entry = self.hcm.encode_episode(content="recon-test", action="a",
                                          importance=0.5, confidence=0.5)
        self.collected.clear()
        self.hcm.reconsolidate(entry.memory_id, reward=1.0, prediction_error=0.3)
        events = self._events_of_kind(MemoryEventKind.MEMORY_RECONSOLIDATED)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.memory_id, entry.memory_id)
        self.assertEqual(ev.details["reward"], 1.0)
        self.assertEqual(ev.details["prediction_error"], 0.3)
        self.assertIn("new_importance", ev.details)
        self.assertIn("new_consolidation_status", ev.details)

    def test_consolidate_emits_memory_consolidated_for_each_source(self):
        # Build a cluster.
        self.hcm.encode_episode(content="apple", action="eat",
                                  tags={"food"}, importance=0.5)
        self.hcm.encode_episode(content="bread", action="eat",
                                  tags={"food"}, importance=0.5)
        self.hcm.encode_episode(content="cheese", action="eat",
                                  tags={"food"}, importance=0.5)
        # Plus an unrelated singleton.
        self.hcm.encode_episode(content="water", action="drink",
                                  tags={"drink"}, importance=0.5)
        self.collected.clear()
        n_targets = self.hcm.consolidate()
        self.assertEqual(n_targets, 1)
        events = self._events_of_kind(MemoryEventKind.MEMORY_CONSOLIDATED)
        # 3 source-side events (one per consolidated source).
        self.assertEqual(len(events), 3)
        all_source_ids = set(ev.memory_id for ev in events)
        self.assertEqual(len(all_source_ids), 3)
        for ev in events:
            self.assertEqual(ev.kind, MemoryEventKind.MEMORY_CONSOLIDATED)
            self.assertEqual(ev.details["new_status"], "CONSOLIDATED")
            # Each source's target_ids list should be the same (1 target).
            self.assertEqual(len(ev.details["target_ids"]), 1)

    def test_forget_emits_memory_forgotten(self):
        entry = self.hcm.encode("forget-me", importance=0.5)
        self.collected.clear()
        self.hcm.forget(entry.memory_id, justification="test soft")
        events = self._events_of_kind(MemoryEventKind.MEMORY_FORGOTTEN)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.memory_id, entry.memory_id)
        self.assertEqual(ev.details["justification"], "test soft")
        self.assertFalse(ev.details["hard"])

    def test_forget_hard_emits_with_hard_flag(self):
        entry = self.hcm.encode("hard-forget", importance=0.5)
        self.collected.clear()
        self.hcm.forget(entry.memory_id, justification="hard delete", hard=True)
        events = self._events_of_kind(MemoryEventKind.MEMORY_FORGOTTEN)
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].details["hard"])

    def test_event_log_capped(self):
        # Set cap low so we can exercise the trim.
        self.hcm._event_log_cap = 5
        # Encode 20 memories → 20 events. Should trim to ~4 (75%).
        for i in range(20):
            self.hcm.encode(f"entry-{i}", importance=0.5)
        self.assertLessEqual(len(self.hcm.event_log), 5)


class TestSetStepForTrajectoryAlignment(unittest.TestCase):
    """The Organism runtime calls hcm.set_step(n) at the start of each
    tick so events get a step number."""

    def test_set_step_propagates_to_events(self):
        hcm = HippoCoreMemory()
        hcm.set_step(42)
        captured: list[MemoryEvent] = []
        hcm.events.on(lambda ev: captured.append(ev))
        hcm.encode("hello", importance=0.5)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].step, 42)

    def test_set_step_none_clears(self):
        hcm = HippoCoreMemory()
        hcm.set_step(10)
        hcm.set_step(None)
        captured: list[MemoryEvent] = []
        hcm.events.on(lambda ev: captured.append(ev))
        hcm.encode("hello", importance=0.5)
        self.assertIsNone(captured[0].step)


if __name__ == "__main__":
    unittest.main()
