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
    ) -> None:
        if replay_policy not in POLICIES:
            raise ValueError(
                f"Unknown replay_policy {replay_policy!r}. "
                f"Known: {sorted(POLICIES.keys())}"
            )
        self.replay_policy = replay_policy
        self.replay_seed = replay_seed

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": 5,
            "knobs": {
                "replay_policy": self.replay_policy,
                "replay_seed": self.replay_seed,
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

    SCHEMA_VERSION = "nuros.hippocore.HippoCoreMemory.v1.phase5"

    def __init__(
        self,
        config: Optional[HippoCoreMemoryConfig] = None,
        epistemic_kernel: Optional[EpistemicKernel] = None,
        organism_id: Optional[str] = None,
        environment_hash: Optional[str] = None,
        replay_policy: Optional[ReplayPolicy] = None,
    ) -> None:
        self._config = config or HippoCoreMemoryConfig()
        # In PHASE 3-5, we delegate non-encode operations to
        # DefaultMemoryContract. PHASE 4 overrides encode() to populate
        # the new episodic-encoding fields and structured_provenance.
        # PHASE 5 overrides replay() to support policy-driven selection.
        # PHASE 6 will override consolidate() and may swap the inner
        # engine for a real dual-store (fast episodic + slow consolidated).
        self._inner = DefaultMemoryContract(epistemic_kernel=epistemic_kernel)
        # PHASE 4: the encoding context (organism + environment) is set
        # via the constructor OR via encode_episode(organism_id=...).
        self._encoding_organism_id = organism_id
        self._encoding_environment_hash = environment_hash
        # PHASE 5: build the replay policy from config OR accept an
        # already-instantiated ReplayPolicy.
        if replay_policy is not None:
            self._replay_policy = replay_policy
        else:
            self._replay_policy = make_policy(self._config.replay_policy)
        # PHASE 5: last replay selection telemetry (for inspect() /
        # checkpoint() consumers).
        self._last_replay_selection: Optional[ReplaySelection] = None

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
        return selection.entries

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
