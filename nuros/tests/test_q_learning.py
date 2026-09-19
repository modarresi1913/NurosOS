"""
Tests for the Q-learning baseline.

Verifies (per docs/BASELINE_SPEC.md):
  1. Determinism: same seed + same obs sequence -> same action sequence.
  2. Q-table capacity enforced (LRU eviction).
  3. Q-update rule is mathematically correct.
  4. State signature is correctly derived (privileged + raw).
  5. eps-greedy is deterministic given a seed.
  6. Result serialization round-trips.
"""

from __future__ import annotations

import unittest
from typing import Any

from nuros.baselines.q_learning import (
    DEFAULT_CONFIG,
    QLearningAgent,
    QLearningConfig,
    run_q_learning_episode,
)
from nuros.baselines.q_learning.q_learning_agent import (
    ACTIONS,
    QTableEntry,
    deterministic_random,
    state_signature,
)


# ============================================================================
# Mock env for deterministic testing
# ============================================================================

class MockEnv:
    """A minimal deterministic env for Q-learning tests."""

    def __init__(self, n_steps: int = 10, seed: int = 42):
        self.n_steps = n_steps
        self.seed = seed
        self.step_count = 0
        self._actions_taken: list[str] = []

    def reset(self) -> dict[str, Any]:
        self.step_count = 0
        self._actions_taken = []
        return self._obs()

    def step(self, action: str) -> tuple[dict[str, Any], float, bool]:
        self._actions_taken.append(action)
        self.step_count += 1
        # Deterministic reward: +1 if action == "consume" and on_resource; -0.1 otherwise.
        obs = self._obs()
        reward = 1.0 if (action == "consume" and obs.get("on_resource")) else -0.1
        done = self.step_count >= self.n_steps
        return obs, reward, done

    def _obs(self) -> dict[str, Any]:
        """Return a deterministic observation that varies with step_count."""
        on_resource = (self.step_count % 3 == 0)
        return {
            "agent_pos": [self.step_count % 5, self.step_count % 3],
            "on_resource": on_resource,
            "on_hazard": (self.step_count % 7 == 0),
            "direction_to_resource": [(self.step_count % 3) - 1, (self.step_count % 2) - 1],
            "nearest_resource_distance": float(self.step_count % 4),
            "total_resource_left": 5.0 - (self.step_count * 0.1),
            "resource_count": max(0, 5 - self.step_count),
        }


# ============================================================================
# Deterministic pseudo-random
# ============================================================================


class TestDeterministicRandom(unittest.TestCase):
    def test_returns_value_in_unit_interval(self):
        for step in range(100):
            for salt in ["a", "b", "test"]:
                v = deterministic_random(step, salt)
                self.assertGreaterEqual(v, 0.0)
                self.assertLess(v, 1.0)

    def test_deterministic(self):
        v1 = deterministic_random(42, "test_salt")
        v2 = deterministic_random(42, "test_salt")
        self.assertEqual(v1, v2)

    def test_different_steps_produce_different_values(self):
        v1 = deterministic_random(1, "salt")
        v2 = deterministic_random(2, "salt")
        # Extremely unlikely to coincide for an FNV-1a hash.
        self.assertNotEqual(v1, v2)


# ============================================================================
# State signature
# ============================================================================


class TestStateSignature(unittest.TestCase):
    def test_privileged_mode_includes_all_fields(self):
        obs = {
            "agent_pos": [3, 4],
            "on_resource": True,
            "on_hazard": False,
            "direction_to_resource": [1, -1],
        }
        sig = state_signature(obs, privileged=True)
        self.assertIn("priv:", sig)
        self.assertIn("[3, 4]", sig)
        self.assertIn("r=1", sig)
        self.assertIn("h=0", sig)
        # dx=1, dy=-1: |dx| >= |dy|, dx > 0 -> "E"
        self.assertIn("d=E", sig)

    def test_raw_mode_excludes_privileged_fields(self):
        obs = {
            "agent_pos": [3, 4],
            "on_resource": True,
            "on_hazard": False,
            "direction_to_resource": [1, -1],
        }
        sig = state_signature(obs, privileged=False)
        self.assertIn("raw:", sig)
        self.assertIn("[3, 4]", sig)
        self.assertNotIn("r=", sig)
        self.assertNotIn("d=", sig)

    def test_on_resource_direction(self):
        obs = {
            "agent_pos": [3, 4],
            "on_resource": True,
            "on_hazard": False,
            "direction_to_resource": [0, 0],
        }
        sig = state_signature(obs, privileged=True)
        self.assertIn("d=on", sig)

    def test_direction_north(self):
        obs = {"agent_pos": [3, 4], "on_resource": False, "on_hazard": False,
               "direction_to_resource": [0, 1]}
        sig = state_signature(obs, privileged=True)
        self.assertIn("d=N", sig)

    def test_direction_west(self):
        obs = {"agent_pos": [3, 4], "on_resource": False, "on_hazard": False,
               "direction_to_resource": [-2, 1]}
        sig = state_signature(obs, privileged=True)
        self.assertIn("d=W", sig)


# ============================================================================
# Q-learning agent
# ============================================================================


class TestQLearningAgent(unittest.TestCase):
    def setUp(self):
        self.config = QLearningConfig(seed=42, q_table_capacity=200)
        self.agent = QLearningAgent(self.config)

    def test_initial_state(self):
        self.assertEqual(self.agent.step, 0)
        self.assertEqual(self.agent.total_reward, 0.0)
        self.assertEqual(self.agent.q_table_size, 0)
        self.assertEqual(self.agent.total_q_updates, 0)
        self.assertEqual(self.agent.eviction_count, 0)

    def test_select_action_returns_valid_action(self):
        obs = {"agent_pos": [0, 0], "on_resource": False, "on_hazard": False,
               "direction_to_resource": [0, 0]}
        action = self.agent.select_action(obs)
        self.assertIn(action, ACTIONS)

    def test_determinism_given_same_seed_and_obs(self):
        obs = {"agent_pos": [0, 0], "on_resource": False, "on_hazard": False,
               "direction_to_resource": [1, 0]}
        a1 = QLearningAgent(self.config)
        a2 = QLearningAgent(self.config)
        actions1 = [a1.select_action(obs) for _ in range(20)]
        actions2 = [a2.select_action(obs) for _ in range(20)]
        self.assertEqual(actions1, actions2)

    def test_q_update_rule(self):
        """Verify Q(s,a) <- Q(s,a) + alpha * [r + gamma * max_a' Q(s',a') - Q(s,a)]."""
        config = QLearningConfig(alpha=0.1, gamma=0.95, epsilon=0.0, seed=42)
        agent = QLearningAgent(config)
        # Set up a known Q(s,a) = 1.0 for state_a|consume.
        agent._set_q("state_a", "consume", 1.0)
        # Set up Q(s', a') values for the ACTUAL next state signature.
        # The next obs is {"agent_pos": [1, 0]} — compute its signature.
        next_obs = {"agent_pos": [1, 0], "on_resource": False, "on_hazard": False,
                    "direction_to_resource": [0, 0]}
        s_next = state_signature(next_obs, privileged=True)
        agent._set_q(s_next, "move_right", 0.5)
        agent._set_q(s_next, "consume", 0.8)
        # Force the agent's last state + action.
        agent._last_state = "state_a"
        agent._last_action = "consume"
        # Reward = 0.5; next state = s_next; max_a' Q(s', a') = 0.8.
        # Expected: Q(s,a) <- 1.0 + 0.1 * [0.5 + 0.95 * 0.8 - 1.0]
        #                 <- 1.0 + 0.1 * [0.5 + 0.76 - 1.0]
        #                 <- 1.0 + 0.1 * 0.26
        #                 <- 1.026
        agent.update(obs_payload={"agent_pos": [0, 0]},
                     action="consume", reward=0.5,
                     next_obs_payload=next_obs, done=False)
        new_q = agent._get_q("state_a", "consume")
        self.assertAlmostEqual(new_q, 1.026, places=3)

    def test_q_update_terminal_state(self):
        """When done=True, target = reward (no bootstrap)."""
        config = QLearningConfig(alpha=0.1, gamma=0.95, epsilon=0.0, seed=42)
        agent = QLearningAgent(config)
        agent._set_q("state_a", "consume", 1.0)
        agent._last_state = "state_a"
        agent._last_action = "consume"
        # Terminal: target = reward = 0.5.
        # Q <- 1.0 + 0.1 * (0.5 - 1.0) = 1.0 + 0.1 * (-0.5) = 0.95
        agent.update({}, "consume", 0.5, {}, done=True)
        self.assertAlmostEqual(agent._get_q("state_a", "consume"), 0.95, places=3)

    def test_q_table_capacity_enforced(self):
        """When the Q-table exceeds capacity, LRU eviction triggers."""
        config = QLearningConfig(q_table_capacity=10, seed=42)
        agent = QLearningAgent(config)
        # Insert 20 distinct (state, action) entries.
        for i in range(20):
            agent._set_q(f"state_{i}", "consume", float(i))
        self.assertEqual(agent.q_table_size, 10)
        self.assertEqual(agent.eviction_count, 10)

    def test_lru_eviction_removes_oldest(self):
        """The least-recently-used entry is the one evicted."""
        config = QLearningConfig(q_table_capacity=3, seed=42)
        agent = QLearningAgent(config)
        agent._set_q("state_a", "consume", 1.0)
        agent._set_q("state_b", "consume", 2.0)
        agent._set_q("state_c", "consume", 3.0)
        # Touch state_a to make it more recently used than state_b.
        agent._touch("state_a")
        # Insert state_d — should evict state_b (LRU).
        agent._set_q("state_d", "consume", 4.0)
        self.assertEqual(agent.q_table_size, 3)
        self.assertEqual(agent.eviction_count, 1)
        # state_a should still be present (was touched).
        self.assertNotEqual(agent._get_q("state_a", "consume"), 0.0)
        # state_b should be evicted.
        self.assertEqual(agent._get_q("state_b", "consume"), 0.0)


# ============================================================================
# Episode runner
# ============================================================================


class TestRunEpisode(unittest.TestCase):
    def test_runs_full_episode(self):
        env = MockEnv(n_steps=10)
        config = QLearningConfig(n_steps=10, seed=42, epsilon=0.0)
        result = run_q_learning_episode(
            env_step_fn=env.step,
            env_reset_fn=env.reset,
            config=config,
        )
        self.assertEqual(result.n_steps, 10)
        self.assertGreaterEqual(result.total_reward, -1.0)  # at least the step costs
        self.assertEqual(len(result.per_step), 10)

    def test_determinism_across_runs(self):
        """Same seed + same env -> same per-step actions + rewards."""
        env1 = MockEnv(n_steps=10)
        env2 = MockEnv(n_steps=10)
        config = QLearningConfig(n_steps=10, seed=42)
        r1 = run_q_learning_episode(env1.step, env1.reset, config)
        r2 = run_q_learning_episode(env2.step, env2.reset, config)
        self.assertEqual(
            [s["action"] for s in r1.per_step],
            [s["action"] for s in r2.per_step],
        )
        self.assertEqual(
            [s["reward"] for s in r1.per_step],
            [s["reward"] for s in r2.per_step],
        )

    def test_episode_result_serialization(self):
        env = MockEnv(n_steps=5)
        config = QLearningConfig(n_steps=5, seed=42)
        result = run_q_learning_episode(env.step, env.reset, config)
        d = result.to_dict()
        self.assertIn("config", d)
        self.assertIn("total_reward", d)
        self.assertIn("per_step", d)
        self.assertIn("final_q_table", d)
        self.assertEqual(len(d["per_step"]), 5)


# ============================================================================
# Agent snapshot/restore
# ============================================================================


class TestSnapshotRestore(unittest.TestCase):
    def test_round_trip(self):
        config = QLearningConfig(n_steps=10, seed=42)
        agent = QLearningAgent(config)
        env = MockEnv(n_steps=5)
        env.reset()
        for _ in range(5):
            obs = env._obs()
            action = agent.select_action(obs)
            next_obs, reward, done = env.step(action)
            agent.update(obs, action, reward, next_obs, done)

        snap = agent.snapshot()
        agent2 = QLearningAgent(config)
        agent2.restore(snap)

        self.assertEqual(agent.q_table_size, agent2.q_table_size)
        self.assertEqual(agent.total_reward, agent2.total_reward)
        self.assertEqual(agent.total_q_updates, agent2.total_q_updates)


if __name__ == "__main__":
    unittest.main()
