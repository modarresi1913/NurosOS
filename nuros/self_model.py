"""
Self Model Contract — Computational Self-Representation.

A computational Self Model that represents (where possible):
    identity, capabilities, limitations, current state, goals,
    beliefs, uncertainty, available resources, active processes,
    recent actions, system version, memory state, architectural changes

Expose queries:
    Who am I? What can I do? What can I not do?
    What do I currently believe? How confident am I?
    What changed? Why did I take this action?
    Which information influenced the action?

IMPORTANT: The Self Model is an operational representation.
It is NOT evidence of subjective consciousness.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class SelfModelQuery(Enum):
    WHO_AM_I = "who_am_i"
    WHAT_CAN_I_DO = "what_can_i_do"
    WHAT_CANT_I_DO = "what_cant_i_do"
    WHAT_DO_I_BELIEVE = "what_do_i_believe"
    HOW_CONFIDENT = "how_confident"
    WHAT_CHANGED = "what_changed"
    WHY_ACTION = "why_action"
    WHAT_INFLUENCED = "what_influenced"


@dataclass
class Belief:
    """A belief held by the organism, with confidence and source."""
    content: str
    confidence: float = 0.5
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    belief_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Capability:
    """A capability of the organism."""
    name: str
    description: str = ""
    enabled: bool = True
    resource_cost: float = 0.0  # Estimated resource cost to use


@dataclass
class Goal:
    """A goal with source, authority, scope, priority, and expiration."""
    content: str
    source: str = "system"
    authority: str = "internal"
    scope: str = "local"  # "local", "global", "persistent"
    priority: float = 0.5
    expiration: Optional[float] = None
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    active: bool = True


@dataclass
class ActionRecord:
    """Record of a recent action for self-reflection."""
    action: str
    reason: str = ""
    influencing_information: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    outcome: Optional[str] = None


@dataclass
class ArchitecturalChange:
    """Record of a change to the organism's architecture."""
    description: str
    timestamp: float = field(default_factory=time.time)
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class SelfModel:
    """
    Computational Self Model.

    Provides the organism with an operational representation of itself.
    This is NOT subjective consciousness — it is a data structure
    that the organism can query to understand its own state,
    capabilities, and limitations.
    """

    def __init__(self, organism_id: str = "", system_version: str = "0.2.0-alpha"):
        self._organism_id = organism_id or str(uuid.uuid4())
        self._system_version = system_version
        self._capabilities: dict[str, Capability] = {}
        self._limitations: list[str] = []
        self._beliefs: dict[str, Belief] = {}
        self._goals: dict[str, Goal] = {}
        self._current_state: dict[str, Any] = {}
        self._available_resources: dict[str, float] = {}
        self._active_processes: list[str] = []
        self._recent_actions: list[ActionRecord] = []
        self._architectural_changes: list[ArchitecturalChange] = []
        self._max_recent_actions: int = 100
        self._created_at: float = time.time()

    @property
    def organism_id(self) -> str:
        return self._organism_id

    def add_capability(self, name: str, description: str = "",
                       resource_cost: float = 0.0) -> None:
        self._capabilities[name] = Capability(
            name=name, description=description, resource_cost=resource_cost,
        )

    def add_limitation(self, limitation: str) -> None:
        self._limitations.append(limitation)

    def add_belief(self, content: str, confidence: float = 0.5,
                   source: str = "") -> Belief:
        belief = Belief(content=content, confidence=confidence, source=source)
        self._beliefs[belief.belief_id] = belief
        return belief

    def revise_belief(self, belief_id: str, new_confidence: float,
                      justification: str = "") -> Optional[Belief]:
        belief = self._beliefs.get(belief_id)
        if not belief:
            return None
        belief.confidence = new_confidence
        return belief

    def add_goal(self, content: str, source: str = "system",
                 authority: str = "internal", scope: str = "local",
                 priority: float = 0.5) -> Goal:
        goal = Goal(
            content=content, source=source, authority=authority,
            scope=scope, priority=priority,
        )
        self._goals[goal.goal_id] = goal
        return goal

    def remove_goal(self, goal_id: str) -> bool:
        if goal_id in self._goals:
            self._goals[goal_id].active = False
            return True
        return False

    def set_resource(self, name: str, amount: float) -> None:
        self._available_resources[name] = amount

    def record_action(self, action: str, reason: str = "",
                      influencing_info: Optional[list[str]] = None) -> None:
        record = ActionRecord(
            action=action, reason=reason,
            influencing_information=influencing_info or [],
        )
        self._recent_actions.append(record)
        if len(self._recent_actions) > self._max_recent_actions:
            self._recent_actions.pop(0)

    def record_architectural_change(self, description: str) -> None:
        self._architectural_changes.append(ArchitecturalChange(description=description))

    def update_state(self, key: str, value: Any) -> None:
        self._current_state[key] = value

    def query(self, query_type: SelfModelQuery) -> Any:
        """Query the self model."""
        if query_type == SelfModelQuery.WHO_AM_I:
            return {
                "organism_id": self._organism_id,
                "system_version": self._system_version,
                "created_at": self._created_at,
                "active_capabilities": [c.name for c in self._capabilities.values() if c.enabled],
                "active_goals": [g.content for g in self._goals.values() if g.active],
            }
        elif query_type == SelfModelQuery.WHAT_CAN_I_DO:
            return {
                name: cap.description
                for name, cap in self._capabilities.items() if cap.enabled
            }
        elif query_type == SelfModelQuery.WHAT_CANT_I_DO:
            return list(self._limitations)
        elif query_type == SelfModelQuery.WHAT_DO_I_BELIEVE:
            return {
                b.content: b.confidence
                for b in self._beliefs.values()
            }
        elif query_type == SelfModelQuery.HOW_CONFIDENT:
            beliefs = list(self._beliefs.values())
            if not beliefs:
                return 0.5
            return sum(b.confidence for b in beliefs) / len(beliefs)
        elif query_type == SelfModelQuery.WHAT_CHANGED:
            return [
                {"description": c.description, "timestamp": c.timestamp}
                for c in self._architectural_changes[-10:]
            ]
        elif query_type == SelfModelQuery.WHY_ACTION:
            if self._recent_actions:
                last = self._recent_actions[-1]
                return {"action": last.action, "reason": last.reason}
            return None
        elif query_type == SelfModelQuery.WHAT_INFLUENCED:
            if self._recent_actions:
                return self._recent_actions[-1].influencing_information
            return []
        return None

    def snapshot(self) -> dict:
        """Full snapshot of the self model state."""
        return {
            "organism_id": self._organism_id,
            "system_version": self._system_version,
            "capabilities": {n: {"desc": c.description, "enabled": c.enabled}
                             for n, c in self._capabilities.items()},
            "limitations": list(self._limitations),
            "beliefs": {b.content: b.confidence for b in self._beliefs.values()},
            "goals": [g.content for g in self._goals.values() if g.active],
            "resources": dict(self._available_resources),
            "state": dict(self._current_state),
            "recent_actions_count": len(self._recent_actions),
            "architectural_changes_count": len(self._architectural_changes),
        }
