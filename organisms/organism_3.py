"""Organism-3: Self-Modeling Organism.

Extends Organism-2 with:
    - Computational self-model
    - Metacognition (thinking about thinking)
    - Self-assessment of capabilities and limitations
    
Still incapable of:
    - Social reasoning
    - Full autonomy
"""

from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.memory import MemoryType
from nuros.self_model import SelfModel, SelfModelQuery

from organisms.organism_2 import Organism2


class Organism3(Organism2):
    """Organism-3: Self-Modeling Organism.
    
    Adds:
        - Computational self-model
        - Metacognitive reflection
        - Self-assessment
    """

    def __init__(self, name: str = "organism-3", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config.genome_id = "organism-3"
        self.config.description = "Self-modeling organism: imagination + self-reflection + metacognition"
        self.self_model = SelfModel()
        self.reflection_log: list[dict] = []

    def reflect(self) -> dict[str, Any]:
        """Metacognitive reflection on own state."""
        # Query self-model about current capabilities
        capabilities = self.self_model.query(SelfModelQuery.CAPABILITIES)
        limitations = self.self_model.query(SelfModelQuery.LIMITATIONS)
        beliefs = self.self_model.query(SelfModelQuery.BELIEFS)
        
        # Assess current state
        assessment = {
            "memory_count": self.memory.memory_count,
            "avg_prediction_error": sum(self.prediction_errors[-20:]) / max(1, len(self.prediction_errors[-20:])),
            "energy": self.homeostasis.get("energy"),
            "uncertainty": self.homeostasis.get("uncertainty"),
            "capabilities": capabilities,
            "limitations": limitations,
            "beliefs": beliefs,
        }
        
        # Update self-model with assessment
        self.self_model.update_state(assessment)
        
        # Store reflection
        self.memory.remember(
            content={"type": "reflection", "assessment": assessment},
            memory_type=MemoryType.SEMANTIC,
            importance=0.7,
            context={"organism_level": 3}
        )
        
        self.reflection_log.append(assessment)
        return assessment

    def observe_and_react(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Observe → Predict → Imagine → Reflect → Decide → Act pipeline."""
        # Inherited pipeline
        reaction = super().observe_and_react(observation)
        
        # Periodic self-reflection
        if len(self.reaction_log) % 5 == 0:
            assessment = self.reflect()
            reaction["self_assessment"] = {
                "confidence": 1.0 - assessment.get("avg_prediction_error", 0.5),
                "energy_sufficient": assessment.get("energy", 0) > 0.3,
            }
        
        return reaction

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base.update({
            "organism_type": "Organism-3",
            "reflections": len(self.reflection_log),
        })
        return base
