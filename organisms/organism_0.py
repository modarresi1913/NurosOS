"""Organism-0: Minimal Viable Organism.

The simplest organism that can exist: a sensory-motor loop with
episodic memory and basic homeostasis. No self-model, no imagination,
no planning. Pure reactivity with memory.

This is the ground state. Everything else is built on top of this.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from nuros.epistemic import EpistemicKernel, EpistemicLabel
from nuros.memory import MemoryContract, MemoryType
from nuros.homeostasis import HomeostasisKernel
from nuros.safety import SafetyKernel, Permission
from nuros.values import ValuesContract
from nuros.body import BodyContract
from nuros.responsibility import ResponsibilityContract
from nuros.organism import Organism, OrganismConfig, OrganismState


class Organism0(Organism):
    """Organism-0: Minimal Viable Organism — sensory loop only.
    
    Capabilities:
        - Observe environment through body
        - Store observations as episodic memories
        - Maintain homeostatic balance
        - React to observations (no planning)
    
    Incapable of:
        - Self-reflection
        - Imagination / counterfactual reasoning
        - Planning
        - Prediction
        - Goal-directed behavior
    """

    def __init__(self, name: str = "organism-0", **kwargs):
        config = OrganismConfig(
            name=name,
            genome_id="organism-0",
            description="Minimal viable organism: sensory-motor loop with episodic memory",
        )
        super().__init__(config, **kwargs)
        self.reaction_log: list[dict] = []

    def observe_and_react(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Observe → Remember → React pipeline."""
        # 1. Epistemic labeling of observation
        obs_rep = self.epistemic.observe(observation)
        
        # 2. Store in episodic memory
        self.memory.remember(
            content=observation,
            memory_type=MemoryType.EPISODIC,
            importance=0.5,
            context={"organism_level": 0}
        )
        
        # 3. Check homeostasis
        self.homeostasis.tick()
        
        # 4. Simple reaction (no planning, no imagination)
        reaction = self._simple_reaction(observation)
        
        # 5. Record in responsibility contract
        self.responsibility.record_action(
            action=reaction,
            cause={"observation": observation},
            epistemic_label=EpistemicLabel.ACTED
        )
        
        self.reaction_log.append({
            "tick": len(self.reaction_log),
            "observation": observation,
            "reaction": reaction
        })
        
        return reaction

    def _simple_reaction(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Generate simple reaction based on observation and homeostatic state."""
        energy = self.homeostasis.get("energy")
        uncertainty = self.homeostasis.get("uncertainty")
        
        reaction = {
            "type": "react",
            "energy_level": energy,
            "uncertainty": uncertainty,
            "action": "explore" if uncertainty > 0.6 else "exploit",
        }
        
        if energy < 0.3:
            reaction["action"] = "conserve"
        
        return reaction

    def summary(self) -> dict[str, Any]:
        return {
            "organism_type": "Organism-0",
            "state": self.state.name,
            "reactions": len(self.reaction_log),
            "memories": self.memory.memory_count,
            "homeostasis": self.homeostasis.summary(),
        }
