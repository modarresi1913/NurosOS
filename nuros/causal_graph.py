"""
DevelopmentalCausalGraph (Python side) — minimal in-memory provenance DAG.

PHASE 8 of the HippoCore integration (master prompt §20, §21).

The Rust side (`nuros-dev/src/causality.rs`) already implements a
`DevelopmentalCausalityGraph` with 11 `EventKind` variants including
`MemoryUpdate` (causality.rs:33). However:
  - The Rust `MemoryUpdate` variant is defined but never produced
    (audit Appendix A — `EventKind::MemoryUpdate` is unused).
  - `MinimumOrganism::tick` does not instantiate the graph at all
    (audit Appendix B.8 — the graph is implemented/tested but unused).
  - Building the Rust extension requires `maturin build --release`,
    which is not available in this environment.

PHASE 8 lands the **Python-side** causal graph that:
  - Mirrors the Rust `EventKind` enum (causality.rs:23-46) including
    the new memory-specific kinds (MemoryEncode, MemoryRetrieve, etc.).
  - Provides a `PythonCausalGraph` that records events + dependency
    edges + supports the `trace(target_id)` walk (audit §15).
  - Wires `HippoCoreMemory` to optionally publish to a `PythonCausalGraph`
    via a callback registered through the existing `MemoryEventEmitter`
    (PHASE 7).

The Python graph is sufficient for:
  - The PHASE 9 benchmarks (they can record memory events into the
    graph and walk traces).
  - The PHASE 10 documentation (which can show end-to-end
    `Outcome → Action → CognitiveState → Memory → Experience` walks).
  - Scientific reproducibility (deterministic given same inputs).

PHASE 8 Rust follow-up: when the Rust extension is rebuilt, the
HippoCoreMemory.events emitter should additionally publish to the
Rust `DevelopmentalCausalityGraph` via a PyO3 callback. This is
flagged as known technical debt in the PHASE 10 docs.

Implementation Status: IMPLEMENTED (Python side).
                  [PROPOSED] (Rust-side wiring — needs maturin build).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventKind(Enum):
    """Mirrors nuros-dev/src/causality.rs:23-46 + adds PHASE 8
    memory-specific kinds (master prompt §21 PHASE 8)."""
    # Original 11 Rust variants (causality.rs:23-46):
    ENVIRONMENT_EVENT = "environment_event"
    SENSORY_OBSERVATION = "sensory_observation"
    PREDICTION = "prediction"
    PREDICTION_ERROR = "prediction_error"
    MEMORY_UPDATE = "memory_update"  # generic (kept for backward-compat)
    BELIEF_REVISION = "belief_revision"
    SELF_MODEL_CHANGE = "self_model_change"
    DECISION = "decision"
    ACTION = "action"
    OUTCOME = "outcome"
    DEVELOPMENTAL_CHANGE = "developmental_change"
    # PHASE 8 NEW: memory-specific kinds (audit §15 recommended adding these
    # alongside the existing MemoryUpdate, OR replacing it. We keep both
    # for backward-compat with any external consumer that records MemoryUpdate
    # — but HippoCoreMemory will use the specific kinds).
    MEMORY_ENCODE = "memory_encode"
    MEMORY_RETRIEVE = "memory_retrieve"
    MEMORY_REPLAY = "memory_replay"
    MEMORY_RECONSOLIDATE = "memory_reconsolidate"
    MEMORY_CONSOLIDATE = "memory_consolidate"
    MEMORY_FORGET = "memory_forget"

    def __str__(self) -> str:
        return self.value


# Map from PHASE 7 MemoryEventKind to PHASE 8 EventKind.
_MEMORY_EVENT_KIND_MAP = {
    "memory_encoded": EventKind.MEMORY_ENCODE,
    "memory_retrieved": EventKind.MEMORY_RETRIEVE,
    "memory_replayed": EventKind.MEMORY_REPLAY,
    "memory_reconsolidated": EventKind.MEMORY_RECONSOLIDATE,
    "memory_consolidated": EventKind.MEMORY_CONSOLIDATE,
    "memory_forgotten": EventKind.MEMORY_FORGET,
}


def memory_event_kind_to_event_kind(memory_event_kind_value: str) -> EventKind:
    """Translate a MemoryEventKind.value string to the corresponding
    EventKind. Falls back to EventKind.MEMORY_UPDATE if unknown."""
    return _MEMORY_EVENT_KIND_MAP.get(
        memory_event_kind_value, EventKind.MEMORY_UPDATE,
    )


@dataclass
class CausalEvent:
    """Mirrors nuros-dev/src/causality.rs:56-69 CausalEvent struct.

    Fields:
      - id: monotonic event ID.
      - step: developmental step at which the event occurred.
      - kind: EventKind.
      - description: free-form.
      - payload: free-form JSON-serializable payload.
      - depends_on: IDs of events this event depends on (provenance
        dependencies; transitive closure is walked by trace()).
    """
    id: int
    step: Optional[int]
    kind: EventKind
    description: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class PythonCausalGraph:
    """In-memory provenance DAG. Mirrors the API of
    nuros-dev/src/causality.rs:73 DevelopmentalCausalityGraph but is
    pure-Python (no Rust dependency).

    The graph is a DAG: events are added in chronological order and
    edges only ever point from earlier events to later events.
    """

    def __init__(self) -> None:
        self._events: dict[int, CausalEvent] = {}
        self._next_id: int = 0

    def record(
        self,
        step: Optional[int],
        kind: EventKind,
        description: str,
        payload: dict[str, Any],
        depends_on: list[int],
    ) -> int:
        """Record a new event. Returns the new event's ID."""
        eid = self._next_id
        self._next_id += 1
        ev = CausalEvent(
            id=eid, step=step, kind=kind, description=description,
            payload=payload, depends_on=list(depends_on),
        )
        self._events[eid] = ev
        return eid

    def get(self, event_id: int) -> Optional[CausalEvent]:
        return self._events.get(event_id)

    def __len__(self) -> int:
        return len(self._events)

    def is_empty(self) -> bool:
        return not self._events

    def events_of_kind(self, kind: EventKind) -> list[CausalEvent]:
        """All events of a particular kind, in chronological order."""
        return [ev for ev in self._events.values() if ev.kind == kind]

    def trace(self, target_id: int) -> list[CausalEvent]:
        """Compute the causal trace leading up to a given event: the
        full set of events that directly or indirectly appear in its
        ``depends_on`` closure. Returned in chronological order (by ID).

        Mirrors causality.rs:127-145 trace().
        """
        visited: set[int] = set()
        stack = [target_id]
        while stack:
            eid = stack.pop()
            if eid in visited:
                continue
            visited.add(eid)
            ev = self._events.get(eid)
            if ev is None:
                continue
            for dep in ev.depends_on:
                if dep not in visited:
                    stack.append(dep)
        # Chronological order.
        return sorted(
            (self._events[eid] for eid in visited if eid in self._events),
            key=lambda e: e.id,
        )

    def trace_outcome_to_experience(self, outcome_id: int) -> list[CausalEvent]:
        """Walk an Outcome event back to the SensoryObservation that
        originated the chain.

        Master prompt §20: the graph should allow tracing
            Outcome -> Action -> CognitiveState -> Memory -> Experience.

        This implementation walks the `depends_on` closure (same as
        trace()) and returns the events in chronological order. The
        caller can then filter to the kinds they care about
        (Outcome, Action, Decision, MemoryEncode/Retrieve/Replay/
        Consolidate/Reconsolidate/Forget, SensoryObservation).
        """
        return self.trace(outcome_id)

    def to_jsonl(self) -> str:
        """Export as JSONL (one JSON object per line) for offline
        analysis. Mirrors causality.rs:190-199."""
        import json
        lines = []
        for ev in self._events.values():
            lines.append(json.dumps({
                "id": ev.id,
                "step": ev.step,
                "kind": ev.kind.value,
                "description": ev.description,
                "payload": ev.payload,
                "depends_on": ev.depends_on,
                "timestamp": ev.timestamp,
            }))
        return "\n".join(lines) + ("\n" if lines else "")


__all__ = [
    "EventKind",
    "CausalEvent",
    "PythonCausalGraph",
    "memory_event_kind_to_event_kind",
]
