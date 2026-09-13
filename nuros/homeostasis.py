"""
Homeostasis Kernel — Internal Operational State Maintenance.

The organism must maintain viable internal operation through
regulation of: energy, arousal, uncertainty, sensory_load,
prediction_error, memory_pressure, threat_level,
exploration_drive, stability, resource_budget.

Example regulations:
    high uncertainty     → increase exploration
    high prediction error → increase learning
    high sensory load    → reduce exploration
    low resource availability → reduce computation
    instability          → enter recovery mode

This is NOT biological homeostasis. It is a computational mechanism
for maintaining viable internal operation.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable


class LifecycleState(Enum):
    AWAKE = "awake"
    SLEEP = "sleep"
    DREAM = "dream"
    CONSOLIDATE = "consolidate"
    RECOVER = "recover"
    TERMINATED = "terminated"


class RegulationDirection(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"


@dataclass
class HomeostaticVariable:
    """A single homeostatic variable with bounds and current value."""
    name: str
    value: float = 0.5
    min_value: float = 0.0
    max_value: float = 1.0
    optimal_value: float = 0.5
    tolerance: float = 0.2  # Acceptable deviation from optimal
    decay_rate: float = 0.01

    @property
    def deviation(self) -> float:
        return abs(self.value - self.optimal_value)

    @property
    def is_stable(self) -> bool:
        return self.deviation <= self.tolerance

    @property
    def needs_regulation(self) -> bool:
        return not self.is_stable

    @property
    def normalized(self) -> float:
        """Value normalized to [0, 1]."""
        rng = self.max_value - self.min_value
        if rng == 0:
            return 0.0
        return (self.value - self.min_value) / rng


@dataclass
class RegulationAction:
    """A regulatory action triggered by homeostatic imbalance."""
    variable_name: str
    direction: RegulationDirection
    magnitude: float
    reason: str
    timestamp: float = field(default_factory=time.time)


class HomeostasisKernel:
    """
    The Homeostasis Kernel.

    Maintains internal operational state through computational
    regulation mechanisms. Inspired by biological homeostasis
    but NOT claiming biological equivalence.
    """

    def __init__(self):
        self._variables: dict[str, HomeostaticVariable] = {}
        self._regulation_history: list[RegulationAction] = []
        self._lifecycle: LifecycleState = LifecycleState.AWAKE
        self._regulation_rules: list[Callable] = []
        self._initialize_variables()
        self._initialize_regulation_rules()

    def _initialize_variables(self) -> None:
        defaults = [
            ("energy", 0.8, 0.0, 1.0, 0.8, 0.2),
            ("arousal", 0.5, 0.0, 1.0, 0.5, 0.2),
            ("uncertainty", 0.3, 0.0, 1.0, 0.2, 0.15),
            ("sensory_load", 0.3, 0.0, 1.0, 0.3, 0.2),
            ("prediction_error", 0.2, 0.0, 1.0, 0.1, 0.15),
            ("memory_pressure", 0.3, 0.0, 1.0, 0.3, 0.2),
            ("threat_level", 0.1, 0.0, 1.0, 0.0, 0.1),
            ("exploration_drive", 0.5, 0.0, 1.0, 0.5, 0.2),
            ("stability", 0.8, 0.0, 1.0, 0.9, 0.15),
            ("resource_budget", 0.7, 0.0, 1.0, 0.7, 0.2),
        ]
        for name, val, lo, hi, opt, tol in defaults:
            self._variables[name] = HomeostaticVariable(
                name=name, value=val, min_value=lo, max_value=hi,
                optimal_value=opt, tolerance=tol,
            )

    def _initialize_regulation_rules(self) -> None:
        """Default regulation rules (computational, not biological)."""
        self._regulation_rules = [
            self._rule_high_uncertainty,
            self._rule_high_prediction_error,
            self._rule_high_sensory_load,
            self._rule_low_resources,
            self._rule_instability,
            self._rule_high_threat,
        ]

    def _rule_high_uncertainty(self) -> list[RegulationAction]:
        """High uncertainty → increase exploration."""
        actions = []
        if self._variables["uncertainty"].value > 0.6:
            actions.append(RegulationAction(
                variable_name="exploration_drive",
                direction=RegulationDirection.INCREASE,
                magnitude=0.1,
                reason="High uncertainty: increasing exploration",
            ))
        return actions

    def _rule_high_prediction_error(self) -> list[RegulationAction]:
        """High prediction error → increase learning (increase arousal)."""
        actions = []
        if self._variables["prediction_error"].value > 0.5:
            actions.append(RegulationAction(
                variable_name="arousal",
                direction=RegulationDirection.INCREASE,
                magnitude=0.1,
                reason="High prediction error: increasing arousal for learning",
            ))
        return actions

    def _rule_high_sensory_load(self) -> list[RegulationAction]:
        """High sensory load → reduce exploration."""
        actions = []
        if self._variables["sensory_load"].value > 0.7:
            actions.append(RegulationAction(
                variable_name="exploration_drive",
                direction=RegulationDirection.DECREASE,
                magnitude=0.1,
                reason="High sensory load: reducing exploration",
            ))
        return actions

    def _rule_low_resources(self) -> list[RegulationAction]:
        """Low resources → reduce computation."""
        actions = []
        if self._variables["resource_budget"].value < 0.3:
            actions.append(RegulationAction(
                variable_name="arousal",
                direction=RegulationDirection.DECREASE,
                magnitude=0.1,
                reason="Low resources: reducing computation",
            ))
        return actions

    def _rule_instability(self) -> list[RegulationAction]:
        """Instability → enter recovery mode."""
        actions = []
        if self._variables["stability"].value < 0.3:
            actions.append(RegulationAction(
                variable_name="stability",
                direction=RegulationDirection.INCREASE,
                magnitude=0.2,
                reason="Instability detected: entering recovery mode",
            ))
            self._lifecycle = LifecycleState.RECOVER
        return actions

    def _rule_high_threat(self) -> list[RegulationAction]:
        """High threat → reduce exploration, increase arousal."""
        actions = []
        if self._variables["threat_level"].value > 0.7:
            actions.append(RegulationAction(
                variable_name="exploration_drive",
                direction=RegulationDirection.DECREASE,
                magnitude=0.15,
                reason="High threat: reducing exploration",
            ))
            actions.append(RegulationAction(
                variable_name="arousal",
                direction=RegulationDirection.INCREASE,
                magnitude=0.1,
                reason="High threat: increasing alertness",
            ))
        return actions

    def tick(self) -> list[RegulationAction]:
        """Run one homeostatic regulation cycle."""
        all_actions = []
        for rule in self._regulation_rules:
            try:
                actions = rule()
                all_actions.extend(actions)
            except Exception:
                pass

        # Apply regulation actions
        for action in all_actions:
            var = self._variables.get(action.variable_name)
            if var:
                delta = action.magnitude * (
                    1 if action.direction == RegulationDirection.INCREASE
                    else -1 if action.direction == RegulationDirection.DECREASE
                    else 0
                )
                var.value = max(var.min_value, min(var.max_value, var.value + delta))
            self._regulation_history.append(action)

        # Apply natural decay
        for var in self._variables.values():
            # Decay toward optimal value
            diff = var.value - var.optimal_value
            var.value -= diff * var.decay_rate

        return all_actions

    def get(self, name: str) -> float:
        var = self._variables.get(name)
        return var.value if var else 0.0

    def set(self, name: str, value: float) -> None:
        var = self._variables.get(name)
        if var:
            var.value = max(var.min_value, min(var.max_value, value))

    @property
    def lifecycle_state(self) -> LifecycleState:
        return self._lifecycle

    def set_lifecycle(self, state: LifecycleState) -> None:
        self._lifecycle = state

    @property
    def is_stable(self) -> bool:
        return all(v.is_stable for v in self._variables.values())

    def snapshot(self) -> dict:
        return {
            name: {
                "value": v.value, "optimal": v.optimal_value,
                "stable": v.is_stable, "deviation": v.deviation,
            }
            for name, v in self._variables.items()
        }

    def summary(self) -> dict:
        return {
            "lifecycle": self._lifecycle.value,
            "stable": self.is_stable,
            "variables": {n: round(v.value, 3) for n, v in self._variables.items()},
            "regulation_actions": len(self._regulation_history),
        }
