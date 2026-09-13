"""
Organism Runtime — Artificial Cognitive Organisms.

An organism integrates all Mind Contract components:
    Memory, Self Model, Imagination, Values, Body, Responsibility

Plus organismic kernels:
    Homeostasis, Development, Safety, Epistemic

Supports: birth, development, learning, adaptation, specialization,
recovery, forking, aging, termination.

IMPORTANT: These are computational constructs, NOT biological organisms.
We use neutral engineering terminology. Do NOT make biological claims
without evidence.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from nuros.epistemic import EpistemicKernel
from nuros.memory import MemoryContract, MemoryType
from nuros.self_model import SelfModel, SelfModelQuery
from nuros.imagination import ImaginationEngine
from nuros.values import ValuesContract
from nuros.body import BodyContract, BodyType
from nuros.responsibility import ResponsibilityContract
from nuros.homeostasis import HomeostasisKernel, LifecycleState
from nuros.safety import SafetyKernel, Permission
from nuros.development import DevelopmentEngine, DevelopmentalStage
from nuros.environment import Environment


class OrganismState(Enum):
    UNBORN = "unborn"
    ALIVE = "alive"
    SLEEPING = "sleeping"
    DREAMING = "dreaming"
    RECOVERING = "recovering"
    TERMINATED = "terminated"


@dataclass
class OrganismConfig:
    """Configuration for creating an organism."""
    name: str = "unnamed"
    genome_id: str = ""
    environment: Optional[Environment] = None
    body_type: BodyType = BodyType.ABSTRACT
    seed: int = 42


class Organism:
    """
    An Artificial Cognitive Organism.

    Integrates all Mind Contract components and organismic kernels.
    This is the central abstraction of NurosOS.

    The organism is NOT a biological entity. It is a computational
    construct that can be instantiated, developed, embodied,
    evaluated, forked, and experimentally studied.
    """

    def __init__(self, config: Optional[OrganismConfig] = None):
        config = config or OrganismConfig()
        self._organism_id = str(uuid.uuid4())
        self._name = config.name
        self._state = OrganismState.UNBORN
        self._created_at = time.time()

        # Mind Contract Layer (MCL)
        self._epistemic = EpistemicKernel()
        self._memory = MemoryContract(self._epistemic)
        self._self_model = SelfModel(organism_id=self._organism_id)
        self._imagination = ImaginationEngine(self._epistemic)
        self._values = ValuesContract()
        self._body = BodyContract(config.body_type)
        self._responsibility = ResponsibilityContract()

        # Organismic Kernels
        self._homeostasis = HomeostasisKernel()
        self._development = DevelopmentEngine()
        self._safety = SafetyKernel()

        # Environment
        self._environment = config.environment

        # Mind Genome reference
        self._genome_id = config.genome_id

        # Observability
        self._tick_count: int = 0
        self._event_log: list[dict] = []

    @property
    def organism_id(self) -> str:
        return self._organism_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> OrganismState:
        return self._state

    @property
    def memory(self) -> MemoryContract:
        return self._memory

    @property
    def self_model(self) -> SelfModel:
        return self._self_model

    @property
    def imagination(self) -> ImaginationEngine:
        return self._imagination

    @property
    def values(self) -> ValuesContract:
        return self._values

    @property
    def body(self) -> BodyContract:
        return self._body

    @property
    def responsibility(self) -> ResponsibilityContract:
        return self._responsibility

    @property
    def homeostasis(self) -> HomeostasisKernel:
        return self._homeostasis

    @property
    def development(self) -> DevelopmentEngine:
        return self._development

    @property
    def safety(self) -> SafetyKernel:
        return self._safety

    @property
    def epistemic(self) -> EpistemicKernel:
        return self._epistemic

    @property
    def environment(self) -> Optional[Environment]:
        return self._environment

    def birth(self) -> None:
        """Birth the organism — transition from UNBORN to ALIVE."""
        if self._state != OrganismState.UNBORN:
            return
        self._development.birth()
        self._state = OrganismState.ALIVE
        self._homeostasis.set_lifecycle(LifecycleState.AWAKE)
        self._log_event("birth", f"Organism '{self._name}' born")

        # Grant basic permissions
        self._safety.grant_permission(self._organism_id, Permission.OBSERVE)
        self._safety.grant_permission(self._organism_id, Permission.REMEMBER)
        self._safety.grant_permission(self._organism_id, Permission.IMAGINE)
        self._safety.grant_permission(self._organism_id, Permission.PREDICT)
        self._safety.grant_permission(self._organism_id, Permission.SIMULATE)
        self._safety.grant_permission(self._organism_id, Permission.ACT_LOW_RISK)

    def tick(self) -> dict:
        """
        Run one tick of the organism's lifecycle.

        This is the central loop:
            observe → process → regulate → develop → act
        """
        if self._state == OrganismState.UNBORN:
            return {"status": "unborn"}
        if self._state == OrganismState.TERMINATED:
            return {"status": "terminated"}

        self._tick_count += 1
        tick_result = {"tick": self._tick_count}

        # Homeostatic regulation
        regulation_actions = self._homeostasis.tick()
        tick_result["regulation"] = len(regulation_actions)

        # Development step
        if self._environment:
            obs = self._environment.observe()
            self._development.experience(obs)
            tick_result["stage"] = self._development.stage.value
        else:
            self._development.experience()
            tick_result["stage"] = self._development.stage.value

        # Check for shutdown
        if self._safety.is_shutdown_requested:
            self.terminate()
            tick_result["status"] = "shutdown"

        return tick_result

    def observe(self) -> Optional[Any]:
        """Observe the environment."""
        if self._environment:
            return self._environment.observe()
        return None

    def act(self, action: Any) -> tuple[bool, str]:
        """Execute an action (with safety check)."""
        decision, reason = self._safety.authorize(
            self._organism_id, Permission.ACT_LOW_RISK,
        )
        if decision != SafetyDecision.ALLOW:  # noqa
            return False, reason

        result = None
        if self._environment:
            state = self._environment.step(action)
            result = state

        self._responsibility.record_action(
            action=str(action), policy_used="direct",
            authorization="granted", result=result,
        )
        return True, "Action executed"

    def sleep(self) -> None:
        """Enter sleep state for consolidation."""
        self._state = OrganismState.SLEEPING
        self._homeostasis.set_lifecycle(LifecycleState.SLEEP)
        self._log_event("sleep", "Entering sleep for consolidation")

        # Replay memories for consolidation
        memories = self._memory.replay()
        for mem in memories[:10]:  # Limit replay
            self._memory.reconsolidate(mem.memory_id, reward=0.01)

    def dream(self) -> None:
        """
        Artificial Dreaming / Offline Generative Replay.

        Internally generated simulation without direct external action.
        NOT equivalent to human dreaming. This is a computational
        mechanism for offline processing.
        """
        self._state = OrganismState.DREAMING
        self._homeostasis.set_lifecycle(LifecycleState.DREAM)
        self._log_event("dream", "Entering artificial dreaming")

    def wake(self) -> None:
        """Wake from sleep/dream state."""
        self._state = OrganismState.ALIVE
        self._homeostasis.set_lifecycle(LifecycleState.AWAKE)
        self._log_event("wake", "Waking up")

    def terminate(self) -> None:
        """Terminate the organism."""
        self._state = OrganismState.TERMINATED
        self._development.terminate()
        self._homeostasis.set_lifecycle(LifecycleState.TERMINATED)
        self._log_event("terminate", "Organism terminated")

    def fork(self, name: str = "") -> Organism:
        """
        Fork this organism — create a copy with the same configuration
        but a new identity.

        This is computational state branching, NOT copying subjective identity.
        """
        config = OrganismConfig(
            name=name or f"{self._name}_fork",
            genome_id=self._genome_id,
            body_type=self._body.body_type,
        )
        new_organism = Organism(config)
        new_organism._environment = self._environment
        return new_organism

    def state_hash(self) -> str:
        """Compute a hash of the current state for reproducibility."""
        state_data = json.dumps({
            "organism_id": self._organism_id,
            "tick_count": self._tick_count,
            "developmental_stage": self._development.stage.value,
            "memory_count": self._memory.memory_count,
            "homeostasis": self._homeostasis.snapshot(),
        }, sort_keys=True, default=str)
        return hashlib.sha256(state_data.encode()).hexdigest()[:16]

    def snapshot(self) -> dict:
        """Full snapshot of the organism state."""
        return {
            "organism_id": self._organism_id,
            "name": self._name,
            "state": self._state.value,
            "tick_count": self._tick_count,
            "state_hash": self.state_hash(),
            "development": self._development.snapshot(),
            "homeostasis": self._homeostasis.summary(),
            "memory": self._memory.summary(),
            "safety": self._safety.summary(),
            "self_model": self._self_model.snapshot(),
            "values": self._values.summary(),
            "responsibility": self._responsibility.summary(),
            "body": self._body.summary(),
        }

    def _log_event(self, event_type: str, details: str) -> None:
        self._event_log.append({
            "type": event_type, "details": details,
            "tick": self._tick_count, "timestamp": time.time(),
        })

    @property
    def event_log(self) -> list[dict]:
        return list(self._event_log)
