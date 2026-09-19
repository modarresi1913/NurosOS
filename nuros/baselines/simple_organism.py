"""
SimpleOrganism — Python port of the Rust MinimumOrganism (nuros-dev/src/organism.rs).

This is a faithful Python reimplementation of the Rust MinimumOrganism::tick()
logic for the scientific audit's experiment harness. It does NOT require the
Rust extension to be built.

Key features ported:
  - ε-greedy action selection with deterministic FNV-1a pseudo-random
    (mirrors organism.rs:573-584).
  - action_preferences learning: TD(0)-like update WITHOUT the max_a' term
    (mirrors organism.rs:206-213).
  - heuristic_bias(): the 6 hard-coded task-knowledge biases
    (mirrors organism.rs:451-503). CRITICAL for the audit.
  - disable_heuristic_bias flag: when True, heuristic_bias() returns 0.0.
  - Maturation schedule (organism.rs:507-528) — hard-coded stage transitions.
  - Plasticity decay (organism.rs:269).
  - Self-model rolling averages (organism.rs:239-244).
  - MemoryRecord storage with 200-entry cap (organism.rs:219-236).
  - Developmental state update (organism.rs:254-272).

The organism is deterministic given a fixed (genome_config, env_seed).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional


# Action list — matches the Rust Action enum.
ACTIONS = ["move_right", "move_left", "move_up", "move_down", "idle", "consume"]


def deterministic_random(step: int, salt: str) -> float:
    """FNV-1a hash → float in [0, 1). Mirrors organism.rs:573-584."""
    h = 0xcbf29ce484222325
    for b in step.to_bytes(8, "little", signed=False):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    for b in salt.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return (h >> 11) / float(1 << 53)


@dataclass
class GenomeConfig:
    """Mirrors the Rust DevelopmentalGenome's relevant fields."""
    learning_rate: float = 0.1
    forgetting_rate: float = 0.01
    exploration_bias: float = 0.3
    risk_sensitivity: float = 0.5
    perceive_cost: float = 0.01
    predict_cost: float = 0.01
    act_cost: float = 0.02
    idle_regen: float = 0.03
    nascent_to_developing: int = 10
    developing_to_maturing: int = 100
    maturing_to_mature: int = 500
    disable_heuristic_bias: bool = False
    disable_maturation: bool = False
    disable_plasticity_decay: bool = False
    disable_self_model: bool = False
    memory_cap: int = 200


class SimpleOrganism:
    """Python port of Rust MinimumOrganism.

    Parameters:
        genome: GenomeConfig with the genome's parameters.
        organism_id: unique ID for this organism.

    The organism is deterministic given a fixed genome + env_seed.
    """

    def __init__(self, genome: GenomeConfig, organism_id: str = "org"):
        self.genome = genome
        self.organism_id = organism_id
        self.step = 0
        self.action_preferences: dict[str, float] = {a: 0.0 for a in ACTIONS}
        self.memory: list[dict] = []
        self.total_reward = 0.0
        self.total_prediction_error = 0.0
        self.last_action: Optional[str] = None
        self.last_observation: dict = {}

        # Developmental state (mirrors DevelopmentalState).
        self.dev_age = 0
        self.dev_stage = "embryonic"
        self.dev_plasticity = 0.8
        self.dev_energy = 1.0
        self.dev_cognitive_load = 0.0
        self.dev_memory_capacity = 0.0
        self.dev_prediction_accuracy = 0.0
        self.dev_self_model_stability = 0.0
        self.dev_exploration_level = genome.exploration_bias
        self.dev_stability = 0.5

        # Self-model (mirrors SelfModel).
        self.sm_expected_reward = 0.0
        self.sm_expected_pe = 0.0
        self.sm_update_count = 0
        self.sm_believed_capabilities: dict[str, float] = {}

    def tick(self, env) -> dict[str, Any]:
        """Run one tick. Mirrors MinimumOrganism::tick (organism.rs:179-290)."""
        self.step += 1
        step = self.step

        # 1. Sensation.
        obs = env.observe()
        self.last_observation = obs

        # 2. Select action.
        candidate = self._select_action(obs)

        # 3-4. Execute + receive reward.
        predicted_reward = self.action_preferences.get(candidate, 0.0)
        next_obs, actual_reward, done = env.step(candidate)

        # 5. Learning.
        prediction_error = abs(predicted_reward - actual_reward)
        lr = self.genome.learning_rate * self.dev_plasticity
        entry = self.action_preferences.get(candidate, 0.0)
        entry += lr * (actual_reward - predicted_reward)
        entry *= 1.0 - self.genome.forgetting_rate
        self.action_preferences[candidate] = entry

        self.total_reward += actual_reward
        self.total_prediction_error += prediction_error
        self.last_action = candidate

        # 6a. Memory update.
        sig = json.dumps(obs, sort_keys=True)[:64]
        self.memory.append({
            "key": sig, "action": candidate, "reward": actual_reward,
            "prediction_error": prediction_error, "step": step,
        })
        if len(self.memory) > self.genome.memory_cap:
            self.memory.sort(key=lambda m: m.get("reward", 0), reverse=True)
            self.memory = self.memory[:self.genome.memory_cap]

        # 6b. Self-model update.
        if not self.genome.disable_self_model:
            alpha = 0.1
            self.sm_expected_reward = (1 - alpha) * self.sm_expected_reward + alpha * actual_reward
            self.sm_expected_pe = (1 - alpha) * self.sm_expected_pe + alpha * prediction_error
            self.sm_update_count += 1
            if candidate == "consume":
                cap = self.sm_believed_capabilities.get("consume", 0.0)
                self.sm_believed_capabilities["consume"] = (1 - alpha) * cap + alpha * (1.0 if actual_reward > 0 else 0.0)

        # 6c. Developmental state.
        self.dev_age = step
        self.dev_cognitive_load = min(1.0, self.dev_cognitive_load * 0.95 + 0.05)
        self.dev_memory_capacity = min(1.0, len(self.memory) / self.genome.memory_cap)
        self.dev_prediction_accuracy = 1.0 / (1.0 + self.sm_expected_pe)
        self.dev_self_model_stability = min(1.0, self.dev_self_model_stability * 0.99 + 0.01 * (1.0 - self.dev_cognitive_load))
        cost = self.genome.perceive_cost + self.genome.predict_cost + (0.0 if candidate == "idle" else self.genome.act_cost)
        regen = self.genome.idle_regen if candidate == "idle" else 0.0
        self.dev_energy = max(0.0, min(1.0, self.dev_energy - cost + regen))
        if not self.genome.disable_plasticity_decay:
            self.dev_plasticity = max(0.05, self.dev_plasticity * 0.999)
        self.dev_stability = 0.5 * self.dev_stability + 0.5 * self.dev_prediction_accuracy

        # 7. Maturation.
        if not self.genome.disable_maturation:
            self._apply_maturation()

        return {
            "step": step, "action": candidate, "reward": actual_reward,
            "prediction_error": prediction_error, "predicted_reward": predicted_reward,
            "dev_stage": self.dev_stage, "energy": self.dev_energy,
            "plasticity": self.dev_plasticity, "memory_size": len(self.memory),
        }

    def _select_action(self, obs: dict) -> str:
        """ε-greedy + heuristic_bias. Mirrors organism.rs:408-441."""
        obs_sig = json.dumps(obs, sort_keys=True)[:64]
        pseudo = deterministic_random(self.step, f"{self._state_hash()}|{obs_sig}")

        if pseudo < self.dev_exploration_level:
            # Explore.
            actions = ACTIONS
            idx = int(deterministic_random(self.step + 1, f"{self._state_hash()}|{obs_sig}") * len(actions)) % len(actions)
            return actions[idx]

        # Exploit: argmax(pref + bias).
        best_action = "idle"
        best_score = float("-inf")
        for a in ACTIONS:
            pref = self.action_preferences.get(a, 0.0)
            bias = self._heuristic_bias(a, obs)
            score = pref + bias
            if score > best_score:
                best_score = score
                best_action = a
        return best_action

    def _heuristic_bias(self, action: str, obs: dict) -> float:
        """The 6 hard-coded biases. Mirrors organism.rs:451-503.

        CRITICAL for the audit: this is the task knowledge that confounds
        the learning claim.
        """
        if self.genome.disable_heuristic_bias:
            return 0.0

        on_resource = obs.get("on_resource", False)
        on_hazard = obs.get("on_hazard", False)
        bias = 0.0

        if on_resource and action == "consume":
            bias += 0.5
        if on_hazard and action == "idle":
            bias -= 0.3

        direction = obs.get("direction_to_resource")
        if isinstance(direction, list) and len(direction) == 2:
            dx, dy = direction[0], direction[1]
            if abs(dx) >= abs(dy):
                if dx > 0 and action == "move_right": bias += 0.2
                if dx < 0 and action == "move_left": bias += 0.2
                if dy > 0 and action == "move_up": bias += 0.1
                if dy < 0 and action == "move_down": bias += 0.1
            else:
                if dy > 0 and action == "move_up": bias += 0.2
                if dy < 0 and action == "move_down": bias += 0.2
                if dx > 0 and action == "move_right": bias += 0.1
                if dx < 0 and action == "move_left": bias += 0.1
            if dx == 0 and dy == 0 and action == "consume":
                bias += 0.1

        nearest = obs.get("nearest_resource_distance")
        if isinstance(nearest, (int, float)) and nearest > 1.0:
            if action not in ("idle", "consume"):
                bias += 0.02

        return bias

    def _apply_maturation(self):
        """Mirrors organism.rs:507-528."""
        age = self.dev_age
        s = self.dev_stage
        if s == "embryonic":
            self.dev_stage = "nascent"
        elif s == "nascent" and age >= self.genome.nascent_to_developing:
            self.dev_stage = "developing"
        elif s == "developing" and age >= self.genome.developing_to_maturing:
            self.dev_stage = "maturing"
        elif s == "maturing" and age >= self.genome.maturing_to_mature:
            self.dev_stage = "mature"

    def _state_hash(self) -> str:
        """Simple hash for deterministic RNG."""
        return f"step={self.step}|reward={self.total_reward:.4f}|pe={self.total_prediction_error:.4f}"
