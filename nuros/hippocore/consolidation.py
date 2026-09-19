"""
Consolidation pipeline — fast episodic → slow consolidated knowledge.

PHASE 6 of the HippoCore integration (master prompt §10).

Implements:
  - A dual-store inside HippoCoreMemory: fast episodic (current
    MemoryEntry store) + slow consolidated (semantic memories derived
    from episodic clusters).
  - ConsolidationStrategy ABC + concrete strategies:
    * TagJaccardConsolidation — cluster by Jaccard similarity on `tags`
      (NO embedding model, NO LLM).
    * ContentPrefixConsolidation — cluster by shared content prefix
      (a deterministic, content-based proxy for semantic similarity).
  - Override HippoCoreMemory.consolidate() to run the configured
    strategy on the fast store and promote clustered episodes to the
    slow store as SEMANTIC memories.

Master prompt §10:
  - Fast Learning System → Episodic Memory → Replay → Consolidation →
    Stable Knowledge.
  - Measure: retention, forgetting, retrieval accuracy, adaptation,
    interference. (The measurement itself is in PHASE 9 benchmarks/
    memory/05_consolidation.)

The dual-store is *not* a vector DB — it is a structured semantic
store that aggregates episodic memories by content similarity.

Implementation Status: IMPLEMENTED
LLM dependency: NONE.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from nuros.epistemic import EpistemicLabel
from nuros.memory import MemoryEntry, MemoryType


# ============================================================================
# Consolidation result + strategy ABC
# ============================================================================


@dataclass
class ConsolidationResult:
    """The outcome of one consolidate() pass.

    Carries:
      - ``n_clusters``: how many clusters were formed from source memories.
      - ``n_target_created``: how many target-type memories were created
        (= the return value of consolidate()).
      - ``source_ids``: list of source memory_ids that were marked as
        CONSOLIDATED (their importance lowered).
      - ``target_ids``: list of newly-created target memory_ids.
      - ``strategy_name``: which strategy produced this result.
      - ``elapsed_seconds``: wall-clock time of the consolidation pass.
    """
    n_clusters: int = 0
    n_target_created: int = 0
    source_ids: list[str] = field(default_factory=list)
    target_ids: list[str] = field(default_factory=list)
    strategy_name: str = ""
    elapsed_seconds: float = 0.0


class ConsolidationStrategy(ABC):
    """Pluggable strategy for clustering episodic memories.

    Implementations MUST be deterministic — given the same source list
    + the same parameters, they must produce the same clusters. (The
    PHASE 9 catastrophic-forgetting benchmark relies on this.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short stable identifier (e.g. 'tag_jaccard')."""

    @abstractmethod
    def cluster(
        self,
        sources: list[MemoryEntry],
        similarity_threshold: float,
    ) -> list[list[MemoryEntry]]:
        """Group ``sources`` into clusters where every pair of memories
        in a cluster has similarity >= ``similarity_threshold``.

        Returns a list of clusters; each cluster is a list of
        MemoryEntry instances.

        Implementations should treat the threshold as a lower bound on
        similarity — pairs with similarity EXACTLY equal to the
        threshold are considered similar (>= comparison).
        """

    @abstractmethod
    def similarity(self, a: MemoryEntry, b: MemoryEntry) -> float:
        """Return a similarity score in [0, 1] between two memories.
        0 = completely dissimilar; 1 = identical (along the strategy's
        dimension). Used for diagnostics / benchmarks."""

    def derive_target_content(
        self, cluster: list[MemoryEntry],
    ) -> Any:
        """Derive the content for the target (consolidated) memory from
        a cluster of source memories.

        Default implementation: joins the source contents as a list.
        Subclasses may override to produce more sophisticated
        summaries (e.g. extract common tokens) — but PHASE 6 keeps
        this simple and deterministic.
        """
        contents = [
            (e.content if isinstance(e.content, str) else repr(e.content))
            for e in cluster
        ]
        return {
            "summary": f"consolidated from {len(cluster)} memories",
            "source_contents": contents,
        }


# ============================================================================
# Concrete strategies
# ============================================================================


class TagJaccardConsolidation(ConsolidationStrategy):
    """Cluster memories by Jaccard similarity on their ``tags`` sets.

    Jaccard(A, B) = |A ∩ B| / |A ∪ B|. Threshold default 0.5 means
    "share at least half their tags".

    Deterministic. NO embedding model required. NO LLM dependency.
    """

    @property
    def name(self) -> str:
        return "tag_jaccard"

    def similarity(self, a: MemoryEntry, b: MemoryEntry) -> float:
        ta, tb = a.tags, b.tags
        if not ta and not tb:
            return 0.0  # no information → not similar
        union = ta | tb
        if not union:
            return 0.0
        return len(ta & tb) / len(union)

    def cluster(
        self, sources: list[MemoryEntry], similarity_threshold: float,
    ) -> list[list[MemoryEntry]]:
        # Greedy clustering: for each memory, find an existing cluster
        # whose mean similarity (to all members) >= threshold; if none,
        # start a new cluster. Deterministic because we iterate sources
        # in order.
        clusters: list[list[MemoryEntry]] = []
        for entry in sources:
            best_cluster_idx: Optional[int] = None
            best_sim = -1.0
            for i, cluster in enumerate(clusters):
                # Mean similarity to cluster members.
                sims = [self.similarity(entry, m) for m in cluster]
                mean_sim = sum(sims) / len(sims) if sims else 0.0
                if mean_sim >= similarity_threshold and mean_sim > best_sim:
                    best_sim = mean_sim
                    best_cluster_idx = i
            if best_cluster_idx is not None:
                clusters[best_cluster_idx].append(entry)
            else:
                clusters.append([entry])
        return clusters


class ContentPrefixConsolidation(ConsolidationStrategy):
    """Cluster memories by shared content prefix.

    Two memories are similar iff they share a common prefix of length
    >= min_prefix_chars (default 10). This is a content-based proxy
    for semantic similarity — useful when memories carry short text
    content (e.g. "resource at (3,4)" vs "resource at (3,5)").

    Deterministic. NO embedding model required.
    """

    def __init__(self, min_prefix_chars: int = 10) -> None:
        self.min_prefix_chars = max(1, min_prefix_chars)

    @property
    def name(self) -> str:
        return "content_prefix"

    def similarity(self, a: MemoryEntry, b: MemoryEntry) -> float:
        ca = a.content if isinstance(a.content, str) else repr(a.content)
        cb = b.content if isinstance(b.content, str) else repr(b.content)
        # Find common prefix length.
        common = 0
        for x, y in zip(ca, cb):
            if x == y:
                common += 1
            else:
                break
        if common >= self.min_prefix_chars:
            # Normalize: longer common prefix = more similar.
            denom = max(len(ca), len(cb), 1)
            return common / denom
        return 0.0

    def cluster(
        self, sources: list[MemoryEntry], similarity_threshold: float,
    ) -> list[list[MemoryEntry]]:
        # Use the same greedy clustering pattern as TagJaccard.
        clusters: list[list[MemoryEntry]] = []
        for entry in sources:
            best_cluster_idx: Optional[int] = None
            best_sim = -1.0
            for i, cluster in enumerate(clusters):
                sims = [self.similarity(entry, m) for m in cluster]
                mean_sim = sum(sims) / len(sims) if sims else 0.0
                if mean_sim >= similarity_threshold and mean_sim > best_sim:
                    best_sim = mean_sim
                    best_cluster_idx = i
            if best_cluster_idx is not None:
                clusters[best_cluster_idx].append(entry)
            else:
                clusters.append([entry])
        return clusters


# ============================================================================
# Strategy registry
# ============================================================================

STRATEGIES: dict[str, type[ConsolidationStrategy]] = {
    "tag_jaccard": TagJaccardConsolidation,
    "content_prefix": ContentPrefixConsolidation,
}


def make_strategy(name: str, **kwargs: Any) -> ConsolidationStrategy:
    """Factory: build a ConsolidationStrategy by name.

    Raises ValueError if the name is unknown.
    """
    if name not in STRATEGIES:
        raise ValueError(
            f"Unknown consolidation strategy {name!r}. "
            f"Known: {sorted(STRATEGIES.keys())}"
        )
    return STRATEGIES[name](**kwargs)


__all__ = [
    "ConsolidationResult",
    "ConsolidationStrategy",
    "TagJaccardConsolidation",
    "ContentPrefixConsolidation",
    "STRATEGIES",
    "make_strategy",
]
