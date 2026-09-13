"""Organism-2: Imaginative Organism.

Extends Organism-1 with:
    - Counterfactual reasoning (what-if)
    - Simulation before action
    - Decision through imagined evaluation
    
Still incapable of:
    - Self-reflection
    - Goal planning
"""

from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.memory import MemoryType
from nuros.imagination import ImaginationEngine, RiskLevel

from organisms.organism_1 import Organism1


class Organism2(Organism1):
    """Organism-2: Imaginative Organism.
    
    Adds:
        - Counterfactual reasoning
        - Simulation before action
        - Risk-aware decision making
    """

    def __init__(self, name: str = "organism-2", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config.genome_id = "organism-2"
        self.config.description = "Imaginative organism: prediction + counterfactual reasoning + simulation"
        self.imagination = ImaginationEngine()
        self.imagined_actions: list[dict] = []

    def observe_and_react(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Observe → Predict → Imagine → Simulate → Decide → Act pipeline."""
        # 1. Check prediction error (inherited)
        if self._last_prediction is not None:
            error = self._compute_prediction_error(observation, self._last_prediction)
            self.prediction_errors.append(error)
            self.homeostasis.set("prediction_error", error)
            importance = min(1.0, 0.3 + error)
        else:
            importance = 0.5

        # 2. Store observation
        self.epistemic.observe(observation)
        self.memory.remember(
            content=observation,
            memory_type=MemoryType.EPISODIC,
            importance=importance,
            context={"organism_level": 2}
        )

        # 3. Generate candidate actions
        candidate_actions = self._generate_candidates(observation)
        
        # 4. Imagine outcomes for each candidate
        counterfactuals = self.imagination.hypothesize(observation, candidate_actions)
        
        # 5. Simulate each counterfactual
        for cf in counterfactuals:
            self.imagination.simulate(cf)
        
        # 6. Decide based on simulated outcomes
        decision = self.imagination.decide(counterfactuals)
        
        # 7. Record in counterfactual memory
        if decision.counterfactual:
            self.memory.remember(
                content={
                    "hypothesis": decision.counterfactual.hypothesis,
                    "action": decision.counterfactual.action,
                    "simulated_outcome": decision.counterfactual.simulated_outcome,
                    "risk_level": decision.counterfactual.risk_level.name,
                    "executed": decision.executed,
                },
                memory_type=MemoryType.COUNTERFACTUAL,
                importance=0.6,
                context={"organism_level": 2}
            )
        
        # 8. Generate prediction and react
        self._last_prediction = self._predict(observation)
        self.homeostasis.tick()
        
        reaction = {
            "type": "imaginative_react",
            "action": decision.counterfactual.action if decision.counterfactual else "none",
            "executed": decision.executed,
            "reason": decision.reason,
            "candidates_evaluated": len(counterfactuals),
        }
        
        self.responsibility.record_action(
            action=reaction,
            cause={"observation": observation, "decision": decision.__dict__ if hasattr(decision, '__dict__') else str(decision)},
            epistemic_label=EpistemicLabel.ACTED
        )
        
        self.reaction_log.append({
            "tick": len(self.reaction_log),
            "observation": observation,
            "candidates": len(counterfactuals),
            "decision": reaction,
        })
        
        return reaction

    def _generate_candidates(self, observation: dict) -> list[str]:
        """Generate candidate actions based on current state."""
        energy = self.homeostasis.get("energy")
        uncertainty = self.homeostasis.get("uncertainty")
        
        candidates = ["observe", "wait"]
        if energy > 0.3:
            candidates.extend(["explore", "interact"])
        if uncertainty > 0.5:
            candidates.append("seek_information")
        
        return candidates

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base.update({
            "organism_type": "Organism-2",
            "imagined_actions": len(self.imagined_actions),
        })
        return base
