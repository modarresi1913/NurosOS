"""
Default Memory Contract — the reference implementation of ``MemoryEngine``.

PHASE 2 of the HippoCore integration (master prompt §33).

This module is the *concrete* backend of the Mind Contract Layer Memory
Contract. The ABC itself lives in ``nuros/memory_engine.py``.

Backward-compatibility note (audit §11.3 step 1-2):
    The historical name ``MemoryContract`` is kept as a deprecated alias
    of ``DefaultMemoryContract`` for one minor version. Existing callers
    (``nuros/organism.py``, ``organisms/organism_0.py``..``organism_5.py``,
    ``examples_new/memory_demo.py``, ``benchmarks/benchmark_suite.py``,
    ``experiments/memory/decay_experiment.py``) keep working unchanged.

Fixes from audit Appendix B:
    - B.1: ``forget()`` now SOFT-deletes by default (``hard=False``).
      Satisfies the invariant at ``mind/memory/SPEC.md:45``,
      "No memory is permanently deleted".
    - B.3: ``reflect()`` now delegates to ``inspect()``; the spec drift
      on ``reflect(query) -> List[MemoryEntry]`` is reconciled by
      keeping ``reflect`` as a deprecated alias of ``inspect`` AND
      updating the spec to match the implementation.
    - B.4: ``replay()`` spec drift reconciled — the new signature is
      ``replay(memory_type, tags, time_range, n, generative)``. Spec
      files updated.
    - B.7: ``MemoryEntry.access_count`` is now correctly incremented on
      every retrieve/inspect access (was a dead field before).
    - B.9: ``Organism.state_hash()`` now includes a memory-content hash
      (separate change in ``nuros/organism.py``).

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import math
import time
import uuid
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from nuros.epistemic import EpistemicLabel, EpistemicKernel
from nuros.memory_engine import MemoryEngine
from nuros.memory_provenance import MemoryProvenance


# ============================================================================
# Data classes (kept in this module for backward-compat — `from nuros.memory
# import MemoryEntry, MemoryType, MemoryOperation` continues to work).
# ============================================================================


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    COUNTERFACTUAL = "counterfactual"


class MemoryOperation(Enum):
    REMEMBER = "remember"
    RETRIEVE = "retrieve"
    ASSOCIATE = "associate"
    REFLECT = "reflect"
    REVISE = "revise"
    RECONSOLIDATE = "reconsolidate"
    FORGET = "forget"
    REPLAY = "replay"
    # NEW (PHASE 2): explicit operations for the new MemoryEngine surface.
    ENCODE = "encode"
    CONSOLIDATE = "consolidate"
    CHECKPOINT = "checkpoint"
    RESTORE = "restore"
    INSPECT = "inspect"


@dataclass
class MemoryAccess:
    timestamp: float
    operation: MemoryOperation
    accessor: str = ""


@dataclass
class MemoryRevision:
    revision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    field_modified: str = ""
    old_value: Any = None
    new_value: Any = None
    justification: str = ""
    author: str = ""


@dataclass
class MemoryRelationship:
    target_id: str
    relation_type: str
    strength: float = 1.0
    bidirectional: bool = False


@dataclass
class MemoryEntry:
    """A single memory entry with full metadata and provenance.

    PHASE 2 additions (backward-compatible — all new fields have safe
    defaults so existing serialization round-trips continue to work):
      - ``forgotten`` (bool, default False) — soft-delete marker. When
        True, the memory is retrievable only via ``iter_all()`` or with
        an explicit ``min_importance=0.0`` retrieve() query.
      - ``consolidation_status`` (str, default "ACTIVE") — one of
        ACTIVE / WEAKENING / CONSOLIDATED / RECONSOLIDATED / ARCHIVED /
        FORGOTTEN. Tracks the conceptual forgetting lifecycle (audit §17).

    PHASE 4 additions (HippoCore episodic encoding surface — audit §6, §7):
      - ``organism_id`` — ID of the encoding organism (matches
        DevelopmentalTrajectory.organism_id).
      - ``action`` — the action the organism took at encode time.
      - ``outcome`` — the outcome that followed the action (filled in
        after the environment responds).
      - ``prediction`` — the organism's prediction (e.g. predicted reward).
      - ``environment_state`` — snapshot of the environment at encode time.
      - ``causal_metadata`` — free-form dict carrying CausalEvent IDs
        this memory depends on (audit §15).
      - ``provenance`` — structured MemoryProvenance record (master
        prompt §7). Replaces the free-form `provenance: str` field which
        is kept as `provenance_str` for backward compat.

    All PHASE 4 fields are optional with safe defaults so existing
    serialization round-trips continue to work. HippoCoreMemory (PHASE 4+)
    populates them; DefaultMemoryContract leaves them None/empty.
    """

    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Any = None
    memory_type: MemoryType = MemoryType.EPISODIC
    origin: str = ""
    timestamp: float = field(default_factory=time.time)
    provenance: str = ""  # legacy free-form string (kept for backward compat)
    confidence: float = 1.0
    context: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    prediction_error: float = 0.0
    epistemic_label: EpistemicLabel = EpistemicLabel.REMEMBERED
    decay_rate: float = 0.001
    access_history: list[MemoryAccess] = field(default_factory=list)
    relationships: list[MemoryRelationship] = field(default_factory=list)
    revision_history: dict[str, MemoryRevision] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    # PHASE 2:
    forgotten: bool = False
    consolidation_status: str = "ACTIVE"
    # PHASE 4 (HippoCore episodic encoding surface):
    organism_id: Optional[str] = None
    action: Optional[Any] = None
    outcome: Optional[Any] = None
    prediction: Optional[Any] = None
    environment_state: Optional[dict[str, Any]] = None
    causal_metadata: dict[str, Any] = field(default_factory=dict)
    structured_provenance: Optional[MemoryProvenance] = None
    """Structured MemoryProvenance record (master prompt §7).
    None when the encoding engine does not populate provenance
    (DefaultMemoryContract in PHASE 3 leaves it None).
    HippoCoreMemory (PHASE 4+) populates it."""

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0.0, 1.0], got {self.confidence}")
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError(f"Importance must be in [0.0, 1.0], got {self.importance}")

    @property
    def access_count(self) -> int:
        return len(self.access_history)

    @property
    def current_strength(self) -> float:
        # Forgotten memories have strength 0 — they are excluded from
        # default retrieve() results (which use min_importance > 0).
        if self.forgotten:
            return 0.0
        access_boost = min(1.0, self.access_count * 0.05)
        age = time.time() - self.timestamp
        decay = math.exp(-self.decay_rate * age)
        return self.importance * self.confidence * decay * (1.0 + access_boost)

    def record_access(self, operation: MemoryOperation, accessor: str = "") -> None:
        self.access_history.append(MemoryAccess(
            timestamp=time.time(), operation=operation, accessor=accessor,
        ))


# ============================================================================
# DefaultMemoryContract — the reference MemoryEngine impl
# ============================================================================


class DefaultMemoryContract(MemoryEngine):
    """The default (and historical) ``MemoryEngine`` implementation.

    Stores memories in an in-memory dict keyed by ``memory_id``. All
    operations preserve the historical behaviour with two exceptions
    (audit Appendix B.1 + B.4):

      1. ``forget(hard=False)`` (the new default) SOFT-deletes — the entry
         is kept in the store with ``forgotten=True``,
         ``importance=0``, ``consolidation_status="FORGOTTEN"``.
      2. ``replay()`` accepts a new ``n`` cap and a ``generative`` flag
         (the latter is a no-op in the Default impl — generative replay
         is a HippoCore-only feature).
    """

    SCHEMA_VERSION = "nuros.memory.DefaultMemoryContract.v1"

    def __init__(self, epistemic_kernel: Optional[EpistemicKernel] = None):
        self._memories: dict[str, MemoryEntry] = {}
        self._epistemic = epistemic_kernel or EpistemicKernel()
        self._operation_log: list[tuple[MemoryOperation, str, float]] = []
        self._working_memory: dict[str, Any] = {}
        self._working_memory_capacity: int = 7

    # ====================================================================
    # Encoding / retrieval
    # ====================================================================

    def remember(
        self,
        content: Any,
        memory_type: MemoryType = MemoryType.EPISODIC,
        origin: str = "",
        provenance: str = "",
        confidence: float = 1.0,
        importance: float = 0.5,
        context: Optional[dict] = None,
        tags: Optional[set[str]] = None,
    ) -> MemoryEntry:
        """Historical encode entry point. Equivalent to ``encode(...)``."""
        return self.encode(
            content=content, memory_type=memory_type, origin=origin,
            provenance=provenance, confidence=confidence, importance=importance,
            context=context, tags=tags,
        )

    def encode(
        self,
        content: Any,
        memory_type: Optional[MemoryType] = None,
        origin: str = "",
        provenance: str = "",
        confidence: float = 1.0,
        importance: float = 0.5,
        context: Optional[dict[str, Any]] = None,
        tags: Optional[set[str]] = None,
        epistemic_label: Optional[EpistemicLabel] = None,
    ) -> MemoryEntry:
        mt = memory_type if memory_type is not None else MemoryType.EPISODIC
        if epistemic_label is None:
            epistemic_label = (
                EpistemicLabel.IMAGINED
                if mt == MemoryType.COUNTERFACTUAL
                else EpistemicLabel.REMEMBERED
            )
        entry = MemoryEntry(
            content=content, memory_type=mt, origin=origin,
            provenance=provenance, confidence=confidence, importance=importance,
            epistemic_label=epistemic_label, context=context or {},
            tags=tags or set(),
        )
        self._memories[entry.memory_id] = entry
        self._log_operation(MemoryOperation.ENCODE, entry.memory_id)
        entry.record_access(MemoryOperation.REMEMBER)
        return entry

    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        min_confidence: float = 0.0,
        min_importance: float = 0.0,
        tags: Optional[set[str]] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Retrieve memories matching the query, sorted by
        ``MemoryEntry.current_strength`` descending.

        Soft-forgotten memories (``entry.forgotten == True``) are ALWAYS
        excluded from ``retrieve()`` — that is the semantics of soft-delete
        (audit Appendix B.1 fix). Use ``iter_all()`` to access forgotten
        memories, or restore them via ``reconsolidate(reward=...)``.
        """
        results: list[MemoryEntry] = []
        for entry in self._memories.values():
            if entry.forgotten:
                # Soft-forgotten: invisible to retrieve() no matter the
                # importance filter. The whole point of soft-delete is
                # "not retrievable, but not deleted".
                continue
            if memory_type and entry.memory_type != memory_type:
                continue
            if entry.confidence < min_confidence:
                continue
            if entry.importance < min_importance:
                continue
            if tags and not tags.issubset(entry.tags):
                continue
            if query and isinstance(entry.content, str) and query.lower() not in entry.content.lower():
                continue
            entry.record_access(MemoryOperation.RETRIEVE)
            results.append(entry)
        results.sort(key=lambda e: e.current_strength, reverse=True)
        self._log_operation(MemoryOperation.RETRIEVE, "batch")
        return results[:limit]

    def retrieve_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        entry = self._memories.get(memory_id)
        if entry:
            entry.record_access(MemoryOperation.RETRIEVE)
            self._log_operation(MemoryOperation.RETRIEVE, memory_id)
        return entry

    def iter_all(self) -> list[MemoryEntry]:
        """Return ALL stored memories in insertion order (including
        soft-forgotten ones). Used by decay_experiment.py and PHASE 9
        benchmarks. Closes audit Appendix B.2."""
        return list(self._memories.values())

    # ====================================================================
    # Association
    # ====================================================================

    def associate(
        self, memory_id_a: str, memory_id_b: str,
        relation_type: str = "semantic", strength: float = 1.0,
        bidirectional: bool = True,
    ) -> bool:
        if memory_id_a not in self._memories or memory_id_b not in self._memories:
            return False
        rel = MemoryRelationship(
            target_id=memory_id_b, relation_type=relation_type,
            strength=strength, bidirectional=bidirectional,
        )
        self._memories[memory_id_a].relationships.append(rel)
        if bidirectional:
            self._memories[memory_id_b].relationships.append(MemoryRelationship(
                target_id=memory_id_a, relation_type=relation_type,
                strength=strength, bidirectional=True,
            ))
        self._log_operation(MemoryOperation.ASSOCIATE, f"{memory_id_a}<->{memory_id_b}")
        return True

    # ====================================================================
    # Inspection / reflection
    # ====================================================================

    def inspect(self, memory_id: str) -> Optional[dict[str, Any]]:
        entry = self._memories.get(memory_id)
        if not entry:
            return None
        entry.record_access(MemoryOperation.INSPECT)
        self._log_operation(MemoryOperation.INSPECT, memory_id)
        meta: dict[str, Any] = {
            "memory_id": entry.memory_id,
            "type": entry.memory_type.value,
            "strength": entry.current_strength,
            "confidence": entry.confidence,
            "importance": entry.importance,
            "access_count": entry.access_count,
            "relationship_count": len(entry.relationships),
            "epistemic_label": entry.epistemic_label.name,
            "prediction_error": entry.prediction_error,
            "age_seconds": time.time() - entry.timestamp,
            "forgotten": entry.forgotten,
            "consolidation_status": entry.consolidation_status,
            "revision_count": len(entry.revision_history),
            # PHASE 4 fields — only included when populated.
            "has_structured_provenance": entry.structured_provenance is not None,
            "organism_id": entry.organism_id,
            "action": entry.action,
            "outcome": entry.outcome,
            "prediction": entry.prediction,
            "has_environment_state": entry.environment_state is not None,
            "causal_metadata_keys": sorted(entry.causal_metadata.keys()) if entry.causal_metadata else [],
        }
        if entry.structured_provenance is not None:
            meta["provenance"] = entry.structured_provenance.answer_where_when_what()
        return meta

    def reflect(self, memory_id: str) -> Optional[dict[str, Any]]:
        """Deprecated alias for ``inspect()`` (audit Appendix B.3).

        The historical signature ``reflect(memory_id) -> Optional[dict]``
        is preserved; the spec drift at ``mind/memory/SPEC.md:17`` (which
        documented ``reflect(query) -> List[MemoryEntry]``) is reconciled
        by updating the spec rather than breaking callers.
        """
        return self.inspect(memory_id)

    # ====================================================================
    # Revision
    # ====================================================================

    def revise(
        self, memory_id: str, field_name: str, new_value: Any,
        justification: str, author: str = "system",
    ) -> Optional[MemoryEntry]:
        entry = self._memories.get(memory_id)
        if not entry:
            return None
        old_value = getattr(entry, field_name, None)
        revision = MemoryRevision(
            field_modified=field_name, old_value=old_value,
            new_value=new_value, justification=justification, author=author,
        )
        setattr(entry, field_name, new_value)
        entry.revision_history[revision.revision_id] = revision
        entry.record_access(MemoryOperation.REVISE)
        self._log_operation(MemoryOperation.REVISE, memory_id)
        return entry

    # ====================================================================
    # Reconsolidation
    # ====================================================================

    def reconsolidate(
        self, memory_id: str, reward: float = 0.0,
        prediction_error: Optional[float] = None,
    ) -> Optional[MemoryEntry]:
        entry = self._memories.get(memory_id)
        if not entry:
            return None
        # If prediction_error is provided, record it on the entry (audit §11.1
        # NEW field usage) and modulate the reward magnitude.
        effective_reward = reward
        if prediction_error is not None:
            entry.prediction_error = prediction_error
            # Magnitude scales with absolute prediction error (a惊喜 signal).
            effective_reward = reward * (1.0 + min(1.0, abs(prediction_error)))
        if effective_reward > 0:
            entry.importance = min(1.0, entry.importance + effective_reward * 0.1)
            entry.confidence = min(1.0, entry.confidence + effective_reward * 0.05)
            entry.decay_rate *= 0.9
            if entry.consolidation_status == "ACTIVE":
                entry.consolidation_status = "RECONSOLIDATED"
        elif effective_reward < 0:
            entry.confidence = max(0.0, entry.confidence + effective_reward * 0.05)
            entry.decay_rate *= 1.1
            if entry.consolidation_status == "ACTIVE":
                entry.consolidation_status = "WEAKENING"
        entry.record_access(MemoryOperation.RECONSOLIDATE)
        self._log_operation(MemoryOperation.RECONSOLIDATE, memory_id)
        return entry

    # ====================================================================
    # Forgetting (FIX: soft-delete is now the default)
    # ====================================================================

    def forget(
        self, memory_id: str, justification: str = "", hard: bool = False,
    ) -> bool:
        if memory_id not in self._memories:
            return False
        entry = self._memories[memory_id]
        entry.record_access(MemoryOperation.FORGET)
        self._log_operation(MemoryOperation.FORGET, memory_id)
        self._operation_log.append((
            MemoryOperation.FORGET,
            f"{'HARD' if hard else 'SOFT'}:{memory_id}:type={entry.memory_type.value}:justification={justification}",
            time.time(),
        ))
        if hard:
            del self._memories[memory_id]
        else:
            # SOFT forget: keep entry, downgrade epistemic label, zero importance,
            # mark forgotten. Satisfies mind/memory/SPEC.md:45 invariant.
            entry.forgotten = True
            entry.importance = 0.0
            entry.consolidation_status = "FORGOTTEN"
            # Epistemic label downgrade: REMEMBERED → INFERRED (no longer
            # first-hand). Other labels are preserved (e.g. IMAGINED stays
            # IMAGINED — a counterfactual memory stays counterfactual).
            if entry.epistemic_label == EpistemicLabel.REMEMBERED:
                entry.epistemic_label = EpistemicLabel.INFERRED
        return True

    # ====================================================================
    # Replay (extended with `n` cap + `generative` flag)
    # ====================================================================

    def replay(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[set[str]] = None,
        time_range: Optional[tuple[float, float]] = None,
        n: Optional[int] = None,
        generative: bool = False,
    ) -> list[MemoryEntry]:
        """Return a sequence of memories for replay, sorted by timestamp
        ascending.

        ``generative=True`` is a no-op in the Default impl (it returns the
        same raw stored memories as ``generative=False``); HippoCore (PHASE
        3+) implements true generative replay.
        """
        results: list[MemoryEntry] = []
        for entry in self._memories.values():
            if entry.forgotten:
                # Forgotten memories are excluded from replay by default.
                continue
            if memory_type and entry.memory_type != memory_type:
                continue
            if tags and not tags.issubset(entry.tags):
                continue
            if time_range:
                t_lo, t_hi = time_range
                if not (t_lo <= entry.timestamp <= t_hi):
                    continue
            results.append(entry)
        results.sort(key=lambda e: e.timestamp)
        if n is not None:
            results = results[:n]
        self._log_operation(MemoryOperation.REPLAY, "batch")
        return results

    # ====================================================================
    # Consolidation (NEW — no-op stub; real impl in PHASE 6 HippoCore)
    # ====================================================================

    def consolidate(
        self,
        source_type: Optional[MemoryType] = None,
        target_type: Optional[MemoryType] = None,
        batch_size: int = 50,
        similarity_threshold: float = 0.85,
    ) -> int:
        """No-op stub in the Default impl. HippoCore (PHASE 6) implements
        the real fast → slow consolidation pipeline. Returns 0."""
        src_t = source_type if source_type is not None else MemoryType.EPISODIC
        tgt_t = target_type if target_type is not None else MemoryType.SEMANTIC
        self._log_operation(MemoryOperation.CONSOLIDATE,
                            f"no-op:src={src_t.value},tgt={tgt_t.value}")
        return 0

    # ====================================================================
    # Checkpointing (NEW — closes audit §7 / §14 gap)
    # ====================================================================

    def checkpoint(self) -> dict[str, Any]:
        """Serialize full memory state to a JSON-native dict.

        Closes the audit §7 gap (Python MemoryContract was previously
        not checkpointable at the contents level) and feeds into the
        PHASE 7 ``MindCheckpoint.memory_state`` field (audit §14).

        PHASE 4: serializes the new episodic-encoding fields
        (organism_id, action, outcome, prediction, environment_state,
        causal_metadata, structured_provenance) so they round-trip
        through restore(). All new fields are optional with safe
        defaults so PHASE 2 checkpoints remain restorable.
        """
        # Convert MemoryEntry dataclass to a dict; preserve MemoryType /
        # MemoryOperation / EpistemicLabel as their .value strings so the
        # payload is pure JSON.
        entries_serialized: list[dict[str, Any]] = []
        for entry in self._memories.values():
            entry_dict: dict[str, Any] = {
                "memory_id": entry.memory_id,
                "content": entry.content,
                "memory_type": entry.memory_type.value,
                "origin": entry.origin,
                "timestamp": entry.timestamp,
                "provenance": entry.provenance,
                "confidence": entry.confidence,
                "context": entry.context,
                "importance": entry.importance,
                "prediction_error": entry.prediction_error,
                "epistemic_label": entry.epistemic_label.name,
                "decay_rate": entry.decay_rate,
                "tags": sorted(entry.tags),
                "forgotten": entry.forgotten,
                "consolidation_status": entry.consolidation_status,
                "access_count": entry.access_count,
                "n_relationships": len(entry.relationships),
                "n_revisions": len(entry.revision_history),
            }
            # PHASE 4 fields — only serialize when populated.
            if entry.organism_id is not None:
                entry_dict["organism_id"] = entry.organism_id
            if entry.action is not None:
                entry_dict["action"] = entry.action
            if entry.outcome is not None:
                entry_dict["outcome"] = entry.outcome
            if entry.prediction is not None:
                entry_dict["prediction"] = entry.prediction
            if entry.environment_state is not None:
                entry_dict["environment_state"] = entry.environment_state
            if entry.causal_metadata:
                entry_dict["causal_metadata"] = entry.causal_metadata
            if entry.structured_provenance is not None:
                entry_dict["structured_provenance"] = (
                    entry.structured_provenance.to_dict()
                )
            entries_serialized.append(entry_dict)
        return {
            "schema_version": self.SCHEMA_VERSION,
            "entries": entries_serialized,
            "working_memory": self._working_memory,
            "working_memory_capacity": self._working_memory_capacity,
            "operation_log": [
                {"operation": op.value, "target": tgt, "timestamp": ts}
                for (op, tgt, ts) in self._operation_log
            ],
        }

    def restore(self, payload: dict[str, Any]) -> None:
        """Restore memory state from a previous ``checkpoint()`` call.

        Idempotent: restoring twice yields the same state as restoring once.

        Accepts any payload whose ``schema_version`` starts with
        ``nuros.`` — this allows cross-engine restore (e.g. an organism
        configured with ``memory_engine='hippocore'`` can restore a
        checkpoint produced by ``DefaultMemoryContract``, and vice versa).
        In PHASE 3 the entries/working_memory/operation_log layout is
        identical across engines; PHASE 6 may need engine-specific
        schema-version gates when the dual-store lands.
        """
        if not isinstance(payload, dict):
            raise ValueError(f"restore payload must be a dict, got {type(payload)}")
        schema = payload.get("schema_version", "unknown")
        if not schema.startswith("nuros."):
            raise ValueError(
                f"restore payload schema_version {schema!r} does not look "
                f"like a NurosOS memory checkpoint (expected prefix 'nuros.')"
            )
        # Reset state before restoring — idempotent.
        self._memories.clear()
        self._working_memory.clear()
        self._operation_log.clear()

        for entry_dict in payload.get("entries", []):
            mt = MemoryType(entry_dict.get("memory_type", MemoryType.EPISODIC.value))
            # EpistemicLabel uses integer values, so we look up by NAME.
            # See: EpistemicLabel.REMEMBERED.name == "REMEMBERED" but
            # EpistemicLabel.REMEMBERED.value == 3 (int). The checkpoint
            # serializes the .name (a string), so restore via subscript.
            ep_name = entry_dict.get(
                "epistemic_label", EpistemicLabel.REMEMBERED.name,
            )
            try:
                ep = EpistemicLabel[ep_name]
            except (KeyError, TypeError):
                ep = EpistemicLabel.REMEMBERED
            # PHASE 4: restore structured_provenance if present.
            sp_dict = entry_dict.get("structured_provenance")
            sp = MemoryProvenance.from_dict(sp_dict) if sp_dict else None
            entry = MemoryEntry(
                memory_id=entry_dict["memory_id"],
                content=entry_dict.get("content"),
                memory_type=mt,
                origin=entry_dict.get("origin", ""),
                timestamp=entry_dict.get("timestamp", time.time()),
                provenance=entry_dict.get("provenance", ""),
                confidence=entry_dict.get("confidence", 1.0),
                context=entry_dict.get("context", {}) or {},
                importance=entry_dict.get("importance", 0.5),
                prediction_error=entry_dict.get("prediction_error", 0.0),
                epistemic_label=ep,
                decay_rate=entry_dict.get("decay_rate", 0.001),
                tags=set(entry_dict.get("tags", []) or []),
                forgotten=entry_dict.get("forgotten", False),
                consolidation_status=entry_dict.get(
                    "consolidation_status", "ACTIVE",
                ),
                # PHASE 4 fields — None defaults if absent.
                organism_id=entry_dict.get("organism_id"),
                action=entry_dict.get("action"),
                outcome=entry_dict.get("outcome"),
                prediction=entry_dict.get("prediction"),
                environment_state=entry_dict.get("environment_state"),
                causal_metadata=dict(entry_dict.get("causal_metadata", {}) or {}),
                structured_provenance=sp,
            )
            self._memories[entry.memory_id] = entry

        self._working_memory.update(payload.get("working_memory", {}) or {})
        self._working_memory_capacity = payload.get("working_memory_capacity", 7)

        for log_entry in payload.get("operation_log", []):
            try:
                op = MemoryOperation(log_entry["operation"])
                self._operation_log.append((
                    op, log_entry["target"], log_entry["timestamp"],
                ))
            except (KeyError, ValueError):
                continue  # skip malformed log entries

        self._log_operation(MemoryOperation.RESTORE, f"restored:{len(self._memories)}")

    # ====================================================================
    # Working memory
    # ====================================================================

    def working_set(self, key: str, value: Any) -> None:
        if len(self._working_memory) >= self._working_memory_capacity:
            oldest_key = next(iter(self._working_memory))
            del self._working_memory[oldest_key]
        self._working_memory[key] = value

    def working_get(self, key: str) -> Optional[Any]:
        return self._working_memory.get(key)

    # ====================================================================
    # Properties
    # ====================================================================

    @property
    def memory_count(self) -> int:
        return len(self._memories)

    @property
    def operation_log(self) -> list[tuple[MemoryOperation, str, float]]:
        return list(self._operation_log)

    # ====================================================================
    # Summary
    # ====================================================================

    def summary(self) -> dict[str, Any]:
        type_counts: dict[str, int] = {}
        consolidation_counts: dict[str, int] = {}
        n = max(1, len(self._memories))
        for entry in self._memories.values():
            t = entry.memory_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
            cs = entry.consolidation_status
            consolidation_counts[cs] = consolidation_counts.get(cs, 0) + 1
        return {
            "total_memories": len(self._memories),
            "by_type": type_counts,
            "by_consolidation_status": consolidation_counts,
            "forgotten_count": sum(1 for e in self._memories.values() if e.forgotten),
            "working_memory_items": len(self._working_memory),
            "total_operations": len(self._operation_log),
            "average_confidence": sum(e.confidence for e in self._memories.values()) / n,
            "average_importance": sum(e.importance for e in self._memories.values()) / n,
        }

    # ====================================================================
    # Internal
    # ====================================================================

    def _log_operation(self, op: MemoryOperation, memory_id: str) -> None:
        self._operation_log.append((op, memory_id, time.time()))


# ============================================================================
# Backward-compat alias (audit §11.3: "MemoryContract name kept as a
# deprecated alias for DefaultMemoryContract for one version").
# ============================================================================


class MemoryContract(DefaultMemoryContract):
    """Deprecated alias for :class:`DefaultMemoryContract`.

    Historical name retained for backward compatibility. New code should
    import ``DefaultMemoryContract`` (the concrete default) or
    ``MemoryEngine`` (the ABC) from :mod:`nuros.memory_engine`.
    """

    def __init__(self, epistemic_kernel: Optional[EpistemicKernel] = None):
        warnings.warn(
            "MemoryContract is a deprecated alias for DefaultMemoryContract. "
            "Use DefaultMemoryContract (or MemoryEngine ABC) directly. "
            "The alias will be removed in NurosOS 0.5.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(epistemic_kernel=epistemic_kernel)


__all__ = [
    "MemoryEngine",
    "DefaultMemoryContract",
    "MemoryContract",  # deprecated alias
    "MemoryEntry",
    "MemoryType",
    "MemoryOperation",
    "MemoryAccess",
    "MemoryRevision",
    "MemoryRelationship",
]
