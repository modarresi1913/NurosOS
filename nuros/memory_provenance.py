"""
MemoryProvenance — structured provenance for every memory.

PHASE 4 of the HippoCore integration (master prompt §7).

Audit Appendix A confirms `MemoryProvenance` does NOT exist in the
historical codebase — `MemoryEntry.provenance` was a free-form string
(`nuros/memory.py:83`). This module replaces that with a structured
dataclass so every memory can answer:

  - WHERE did it come from?      → origin
  - WHEN was it created?         → encoded_at
  - WHAT experience generated it?→ experience_id
  - WHAT organism encoded it?    → organism_id
  - WHAT environment existed?    → environment_hash, environment_state
  - WHAT internal state existed? → internal_state
  - WHAT action occurred?        → action
  - WHAT outcome followed?       → outcome
  - WHAT later modifications?    → revision_history (already on MemoryEntry)

This integrates with:
  - DevelopmentalTrajectory  (nuros-dev/src/trajectory.rs:59)
  - DevelopmentalCausalityGraph (nuros-dev/src/causality.rs:73) via the
    `causal_metadata` field which carries the CausalEvent IDs that
    this memory depends on.

Implementation Status: IMPLEMENTED (PHASE 4).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MemoryProvenance:
    """Structured provenance for a single memory.

    A memory should answer (master prompt §7):
      WHERE / WHEN / WHAT experience / WHAT organism / WHAT environment /
      WHAT internal state / WHAT action / WHAT outcome / WHAT later
      modifications.

    All fields are optional so callers can populate them incrementally
    (e.g. the outcome may not be known at encode time and is filled in
    via ``revise()`` after the environment responds).

    Integration with the developmental substrate:
      - ``organism_id`` matches ``DevelopmentalTrajectory.organism_id``
        (nuros-dev/src/trajectory.rs:61)
      - ``environment_hash`` matches ``DevelopmentalTrajectory.environment_hash``
        (nuros-dev/src/trajectory.rs:65)
      - ``causal_metadata.causal_event_ids`` carries the CausalEvent.id
        values (nuros-dev/src/causality.rs:56) that this memory depends on,
        enabling the trace walk `Outcome → Action → CognitiveState →
        Memory → Experience` (audit §15, master prompt §20).
    """

    # ---- WHERE / WHEN ----
    origin: str = ""
    """Human-readable source label (e.g. 'sensory_observation',
    'inferred_from_pattern', 'imagined_via_counterfactual')."""

    encoded_at: float = field(default_factory=time.time)
    """Wall-clock seconds since Unix epoch when the memory was encoded."""

    # ---- WHAT experience / WHAT organism ----
    experience_id: Optional[str] = None
    """Optional reference to the experience event that generated this
    memory. May match a CausalEvent.id (nuros-dev/src/causality.rs:56)
    or a TrajectoryPoint.step (nuros-dev/src/trajectory.rs:21)."""

    organism_id: Optional[str] = None
    """ID of the organism that encoded this memory. Must match
    DevelopmentalTrajectory.organism_id (nuros-dev/src/trajectory.rs:61)
    when the memory is encoded by a NurosOS organism."""

    # ---- WHAT environment existed ----
    environment_hash: Optional[str] = None
    """Hash of the environment state at encode time (matches
    DevelopmentalTrajectory.environment_hash,
    nuros-dev/src/trajectory.rs:65). Used for cross-trajectory
    provenance alignment (audit §20)."""

    environment_state: Optional[dict[str, Any]] = None
    """Snapshot of the environment state at encode time. Free-form dict;
    implementations decide what to capture (e.g. ResourceWorld agent_pos
    + visible_resources)."""

    # ---- WHAT internal state existed ----
    internal_state: Optional[dict[str, Any]] = None
    """Snapshot of the organism's internal state at encode time. Free-form
    dict; implementations decide what to capture (e.g. HomeostasisKernel
    variables: energy, uncertainty, prediction_error, sensory_load,
    threat_level, stability)."""

    # ---- WHAT action occurred / WHAT outcome followed ----
    action: Optional[Any] = None
    """The action the organism took (or is about to take) at encode time.
    May be an enum (e.g. ResourceWorld::Action::MoveRight) or any
    JSON-serializable value."""

    outcome: Optional[Any] = None
    """The outcome that followed the action. May not be known at encode
    time — fill in via MemoryEngine.revise() after the environment
    responds."""

    prediction: Optional[Any] = None
    """The organism's prediction (e.g. predicted reward) for the action
    above. Used to compute prediction_error."""

    prediction_error: Optional[float] = None
    """Signed difference between predicted and actual outcome. If
    provided at encode time, also stored on MemoryEntry.prediction_error
    (audit §11.1 NEW field usage)."""

    # ---- Causal graph integration ----
    causal_metadata: dict[str, Any] = field(default_factory=dict)
    """Free-form metadata for the developmental causal graph (audit §15).
    Recommended keys:
      - 'causal_event_ids': list[int] — CausalEvent.id values
        (nuros-dev/src/causality.rs:56) this memory depends on.
      - 'depends_on_step': Optional[int] — TrajectoryPoint.step this
        memory was encoded at.
      - 'produces_event_kind': Optional[str] — the EventKind this memory
        will produce when consulted (PHASE 8 wires this).
    """

    # ---- Encoding provenance ----
    encoder: str = "unknown"
    """Which MemoryEngine produced this memory. One of:
      'default' — DefaultMemoryContract
      'hippocore' — HippoCoreMemory (PHASE 4+)
      'hippocore_phase4' — HippoCoreMemory with real episodic encoding
    """

    # ---- Optional ID for the provenance record itself ----
    provenance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique ID for this provenance record. Useful when a single memory
    accumulates multiple provenance records across reconsolidation
    events (audit §18 — versioned memory state)."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-native dict for checkpoint/restore."""
        return {
            "origin": self.origin,
            "encoded_at": self.encoded_at,
            "experience_id": self.experience_id,
            "organism_id": self.organism_id,
            "environment_hash": self.environment_hash,
            "environment_state": self.environment_state,
            "internal_state": self.internal_state,
            "action": self.action,
            "outcome": self.outcome,
            "prediction": self.prediction,
            "prediction_error": self.prediction_error,
            "causal_metadata": self.causal_metadata,
            "encoder": self.encoder,
            "provenance_id": self.provenance_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MemoryProvenance":
        """Deserialize from a to_dict() payload."""
        return cls(
            origin=d.get("origin", ""),
            encoded_at=d.get("encoded_at", time.time()),
            experience_id=d.get("experience_id"),
            organism_id=d.get("organism_id"),
            environment_hash=d.get("environment_hash"),
            environment_state=d.get("environment_state"),
            internal_state=d.get("internal_state"),
            action=d.get("action"),
            outcome=d.get("outcome"),
            prediction=d.get("prediction"),
            prediction_error=d.get("prediction_error"),
            causal_metadata=dict(d.get("causal_metadata", {}) or {}),
            encoder=d.get("encoder", "unknown"),
            provenance_id=d.get("provenance_id", str(uuid.uuid4())),
        )

    def answer_where_when_what(self) -> dict[str, Any]:
        """Convenience: produce a dict answering WHERE/WHEN/WHAT
        per master prompt §7. Used by MemoryEngine.inspect() and
        by the PHASE 8 causal trace walk."""
        return {
            "where": self.origin,
            "when": self.encoded_at,
            "what_experience": self.experience_id,
            "what_organism": self.organism_id,
            "what_environment": self.environment_hash,
            "what_internal_state": self.internal_state,
            "what_action": self.action,
            "what_outcome": self.outcome,
            "what_prediction": self.prediction,
            "what_prediction_error": self.prediction_error,
            "what_later_modifications": self.causal_metadata,
            "encoder": self.encoder,
        }
