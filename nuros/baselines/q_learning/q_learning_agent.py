"""
Tabular Q-Learning Agent — for the NurosOS scientific audit.

Per docs/BASELINE_SPEC.md:
  - Standard tabular Q-learning with Bellman backup:
        Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]
  - eps-greedy action selection.
  - LRU eviction when the Q-table exceeds q_table_capacity (default 200).
  - Deterministic given a fixed seed (uses an FNV-1a-derived pseudo-random
    that mirrors the Rust MinimumOrganism::deterministic_random at
    organism.rs:573-584).

NO LLM dependency. NO neural network. NO NurosOS-privileged info beyond what
the env provides to any organism.
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

from nuros.baselines.q_learning.config import QLearningConfig


# ============================================================================
# Action space (mirrors nuros-dev/src/environment.rs:Action)
# ============================================================================

ACTIONS: list[str] = [
    "move_right", "move_left", "move_up", "move_down", "idle", "consume",
]
"""The same 6 actions as the Rust MinimumOrganism (environment.rs:32-45)."""


# ============================================================================
# Deterministic pseudo-random (mirrors organism.rs:573-584 FNV-1a)
# ============================================================================

def deterministic_random(step: int, salt: str) -> float:
    """Deterministic pseudo-random in [0, 1) derived from (step, salt).

    Mirrors the Rust MinimumOrganism::deterministic_random (organism.rs:573-584)
    so that the Q-learning baseline's eps-greedy exploration is reproducible
    AND uses the same RNG family as the NurosOS organism.
    """
    h: int = 0xcbf29ce484222325
    for b in step.to_bytes(8, "little", signed=False):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    for b in salt.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    # Take the top 53 bits to get a value in [0, 1).
    return (h >> 11) / float(1 << 53)


# ============================================================================
# State signature
# ============================================================================

def state_signature(obs: dict[str, Any], privileged: bool) -> str:
    """Compute the Q-table state signature from the observation payload.

    Privileged mode: (agent_pos, on_resource, on_hazard, direction_to_resource_quantized).
        Matches the information available to MinimumOrganism::heuristic_bias.
    Raw mode: (agent_pos) only.
        The Q-learner must learn from reward alone.
    """
    agent_pos = obs.get("agent_pos")
    if not privileged:
        return f"raw:{agent_pos}"
    on_resource = obs.get("on_resource", False)
    on_hazard = obs.get("on_hazard", False)
    direction = obs.get("direction_to_resource", [0, 0])
    dx = direction[0] if isinstance(direction, list) and len(direction) >= 1 else 0
    dy = direction[1] if isinstance(direction, list) and len(direction) >= 2 else 0
    # Quantize direction to one of 9 buckets: 8 compass + "on resource".
    if dx == 0 and dy == 0:
        dir_bucket = "on"
    elif abs(dx) >= abs(dy):
        dir_bucket = "E" if dx > 0 else "W"
    else:
        dir_bucket = "N" if dy > 0 else "S"
    return f"priv:{agent_pos}|r={int(bool(on_resource))}|h={int(bool(on_hazard))}|d={dir_bucket}"


# ============================================================================
# Q-learning agent
# ============================================================================

@dataclass
class QTableEntry:
    """A single (state, action) -> Q-value entry with LRU tracking."""
    q_value: float = 0.0
    last_used: int = 0  # step count at last access


class QLearningAgent:
    """Tabular Q-learning agent.

    Standard Q-update:
        Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]

    eps-greedy action selection. LRU eviction when the Q-table exceeds
    q_table_capacity (default 200 — matches the Rust organism cap).

    The agent is deterministic given a fixed (config, env_seed).
    """

    def __init__(self, config: QLearningConfig):
        self.config = config
        # OrderedDict for LRU: most-recently-used at the end.
        self._q_table: OrderedDict[str, QTableEntry] = OrderedDict()
        self._step: int = 0
        self._total_reward: float = 0.0
        self._total_q_updates: int = 0
        self._eviction_count: int = 0
        self._last_state: Optional[str] = None
        self._last_action: Optional[str] = None

    @property
    def step(self) -> int:
        return self._step

    @property
    def total_reward(self) -> float:
        return self._total_reward

    @property
    def q_table_size(self) -> int:
        return len(self._q_table)

    @property
    def total_q_updates(self) -> int:
        return self._total_q_updates

    @property
    def eviction_count(self) -> int:
        return self._eviction_count

    def select_action(self, obs_payload: dict[str, Any]) -> str:
        """eps-greedy action selection.

        With probability epsilon, pick uniformly random.
        Otherwise, pick argmax_a Q(s, a).
        """
        self._step += 1
        sig = state_signature(obs_payload, self.config.privileged_obs)
        pseudo = deterministic_random(self._step, f"{sig}|eps")

        if pseudo < self.config.epsilon:
            # Explore: uniform random action.
            idx = int(deterministic_random(self._step + 1, f"{sig}|explore") * len(ACTIONS)) % len(ACTIONS)
            action = ACTIONS[idx]
        else:
            # Exploit: argmax_a Q(s, a).
            action = self._argmax_q(sig)

        self._last_state = sig
        self._last_action = action
        self._touch(sig)
        return action

    def update(self, obs_payload: dict[str, Any], action: str, reward: float,
               next_obs_payload: dict[str, Any], done: bool) -> None:
        """Q-update: Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]."""
        if self._last_state is None or self._last_action is None:
            return  # nothing to update (first step)

        s = self._last_state
        a = self._last_action
        s_next = state_signature(next_obs_payload, self.config.privileged_obs)

        q_sa = self._get_q(s, a)
        if done:
            target = reward
        else:
            max_q_next = max(
                (self._get_q(s_next, a_next) for a_next in ACTIONS),
                default=0.0,
            )
            target = reward + self.config.gamma * max_q_next
        new_q = q_sa + self.config.alpha * (target - q_sa)
        self._set_q(s, a, new_q)
        self._total_q_updates += 1

        self._total_reward += reward

    # ========================================================================
    # Q-table operations with LRU eviction
    # ========================================================================

    def _get_q(self, state: str, action: str) -> float:
        key = f"{state}|{action}"
        entry = self._q_table.get(key)
        if entry is None:
            return 0.0
        return entry.q_value

    def _set_q(self, state: str, action: str, q_value: float) -> None:
        key = f"{state}|{action}"
        if key in self._q_table:
            # Update existing + move to end (most recently used).
            self._q_table.move_to_end(key)
            self._q_table[key].q_value = q_value
            self._q_table[key].last_used = self._step
        else:
            # Evict LRU if at capacity.
            while len(self._q_table) >= self.config.q_table_capacity:
                self._q_table.popitem(last=False)  # pop least-recently-used
                self._eviction_count += 1
            self._q_table[key] = QTableEntry(q_value=q_value, last_used=self._step)

    def _touch(self, state: str) -> None:
        """Mark all (state, action) entries as recently used (LRU update)."""
        for action in ACTIONS:
            key = f"{state}|{action}"
            if key in self._q_table:
                self._q_table.move_to_end(key)
                self._q_table[key].last_used = self._step

    def _argmax_q(self, state: str) -> str:
        """Return the action with the highest Q-value at this state.

        Ties broken by action order (ACTIONS list order)."""
        best_action = ACTIONS[0]
        best_q = float("-inf")
        for action in ACTIONS:
            q = self._get_q(state, action)
            if q > best_q:
                best_q = q
                best_action = action
        return best_action

    # ========================================================================
    # Serialization
    # ========================================================================

    def snapshot(self) -> dict[str, Any]:
        """Serialize the agent state for checkpointing."""
        return {
            "config": self.config.to_dict(),
            "step": self._step,
            "total_reward": self._total_reward,
            "total_q_updates": self._total_q_updates,
            "eviction_count": self._eviction_count,
            "q_table_size": len(self._q_table),
            "q_table": [
                {"key": k, "q_value": v.q_value, "last_used": v.last_used}
                for k, v in self._q_table.items()
            ],
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore from a snapshot."""
        self._step = snapshot.get("step", 0)
        self._total_reward = snapshot.get("total_reward", 0.0)
        self._total_q_updates = snapshot.get("total_q_updates", 0)
        self._eviction_count = snapshot.get("eviction_count", 0)
        self._q_table.clear()
        for entry in snapshot.get("q_table", []):
            self._q_table[entry["key"]] = QTableEntry(
                q_value=entry["q_value"],
                last_used=entry["last_used"],
            )


# ============================================================================
# Episode runner
# ============================================================================

@dataclass
class EpisodeResult:
    """Result of running one Q-learning episode."""
    config: dict[str, Any]
    total_reward: float
    n_steps: int
    q_table_size: int
    total_q_updates: int
    eviction_count: int
    per_step: list[dict[str, Any]] = field(default_factory=list)
    final_q_table: dict[str, float] = field(default_factory=dict)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config,
            "total_reward": self.total_reward,
            "n_steps": self.n_steps,
            "q_table_size": self.q_table_size,
            "total_q_updates": self.total_q_updates,
            "eviction_count": self.eviction_count,
            "per_step": self.per_step,
            "final_q_table": self.final_q_table,
            "elapsed_seconds": self.elapsed_seconds,
        }


def run_q_learning_episode(
    env_step_fn,           # callable(action: str) -> (obs_payload: dict, reward: float, done: bool)
    env_reset_fn,          # callable() -> obs_payload: dict
    config: QLearningConfig,
) -> EpisodeResult:
    """Run one Q-learning episode against an env interface.

    The env interface is intentionally minimal so this runner can be used
    against any env (the non-stationary wrapper, a raw ResourceWorld via PyO3,
    or a mock env for testing).

    Args:
        env_step_fn: callable(action_name: str) -> (obs_payload, reward, done)
        env_reset_fn: callable() -> initial obs_payload
        config: QLearningConfig

    Returns: EpisodeResult.
    """
    agent = QLearningAgent(config)
    per_step: list[dict[str, Any]] = []

    start = time.perf_counter()

    obs = env_reset_fn()

    for step in range(config.n_steps):
        action = agent.select_action(obs)
        next_obs, reward, done = env_step_fn(action)
        agent.update(obs, action, reward, next_obs, done)
        per_step.append({
            "step": step + 1,
            "action": action,
            "reward": reward,
            "q_table_size": agent.q_table_size,
            "total_q_updates": agent.total_q_updates,
            "eviction_count": agent.eviction_count,
            "state_signature": state_signature(obs, config.privileged_obs),
        })
        obs = next_obs
        if done:
            break

    elapsed = time.perf_counter() - start

    final_q = {k: v.q_value for k, v in agent._q_table.items()}

    return EpisodeResult(
        config=config.to_dict(),
        total_reward=agent.total_reward,
        n_steps=len(per_step),
        q_table_size=agent.q_table_size,
        total_q_updates=agent.total_q_updates,
        eviction_count=agent.eviction_count,
        per_step=per_step,
        final_q_table=final_q,
        elapsed_seconds=elapsed,
    )
