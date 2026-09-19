"""
ReplayPolicy — configurable replay selection for HippoCoreMemory.

PHASE 5 of the HippoCore integration (master prompt §9).

Replay must become a *developmental mechanism*, not just a debugging
feature. This module defines a pluggable ReplayPolicy ABC and 5 concrete
policies:

  - RecentReplayPolicy           — select the most recent N memories
  - ImportanceWeightedReplayPolicy — weighted sampling by `importance`
  - NoveltyWeightedReplayPolicy   — weighted by 1 / (1 + access_count)
                                    (memories that have been accessed
                                    less are more "novel" and worth
                                    replaying)
  - PredictionErrorWeightedReplayPolicy — weighted by |prediction_error|
                                    (memories that violated predictions
                                    are prioritized — exploitation of
                                    the surprise signal)
  - RandomReplayPolicy            — uniform random sampling (baseline)

All policies are DETERMINISTIC when seeded — given the same input set
and the same RNG seed, they produce the same output order. This is
critical for the master prompt §36 final architectural test
(`EXPERIENCE → EPISODIC MEMORY → REPLAY → CONSOLIDATION → MEMORY-
DEPENDENT BEHAVIOR → DEVELOPMENTAL CHANGE → MEASURABLE TRAJECTORY`)
to be reproducible.

Master prompt §9 explicitly says: "Do not assume one policy is superior.
Benchmark them." — the PHASE 9 benchmark suite (master prompt §25 item
04_replay) will compare these 5 policies on identical input sets.

Implementation Status: IMPLEMENTED
LLM dependency: NONE.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from nuros.memory import MemoryEntry, MemoryType


@dataclass
class ReplaySelection:
    """The result of a ReplayPolicy.select() call.

    Carries the selected entries plus per-entry sampling metadata useful
    for telemetry (PHASE 7 trajectory integration) and PHASE 9
    benchmarks.
    """
    entries: list[MemoryEntry]
    """The selected memories, in the order they should be replayed."""
    policy_name: str
    """Name of the policy that produced this selection
    (e.g. 'importance_weighted')."""
    n_requested: int
    """How many memories were requested (may be larger than
    len(entries) if the buffer is smaller)."""
    n_available: int
    """How many memories were available in the buffer before selection."""
    n_selected: int = field(default=0)
    """len(entries). Convenience for telemetry."""
    selection_weights: Optional[list[float]] = None
    """The weight each available entry had under this policy, BEFORE
    selection. Length == n_available. None if the policy doesn't
    compute per-entry weights (e.g. recent/random)."""
    seed: Optional[int] = None
    """The RNG seed used for this selection (for reproducibility)."""

    def __post_init__(self):
        self.n_selected = len(self.entries)


class ReplayPolicy(ABC):
    """Pluggable replay selection policy.

    Implementations select up to ``n`` memories from a buffer and
    return them in the order they should be replayed. Implementations
    MUST be deterministic when seeded.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short stable identifier for telemetry / config serialization."""

    @abstractmethod
    def select(
        self,
        buffer: list[MemoryEntry],
        n: int,
        seed: Optional[int] = None,
    ) -> ReplaySelection:
        """Select up to ``n`` memories from ``buffer`` for replay.

        ``buffer`` is the list of currently-stored memories (the caller
        should pre-filter forgotten entries — they are excluded from
        replay by default; see DefaultMemoryContract.replay()).

        ``seed`` controls RNG-based policies. If None, the policy is
        free to use a non-deterministic source — but reproducible
        benchmarks should always pass a seed.

        Returns a ReplaySelection with up to ``n`` entries. If
        ``len(buffer) <= n``, the policy returns all of them (order
        depends on the policy).
        """

    # Convenience: policy name as a string for easy config.
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# ============================================================================
# Concrete policies
# ============================================================================


class RecentReplayPolicy(ReplayPolicy):
    """Select the most recent N memories by timestamp (descending).

    This is the simplest baseline: "replay what just happened".
    Useful for short-term consolidation and for environments where
    recency is a strong signal (e.g. ChangingWorld,
    nuros-dev/src/environment.rs::ChangingWorld).
    """

    @property
    def name(self) -> str:
        return "recent"

    def select(self, buffer, n, seed=None) -> ReplaySelection:
        # Sort by timestamp descending (most recent first).
        sorted_buf = sorted(buffer, key=lambda e: e.timestamp, reverse=True)
        selected = sorted_buf[:n]
        return ReplaySelection(
            entries=selected,
            policy_name=self.name,
            n_requested=n,
            n_available=len(buffer),
            selection_weights=None,
            seed=seed,
        )


class ImportanceWeightedReplayPolicy(ReplayPolicy):
    """Sample with probability proportional to `importance`.

    Master prompt §9 lists importance as a possible replay weight.
    Uses importance^2 to amplify the difference between high- and
    low-importance memories (without this, near-equal importances
    would produce a near-uniform distribution).

    Deterministic when seeded.
    """

    @property
    def name(self) -> str:
        return "importance_weighted"

    def select(self, buffer, n, seed=None) -> ReplaySelection:
        rng = random.Random(seed)
        if not buffer:
            return ReplaySelection(
                entries=[], policy_name=self.name,
                n_requested=n, n_available=0, selection_weights=[],
                seed=seed,
            )
        weights = [e.importance ** 2 for e in buffer]
        total = sum(weights)
        if total <= 0:
            # Fallback to uniform if all importances are 0.
            weights = [1.0] * len(buffer)
            total = float(len(buffer))
        probs = [w / total for w in weights]
        # Weighted sampling without replacement.
        n_pick = min(n, len(buffer))
        chosen_indices: list[int] = []
        available_indices = list(range(len(buffer)))
        available_probs = list(probs)
        for _ in range(n_pick):
            # Re-normalize over the still-available indices.
            sub_total = sum(available_probs[i] for i in available_indices)
            if sub_total <= 0:
                # Fallback to uniform among remaining.
                pick_idx = rng.choice(available_indices)
            else:
                r = rng.random() * sub_total
                cum = 0.0
                pick_idx = available_indices[-1]
                for i in available_indices:
                    cum += available_probs[i]
                    if cum >= r:
                        pick_idx = i
                        break
            chosen_indices.append(pick_idx)
            available_indices = [i for i in available_indices if i != pick_idx]
        selected = [buffer[i] for i in chosen_indices]
        return ReplaySelection(
            entries=selected,
            policy_name=self.name,
            n_requested=n,
            n_available=len(buffer),
            selection_weights=probs,
            seed=seed,
        )


class NoveltyWeightedReplayPolicy(ReplayPolicy):
    """Sample with probability proportional to novelty = 1 / (1 + access_count).

    Master prompt §9 lists novelty as a possible replay weight.
    Memories that have been accessed fewer times are "more novel" and
    deserve replay. The 1/(1+k) form is a simple inverse-frequency
    weighting that requires NO embedding model and NO LLM.

    Deterministic when seeded.
    """

    @property
    def name(self) -> str:
        return "novelty_weighted"

    def select(self, buffer, n, seed=None) -> ReplaySelection:
        rng = random.Random(seed)
        if not buffer:
            return ReplaySelection(
                entries=[], policy_name=self.name,
                n_requested=n, n_available=0, selection_weights=[],
                seed=seed,
            )
        weights = [1.0 / (1.0 + float(e.access_count)) for e in buffer]
        total = sum(weights)
        probs = [w / total for w in weights] if total > 0 else [1.0 / len(buffer)] * len(buffer)
        n_pick = min(n, len(buffer))
        chosen_indices: list[int] = []
        available_indices = list(range(len(buffer)))
        available_probs = list(probs)
        for _ in range(n_pick):
            sub_total = sum(available_probs[i] for i in available_indices)
            if sub_total <= 0:
                pick_idx = rng.choice(available_indices)
            else:
                r = rng.random() * sub_total
                cum = 0.0
                pick_idx = available_indices[-1]
                for i in available_indices:
                    cum += available_probs[i]
                    if cum >= r:
                        pick_idx = i
                        break
            chosen_indices.append(pick_idx)
            available_indices = [i for i in available_indices if i != pick_idx]
        selected = [buffer[i] for i in chosen_indices]
        return ReplaySelection(
            entries=selected,
            policy_name=self.name,
            n_requested=n,
            n_available=len(buffer),
            selection_weights=probs,
            seed=seed,
        )


class PredictionErrorWeightedReplayPolicy(ReplayPolicy):
    """Sample with probability proportional to |prediction_error|.

    Master prompt §9 lists prediction error as a possible replay weight.
    Memories that violated the organism's predictions are prioritized —
    this exploits the unused `MemoryEntry.prediction_error` field
    (audit Appendix B.7 mentions this field was dead).

    Deterministic when seeded.
    """

    @property
    def name(self) -> str:
        return "prediction_error_weighted"

    def select(self, buffer, n, seed=None) -> ReplaySelection:
        rng = random.Random(seed)
        if not buffer:
            return ReplaySelection(
                entries=[], policy_name=self.name,
                n_requested=n, n_available=0, selection_weights=[],
                seed=seed,
            )
        weights = [abs(e.prediction_error) for e in buffer]
        total = sum(weights)
        if total <= 0:
            # All prediction errors are zero — fall back to uniform.
            weights = [1.0] * len(buffer)
            total = float(len(buffer))
        probs = [w / total for w in weights]
        n_pick = min(n, len(buffer))
        chosen_indices: list[int] = []
        available_indices = list(range(len(buffer)))
        available_probs = list(probs)
        for _ in range(n_pick):
            sub_total = sum(available_probs[i] for i in available_indices)
            if sub_total <= 0:
                pick_idx = rng.choice(available_indices)
            else:
                r = rng.random() * sub_total
                cum = 0.0
                pick_idx = available_indices[-1]
                for i in available_indices:
                    cum += available_probs[i]
                    if cum >= r:
                        pick_idx = i
                        break
            chosen_indices.append(pick_idx)
            available_indices = [i for i in available_indices if i != pick_idx]
        selected = [buffer[i] for i in chosen_indices]
        return ReplaySelection(
            entries=selected,
            policy_name=self.name,
            n_requested=n,
            n_available=len(buffer),
            selection_weights=probs,
            seed=seed,
        )


class RandomReplayPolicy(ReplayPolicy):
    """Uniformly random sampling. Baseline.

    Deterministic when seeded. Used as the control condition in the
    PHASE 9 catastrophic-forgetting benchmark (master prompt §11).
    """

    @property
    def name(self) -> str:
        return "random"

    def select(self, buffer, n, seed=None) -> ReplaySelection:
        rng = random.Random(seed)
        if not buffer:
            return ReplaySelection(
                entries=[], policy_name=self.name,
                n_requested=n, n_available=0, selection_weights=[],
                seed=seed,
            )
        n_pick = min(n, len(buffer))
        # Use rng.sample for unbiased uniform sampling without replacement.
        chosen_indices = rng.sample(range(len(buffer)), n_pick)
        selected = [buffer[i] for i in chosen_indices]
        # Uniform weights for telemetry.
        uniform = 1.0 / len(buffer)
        return ReplaySelection(
            entries=selected,
            policy_name=self.name,
            n_requested=n,
            n_available=len(buffer),
            selection_weights=[uniform] * len(buffer),
            seed=seed,
        )


# ============================================================================
# Policy registry — used by HippoCoreMemoryConfig.replay_policy
# ============================================================================

POLICIES: dict[str, type[ReplayPolicy]] = {
    "recent": RecentReplayPolicy,
    "importance_weighted": ImportanceWeightedReplayPolicy,
    "novelty_weighted": NoveltyWeightedReplayPolicy,
    "prediction_error_weighted": PredictionErrorWeightedReplayPolicy,
    "random": RandomReplayPolicy,
}


def make_policy(name: str) -> ReplayPolicy:
    """Factory: build a ReplayPolicy by name.

    Raises ValueError if the name is unknown.
    """
    if name not in POLICIES:
        raise ValueError(
            f"Unknown replay policy {name!r}. "
            f"Known policies: {sorted(POLICIES.keys())}"
        )
    return POLICIES[name]()


__all__ = [
    "ReplayPolicy",
    "ReplaySelection",
    "RecentReplayPolicy",
    "ImportanceWeightedReplayPolicy",
    "NoveltyWeightedReplayPolicy",
    "PredictionErrorWeightedReplayPolicy",
    "RandomReplayPolicy",
    "POLICIES",
    "make_policy",
]
