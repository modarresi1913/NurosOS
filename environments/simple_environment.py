"""Simple Environment for Organism Testing.

A minimal environment that organisms can interact with.
Provides observations and accepts actions.
"""

import random
import math
from typing import Any


class SimpleEnvironment:
    """A simple 2D grid-like environment for testing organisms."""

    def __init__(self, size: int = 10, n_objects: int = 5):
        self.size = size
        self.tick = 0
        self.agent_position = [size // 2, size // 2]
        self.objects: list[dict] = []

        for i in range(n_objects):
            self.objects.append({
                "id": i,
                "position": [random.randint(0, size-1), random.randint(0, size-1)],
                "type": random.choice(["food", "obstacle", "goal", "neutral"]),
                "value": random.uniform(-1, 1),
            })

    def observe(self) -> dict[str, Any]:
        """Get current observation."""
        nearby = []
        for obj in self.objects:
            dx = obj["position"][0] - self.agent_position[0]
            dy = obj["position"][1] - self.agent_position[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 3:
                nearby.append({**obj, "distance": dist})

        return {
            "tick": self.tick,
            "position": self.agent_position.copy(),
            "nearby_objects": nearby,
            "n_objects_visible": len(nearby),
        }

    def act(self, action: dict[str, Any]) -> dict[str, Any]:
        """Execute an action in the environment."""
        action_type = action.get("action", "wait")

        if action_type == "move":
            dx = action.get("dx", 0)
            dy = action.get("dy", 0)
            self.agent_position[0] = max(0, min(self.size-1, self.agent_position[0] + dx))
            self.agent_position[1] = max(0, min(self.size-1, self.agent_position[1] + dy))

        self.tick += 1
        return {"success": True, "new_position": self.agent_position.copy()}

    def reset(self) -> None:
        """Reset environment to initial state."""
        self.tick = 0
        self.agent_position = [self.size // 2, self.size // 2]


class NoopEnvironment:
    """An environment that does nothing. For unit testing."""

    def observe(self) -> dict:
        return {"tick": 0}

    def act(self, action: dict) -> dict:
        return {"success": True}

    def reset(self) -> None:
        pass
