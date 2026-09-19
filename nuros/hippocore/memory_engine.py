"""
HippoCoreMemory — PHASE 3 adapter scaffold.

In PHASE 3, ``HippoCoreMemory`` is a thin wrapper around
``DefaultMemoryContract``. It produces byte-identical behavior to
the default engine — the point is to exercise the integration surface
(``Organism``, ``OrganismConfig``, tests, benchmarks) against a
non-default ``MemoryEngine`` class.

PHASE 4 will override ``encode()`` to perform real episodic encoding
with pattern separation. PHASE 5 will override ``replay()`` to support
policy-driven generative replay. PHASE 6 will override ``consolidate()``
to run the fast → slow pipeline.

Every override will preserve the ``MemoryEngine`` contract so callers
(``Organism``, ``Organism0..5``, ``benchmark_suite``,
``decay_experiment``) keep working unchanged.

Implementation Status: IMPLEMENTED (PHASE 3 — adapter scaffold)
"""

from __future__ import annotations

from typing import Any, Optional

from nuros.epistemic import EpistemicKernel
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType
from nuros.memory_engine import MemoryEngine


class HippoCoreMemoryConfig:
    """Configuration for ``HippoCoreMemory``.

    PHASE 3: no knobs (the adapter is behaviour-identical to the
    default). PHASE 4+ will add:
      - pattern_separation_threshold: float  (PHASE 4)
      - replay_policy: str                 (PHASE 5: 'recent' |
                                              'importance_weighted' |
                                              'novelty_weighted' |
                                              'prediction_error_weighted' |
                                              'random')
      - max_episodes: Optional[int]        (PHASE 6 memory budget)
      - max_memory_bytes: Optional[int]    (PHASE 6 memory budget)
      - consolidation_batch_size: int     (PHASE 6)
      - consolidation_similarity_threshold: float  (PHASE 6)
    """

    def __init__(self) -> None:
        # PHASE 4+ fields land here. For PHASE 3, no knobs.
        pass

    def to_dict(self) -> dict[str, Any]:
        return {"phase": 3, "knobs": {}}


class HippoCoreMemory(MemoryEngine):
    """PHASE 3 adapter scaffold.

    Delegates every operation to an internal ``DefaultMemoryContract``
    instance. PHASE 4 will replace the delegated methods with real
    HippoCore implementations (episodic encoding + pattern separation);
    PHASE 5 will add policy-driven replay; PHASE 6 will add fast→slow
    consolidation. The ABC contract stays stable across all phases so
    no caller breaks.
    """

    SCHEMA_VERSION = "nuros.hippocore.HippoCoreMemory.v1.phase3"

    def __init__(
        self,
        config: Optional[HippoCoreMemoryConfig] = None,
        epistemic_kernel: Optional[EpistemicKernel] = None,
    ) -> None:
        self._config = config or HippoCoreMemoryConfig()
        # In PHASE 3, we delegate to DefaultMemoryContract. PHASE 4 will
        # replace this with a real dual-store (fast episodic + slow
        # consolidated) and override encode/retrieve/etc.
        self._inner = DefaultMemoryContract(epistemic_kernel=epistemic_kernel)

    # ====================================================================
    # Encoding / retrieval — PHASE 4 will override with real episodic
    # encoding + pattern separation.
    # ====================================================================

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
        epistemic_label: Optional[Any] = None,
    ) -> MemoryEntry:
        """PHASE 3: direct delegation to DefaultMemoryContract.
        PHASE 4: real episodic encoding with pattern separation —
        similar content will NOT silently overwrite existing memories;
        near-duplicates will be associated via ``associate()`` rather
        than collapsed."""
        return self._inner.encode(
            content=content, memory_type=memory_type, origin=origin,
            provenance=provenance, confidence=confidence, importance=importance,
            context=context, tags=tags, epistemic_label=epistemic_label,
        )

    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        min_confidence: float = 0.0,
        min_importance: float = 0.0,
        tags: Optional[set[str]] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """PHASE 3: substring filter (delegated).
        PHASE 4: similarity-based k-NN retrieval + pattern completion."""
        return self._inner.retrieve(
            query=query, memory_type=memory_type,
            min_confidence=min_confidence, min_importance=min_importance,
            tags=tags, limit=limit,
        )

    def retrieve_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        return self._inner.retrieve_by_id(memory_id)

    # ====================================================================
    # Association — already DUPLICATED in DefaultMemoryContract (audit §9).
    # ====================================================================

    def associate(
        self, memory_id_a: str, memory_id_b: str,
        relation_type: str = "semantic", strength: float = 1.0,
        bidirectional: bool = True,
    ) -> bool:
        return self._inner.associate(
            memory_id_a, memory_id_b, relation_type, strength, bidirectional,
        )

    # ====================================================================
    # Reconsolidation — accepts optional prediction_error (PHASE 2 surface).
    # PHASE 6 will add real reconsolidation with versioned state.
    # ====================================================================

    def reconsolidate(
        self, memory_id: str, reward: float = 0.0,
        prediction_error: Optional[float] = None,
    ) -> Optional[MemoryEntry]:
        return self._inner.reconsolidate(
            memory_id, reward=reward, prediction_error=prediction_error,
        )

    # ====================================================================
    # Replay — PHASE 5 will override with policy-driven generative replay.
    # ====================================================================

    def replay(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[set[str]] = None,
        time_range: Optional[tuple[float, float]] = None,
        n: Optional[int] = None,
        generative: bool = False,
    ) -> list[MemoryEntry]:
        """PHASE 3: delegated (generative=True is a no-op).
        PHASE 5: if generative=True, return RECONSTRUCTED memories
        re-encoded from compressed traces with fresh memory_ids."""
        return self._inner.replay(
            memory_type=memory_type, tags=tags, time_range=time_range,
            n=n, generative=generative,
        )

    # ====================================================================
    # Consolidation — PHASE 6 will override with the real fast→slow pipeline.
    # ====================================================================

    def consolidate(
        self,
        source_type: Optional[MemoryType] = None,
        target_type: Optional[MemoryType] = None,
        batch_size: int = 50,
        similarity_threshold: float = 0.85,
    ) -> int:
        """PHASE 3: no-op stub (returns 0).
        PHASE 6: real fast→slow consolidation pipeline — clusters
        source memories by content similarity, derives target memories
        with summaries, lowers source importance."""
        return self._inner.consolidate(
            source_type=source_type, target_type=target_type,
            batch_size=batch_size, similarity_threshold=similarity_threshold,
        )

    # ====================================================================
    # Forgetting — uses the same soft-delete semantics as DefaultMemoryContract.
    # PHASE 6 will add a more sophisticated forgetting lifecycle (audit §17).
    # ====================================================================

    def forget(
        self, memory_id: str, justification: str = "", hard: bool = False,
    ) -> bool:
        return self._inner.forget(memory_id, justification, hard)

    # ====================================================================
    # Checkpoint / restore — same schema as DefaultMemoryContract in PHASE 3.
    # PHASE 6 will extend the schema to carry the dual-store state.
    # ====================================================================

    def checkpoint(self) -> dict[str, Any]:
        """PHASE 3: delegates to DefaultMemoryContract.checkpoint().
        The schema_version is overridden to indicate this came from
        HippoCoreMemory (PHASE 3 adapter) so that downstream consumers
        (e.g. MindCheckpoint.memory_state in PHASE 7) can distinguish."""
        payload = self._inner.checkpoint()
        # Mark the payload as coming from HippoCoreMemory (PHASE 3 adapter).
        payload["schema_version"] = self.SCHEMA_VERSION
        payload["engine"] = "hippocore"
        payload["engine_phase"] = 3
        return payload

    def restore(self, payload: dict[str, Any]) -> None:
        """PHASE 3: delegates to DefaultMemoryContract.restore().
        Accepts both HippoCoreMemory and DefaultMemoryContract payloads
        (since PHASE 3 is a thin wrapper)."""
        if not isinstance(payload, dict):
            raise ValueError(
                f"HippoCoreMemory.restore payload must be a dict, got {type(payload)}"
            )
        schema = payload.get("schema_version", "unknown")
        if not (schema.startswith("nuros.memory.") or schema.startswith("nuros.hippocore.")):
            raise ValueError(
                f"HippoCoreMemory.restore payload schema_version {schema!r} "
                f"does not look like a NurosOS memory checkpoint"
            )
        # Delegate the actual restore work to DefaultMemoryContract, which
        # understands both schema versions (the entries/working_memory/
        # operation_log layout is identical in PHASE 3).
        self._inner.restore(payload)

    # ====================================================================
    # Inspection
    # ====================================================================

    def inspect(self, memory_id: str) -> Optional[dict[str, Any]]:
        meta = self._inner.inspect(memory_id)
        if meta is not None:
            meta["engine"] = "hippocore"
            meta["engine_phase"] = 3
        return meta

    def iter_all(self) -> list[MemoryEntry]:
        return self._inner.iter_all()

    # ====================================================================
    # Backward-compat properties / working memory / summary
    # ====================================================================

    @property
    def memory_count(self) -> int:
        return self._inner.memory_count

    @property
    def operation_log(self):
        return self._inner.operation_log

    def working_set(self, key: str, value: Any) -> None:
        self._inner.working_set(key, value)

    def working_get(self, key: str) -> Optional[Any]:
        return self._inner.working_get(key)

    def summary(self) -> dict[str, Any]:
        s = self._inner.summary()
        s["engine"] = "hippocore"
        s["engine_phase"] = 3
        s["config"] = self._config.to_dict()
        return s

    # ====================================================================
    # Convenience: direct access to the inner engine (for tests + PHASE 9
    # benchmarks that need to compare HippoCore vs Default side-by-side).
    # ====================================================================

    @property
    def inner(self) -> DefaultMemoryContract:
        """Direct access to the wrapped DefaultMemoryContract instance.
        Used by PHASE 9 benchmarks to compare HippoCore vs Default
        behavior on identical inputs. NOT part of the MemoryEngine ABC
        — callers should prefer the ABC surface."""
        return self._inner
