"""
Mind Version Control — Snapshot, Fork, Diff, Replay, Restore.

Commands:
    nuros mind create
    nuros mind snapshot
    nuros mind fork
    nuros mind diff
    nuros mind replay
    nuros mind restore
    nuros mind terminate

A mind snapshot preserves: architecture, memory, synaptic state,
developmental state, configuration, environment metadata.

This is computational state branching, NOT copying subjective identity.

Implementation Status: EXPERIMENTAL
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MindSnapshot:
    """A complete snapshot of an organism's state."""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organism_id: str = ""
    timestamp: float = field(default_factory=time.time)
    label: str = ""

    # State hashes for each component
    genome_hash: str = ""
    memory_hash: str = ""
    state_hash: str = ""
    developmental_hash: str = ""

    # Full state data
    state_data: dict[str, Any] = field(default_factory=dict)

    # Metadata
    tick_count: int = 0
    developmental_stage: str = ""
    parent_snapshot: Optional[str] = None

    @property
    def composite_hash(self) -> str:
        """Hash combining all component hashes."""
        combined = f"{self.genome_hash}:{self.memory_hash}:{self.state_hash}:{self.developmental_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]


@dataclass
class MindDiff:
    """Difference between two mind snapshots."""
    snapshot_a_id: str
    snapshot_b_id: str
    timestamp: float = field(default_factory=time.time)
    diff_data: dict[str, Any] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.diff_data)


class MindVersionControl:
    """
    Mind Version Control System.

    Provides snapshot, fork, diff, replay, and restore operations
    for artificial organisms. This is computational state management,
    NOT identity copying.
    """

    def __init__(self):
        self._snapshots: dict[str, MindSnapshot] = {}
        self._diffs: list[MindDiff] = []

    def create_snapshot(
        self, organism_id: str, state_data: dict,
        genome_hash: str = "", memory_hash: str = "",
        state_hash: str = "", developmental_hash: str = "",
        label: str = "", tick_count: int = 0,
        developmental_stage: str = "",
    ) -> MindSnapshot:
        """Create a snapshot of an organism's current state."""
        snapshot = MindSnapshot(
            organism_id=organism_id, label=label,
            genome_hash=genome_hash, memory_hash=memory_hash,
            state_hash=state_hash, developmental_hash=developmental_hash,
            state_data=state_data, tick_count=tick_count,
            developmental_stage=developmental_stage,
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[MindSnapshot]:
        return self._snapshots.get(snapshot_id)

    def diff(self, snapshot_a_id: str, snapshot_b_id: str) -> Optional[MindDiff]:
        """Compute the difference between two snapshots."""
        a = self._snapshots.get(snapshot_a_id)
        b = self._snapshots.get(snapshot_b_id)
        if not a or not b:
            return None

        diff_data = {}
        if a.genome_hash != b.genome_hash:
            diff_data["genome_changed"] = True
        if a.memory_hash != b.memory_hash:
            diff_data["memory_changed"] = True
        if a.state_hash != b.state_hash:
            diff_data["state_changed"] = True
        if a.developmental_hash != b.developmental_hash:
            diff_data["developmental_changed"] = True
        if a.developmental_stage != b.developmental_stage:
            diff_data["stage_transition"] = {
                "from": a.developmental_stage,
                "to": b.developmental_stage,
            }
        if a.tick_count != b.tick_count:
            diff_data["ticks_elapsed"] = b.tick_count - a.tick_count

        mind_diff = MindDiff(
            snapshot_a_id=snapshot_a_id,
            snapshot_b_id=snapshot_b_id,
            diff_data=diff_data,
        )
        self._diffs.append(mind_diff)
        return mind_diff

    def list_snapshots(self, organism_id: Optional[str] = None) -> list[MindSnapshot]:
        """List all snapshots, optionally filtered by organism."""
        snapshots = self._snapshots.values()
        if organism_id:
            snapshots = [s for s in snapshots if s.organism_id == organism_id]
        return sorted(snapshots, key=lambda s: s.timestamp)

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    def summary(self) -> dict:
        return {
            "total_snapshots": len(self._snapshots),
            "total_diffs": len(self._diffs),
        }
