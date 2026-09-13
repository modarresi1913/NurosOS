"""Organism-4: Social Organism.

Extends Organism-3 with:
    - Theory of mind (modeling other agents)
    - Communication capability
    - Collaborative and competitive strategies
    
Still incapable of:
    - Full autonomous goal-setting
"""

from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.memory import MemoryType

from organisms.organism_3 import Organism3


class Organism4(Organism3):
    """Organism-4: Social Organism.
    
    Adds:
        - Theory of mind
        - Communication
        - Social reasoning
    """

    def __init__(self, name: str = "organism-4", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config.genome_id = "organism-4"
        self.config.description = "Social organism: self-model + theory of mind + communication"
        self.other_agent_models: dict[str, dict] = {}
        self.communications: list[dict] = []

    def model_other(self, agent_id: str, observation: dict[str, Any]) -> dict[str, Any]:
        """Build/maintain a model of another agent."""
        if agent_id not in self.other_agent_models:
            self.other_agent_models[agent_id] = {
                "observations": [],
                "predicted_goals": [],
                "reliability": 0.5,
            }
        
        model = self.other_agent_models[agent_id]
        model["observations"].append(observation)
        
        # Store in semantic memory
        self.memory.remember(
            content={"type": "other_agent", "agent_id": agent_id, "observation": observation},
            memory_type=MemoryType.SEMANTIC,
            importance=0.6,
            context={"organism_level": 4, "social": True}
        )
        
        return model

    def communicate(self, message: dict[str, Any], recipient: str = "broadcast") -> dict[str, Any]:
        """Send a communication to another agent or broadcast."""
        comm = {
            "sender": self.config.name,
            "recipient": recipient,
            "content": message,
            "tick": len(self.communications),
        }
        self.communications.append(comm)
        
        self.memory.remember(
            content={"type": "communication", **comm},
            memory_type=MemoryType.EPISODIC,
            importance=0.5,
            context={"organism_level": 4}
        )
        
        return comm

    def receive_communication(self, comm: dict[str, Any]) -> None:
        """Process incoming communication."""
        sender = comm.get("sender", "unknown")
        self.memory.remember(
            content={"type": "received_communication", **comm},
            memory_type=MemoryType.EPISODIC,
            importance=0.6,
            context={"organism_level": 4, "from": sender}
        )

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base.update({
            "organism_type": "Organism-4",
            "known_agents": len(self.other_agent_models),
            "communications": len(self.communications),
        })
        return base
