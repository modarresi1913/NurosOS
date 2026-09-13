"""
Memory Contract — Living, Evolving Cognitive Memory Subsystem.

Memory is NOT simple vector storage. It is a living, evolving
cognitive subsystem with multiple types, provenance, auditable
revision, and epistemic labeling.

Memory Types: Episodic, Semantic, Procedural, Working, Counterfactual
Operations: remember, retrieve, associate, reflect, revise,
           reconsolidate, forget, replay

IMPORTANT: These are computational abstractions, NOT biologically
equivalent to human memory.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from nuros.epistemic import EpistemicLabel, EpistemicKernel


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
    """A single memory entry with full metadata and provenance."""
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: Any = None
    memory_type: MemoryType = MemoryType.EPISODIC
    origin: str = ""
    timestamp: float = field(default_factory=time.time)
    provenance: str = ""
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
        access_boost = min(1.0, self.access_count * 0.05)
        age = time.time() - self.timestamp
        decay = math.exp(-self.decay_rate * age)
        return self.importance * self.confidence * decay * (1.0 + access_boost)

    def record_access(self, operation: MemoryOperation, accessor: str = "") -> None:
        self.access_history.append(MemoryAccess(
            timestamp=time.time(), operation=operation, accessor=accessor,
        ))


class MemoryContract:
    """
    The Memory Contract — Interface for the Memory subsystem.

    Implements the Memory portion of the Mind Contract Layer (MCL).
    Living, evolving memory with: multiple types, content-addressable
    retrieval, auditable revision, epistemic labeling, decay,
    reconsolidation, and association tracking.
    """

    def __init__(self, epistemic_kernel: Optional[EpistemicKernel] = None):
        self._memories: dict[str, MemoryEntry] = {}
        self._epistemic = epistemic_kernel or EpistemicKernel()
        self._operation_log: list[tuple[MemoryOperation, str, float]] = []
        self._working_memory: dict[str, Any] = {}
        self._working_memory_capacity: int = 7

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
        epistemic_label = (
            EpistemicLabel.IMAGINED
            if memory_type == MemoryType.COUNTERFACTUAL
            else EpistemicLabel.REMEMBERED
        )
        entry = MemoryEntry(
            content=content, memory_type=memory_type, origin=origin,
            provenance=provenance, confidence=confidence, importance=importance,
            epistemic_label=epistemic_label, context=context or {},
            tags=tags or set(),
        )
        self._memories[entry.memory_id] = entry
        self._log_operation(MemoryOperation.REMEMBER, entry.memory_id)
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
        results = []
        for entry in self._memories.values():
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

    def reflect(self, memory_id: str) -> Optional[dict]:
        entry = self._memories.get(memory_id)
        if not entry:
            return None
        entry.record_access(MemoryOperation.REFLECT)
        self._log_operation(MemoryOperation.REFLECT, memory_id)
        return {
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
        }

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

    def reconsolidate(self, memory_id: str, reward: float = 0.0) -> Optional[MemoryEntry]:
        entry = self._memories.get(memory_id)
        if not entry:
            return None
        if reward > 0:
            entry.importance = min(1.0, entry.importance + reward * 0.1)
            entry.confidence = min(1.0, entry.confidence + reward * 0.05)
            entry.decay_rate *= 0.9
        elif reward < 0:
            entry.confidence = max(0.0, entry.confidence + reward * 0.05)
            entry.decay_rate *= 1.1
        entry.record_access(MemoryOperation.RECONSOLIDATE)
        self._log_operation(MemoryOperation.RECONSOLIDATE, memory_id)
        return entry

    def forget(self, memory_id: str, justification: str = "") -> bool:
        if memory_id not in self._memories:
            return False
        entry = self._memories[memory_id]
        entry.record_access(MemoryOperation.FORGET)
        self._log_operation(MemoryOperation.FORGET, memory_id)
        self._operation_log.append((
            MemoryOperation.FORGET,
            f"DELETED:{memory_id}:type={entry.memory_type.value}:justification={justification}",
            time.time(),
        ))
        del self._memories[memory_id]
        return True

    def replay(
        self, memory_type: Optional[MemoryType] = None,
        tags: Optional[set[str]] = None,
        time_range: Optional[tuple[float, float]] = None,
    ) -> list[MemoryEntry]:
        results = []
        for entry in self._memories.values():
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
        self._log_operation(MemoryOperation.REPLAY, "batch")
        return results

    def working_set(self, key: str, value: Any) -> None:
        if len(self._working_memory) >= self._working_memory_capacity:
            oldest_key = next(iter(self._working_memory))
            del self._working_memory[oldest_key]
        self._working_memory[key] = value

    def working_get(self, key: str) -> Optional[Any]:
        return self._working_memory.get(key)

    @property
    def memory_count(self) -> int:
        return len(self._memories)

    @property
    def operation_log(self) -> list[tuple[MemoryOperation, str, float]]:
        return list(self._operation_log)

    def _log_operation(self, op: MemoryOperation, memory_id: str) -> None:
        self._operation_log.append((op, memory_id, time.time()))

    def summary(self) -> dict:
        type_counts = {}
        for entry in self._memories.values():
            t = entry.memory_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        n = max(1, len(self._memories))
        return {
            "total_memories": len(self._memories),
            "by_type": type_counts,
            "working_memory_items": len(self._working_memory),
            "total_operations": len(self._operation_log),
            "average_confidence": sum(e.confidence for e in self._memories.values()) / n,
            "average_importance": sum(e.importance for e in self._memories.values()) / n,
        }
