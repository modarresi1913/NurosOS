"""
Environment API — Environment Abstraction for Embodiment.

Environment {
    observe()    — Get current observation from the environment
    act()        — Execute an action in the environment
    step()       — Advance environment by one timestep
    reset()      — Reset environment to initial state
    reward()     — Get current reward signal
    constraints() — Get environment constraints
    state()      — Get full environment state
}

Supports: toy environments, grid worlds, physics simulators,
scientific simulations, virtual worlds, robotics environments.

The objective is NOT to build every simulator.
The objective is to make NurosOS environment-agnostic.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Callable


@dataclass
class EnvironmentState:
    """Full state of an environment."""
    observation: Any = None
    reward: float = 0.0
    done: bool = False
    info: dict[str, Any] = field(default_factory=dict)
    timestep: int = 0


class Environment:
    """
    Abstract Environment — The world an organism inhabits.

    Provides the standard observe/act/step/reset interface.
    Can wrap any simulator: grid world, physics engine,
    API endpoint, etc.
    """

    def __init__(self, env_id: str = "", name: str = "abstract"):
        self._env_id = env_id or str(uuid.uuid4())
        self._name = name
        self._state = EnvironmentState()
        self._step_callback: Optional[Callable] = None
        self._reset_callback: Optional[Callable] = None
        self._observation_callback: Optional[Callable] = None
        self._action_callback: Optional[Callable] = None
        self._reward_callback: Optional[Callable] = None
        self._constraints: dict[str, Any] = {}
        self._action_history: list[tuple[int, Any, float]] = []
        self._initialized: bool = False

    @property
    def env_id(self) -> str:
        return self._env_id

    @property
    def name(self) -> str:
        return self._name

    def set_callbacks(
        self,
        step: Optional[Callable] = None,
        reset: Optional[Callable] = None,
        observe: Optional[Callable] = None,
        act: Optional[Callable] = None,
        reward: Optional[Callable] = None,
    ) -> None:
        self._step_callback = step
        self._reset_callback = reset
        self._observation_callback = observe
        self._action_callback = act
        self._reward_callback = reward

    def reset(self) -> Any:
        """Reset environment to initial state."""
        if self._reset_callback:
            obs = self._reset_callback()
        else:
            obs = None
        self._state = EnvironmentState(observation=obs, timestep=0)
        self._action_history.clear()
        self._initialized = True
        return obs

    def observe(self) -> Any:
        """Get current observation."""
        if self._observation_callback:
            return self._observation_callback(self._state)
        return self._state.observation

    def act(self, action: Any) -> Any:
        """Execute an action in the environment."""
        if self._action_callback:
            result = self._action_callback(action, self._state)
        else:
            result = None
        self._action_history.append((self._state.timestep, action, time.time()))
        return result

    def step(self, action: Any = None) -> EnvironmentState:
        """Advance environment by one timestep with an optional action."""
        if action is not None:
            self.act(action)
        if self._step_callback:
            obs, reward, done, info = self._step_callback(action, self._state)
            self._state = EnvironmentState(
                observation=obs, reward=reward, done=done,
                info=info, timestep=self._state.timestep + 1,
            )
        else:
            self._state.timestep += 1
        return self._state

    def reward(self) -> float:
        """Get current reward signal."""
        if self._reward_callback:
            return self._reward_callback(self._state)
        return self._state.reward

    def constraints(self) -> dict[str, Any]:
        """Get environment constraints."""
        return dict(self._constraints)

    def set_constraints(self, **kwargs) -> None:
        self._constraints.update(kwargs)

    @property
    def state(self) -> EnvironmentState:
        return self._state

    @property
    def is_done(self) -> bool:
        return self._state.done

    @property
    def timestep(self) -> int:
        return self._state.timestep

    def summary(self) -> dict:
        return {
            "env_id": self._env_id,
            "name": self._name,
            "timestep": self._state.timestep,
            "done": self._state.done,
            "actions_taken": len(self._action_history),
            "last_reward": self._state.reward,
        }


class GridWorld(Environment):
    """Simple grid world environment for organism experiments."""

    def __init__(self, width: int = 10, height: int = 10):
        super().__init__(name="grid_world")
        self._width = width
        self._height = height
        self._agent_pos: tuple[int, int] = (0, 0)
        self._goal_pos: tuple[int, int] = (width - 1, height - 1)
        self._obstacles: set[tuple[int, int]] = set()

        def reset_fn():
            self._agent_pos = (0, 0)
            return self._get_observation()

        def step_fn(action, state):
            dx, dy = {"up": (0,-1), "down": (0,1), "left": (-1,0), "right": (1,0)}.get(action, (0,0))
            new_x = max(0, min(self._width - 1, self._agent_pos[0] + dx))
            new_y = max(0, min(self._height - 1, self._agent_pos[1] + dy))
            if (new_x, new_y) not in self._obstacles:
                self._agent_pos = (new_x, new_y)
            done = self._agent_pos == self._goal_pos
            reward = 1.0 if done else -0.01
            obs = self._get_observation()
            return obs, reward, done, {"position": self._agent_pos}

        self.set_callbacks(reset=reset_fn, step=step_fn)

    def _get_observation(self) -> dict:
        return {
            "agent_position": self._agent_pos,
            "goal_position": self._goal_pos,
            "distance_to_goal": abs(self._agent_pos[0] - self._goal_pos[0]) + abs(self._agent_pos[1] - self._goal_pos[1]),
        }

    def add_obstacle(self, x: int, y: int) -> None:
        self._obstacles.add((x, y))
