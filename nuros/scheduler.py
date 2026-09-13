"""
Metabolic Cognitive Scheduler — Resource-Aware Process Scheduling.

Extends ordinary scheduling (CPU → process → task) with:
    internal state → resource availability → cognitive priority → process scheduling

Prioritizes processes based on:
    urgency, uncertainty, prediction error, energy cost,
    goal relevance, safety, environmental pressure

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional, Callable


class ProcessPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class CognitiveProcess:
    """A schedulable cognitive process."""
    process_id: str
    name: str
    priority: ProcessPriority = ProcessPriority.MEDIUM
    urgency: float = 0.5
    uncertainty: float = 0.0
    prediction_error: float = 0.0
    energy_cost: float = 1.0
    goal_relevance: float = 0.5
    safety_critical: bool = False
    environmental_pressure: float = 0.0
    deadline: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    last_run: float = 0.0
    run_count: int = 0


class MetabolicCognitiveScheduler:
    """
    The Metabolic Cognitive Scheduler.

    Schedules cognitive processes based on internal state,
    resource availability, and cognitive priority — not just
    CPU time slices.
    """

    def __init__(self, total_energy: float = 100.0):
        self._processes: dict[str, CognitiveProcess] = {}
        self._total_energy = total_energy
        self._available_energy: float = total_energy
        self._schedule_history: list[dict] = []
        self._current_tick: int = 0

    def register_process(self, process: CognitiveProcess) -> None:
        self._processes[process.process_id] = process

    def remove_process(self, process_id: str) -> None:
        self._processes.pop(process_id, None)

    def schedule(self, homeostasis_state: Optional[dict] = None) -> list[CognitiveProcess]:
        """
        Run one scheduling cycle. Returns ordered list of processes to execute.
        """
        self._current_tick += 1

        if not self._processes:
            return []

        # Calculate metabolic priority score for each process
        scored: list[tuple[float, CognitiveProcess]] = []
        for proc in self._processes.values():
            score = self._calculate_metabolic_score(proc, homeostasis_state)
            scored.append((score, proc))

        # Sort by score (highest priority first)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Filter by available energy
        scheduled = []
        remaining_energy = self._available_energy
        for score, proc in scored:
            if proc.energy_cost <= remaining_energy:
                scheduled.append(proc)
                remaining_energy -= proc.energy_cost
                proc.last_run = time.time()
                proc.run_count += 1

        self._schedule_history.append({
            "tick": self._current_tick,
            "scheduled": [p.process_id for p in scheduled],
            "energy_used": self._available_energy - remaining_energy,
        })

        return scheduled

    def _calculate_metabolic_score(
        self, proc: CognitiveProcess,
        homeostasis_state: Optional[dict],
    ) -> float:
        """
        Calculate metabolic priority score.

        Factors:
            - Base priority (higher priority processes get higher scores)
            - Urgency (more urgent = higher score)
            - Uncertainty (higher uncertainty = higher score for exploration)
            - Prediction error (higher error = higher score for learning)
            - Goal relevance (more relevant = higher score)
            - Safety criticality (safety processes always get high scores)
            - Energy efficiency (lower cost = slight bonus)
            - Environmental pressure
        """
        # Base priority score (invert so CRITICAL=0 gets highest score)
        priority_score = (4 - proc.priority.value) / 4.0

        # Urgency component
        urgency_score = proc.urgency

        # Uncertainty-driven exploration
        uncertainty_score = proc.uncertainty * 0.3

        # Prediction error-driven learning
        prediction_score = proc.prediction_error * 0.3

        # Goal relevance
        goal_score = proc.goal_relevance * 0.2

        # Safety criticality — always high
        safety_score = 1.0 if proc.safety_critical else 0.0

        # Energy efficiency
        energy_score = 1.0 / (1.0 + proc.energy_cost)

        # Environmental pressure
        env_score = proc.environmental_pressure * 0.2

        # Homeostatic modulation
        homeo_mod = 1.0
        if homeostasis_state:
            # Low energy → deprioritize non-critical
            if homeostasis_state.get("energy", 1.0) < 0.3 and not proc.safety_critical:
                homeo_mod = 0.5
            # High threat → prioritize safety
            if homeostasis_state.get("threat_level", 0.0) > 0.7:
                if proc.safety_critical:
                    homeo_mod = 2.0

        total = (
            priority_score * 0.2 +
            urgency_score * 0.25 +
            uncertainty_score +
            prediction_score +
            goal_score +
            safety_score * 0.5 +
            energy_score * 0.1 +
            env_score
        ) * homeo_mod

        return total

    def set_energy(self, amount: float) -> None:
        self._available_energy = min(amount, self._total_energy)

    @property
    def available_energy(self) -> float:
        return self._available_energy

    @property
    def tick(self) -> int:
        return self._current_tick

    def summary(self) -> dict:
        return {
            "registered_processes": len(self._processes),
            "available_energy": self._available_energy,
            "total_energy": self._total_energy,
            "current_tick": self._current_tick,
            "schedule_cycles": len(self._schedule_history),
        }
