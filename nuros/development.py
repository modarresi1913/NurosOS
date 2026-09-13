"""
Development Engine — Synthetic Development Runtime.

Instead of: fully specified brain → execute
Support: initial substrate → development → experience → plasticity
         → specialization → memory → behavior → self-model

The programmer increasingly specifies:
    rules, constraints, environment, resources,
    plasticity mechanisms, developmental objectives

rather than explicitly specifying every final cognitive behavior.

Core principle:
    "Program the conditions under which a mind can develop,
     not every behavior the mind must contain."

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable


class DevelopmentalStage(Enum):
    EMBRYONIC = "embryonic"       # Initial configuration
    NASCENT = "nascent"           # First experiences
    DEVELOPING = "developing"     # Active development
    MATURING = "maturing"         # Approaching stability
    MATURE = "mature"            # Stable behavior
    SPECIALIZED = "specialized"  # Domain-adapted
    AGING = "aging"             # Gradual decline
    TERMINATED = "terminated"    # No longer active


@dataclass
class DevelopmentalCheckpoint:
    """A checkpoint in the organism's developmental trajectory."""
    stage: DevelopmentalStage
    timestamp: float = field(default_factory=time.time)
    metrics: dict[str, float] = field(default_factory=dict)
    notes: str = ""
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class DevelopmentalRule:
    """A rule that governs development (NOT a behavior specification)."""
    name: str
    condition: Callable[..., bool]
    action: Callable[..., None]
    description: str = ""
    priority: float = 0.5
    active: bool = True


@dataclass
class PlasticityEvent:
    """Record of a structural adaptation."""
    description: str
    timestamp: float = field(default_factory=time.time)
    trigger: str = ""
    magnitude: float = 0.0


class DevelopmentEngine:
    """
    The Development Engine — Synthetic Development Runtime.

    Manages the developmental trajectory of an artificial organism.
    Instead of specifying every behavior, the programmer specifies
    the conditions, rules, and mechanisms under which behaviors
    can emerge through experience.
    """

    def __init__(self):
        self._stage: DevelopmentalStage = DevelopmentalStage.EMBRYONIC
        self._checkpoints: list[DevelopmentalCheckpoint] = []
        self._rules: list[DevelopmentalRule] = []
        self._plasticity_events: list[PlasticityEvent] = []
        self._experience_count: int = 0
        self._developmental_objectives: list[str] = []
        self._stage_transitions: list[tuple[DevelopmentalStage, DevelopmentalStage, float]] = []
        self._birth_time: float = time.time()

    @property
    def stage(self) -> DevelopmentalStage:
        return self._stage

    @property
    def age(self) -> float:
        """Age in seconds since birth (embryonic → nascent transition)."""
        return time.time() - self._birth_time

    @property
    def experience_count(self) -> int:
        return self._experience_count

    def add_rule(self, name: str, condition: Callable, action: Callable,
                 description: str = "", priority: float = 0.5) -> None:
        """Add a developmental rule."""
        self._rules.append(DevelopmentalRule(
            name=name, condition=condition, action=action,
            description=description, priority=priority,
        ))

    def add_objective(self, objective: str) -> None:
        """Add a developmental objective (what the organism should develop toward)."""
        self._developmental_objectives.append(objective)

    def birth(self) -> DevelopmentalCheckpoint:
        """Transition from EMBRYONIC to NASCENT — the organism begins experiencing."""
        if self._stage != DevelopmentalStage.EMBRYONIC:
            return self._checkpoints[-1] if self._checkpoints else DevelopmentalCheckpoint(self._stage)
        self._transition_to(DevelopmentalStage.NASCENT)
        cp = DevelopmentalCheckpoint(
            stage=DevelopmentalStage.NASCENT,
            notes="Organism born — beginning to experience environment",
        )
        self._checkpoints.append(cp)
        return cp

    def experience(self, experience_data: Any = None) -> None:
        """Process one experience. This is the core developmental driver."""
        self._experience_count += 1

        # Apply developmental rules
        for rule in sorted(self._rules, key=lambda r: r.priority, reverse=True):
            if rule.active:
                try:
                    if rule.condition(self._stage, self._experience_count, experience_data):
                        rule.action(self._stage, self._experience_count, experience_data)
                except Exception:
                    pass

        # Automatic stage transitions based on experience
        if self._stage == DevelopmentalStage.NASCENT and self._experience_count >= 10:
            self._transition_to(DevelopmentalStage.DEVELOPING)
        elif self._stage == DevelopmentalStage.DEVELOPING and self._experience_count >= 100:
            self._transition_to(DevelopmentalStage.MATURING)
        elif self._stage == DevelopmentalStage.MATURING and self._experience_count >= 500:
            self._transition_to(DevelopmentalStage.MATURE)

    def record_plasticity(self, description: str, trigger: str = "",
                          magnitude: float = 0.0) -> None:
        """Record a plasticity (structural adaptation) event."""
        self._plasticity_events.append(PlasticityEvent(
            description=description, trigger=trigger, magnitude=magnitude,
        ))

    def checkpoint(self, metrics: Optional[dict[str, float]] = None,
                   notes: str = "") -> DevelopmentalCheckpoint:
        """Create a developmental checkpoint."""
        cp = DevelopmentalCheckpoint(
            stage=self._stage, metrics=metrics or {}, notes=notes,
        )
        self._checkpoints.append(cp)
        return cp

    def _transition_to(self, new_stage: DevelopmentalStage) -> None:
        old = self._stage
        self._stage = new_stage
        self._stage_transitions.append((old, new_stage, time.time()))

    def terminate(self) -> None:
        self._transition_to(DevelopmentalStage.TERMINATED)

    @property
    def trajectory(self) -> list[tuple[str, str, float]]:
        """Full developmental trajectory as (from_stage, to_stage, timestamp)."""
        return [(s1.value, s2.value, t) for s1, s2, t in self._stage_transitions]

    def snapshot(self) -> dict:
        return {
            "stage": self._stage.value,
            "experience_count": self._experience_count,
            "age_seconds": self.age,
            "checkpoints": len(self._checkpoints),
            "plasticity_events": len(self._plasticity_events),
            "objectives": list(self._developmental_objectives),
            "trajectory": self.trajectory,
        }
