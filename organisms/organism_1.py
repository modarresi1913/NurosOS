"""Organism-1: Predictive Organism.

Extends Organism-0 with:
    - Prediction capability (anticipate next observation)
    - Prediction error tracking
    - Semantic memory formation from repeated patterns
    
Still incapable of:
    - Self-reflection
    - Imagination / counterfactual reasoning
    - Planning
"""

from typing import Any

from nuros.epistemic import EpistemicKernel, EpistemicLabel
from nuros.memory import MemoryContract, MemoryType
from nuros.homeostasis import HomeostasisKernel
from nuros.organism import Organism, OrganismConfig

from organisms.organism_0 import Organism0


class Organism1(Organism0):
    """Organism-1: Predictive Organism.
    
    Adds:
        - Prediction of next observation
        - Prediction error computation
        - Semantic memory from patterns
    """

    def __init__(self, name: str = "organism-1", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config.genome_id = "organism-1"
        self.config.description = "Predictive organism: sensory loop + prediction + semantic memory"
        self.predictions: list[dict] = []
        self.prediction_errors: list[float] = []
        self._last_prediction: dict | None = None

    def observe_and_react(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Observe → Predict → Remember → React pipeline."""
        # 1. Check prediction error if we had a prediction
        if self._last_prediction is not None:
            error = self._compute_prediction_error(observation, self._last_prediction)
            self.prediction_errors.append(error)
            self.homeostasis.set("prediction_error", error)
            
            # If error is high, this is surprising — increase importance
            importance = min(1.0, 0.3 + error)

            # Store prediction error as episodic memory
            self.memory.remember(
                content={"prediction": self._last_prediction, "actual": observation, "error": error},
                memory_type=MemoryType.EPISODIC,
                importance=importance,
            )
        else:
            importance = 0.5

        # 2. Epistemic labeling
        obs_rep = self.epistemic.observe(observation)
        
        # 3. Store observation
        self.memory.remember(
            content=observation,
            memory_type=MemoryType.EPISODIC,
            importance=importance,
            context={"organism_level": 1}
        )
        
        # 4. Generate prediction for next step
        self._last_prediction = self._predict(observation)
        pred_rep = self.epistemic.predict(self._last_prediction)
        self.predictions.append(self._last_prediction)
        
        # 5. Check homeostasis and react
        self.homeostasis.tick()
        reaction = self._predictive_reaction(observation, self._last_prediction)
        
        # 6. Record
        self.responsibility.record_action(
            action=reaction,
            cause={"observation": observation, "prediction": self._last_prediction},
            epistemic_label=EpistemicLabel.ACTED
        )
        
        self.reaction_log.append({
            "tick": len(self.reaction_log),
            "observation": observation,
            "prediction": self._last_prediction,
            "reaction": reaction
        })
        
        return reaction

    def _predict(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Simple prediction: assume next observation is similar to current."""
        recent = self.memory.retrieve(query=None, limit=3)
        if not recent:
            return observation  # No history, predict same as current
        
        # Weight recent observations
        predicted = {}
        for key in observation:
            values = [entry.content.get(key, 0) for entry in recent if isinstance(entry.content, dict)]
            if values:
                predicted[key] = sum(values) / len(values)
            else:
                predicted[key] = observation[key]
        
        return predicted

    def _compute_prediction_error(self, actual: dict, predicted: dict) -> float:
        """Compute mean absolute error between prediction and actual."""
        if not predicted:
            return 1.0
        errors = []
        for key in predicted:
            if key in actual:
                try:
                    errors.append(abs(float(actual[key]) - float(predicted[key])))
                except (TypeError, ValueError):
                    errors.append(0.0 if actual[key] == predicted[key] else 1.0)
            else:
                errors.append(1.0)
        return sum(errors) / len(errors) if errors else 0.0

    def _predictive_reaction(self, observation: dict, prediction: dict) -> dict:
        """React considering prediction."""
        energy = self.homeostasis.get("energy")
        avg_error = sum(self.prediction_errors[-10:]) / max(1, len(self.prediction_errors[-10:]))
        
        return {
            "type": "predictive_react",
            "energy_level": energy,
            "avg_prediction_error": avg_error,
            "action": "explore" if avg_error > 0.5 else "exploit",
        }

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base.update({
            "organism_type": "Organism-1",
            "predictions": len(self.predictions),
            "avg_prediction_error": sum(self.prediction_errors) / max(1, len(self.prediction_errors)),
        })
        return base
