"""
SimpleResourceWorld — Python port of the Rust ResourceWorld (nuros-dev/src/environment.rs).

This is a faithful Python reimplementation of the Rust ResourceWorld for
the scientific audit's experiment harness. It does NOT require the Rust
extension to be built.

Key difference from the Rust original: the `privileged_obs` flag controls
whether the observation payload includes the privileged fields
(direction_to_resource, nearest_resource_distance, on_resource, on_hazard,
total_resource_left, resource_count). When False, only agent_pos is emitted.

This toggle is CRITICAL for the audit (RESEARCH_AUDIT.md §11 — the env
is "teacher-shaped" because it leaks privileged state).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimpleRng:
    """Minimal deterministic RNG matching the Rust SimpleRng (LCG)."""
    state: int

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next_u32(self) -> int:
        # Simple LCG matching the Rust implementation.
        self.state = (self.state * 6364136223846793005 + 1) & 0xFFFFFFFFFFFFFFFF
        return (self.state >> 32) & 0xFFFFFFFF

    def next_f64(self) -> float:
        return self.next_u32() / float(0xFFFFFFFF + 1)


class SimpleResourceWorld:
    """Python port of Rust ResourceWorld.

    2D grid with resources and hazards. The organism must locate and
    consume resources. Variables: energy gain from consumption, distance
    traveled, risk from hazardous cells, resource availability.

    Args:
        width, height: Grid dimensions.
        seed: RNG seed for deterministic resource/hazard placement.
        n_resources: Number of resource cells (default 5).
        n_hazards: Number of hazard cells (default 3).
        privileged_obs: If True (default), emit privileged observation
            fields (direction_to_resource, etc.). If False, emit only
            agent_pos.
    """

    def __init__(self, width: int = 8, height: int = 8, seed: int = 42,
                 n_resources: int = 5, n_hazards: int = 3,
                 privileged_obs: bool = True):
        self.width = width
        self.height = height
        self.seed = seed
        self.n_resources = n_resources
        self.n_hazards = n_hazards
        self.privileged_obs = privileged_obs
        self.step_count = 0
        self.agent_pos = (width // 2, height // 2)
        self.initial_agent_pos = self.agent_pos
        self.resources: list[list] = []  # [[x, y, quantity], ...]
        self.hazards: list[tuple] = []
        self._generate()
        self.initial_resources = [r.copy() for r in self.resources]

    def _generate(self):
        rng = SimpleRng(self.seed)
        used = set()
        self.resources = []
        while len(self.resources) < self.n_resources:
            x = rng.next_u32() % max(1, self.width)
            y = rng.next_u32() % max(1, self.height)
            if (x, y) not in used:
                used.add((x, y))
                qty = 0.5 + rng.next_f64() * 0.5
                self.resources.append([x, y, qty])
        rng2 = SimpleRng(self.seed + 1)
        self.hazards = []
        while len(self.hazards) < self.n_hazards:
            x = rng2.next_u32() % max(1, self.width)
            y = rng2.next_u32() % max(1, self.height)
            if (x, y) not in used:
                used.add((x, y))
                self.hazards.append((x, y))

    def reset(self) -> dict[str, Any]:
        self.agent_pos = self.initial_agent_pos
        self.resources = [r.copy() for r in self.initial_resources]
        self.step_count = 0
        return self.observe()

    def observe(self) -> dict[str, Any]:
        ax, ay = self.agent_pos
        # Nearest resource (Manhattan distance + direction).
        nearest_dist = -1.0
        dir_x, dir_y = 0, 0
        for rx, ry, qty in self.resources:
            if qty <= 0.0:
                continue
            dx = rx - ax
            dy = ry - ay
            dist = abs(dx) + abs(dy)
            if nearest_dist < 0 or dist < nearest_dist:
                nearest_dist = dist
                dir_x, dir_y = dx, dy
        on_resource = any(r[0] == ax and r[1] == ay and r[2] > 0 for r in self.resources)
        on_hazard = (ax, ay) in self.hazards

        if self.privileged_obs:
            total_left = sum(r[2] for r in self.resources)
            count = sum(1 for r in self.resources if r[2] > 0)
            return {
                "agent_pos": [ax, ay],
                "nearest_resource_distance": nearest_dist,
                "direction_to_resource": [dir_x, dir_y],
                "on_resource": on_resource,
                "on_hazard": on_hazard,
                "total_resource_left": total_left,
                "resource_count": count,
            }
        else:
            # Raw mode: only agent_pos. No privileged fields.
            return {"agent_pos": [ax, ay]}

    def step(self, action: str) -> tuple[dict[str, Any], float, bool]:
        self.step_count += 1
        dx, dy = self._action_delta(action)
        new_x = max(0, min(self.width - 1, self.agent_pos[0] + dx))
        new_y = max(0, min(self.height - 1, self.agent_pos[1] + dy))
        self.agent_pos = (new_x, new_y)

        reward = -0.01  # step cost

        if action == "consume":
            for r in self.resources:
                if r[0] == new_x and r[1] == new_y and r[2] > 0:
                    reward += r[2]
                    r[2] = 0.0
                    break
            else:
                reward -= 0.05  # wasted consume

        if (new_x, new_y) in self.hazards:
            reward -= 0.2

        done = all(r[2] <= 0 for r in self.resources)
        return self.observe(), reward, done

    @staticmethod
    def _action_delta(action: str) -> tuple[int, int]:
        return {
            "move_right": (1, 0), "move_left": (-1, 0),
            "move_up": (0, 1), "move_down": (0, -1),
            "idle": (0, 0), "consume": (0, 0),
        }.get(action, (0, 0))

    def hash_str(self) -> str:
        return json.dumps({
            "w": self.width, "h": self.height, "seed": self.seed,
            "agent": list(self.agent_pos),
            "resources": [[r[0], r[1], r[2]] for r in self.resources],
            "hazards": list(self.hazards),
            "step": self.step_count,
        }, sort_keys=True)


class SimpleChangingWorld:
    """Python port of Rust ChangingWorld — 1D shifting-resource env."""

    def __init__(self, size: int = 10, shift_interval: int = 20, seed: int = 42,
                 privileged_obs: bool = True):
        self.size = size
        self.shift_interval = shift_interval
        self.seed = seed
        self.privileged_obs = privileged_obs
        self.step_count = 0
        self.agent_pos = 0
        self.resource_pos = size // 2
        self.initial_agent_pos = 0
        self.initial_resource_pos = size // 2
        self.shifts = 0

    def reset(self) -> dict[str, Any]:
        self.agent_pos = self.initial_agent_pos
        self.resource_pos = self.initial_resource_pos
        self.step_count = 0
        self.shifts = 0
        return self.observe()

    def _maybe_shift(self):
        if self.step_count > 0 and self.step_count % self.shift_interval == 0:
            rng = SimpleRng(self.seed + self.shifts)
            new_pos = rng.next_u32() % max(1, self.size)
            if new_pos != self.resource_pos:
                self.resource_pos = new_pos
                self.shifts += 1

    def observe(self) -> dict[str, Any]:
        dist = abs(self.agent_pos - self.resource_pos)
        on_resource = self.agent_pos == self.resource_pos
        if self.privileged_obs:
            return {
                "agent_pos": self.agent_pos,
                "resource_pos": self.resource_pos,
                "distance_to_resource": dist,
                "on_resource": on_resource,
            }
        else:
            return {"agent_pos": self.agent_pos}

    def step(self, action: str) -> tuple[dict[str, Any], float, bool]:
        self.step_count += 1
        if action == "move_right":
            self.agent_pos = min(self.size - 1, self.agent_pos + 1)
        elif action == "move_left":
            self.agent_pos = max(0, self.agent_pos - 1)
        # idle and consume don't move the agent in 1D.
        self._maybe_shift()
        on_resource = self.agent_pos == self.resource_pos
        if action == "consume" and on_resource:
            reward = 1.0
        elif action == "consume" and not on_resource:
            reward = -0.05
        else:
            reward = -0.01  # step cost
        return self.observe(), reward, False
