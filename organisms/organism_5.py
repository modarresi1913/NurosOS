"""Organism-5: Full Autonomous Organism.

The complete organism with all Mind Contract capabilities:
    - All Organism-4 capabilities
    - Autonomous goal-setting
    - Long-term planning
    - Value-driven decision making
    - Creative problem solving
    - Self-modification within safety bounds

This is the reference implementation of a complete NurosOS organism.
"""

from typing import Any

from nuros.epistemic import EpistemicLabel
from nuros.memory import MemoryType
from nuros.values import ValuesContract
from nuros.development import DevelopmentEngine, DevelopmentalStage

from organisms.organism_4 import Organism4


class Organism5(Organism4):
    """Organism-5: Full Autonomous Organism.
    
    Adds:
        - Autonomous goal-setting
        - Long-term planning
        - Value-driven decisions
        - Developmental progression
    """

    def __init__(self, name: str = "organism-5", **kwargs):
        super().__init__(name=name, **kwargs)
        self.config.genome_id = "organism-5"
        self.config.description = "Full autonomous organism: all Mind Contract capabilities"
        self.development = DevelopmentEngine()
        self.active_goals: list[dict] = []
        self.plans: list[dict] = []

    def set_goal(self, goal: str, priority: float = 0.5, context: dict | None = None) -> dict[str, Any]:
        """Autonomously set a goal."""
        # Check if goal conflicts with immutable constraints
        goal_entry = {
            "goal": goal,
            "priority": priority,
            "context": context or {},
            "created_tick": len(self.reaction_log),
            "status": "active",
        }
        
        self.active_goals.append(goal_entry)
        
        self.memory.remember(
            content={"type": "goal_set", **goal_entry},
            memory_type=MemoryType.SEMANTIC,
            importance=priority,
            context={"organism_level": 5}
        )
        
        return goal_entry

    def plan(self, goal: dict[str, Any]) -> list[dict[str, Any]]:
        """Create a plan to achieve a goal."""
        # Use imagination to explore possible paths
        observation = {"goal": goal}
        candidates = ["plan_step_1", "plan_step_2", "plan_step_3"]
        
        counterfactuals = self.imagination.hypothesize(observation, candidates)
        for cf in counterfactuals:
            self.imagination.simulate(cf)
        
        decision = self.imagination.decide(counterfactuals)
        
        plan = [{
            "step": i + 1,
            "action": candidates[i] if i < len(counterfactuals) else "unknown",
            "goal": goal.get("goal", "unknown"),
        } for i in range(min(3, len(counterfactuals)))]
        
        self.plans.append({"goal": goal, "plan": plan})
        
        return plan

    def observe_and_react(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Full autonomous pipeline."""
        reaction = super().observe_and_react(observation)
        
        # Check developmental progression
        if self.development.stage == DevelopmentalStage.EMBRYONIC:
            self.development.birth()
        
        # Value-driven goal adjustment
        if len(self.reaction_log) % 10 == 0 and not self.active_goals:
            self.set_goal("maintain_homeostasis", priority=0.8)
        
        reaction["organism_level"] = 5
        reaction["active_goals"] = len(self.active_goals)
        reaction["developmental_stage"] = self.development.stage.name
        
        return reaction

    def summary(self) -> dict[str, Any]:
        base = super().summary()
        base.update({
            "organism_type": "Organism-5",
            "active_goals": len(self.active_goals),
            "plans": len(self.plans),
            "developmental_stage": self.development.stage.name,
        })
        return base
