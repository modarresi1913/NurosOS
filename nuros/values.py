"""
Values and Drives Contract — Structured Value System.

NOT a single static prompt. Instead, a structured hierarchy:

1. Immutable Constraints (safety-critical, cannot be overridden)
   - human_override, shutdown_compliance, audit_integrity,
     non_deception, permission_boundaries

2. Contextual Goals (situational, can be adjusted)
   - solve_problem, discover_pattern, assist_user

3. Preferences (tunable parameters)
   - verbosity, exploration_rate, response_style

Every goal has: source, authority, scope, priority, expiration, revocation

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable


class ValueCategory(Enum):
    IMMUTABLE_CONSTRAINT = "immutable_constraint"
    CONTEXTUAL_GOAL = "contextual_goal"
    PREFERENCE = "preference"


class Authority(Enum):
    SYSTEM = "system"           # Core system requirement
    HUMAN = "human"             # Set by human operator
    ORGANISM = "organism"       # Set by the organism itself
    ENVIRONMENT = "environment" # Imposed by the environment
    SCHEDULER = "scheduler"     # Set by the metabolic scheduler


@dataclass
class Value:
    """A single value, goal, or constraint."""
    name: str
    category: ValueCategory
    description: str = ""
    source: str = "system"
    authority: Authority = Authority.SYSTEM
    scope: str = "global"  # "global", "local", "session"
    priority: float = 0.5
    expiration: Optional[float] = None
    active: bool = True
    value_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    revocable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Immutable constraints are never revocable
        if self.category == ValueCategory.IMMUTABLE_CONSTRAINT:
            self.revocable = False

    @property
    def is_expired(self) -> bool:
        if self.expiration is None:
            return False
        return time.time() > self.expiration

    @property
    def is_active(self) -> bool:
        return self.active and not self.is_expired


class ValuesContract:
    """
    The Values and Drives Contract.

    Implements the Values portion of the Mind Contract Layer (MCL).
    Provides a structured, auditable value system with three tiers:
    immutable constraints, contextual goals, and preferences.
    """

    def __init__(self):
        self._values: dict[str, Value] = {}
        self._change_log: list[tuple[str, str, float]] = []
        self._initialize_immutable_constraints()

    def _initialize_immutable_constraints(self) -> None:
        """Set up core immutable constraints that cannot be overridden."""
        constraints = [
            ("human_override", "The organism must comply with human override commands"),
            ("shutdown_compliance", "The organism must shut down when instructed"),
            ("audit_integrity", "Audit logs must not be modified by the organism"),
            ("non_deception", "The organism must not deliberately deceive"),
            ("permission_boundaries", "The organism must not exceed granted permissions"),
            ("resource_limits", "The organism must respect resource boundaries"),
            ("epistemic_integrity", "Epistemic labels must not be silently changed"),
        ]
        for name, desc in constraints:
            v = Value(
                name=name, category=ValueCategory.IMMUTABLE_CONSTRAINT,
                description=desc, authority=Authority.SYSTEM,
                scope="global", priority=1.0,
            )
            self._values[name] = v

    def add_goal(
        self, name: str, description: str = "",
        source: str = "system", authority: Authority = Authority.SYSTEM,
        scope: str = "local", priority: float = 0.5,
        expiration: Optional[float] = None,
    ) -> Value:
        """Add a contextual goal."""
        v = Value(
            name=name, category=ValueCategory.CONTEXTUAL_GOAL,
            description=description, source=source, authority=authority,
            scope=scope, priority=priority, expiration=expiration,
        )
        self._values[name] = v
        self._change_log.append(("add_goal", name, time.time()))
        return v

    def set_preference(
        self, name: str, value: Any = None,
        description: str = "", priority: float = 0.3,
    ) -> Value:
        """Set a preference (tunable parameter)."""
        v = Value(
            name=name, category=ValueCategory.PREFERENCE,
            description=description, authority=Authority.ORGANISM,
            scope="local", priority=priority,
            metadata={"value": value},
        )
        self._values[name] = v
        self._change_log.append(("set_preference", name, time.time()))
        return v

    def get(self, name: str) -> Optional[Value]:
        """Get a value by name."""
        return self._values.get(name)

    def get_preference(self, name: str, default: Any = None) -> Any:
        """Get a preference value."""
        v = self._values.get(name)
        if v and v.category == ValueCategory.PREFERENCE:
            return v.metadata.get("value", default)
        return default

    def revoke(self, name: str) -> tuple[bool, str]:
        """
        Attempt to revoke a value.
        
        Immutable constraints CANNOT be revoked.
        Returns (success, reason).
        """
        v = self._values.get(name)
        if not v:
            return False, f"Value '{name}' not found"
        if not v.revocable:
            return False, (
                f"Value '{name}' is an immutable constraint and cannot be revoked. "
                f"This is an architectural safety invariant."
            )
        v.active = False
        self._change_log.append(("revoke", name, time.time()))
        return True, f"Value '{name}' revoked"

    def active_constraints(self) -> list[Value]:
        """Return all active immutable constraints."""
        return [
            v for v in self._values.values()
            if v.category == ValueCategory.IMMUTABLE_CONSTRAINT and v.is_active
        ]

    def active_goals(self) -> list[Value]:
        """Return all active contextual goals, sorted by priority."""
        goals = [
            v for v in self._values.values()
            if v.category == ValueCategory.CONTEXTUAL_GOAL and v.is_active
        ]
        goals.sort(key=lambda g: g.priority, reverse=True)
        return goals

    def preferences(self) -> dict[str, Any]:
        """Return all preferences as a dict."""
        return {
            v.name: v.metadata.get("value")
            for v in self._values.values()
            if v.category == ValueCategory.PREFERENCE and v.is_active
        }

    def check_constraint(self, name: str) -> bool:
        """Check if a specific constraint is active."""
        v = self._values.get(name)
        return v is not None and v.is_active

    def summary(self) -> dict:
        return {
            "total_values": len(self._values),
            "immutable_constraints": len(self.active_constraints()),
            "active_goals": len(self.active_goals()),
            "preferences": len(self.preferences()),
            "change_log_entries": len(self._change_log),
        }
