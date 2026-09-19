"""
HippoCoreMemory — PHASE 3 adapter scaffold + PHASE 4 episodic encoding.

PHASE 3 (audit §21): thin wrapper around DefaultMemoryContract.
PHASE 4 (master prompt §6, §7): overrides encode() to populate the new
episodic-encoding fields (organism_id, action, outcome, prediction,
environment_state, causal_metadata) and a structured MemoryProvenance
record. This is the FIRST intentional divergence from
DefaultMemoryContract — the golden-file equivalence tests in
``test_hippocore_smoke.py::TestHippoCorePhase3Equivalence`` will still
pass for encode() because the equivalence assertion only checks
content/type/importance/confidence/epistemic_label/forgotten/
consolidation_status/tags (NOT the new PHASE 4 fields).

PHASE 5 will override replay() to support policy-driven generative
replay. PHASE 6 will override consolidate() to run the real
fast→slow pipeline.

The MemoryEngine ABC contract is preserved across all phases so no
caller (Organism, Organism0..5, benchmark_suite, decay_experiment)
breaks.

Implementation Status: IMPLEMENTED (PHASE 3 + PHASE 4 episodic encoding).
"""

from __future__ import annotations

import time
from typing import Any, Optional

from nuros.epistemic import EpistemicKernel, EpistemicLabel
from nuros.memory import DefaultMemoryContract, MemoryEntry, MemoryType
from nuros.memory_engine import MemoryEngine
from nuros.memory_provenance import MemoryProvenance
from nuros.hippocore.replay_policy import (
    POLICIES,
    RandomReplayPolicy,
    ReplayPolicy,
    ReplaySelection,
    make_policy,
)
from nuros.hippocore.consolidation import (
    ConsolidationResult,
    ConsolidationStrategy,
    STRATEGIES,
    TagJaccardConsolidation,
    make_strategy,
)
from nuros.memory_events import (
    MemoryEvent,
    MemoryEventCallback,
    MemoryEventEmitter,
    MemoryEventKind,
)


class HippoCoreMemoryConfig:
    """Configuration for ``HippoCoreMemory``.

    PHASE 5: adds ``replay_policy`` knob (one of 'recent',
    'importance_weighted', 'novelty_weighted',
    'prediction_error_weighted', 'random') and ``replay_seed`` for
    deterministic replay selection.

    PHASE 6+ will add:
      - pattern_separation_threshold: float  (PHASE 4 — deferred)
      - max_episodes: Optional[int]        (PHASE 6 memory budget)
      - max_memory_bytes: Optional[int]    (PHASE 6 memory budget)
      - consolidation_batch_size: int     (PHASE 6)
      - consolidation_similarity_threshold: float  (PHASE 6)
    """

    def __init__(
        self,
        replay_policy: str = "recent",
        replay_seed: Optional[int] = None,
        consolidation_strategy: str = "tag_jaccard",
        consolidation_batch_size: int = 50,
        consolidation_similarity_threshold: float = 0.5,
        max_episodes: Optional[int] = None,
        max_memory_bytes: Optional[int] = None,
    ) -> None:
        if replay_policy not in POLICIES:
            raise ValueError(
                f"Unknown replay_policy {replay_policy!r}. "
                f"Known: {sorted(POLICIES.keys())}"
            )
        if consolidation_strategy not in STRATEGIES:
            raise ValueError(
                f"Unknown consolidation_strategy {consolidation_strategy!r}. "
                f"Known: {sorted(STRATEGIES.keys())}"
            )
        self.replay_policy = replay_policy
        self.replay_seed = replay_seed
        # PHASE 6: consolidation knobs.
        self.consolidation_strategy = consolidation_strategy
        self.consolidation_batch_size = max(1, consolidation_batch_size)
        self.consolidation_similarity_threshold = float(consolidation_similarity_threshold)
        # PHASE 6: memory budget knobs (master prompt §16).
        self.max_episodes = max_episodes
        self.max_memory_bytes = max_memory_bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": 6,
            "knobs": {
                "replay_policy": self.replay_policy,
                "replay_seed": self.replay_seed,
                "consolidation_strategy": self.consolidation_strategy,
                "consolidation_batch_size": self.consolidation_batch_size,
                "consolidation_similarity_threshold": self.consolidation_similarity_threshold,
                "max_episodes": self.max_episodes,
                "max_memory_bytes": self.max_memory_bytes,
            },
        }


class HippoCoreMemory(MemoryEngine):
    """PHASE 3 adapter scaffold.

    Delegates every operation to an internal ``DefaultMemoryContract``
    instance. PHASE 4 will replace the delegated methods with real
    HippoCore implementations (episodic encoding + pattern separation);
    PHASE 5 will add policy-driven replay; PHASE 6 will add fast→slow
    consolidation. The ABC contract stays stable across all phases so
    no caller breaks.
    """

    SCHEMA_VERSION = "nuros.hippocore.HippoCoreMemory.v1.phase7"

    def __init__(
        self,
        config: Optional[HippoCoreMemoryConfig] = None,
        epistemic_kernel: Optional[EpistemicKernel] = None,
        organism_id: Optional[str] = None,
        environment_hash: Optional[str] = None,
        replay_policy: Optional[ReplayPolicy] = None,
        consolidation_strategy: Optional[ConsolidationStrategy] = None,
        event_emitter: Optional[MemoryEventEmitter] = None,
    ) -> None:
        self._config = config or HippoCoreMemoryConfig()
        self._inner = DefaultMemoryContract(epistemic_kernel=epistemic_kernel)
        self._encoding_organism_id = organism_id
        self._encoding_environment_hash = environment_hash
        # PHASE 5: replay policy.
        if replay_policy is not None:
            self._replay_policy = replay_policy
        else:
            self._replay_policy = make_policy(self._config.replay_policy)
        self._last_replay_selection: Optional[ReplaySelection] = None
        # PHASE 6: consolidation strategy.
        if consolidation_strategy is not None:
            self._consolidation_strategy = consolidation_strategy
        else:
            self._consolidation_strategy = make_strategy(
                self._config.consolidation_strategy,
            )
        self._last_consolidation_result: Optional[ConsolidationResult] = None
        # PHASE 7: memory event emitter. External consumers (Organism,
        # DevelopmentalTrajectory adapter, PHASE 9 benchmarks) register
        # callbacks via self.events.on(callback).
        self._event_emitter = event_emitter or MemoryEventEmitter()
        # PHASE 7: the events emitted so far (in-memory ring; full list
        # for short runs, capped at 1000 to prevent unbounded growth in
        # long-running organisms — the persistent record goes through
        # the registered callbacks to the trajectory).
        self._event_log: list[MemoryEvent] = []
        self._event_log_cap: int = 1000
        # PHASE 7: optional developmental step counter — set externally
        # by the Organism runtime via set_step(n). Used to populate
        # MemoryEvent.step.
        self._current_step: Optional[int] = None

    # ====================================================================
    # Encoding (PHASE 4) — populates the new episodic-encoding fields
    # and a structured MemoryProvenance record. This is the FIRST
    # intentional divergence from DefaultMemoryContract.
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
        epistemic_label: Optional[EpistemicLabel] = None,
    ) -> MemoryEntry:
        """PHASE 4 encode: delegates the underlying store to
        DefaultMemoryContract.encode() but then enriches the returned
        MemoryEntry with:
          - structured_provenance: a MemoryProvenance record (master
            prompt §7) carrying organism_id, environment_hash, encoder,
            encoded_at, origin, and the (optional) prediction_error if
            the caller set it via the context dict.
          - organism_id: from the encoding context (constructor or
            encode_episode()).
          - causal_metadata: seeded with environment_hash + organism_id
            for downstream PHASE 8 causal graph integration.

        Callers wanting to populate ALL PHASE 4 fields (action, outcome,
        prediction, environment_state) should use ``encode_episode()``
        below — it is the HippoCore-specific entry point for full
        episodic encoding.
        """
        entry = self._inner.encode(
            content=content, memory_type=memory_type, origin=origin,
            provenance=provenance, confidence=confidence, importance=importance,
            context=context, tags=tags, epistemic_label=epistemic_label,
        )
        # Enrich with PHASE 4 structured provenance.
        self._enrich_with_provenance(entry, action=None, outcome=None,
                                    prediction=None, environment_state=None,
                                    experience_id=None, internal_state=None)
        # PHASE 7: emit MEMORY_ENCODED event.
        self._emit(MemoryEventKind.MEMORY_ENCODED,
                   memory_id=entry.memory_id,
                   details={"memory_type": entry.memory_type.value,
                            "origin": entry.origin})
        return entry

    def encode_episode(
        self,
        content: Any,
        *,
        action: Any,
        prediction: Any = None,
        outcome: Any = None,
        prediction_error: Optional[float] = None,
        environment_state: Optional[dict[str, Any]] = None,
        internal_state: Optional[dict[str, Any]] = None,
        experience_id: Optional[str] = None,
        importance: float = 0.5,
        confidence: float = 1.0,
        origin: str = "episodic_observation",
        tags: Optional[set[str]] = None,
        epistemic_label: Optional[EpistemicLabel] = None,
    ) -> MemoryEntry:
        """HippoCore-specific entry point for full episodic encoding
        (master prompt §6).

        Encodes a memory with the full PHASE 4 schema populated:
          - ``content`` is the sensory/context representation.
          - ``action`` is the action the organism took (or is about to take).
          - ``prediction`` is the organism's prediction (e.g. predicted reward).
          - ``outcome`` is the outcome that followed (may be None at encode
            time, filled in via ``revise()`` after the environment responds).
          - ``prediction_error`` is the signed difference between predicted
            and actual outcome. If provided, also recorded on
            ``MemoryEntry.prediction_error``.
          - ``environment_state`` is the environment snapshot at encode time.
          - ``internal_state`` is the organism's internal state at encode time.
          - ``experience_id`` is an optional reference to the experience event
            that generated this memory (may match a CausalEvent.id or
            TrajectoryPoint.step in PHASE 8).

        All HippoCore-specific fields are persisted on the MemoryEntry
        AND on the structured_provenance record, so ``inspect()`` and
        ``checkpoint()`` expose them.

        Returns the encoded MemoryEntry. The memory is EPISODIC by
        default (matching master prompt §6); pass ``memory_type=`` to
        encode as a different type if needed.
        """
        # Delegate the underlying store to DefaultMemoryContract.encode().
        entry = self._inner.encode(
            content=content,
            memory_type=MemoryType.EPISODIC,
            origin=origin,
            confidence=confidence,
            importance=importance,
            context=None,  # PHASE 4: context is replaced by structured_provenance
            tags=tags,
            epistemic_label=epistemic_label,
        )
        # Populate the PHASE 4 episodic-encoding fields directly on the entry.
        entry.action = action
        entry.prediction = prediction
        entry.outcome = outcome
        entry.environment_state = environment_state
        if prediction_error is not None:
            entry.prediction_error = prediction_error
        # Enrich with structured provenance.
        self._enrich_with_provenance(
            entry, action=action, outcome=outcome, prediction=prediction,
            environment_state=environment_state, experience_id=experience_id,
            internal_state=internal_state, prediction_error=prediction_error,
        )
        # PHASE 7: emit MEMORY_ENCODED event with episode-specific details.
        self._emit(MemoryEventKind.MEMORY_ENCODED,
                   memory_id=entry.memory_id,
                   details={"memory_type": entry.memory_type.value,
                            "origin": entry.origin,
                            "action": repr(action),
                            "prediction_error": prediction_error,
                            "experience_id": experience_id})
        return entry

    def _enrich_with_provenance(
        self,
        entry: MemoryEntry,
        *,
        action: Any,
        outcome: Any,
        prediction: Any,
        environment_state: Optional[dict[str, Any]],
        experience_id: Optional[str],
        internal_state: Optional[dict[str, Any]],
        prediction_error: Optional[float] = None,
    ) -> None:
        """Attach a MemoryProvenance record to the entry and populate
        the PHASE 4 fields."""
        entry.organism_id = self._encoding_organism_id
        # action / outcome / prediction / environment_state are set by
        # the caller (encode() leaves them None; encode_episode() sets them).
        if action is not None:
            entry.action = action
        if outcome is not None:
            entry.outcome = outcome
        if prediction is not None:
            entry.prediction = prediction
        if environment_state is not None:
            entry.environment_state = environment_state
        # Seed causal_metadata with environment_hash + organism_id for
        # downstream PHASE 8 causal graph integration.
        if entry.organism_id is not None or self._encoding_environment_hash is not None:
            entry.causal_metadata = {
                "organism_id": entry.organism_id,
                "environment_hash": self._encoding_environment_hash,
            }
            if experience_id is not None:
                entry.causal_metadata["experience_id"] = experience_id
            if internal_state is not None:
                entry.causal_metadata["internal_state"] = internal_state
        # Build the structured provenance record.
        entry.structured_provenance = MemoryProvenance(
            origin=entry.origin or "hippocore_encode",
            encoded_at=entry.timestamp,
            experience_id=experience_id,
            organism_id=entry.organism_id,
            environment_hash=self._encoding_environment_hash,
            environment_state=environment_state,
            internal_state=internal_state,
            action=action,
            outcome=outcome,
            prediction=prediction,
            prediction_error=prediction_error if prediction_error is not None
                            else (entry.prediction_error if entry.prediction_error else None),
            causal_metadata=entry.causal_metadata,
            encoder="hippocore_phase4",
        )

    def set_encoding_context(
        self,
        organism_id: Optional[str] = None,
        environment_hash: Optional[str] = None,
    ) -> None:
        """Set the encoding context for subsequent encode() / encode_episode()
        calls. Used by the Organism runtime when it instantiates a
        HippoCoreMemory and wants subsequent encode() calls to be
        attributed to the organism + environment.

        Both arguments are optional — pass None to clear.
        """
        self._encoding_organism_id = organism_id
        self._encoding_environment_hash = environment_hash

    # ====================================================================
    # PHASE 7: memory event emission
    # ====================================================================

    @property
    def events(self) -> MemoryEventEmitter:
        """Public emitter for external consumers to register callbacks.

        Usage:
            hcm.events.on(lambda ev: trajectory.record(ev))
        """
        return self._event_emitter

    @property
    def event_log(self) -> list[MemoryEvent]:
        """In-memory ring of recent events (capped at 1000). For the
        full event stream, register a callback via ``events.on(...)``."""
        return list(self._event_log)

    def set_step(self, step: Optional[int]) -> None:
        """Set the current developmental step. The Organism runtime calls
        this at the start of each tick so memory events get a step
        number for trajectory alignment. Pass None to clear."""
        self._current_step = step

    def _emit(
        self,
        kind: MemoryEventKind,
        memory_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Emit a memory event to all registered callbacks + append to
        the in-memory log (capped)."""
        event = MemoryEvent(
            kind=kind,
            memory_id=memory_id,
            step=self._current_step,
            organism_id=self._encoding_organism_id,
            engine="hippocore",
            details=details or {},
        )
        self._event_log.append(event)
        # Cap the in-memory log to prevent unbounded growth.
        if len(self._event_log) > self._event_log_cap:
            # Drop the oldest 25% (avoid per-event cost).
            keep = int(self._event_log_cap * 0.75)
            self._event_log = self._event_log[-keep:]
        self._event_emitter.emit(event)

    @property
    def replay_policy(self) -> ReplayPolicy:
        """The currently-configured ReplayPolicy instance."""
        return self._replay_policy

    def set_replay_policy(self, policy: ReplayPolicy) -> None:
        """Swap the replay policy at runtime. Used by PHASE 9 benchmarks
        to compare policies on identical input sets without rebuilding
        the HippoCoreMemory instance."""
        self._replay_policy = policy
        # Reset last selection telemetry.
        self._last_replay_selection = None

    @property
    def last_replay_selection(self) -> Optional[ReplaySelection]:
        """Telemetry: the result of the most recent replay() call that
        used a policy. None if replay() has not been called with an
        ``n`` argument yet. Used by inspect() and PHASE 9 benchmarks."""
        return self._last_replay_selection

    def revise(
        self, memory_id: str, field_name: str, new_value: Any,
        justification: str, author: str = "system",
    ) -> Optional[MemoryEntry]:
        """Delegate to DefaultMemoryContract.revise().

        Used to fill in PHASE 4 fields after encode time — e.g. when
        ``encode_episode()`` was called without ``outcome=`` (the
        outcome wasn't known yet), the caller can later do::

            hcm.revise(entry.memory_id, "outcome",
                       {"reward": 0.5, "new_pos": [4, 4]},
                       justification="environment responded")

        The revision is recorded in ``entry.revision_history`` (audit
        Appendix B.7 — auditable revision). The same revision is also
        mirrored on ``entry.structured_provenance`` when the revised
        field is a PHASE 4 field (organism_id, action, outcome,
        prediction, environment_state, prediction_error).
        """
        entry = self._inner.revise(memory_id, field_name, new_value,
                                   justification, author)
        if entry is not None and field_name in (
            "organism_id", "action", "outcome", "prediction",
            "environment_state", "prediction_error",
        ) and entry.structured_provenance is not None:
            # Mirror the revision onto the structured provenance record
            # so the provenance chain stays consistent.
            setattr(entry.structured_provenance, field_name, new_value)
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
        """PHASE 3: substring filter (delegated).
        PHASE 4: similarity-based k-NN retrieval + pattern completion."""
        results = self._inner.retrieve(
            query=query, memory_type=memory_type,
            min_confidence=min_confidence, min_importance=min_importance,
            tags=tags, limit=limit,
        )
        # PHASE 7: emit MEMORY_RETRIEVED for each returned memory.
        for entry in results:
            self._emit(MemoryEventKind.MEMORY_RETRIEVED,
                       memory_id=entry.memory_id,
                       details={"query": query, "limit": limit})
        return results

    def retrieve_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        result = self._inner.retrieve_by_id(memory_id)
        if result is not None:
            # PHASE 7: emit MEMORY_RETRIEVED for direct lookups too.
            self._emit(MemoryEventKind.MEMORY_RETRIEVED,
                       memory_id=memory_id,
                       details={"query": None, "limit": 1, "direct": True})
        return result

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
        result = self._inner.reconsolidate(
            memory_id, reward=reward, prediction_error=prediction_error,
        )
        if result is not None:
            # PHASE 7: emit MEMORY_RECONSOLIDATED event.
            self._emit(MemoryEventKind.MEMORY_RECONSOLIDATED,
                       memory_id=memory_id,
                       details={"reward": reward,
                                "prediction_error": prediction_error,
                                "new_importance": result.importance,
                                "new_consolidation_status": result.consolidation_status})
        return result

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
        """PHASE 5 replay: when ``n`` is provided, delegates selection
        to the configured ReplayPolicy. Otherwise falls back to the
        DefaultMemoryContract.replay() behaviour (return all matching
        memories sorted by timestamp ascending).

        ``generative=True`` is still a no-op in PHASE 5 (will land in
        PHASE 6 alongside the real consolidation pipeline). The
        returned entries are raw stored memories (not reconstructed).

        The policy selection is recorded in ``self._last_replay_selection``
        for telemetry — ``inspect()`` and PHASE 9 benchmarks read it
        to confirm which policy produced a given selection.
        """
        if n is None:
            # No n specified — fall back to default behaviour (return all).
            return self._inner.replay(
                memory_type=memory_type, tags=tags, time_range=time_range,
                n=n, generative=generative,
            )
        # PHASE 5: use the policy to select n memories.
        # First, apply the same filters DefaultMemoryContract.replay()
        # uses (memory_type, tags, time_range). Then run the policy.
        candidates: list[MemoryEntry] = []
        for entry in self._inner.iter_all():
            if entry.forgotten:
                continue
            if memory_type and entry.memory_type != memory_type:
                continue
            if tags and not tags.issubset(entry.tags):
                continue
            if time_range:
                t_lo, t_hi = time_range
                if not (t_lo <= entry.timestamp <= t_hi):
                    continue
            candidates.append(entry)
        # PHASE 5: run the policy. Seed from config (for reproducibility)
        # unless the caller overrides via a per-call attribute.
        seed = self._config.replay_seed
        selection = self._replay_policy.select(candidates, n=n, seed=seed)
        self._last_replay_selection = selection
        # PHASE 7: emit MEMORY_REPLAYED for each selected memory.
        for entry in selection.entries:
            self._emit(MemoryEventKind.MEMORY_REPLAYED,
                       memory_id=entry.memory_id,
                       details={"policy": selection.policy_name,
                                "n_requested": selection.n_requested,
                                "n_selected": selection.n_selected,
                                "seed": selection.seed})
        return selection.entries

    # ====================================================================
    # Consolidation — PHASE 6 will override with the real fast→slow pipeline.
    # ====================================================================

    def consolidate(
        self,
        source_type: Optional[MemoryType] = None,
        target_type: Optional[MemoryType] = None,
        batch_size: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> int:
        """PHASE 6 real fast→slow consolidation pipeline.

        Algorithm (master prompt §10):
          1. Select up to ``batch_size`` memories of ``source_type``
             (default EPISODIC) that are NOT yet consolidated
             (consolidation_status == 'ACTIVE').
          2. Cluster them by content similarity (via the configured
             ConsolidationStrategy).
          3. For each cluster of size > 1, derive one ``target_type``
             memory (default SEMANTIC) whose ``content`` is a summary
             and whose ``relationships`` link back to the source memories
             via associate(). Singleton clusters (size 1) are not
             consolidated (no benefit).
          4. Mark the consolidated sources: ``consolidation_status =
             'CONSOLIDATED'`` and lower their importance by 50%.

        Returns the number of ``target_type`` memories created.

        The result is stored in ``self._last_consolidation_result`` for
        telemetry (used by inspect() and PHASE 9 benchmarks).
        """
        src_t = source_type if source_type is not None else MemoryType.EPISODIC
        tgt_t = target_type if target_type is not None else MemoryType.SEMANTIC
        bs = batch_size if batch_size is not None else self._config.consolidation_batch_size
        sim_thr = (similarity_threshold
                   if similarity_threshold is not None
                   else self._config.consolidation_similarity_threshold)

        start = time.time()

        # 1. Select candidate sources (not yet consolidated).
        candidates: list[MemoryEntry] = []
        for entry in self._inner.iter_all():
            if entry.memory_type != src_t:
                continue
            if entry.consolidation_status != "ACTIVE":
                continue
            if entry.forgotten:
                continue
            candidates.append(entry)
            if len(candidates) >= bs:
                break

        if not candidates:
            self._last_consolidation_result = ConsolidationResult(
                strategy_name=self._consolidation_strategy.name,
                elapsed_seconds=time.time() - start,
            )
            return 0

        # 2. Cluster.
        clusters = self._consolidation_strategy.cluster(candidates, sim_thr)

        # 3. Derive target memories from clusters of size > 1.
        target_ids: list[str] = []
        source_ids_marked: list[str] = []
        for cluster in clusters:
            if len(cluster) < 2:
                # Singleton cluster — nothing to consolidate.
                continue
            # Derive content for the consolidated memory.
            derived_content = self._consolidation_strategy.derive_target_content(cluster)
            # Build the target entry — use the underlying store so it
            # gets a fresh memory_id and proper access tracking.
            target = self._inner.encode(
                content=derived_content,
                memory_type=tgt_t,
                origin=f"consolidated_by_{self._consolidation_strategy.name}",
                # Importance = mean of source importances (preserves signal).
                importance=sum(e.importance for e in cluster) / len(cluster),
                confidence=1.0,
                epistemic_label=EpistemicLabel.INFERRED,
                tags=set().union(*(e.tags for e in cluster)) if cluster else set(),
            )
            target.consolidation_status = "CONSOLIDATED"
            # Mark all source memories as consolidated + lower importance.
            for src in cluster:
                src.consolidation_status = "CONSOLIDATED"
                src.importance = max(0.0, src.importance * 0.5)
                # Associate the source ↔ the target.
                self._inner.associate(
                    src.memory_id, target.memory_id,
                    relation_type="consolidated_into",
                    strength=1.0, bidirectional=True,
                )
                source_ids_marked.append(src.memory_id)
            target_ids.append(target.memory_id)

        elapsed = time.time() - start
        self._last_consolidation_result = ConsolidationResult(
            n_clusters=len(clusters),
            n_target_created=len(target_ids),
            source_ids=source_ids_marked,
            target_ids=target_ids,
            strategy_name=self._consolidation_strategy.name,
            elapsed_seconds=elapsed,
        )
        # PHASE 7: emit MEMORY_CONSOLIDATED for each source + MEMORY_ENCODED
        # for each target (so the trajectory records both the source-side
        # status change AND the new semantic memory creation).
        for src_id in source_ids_marked:
            self._emit(MemoryEventKind.MEMORY_CONSOLIDATED,
                       memory_id=src_id,
                       details={"strategy": self._consolidation_strategy.name,
                                "target_ids": target_ids,
                                "new_status": "CONSOLIDATED"})
        return len(target_ids)

    @property
    def consolidation_strategy(self) -> ConsolidationStrategy:
        """The currently-configured ConsolidationStrategy."""
        return self._consolidation_strategy

    def set_consolidation_strategy(self, strategy: ConsolidationStrategy) -> None:
        """Swap the consolidation strategy at runtime. Used by PHASE 9
        benchmarks to compare strategies on identical input sets."""
        self._consolidation_strategy = strategy
        self._last_consolidation_result = None

    @property
    def last_consolidation_result(self) -> Optional[ConsolidationResult]:
        """Telemetry: the result of the most recent consolidate() call.
        None if consolidate() has not been called yet."""
        return self._last_consolidation_result

    # ====================================================================
    # Forgetting — uses the same soft-delete semantics as DefaultMemoryContract.
    # PHASE 6 will add a more sophisticated forgetting lifecycle (audit §17).
    # ====================================================================

    def forget(
        self, memory_id: str, justification: str = "", hard: bool = False,
    ) -> bool:
        result = self._inner.forget(memory_id, justification, hard)
        if result:
            # PHASE 7: emit MEMORY_FORGOTTEN event.
            self._emit(MemoryEventKind.MEMORY_FORGOTTEN,
                       memory_id=memory_id,
                       details={"justification": justification,
                                "hard": hard})
        return result

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
