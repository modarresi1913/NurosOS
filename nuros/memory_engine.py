"""
MemoryEngine — pluggable memory backend for the NurosOS Mind Contract Layer.

PHASE 2 of the HippoCore integration (master prompt §33).

This module defines the *contract*; concrete implementations live in:
  - ``nuros/memory.py`` (``DefaultMemoryContract`` — the current behaviour,
    retained for full backward compatibility).
  - ``nuros/hippocore/memory_engine.py`` (``HippoCoreMemory`` — episodic
    encoding + pattern separation + replay + consolidation + reconsolidation
    + forgetting; lands in PHASE 3+).

Design rules (from docs/HIPPOCORE_INTEGRATION_AUDIT.md §11.1):

  1. All implementations MUST return ``MemoryEntry`` instances from
     ``encode``/``retrieve``/``replay`` so existing callers
     (``Organism``, ``Organism0..5``, ``benchmark_suite``,
     ``decay_experiment``) keep working unchanged.

  2. The invariant at ``mind/memory/SPEC.md:45`` — "No memory is permanently
     deleted" — is restored: ``forget(hard=False)`` (the new default)
     SOFT-forgets; only ``hard=True`` permanently removes.

  3. ``consolidate()``, ``checkpoint()``, ``restore()``, ``inspect()`` are
     NEW first-class operations exposed by the contract so HippoCore can
     plug in without leaking its internals to the organism layer.

  4. ``MemoryContract`` (the historical name) is kept as a deprecated alias
     of ``DefaultMemoryContract`` for one minor version. A
     ``DeprecationWarning`` is emitted on construction via ``__init_subclass__``.

Scientific status: [IMPLEMENTED] — abstract contract only.
                   [PROPOSED]      — HippoCoreMemory concrete impl (PHASE 3+).

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # avoid circular import with nuros.memory at runtime
    from nuros.epistemic import EpistemicKernel, EpistemicLabel
    from nuros.memory import MemoryEntry, MemoryOperation, MemoryType


class MemoryEngine(ABC):
    """Pluggable memory backend.

    The contract is intentionally close to the historical
    ``MemoryContract`` (so existing callers keep working) but adds the
    operations HippoCore needs:

      - ``encode``       (alias for ``remember`` — kept for symmetric naming)
      - ``retrieve``     (substring filter by default; HippoCore: k-NN)
      - ``retrieve_by_id``
      - ``associate``    (already bidirectional; DUPLICATED, not reimplemented)
      - ``reconsolidate`` (now accepts optional ``prediction_error``)
      - ``replay``       (NEW: ``n`` cap + ``generative`` flag)
      - ``consolidate``  (NEW: fast → slow pipeline entry point)
      - ``forget``       (FIX: ``hard=False`` soft-forgets by default)
      - ``checkpoint``   (NEW: serialize full state)
      - ``restore``      (NEW: restore from a previous checkpoint)
      - ``inspect``      (SUPERSEDES ``reflect`` — see audit §10.2 spec drift)
      - ``working_set`` / ``working_get`` / ``summary`` / ``memory_count`` /
        ``operation_log``  (backward-compat surface)

    Every method that returns ``MemoryEntry`` MUST return concrete
    ``MemoryEntry`` instances (not proxies) so that downstream consumers
    (``Organism.snapshot()``, ``MindDiff``, ``benchmark_suite``) can read
    ``memory_id``, ``content``, ``memory_type``, ``importance``,
    ``current_strength`` etc. without dependency injection.
    """

    # ====================================================================
    # Encoding / retrieval
    # ====================================================================

    @abstractmethod
    def encode(
        self,
        content: Any,
        memory_type: Optional["MemoryType"] = None,
        origin: str = "",
        provenance: str = "",
        confidence: float = 1.0,
        importance: float = 0.5,
        context: Optional[dict[str, Any]] = None,
        tags: Optional[set[str]] = None,
        epistemic_label: Optional["EpistemicLabel"] = None,
    ) -> "MemoryEntry":
        """Encode a new memory.

        ``memory_type=None`` resolves to ``MemoryType.EPISODIC`` at impl time.
        ``epistemic_label=None`` resolves to ``EpistemicLabel.REMEMBERED``,
        except for ``MemoryType.COUNTERFACTUAL`` which MUST be
        ``EpistemicLabel.IMAGINED`` (matches ``nuros/memory.py:146-150``).

        Implementations SHOULD perform pattern separation: similar content
        must NOT silently overwrite existing memories. The contract is to
        return a NEW ``MemoryEntry`` with a fresh ``memory_id``, but
        implementations MAY register an association with near-duplicate
        existing entries via ``associate()``.
        """

    @abstractmethod
    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional["MemoryType"] = None,
        min_confidence: float = 0.0,
        min_importance: float = 0.0,
        tags: Optional[set[str]] = None,
        limit: int = 10,
    ) -> list["MemoryEntry"]:
        """Retrieve memories matching the query, sorted by
        ``MemoryEntry.current_strength`` descending.

        Implementations MAY use substring match (Default) or
        content-embedding k-NN (HippoCore). The substring contract on
        ``entry.content`` (``nuros/memory.py:181``) is preserved as a
        fallback: HippoCore implementations MUST also support ``query`` as
        a substring filter when ``query is not None``.
        """

    @abstractmethod
    def retrieve_by_id(self, memory_id: str) -> Optional["MemoryEntry"]:
        """Direct lookup by ``memory_id``."""

    # ====================================================================
    # Association
    # ====================================================================

    @abstractmethod
    def associate(
        self,
        memory_id_a: str,
        memory_id_b: str,
        relation_type: str = "semantic",
        strength: float = 1.0,
        bidirectional: bool = True,
    ) -> bool:
        """Create an association edge between two memories.
        Returns ``False`` if either id is unknown."""

    # ====================================================================
    # Reconsolidation
    # ====================================================================

    @abstractmethod
    def reconsolidate(
        self,
        memory_id: str,
        reward: float = 0.0,
        prediction_error: Optional[float] = None,
    ) -> Optional["MemoryEntry"]:
        """Re-strengthen (``reward > 0``) or weaken (``reward < 0``) a
        memory after reactivation. ``reward > 0`` raises
        ``importance``/``confidence`` and lowers ``decay_rate``;
        ``reward < 0`` lowers ``confidence`` and raises ``decay_rate``
        (matches ``nuros/memory.py:257-263``).

        NEW (HippoCore): if ``prediction_error`` is provided, modulate the
        update magnitude by the error signal — this exploits the unused
        ``MemoryEntry.prediction_error`` field (``nuros/memory.py:87``).
        """

    # ====================================================================
    # Replay (developmental mechanism, not just debugging)
    # ====================================================================

    @abstractmethod
    def replay(
        self,
        memory_type: Optional["MemoryType"] = None,
        tags: Optional[set[str]] = None,
        time_range: Optional[tuple[float, float]] = None,
        n: Optional[int] = None,
        generative: bool = False,
    ) -> list["MemoryEntry"]:
        """Return a sequence of memories for replay, sorted by timestamp
        ascending (matches ``nuros/memory.py:298``).

        ``generative=False`` (Default): returns raw stored memories
        filtered by ``memory_type``/``tags``/``time_range``.

        ``generative=True`` (HippoCore): returns RECONSTRUCTED memories
        re-encoded from compressed traces. The returned ``MemoryEntry``s
        have fresh ``memory_id``s and ``EpistemicLabel.REMEMBERED``.
        Implementations MAY internally call ``reconsolidate()`` on each
        replayed source memory (the sleep-consolidation pattern from
        ``nuros/organism.py:244-247``).

        ``n`` (NEW, optional): cap the number of returned memories. The
        current ``limit`` parameter on ``retrieve()`` is NOT used by
        ``replay()``; this fills the gap.
        """

    # ====================================================================
    # Consolidation (NEW — fast → slow pipeline entry point)
    # ====================================================================

    @abstractmethod
    def consolidate(
        self,
        source_type: Optional["MemoryType"] = None,
        target_type: Optional["MemoryType"] = None,
        batch_size: int = 50,
        similarity_threshold: float = 0.85,
    ) -> int:
        """NEW OPERATION (not in historical ``MemoryContract``). Run one
        pass of fast → slow consolidation:

          1. Select up to ``batch_size`` memories of ``source_type``
             (default ``EPISODIC``).
          2. Cluster them by content similarity (implementation-defined).
          3. For each cluster, derive one ``target_type`` memory
             (default ``SEMANTIC``) whose ``content`` is a summary and
             whose ``relationships`` link back to the source memories.
          4. Lower the ``importance`` of consolidated sources (mark them
             as consolidated-but-not-forgotten).

        Returns the number of ``target_type`` memories created.

        This operation is the entry point for HippoCore's
        fast-episodic → slow-semantic pipeline — see audit §2 / §4.

        Default impl returns 0 (no-op). HippoCore impl (PHASE 6) does
        the real work.
        """

    # ====================================================================
    # Forgetting (FIX: soft-delete is now the default)
    # ====================================================================

    @abstractmethod
    def forget(
        self,
        memory_id: str,
        justification: str = "",
        hard: bool = False,
    ) -> bool:
        """Mark a memory as forgotten.

        ``hard=False`` (NEW default, FIX for the spec violation at
        ``nuros/memory.py:279``): the memory is SOFT-forgotten — kept in
        store, ``epistemic_label`` downgraded, ``importance`` set to 0,
        retrievable only with an explicit ``min_importance=0.0`` query.
        This satisfies the invariant at ``mind/memory/SPEC.md:45``:
        "No memory is permanently deleted".

        ``hard=True`` (legacy behaviour): the memory is permanently
        deleted (matches ``nuros/memory.py:279``).
        """

    # ====================================================================
    # Checkpointing (NEW — closes the audit §7 / §14 gap)
    # ====================================================================

    @abstractmethod
    def checkpoint(self) -> dict[str, Any]:
        """Serialize the full memory state to a JSON-native dict.

        MUST round-trip via ``restore()``. The payload schema is
        implementation-defined but MUST include at minimum:
          - ``schema_version``: str
          - ``entries``: list[dict] (each serializing a MemoryEntry)
          - ``working_memory``: dict[str, Any]
          - ``operation_log``: list (serialized tuples)

        This closes the gap noted in audit §7 (Python MemoryContract is
        currently not checkpointable at the contents level — see also
        audit §14 for the broader ``MindCheckpoint`` schema gap).
        """

    @abstractmethod
    def restore(self, payload: dict[str, Any]) -> None:
        """Restore memory state from a previous ``checkpoint()`` call.

        Implementations MUST be idempotent: restoring twice yields the
        same state as restoring once. Implementations MAY emit a warning
        if the schema_version does not match the current schema.
        """

    # ====================================================================
    # Inspection (SUPERSEDES reflect — fixes audit §10.2 spec drift)
    # ====================================================================

    @abstractmethod
    def inspect(self, memory_id: str) -> Optional[dict[str, Any]]:
        """Return a dict of human-readable metadata about a memory.

        SUPERSEDES ``MemoryContract.reflect(memory_id)`` (the impl at
        ``nuros/memory.py:216``) which has a signature that DIVERGES from
        the documented spec at ``mind/memory/SPEC.md:17`` (which says
        ``reflect(query) -> List[MemoryEntry]``).

        ``inspect`` is the new name; ``reflect`` is kept on
        ``DefaultMemoryContract`` for backward compatibility (it now
        delegates to ``inspect``).
        """

    # ====================================================================
    # Public iterator (NEW — used by experiments/memory/decay_experiment.py)
    # ====================================================================

    @abstractmethod
    def iter_all(self) -> "list[MemoryEntry]":
        """Return ALL stored memories (including soft-forgotten ones) in
        insertion order.

        Used by ``experiments/memory/decay_experiment.py`` (which
        previously accessed the private ``memory._store`` attribute —
        see audit Appendix B.2) and by ``benchmarks/memory/`` benchmarks
        (PHASE 9).

        Default impl: returns ``list(self._memories.values())``.
        """

    # ====================================================================
    # Backward-compat properties (kept verbatim from nuros/memory.py)
    # ====================================================================

    @property
    @abstractmethod
    def memory_count(self) -> int:
        """Number of stored memories (matches ``nuros/memory.py:311-313``)."""

    @property
    @abstractmethod
    def operation_log(self) -> "list[tuple[MemoryOperation, str, float]]":
        """Append-only log of (operation, memory_id, timestamp) tuples
        (matches ``nuros/memory.py:315-317``)."""

    # ====================================================================
    # Working memory (kept for compat — audit §1.1)
    # ====================================================================

    @abstractmethod
    def working_set(self, key: str, value: Any) -> None:
        """Insert into the fixed-capacity working-memory buffer
        (matches ``nuros/memory.py:302-306``, capacity 7)."""

    @abstractmethod
    def working_get(self, key: str) -> Optional[Any]:
        """Lookup in the working-memory buffer (matches
        ``nuros/memory.py:308-309``)."""

    @abstractmethod
    def summary(self) -> dict[str, Any]:
        """Summary statistics (matches ``nuros/memory.py:322-335``)."""
