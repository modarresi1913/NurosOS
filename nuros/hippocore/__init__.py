"""
HippoCore — episodic memory & continual-learning engine for NurosOS.

PHASE 3: adapter scaffold (thin wrapper around DefaultMemoryContract).
PHASE 4: real episodic encoding with structured provenance.
PHASE 5: policy-driven replay (recent / importance_weighted /
         novelty_weighted / prediction_error_weighted / random).
PHASE 6: fast→slow consolidation pipeline.
PHASE 7: memory event emission for the developmental trajectory.

This package provides an alternative ``MemoryEngine`` implementation
that delivers genuine hippocampal-inspired computational mechanisms
(episodic encoding + pattern separation + replay + consolidation +
reconsolidation + forgetting) behind the stable ``MemoryEngine`` ABC.

Status: [IMPLEMENTED] PHASE 3-7.
        [PROPOSED]    PHASE 8 causal graph (Rust side).

LLM dependency: NONE. The HippoCore package is fully local and
deterministic, satisfying master prompt §23.
"""

from nuros.hippocore.memory_engine import HippoCoreMemory, HippoCoreMemoryConfig
from nuros.hippocore.replay_policy import (
    POLICIES,
    ImportanceWeightedReplayPolicy,
    NoveltyWeightedReplayPolicy,
    PredictionErrorWeightedReplayPolicy,
    RandomReplayPolicy,
    RecentReplayPolicy,
    ReplayPolicy,
    ReplaySelection,
    make_policy,
)
from nuros.hippocore.consolidation import (
    STRATEGIES,
    ConsolidationResult,
    ConsolidationStrategy,
    ContentPrefixConsolidation,
    TagJaccardConsolidation,
    make_strategy,
)
from nuros.memory_events import (
    MemoryEvent,
    MemoryEventCallback,
    MemoryEventEmitter,
    MemoryEventKind,
)

__all__ = [
    "HippoCoreMemory",
    "HippoCoreMemoryConfig",
    "POLICIES",
    "ReplayPolicy",
    "ReplaySelection",
    "RecentReplayPolicy",
    "ImportanceWeightedReplayPolicy",
    "NoveltyWeightedReplayPolicy",
    "PredictionErrorWeightedReplayPolicy",
    "RandomReplayPolicy",
    "make_policy",
    "STRATEGIES",
    "ConsolidationResult",
    "ConsolidationStrategy",
    "ContentPrefixConsolidation",
    "TagJaccardConsolidation",
    "make_strategy",
    "MemoryEvent",
    "MemoryEventCallback",
    "MemoryEventEmitter",
    "MemoryEventKind",
]
