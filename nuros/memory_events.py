"""
MemoryEventKind — types of memory events for the developmental trajectory.

PHASE 7 of the HippoCore integration (master prompt §8, §21).

Master prompt §8 mandates that the developmental trajectory record
memory events:
  MEMORY_ENCODED
  MEMORY_RETRIEVED
  MEMORY_REPLAYED
  MEMORY_RECONSOLIDATED
  MEMORY_CONSOLIDATED
  MEMORY_FORGOTTEN

This module defines the corresponding enum + a MemoryEvent dataclass
that carries enough metadata for:
  - telemetry (PHASE 7 trajectory integration)
  - provenance (master prompt §7)
  - replay (the trajectory events themselves are replayable)
  - causal analysis (PHASE 8 will wire these to the causal graph)
  - debugging

PHASE 7 also adds a MemoryEventEmitter callback interface that
HippoCoreMemory uses to publish events as it executes operations. The
callback is registered externally (e.g. by the Organism runtime, or by
a DevelopmentalTrajectory adapter).

Note on the Rust side: the audit (sec 13) recommended introducing
MemoryEventKind in nuros-dev/src/trajectory.rs as well, parallel to
EventKind (nuros-dev/src/causality.rs:23). PHASE 7 lands the Python
side first because:
  1. The Rust extension is not built in the current environment
     (maturin build --release is required).
  2. The Python HippoCoreMemory already emits memory operations; adding
     event emission here is a small change.
  3. The Rust side will mirror this enum when the Rust extension is
     next rebuilt (PHASE 7+ Rust follow-up — flagged in the audit's
     PHASE 10 documentation as known technical debt).

Implementation Status: IMPLEMENTED (Python side)
                  [PROPOSED] (Rust side — needs PyO3 rebuild)
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class MemoryEventKind(Enum):
    """The 6 memory event kinds that must be recorded in the
    developmental trajectory (master prompt §8)."""
    MEMORY_ENCODED = "memory_encoded"
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_REPLAYED = "memory_replayed"
    MEMORY_RECONSOLIDATED = "memory_reconsolidated"
    MEMORY_CONSOLIDATED = "memory_consolidated"
    MEMORY_FORGOTTEN = "memory_forgotten"

    def __str__(self) -> str:
        return self.value


@dataclass
class MemoryEvent:
    """A single memory event for the developmental trajectory.

    Carries enough metadata for telemetry, provenance, replay, causal
    analysis, and debugging (master prompt §8 + §21).

    The `step` field is optional — callers that don't have a notion
    of "step" (e.g. a unit test) leave it None; the Organism runtime
    sets it to the current tick count.

    The `causal_event_id` field is the link to the PHASE 8 causal graph
    — when set, this memory event corresponds to a specific
    DevelopmentalCausalityGraph CausalEvent.id (Rust side). The Python
    side records the id but does not create the CausalEvent (that
    requires the Rust extension).
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kind: MemoryEventKind = MemoryEventKind.MEMORY_ENCODED
    memory_id: str = ""
    """ID of the memory the event concerns. For MEMORY_ENCODED, this is
    the new memory's ID. For MEMORY_RETRIEVED, it's the retrieved
    memory's ID. For MEMORY_REPLAYED, it's the replayed memory's ID.
    For MEMORY_CONSOLIDATED, it's the SOURCE memory's ID (the one
    being marked CONSOLIDATED). For MEMORY_FORGOTTEN, it's the
    forgotten memory's ID."""
    timestamp: float = field(default_factory=time.time)
    step: Optional[int] = None
    """Developmental step at which the event occurred. Matches
    TrajectoryPoint.step on the Rust side (nuros-dev/src/trajectory.rs:21)."""
    organism_id: Optional[str] = None
    """ID of the organism that produced this event. Matches
    DevelopmentalTrajectory.organism_id (nuros-dev/src/trajectory.rs:61)."""
    engine: str = "unknown"
    """Which MemoryEngine produced this event. One of 'default',
    'hippocore'."""
    details: dict[str, Any] = field(default_factory=dict)
    """Free-form metadata: e.g. for MEMORY_REPLAYED, the replay policy
    name + n_selected; for MEMORY_CONSOLIDATED, the strategy name +
    source_ids + target_id; for MEMORY_FORGOTTEN, the justification +
    soft/hard flag."""
    causal_event_id: Optional[int] = None
    """Optional link to the PHASE 8 causal graph: when set, this memory
    event corresponds to a CausalEvent.id (nuros-dev/src/causality.rs:56).
    The Python side records the id; the Rust side creates the CausalEvent
    (PHASE 8 Rust follow-up)."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind.value,
            "memory_id": self.memory_id,
            "timestamp": self.timestamp,
            "step": self.step,
            "organism_id": self.organism_id,
            "engine": self.engine,
            "details": self.details,
            "causal_event_id": self.causal_event_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MemoryEvent":
        return cls(
            event_id=d.get("event_id", str(uuid.uuid4())),
            kind=MemoryEventKind(d.get("kind", "memory_encoded")),
            memory_id=d.get("memory_id", ""),
            timestamp=d.get("timestamp", time.time()),
            step=d.get("step"),
            organism_id=d.get("organism_id"),
            engine=d.get("engine", "unknown"),
            details=dict(d.get("details", {}) or {}),
            causal_event_id=d.get("causal_event_id"),
        )


# ============================================================================
# MemoryEventEmitter — callback interface
# ============================================================================

MemoryEventCallback = Callable[[MemoryEvent], None]
"""A function called by HippoCoreMemory when a memory event occurs.
Implementations should be cheap (the call happens synchronously during
encode/retrieve/replay/etc.) and must NOT raise exceptions — exceptions
in the callback would break the engine's main operation."""


class MemoryEventEmitter:
    """A simple event-bus for MemoryEvent callbacks.

    HippoCoreMemory holds an instance of this class and emits events
    through it. External consumers (Organism, DevelopmentalTrajectory
    adapter, PHASE 9 benchmarks) register callbacks via
    ``emitter.on(callback)``.

    The emitter is *synchronous* — callbacks are called inline during
    the operation that produced the event. This is intentional: it
    keeps the event ordering deterministic (PHASE 7 + audit §13).

    For high-throughput scenarios (e.g. 10K-step benchmarks), callers
    can detach the callback via ``emitter.off(callback)`` to disable
    event emission entirely.
    """

    def __init__(self) -> None:
        self._callbacks: list[MemoryEventCallback] = []

    def on(self, callback: MemoryEventCallback) -> MemoryEventCallback:
        """Register a callback. Returns the callback (for use as a
        decorator)."""
        self._callbacks.append(callback)
        return callback

    def off(self, callback: MemoryEventCallback) -> None:
        """Detach a previously-registered callback. No-op if not found."""
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    def emit(self, event: MemoryEvent) -> None:
        """Emit an event to all registered callbacks.

        Exceptions raised by individual callbacks are swallowed (logged
        to stderr) so a buggy consumer cannot break the engine's main
        operation.
        """
        for cb in list(self._callbacks):  # copy in case callback detaches itself
            try:
                cb(event)
            except Exception:
                # Swallow — never break the caller's operation.
                # In a real production system, log to a structured logger.
                import sys
                print(f"[MemoryEventEmitter] callback {cb!r} raised:",
                      file=sys.stderr, flush=True)

    def clear(self) -> None:
        """Detach all callbacks."""
        self._callbacks.clear()

    @property
    def n_callbacks(self) -> int:
        return len(self._callbacks)


__all__ = [
    "MemoryEventKind",
    "MemoryEvent",
    "MemoryEventCallback",
    "MemoryEventEmitter",
]
