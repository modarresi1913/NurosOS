"""
Non-stationary 3-regime environment for the NurosOS scientific audit.

Per experiments/EXPERIMENTS.md §7:
  Regime A (steps 0-99):   SimpleResourceWorld(width=8, height=8, seed=env_seed, 5 resources, 3 hazards)
  Regime B (steps 100-199): SimpleResourceWorld(width=8, height=8, seed=env_seed+1000, 3 resources, 4 hazards)
  Regime C (steps 200-299): SimpleChangingWorld(size=10, shift_interval=20, seed=env_seed+2000)

Explicit regime transitions at fixed steps. Deterministic seed control.
The env has NO hidden privileged information — the privileged_obs flag
controls what the organism sees.
"""

from __future__ import annotations

from typing import Any

from nuros.baselines.simple_env import SimpleResourceWorld, SimpleChangingWorld


class NonStationaryEnv:
    """3-regime non-stationary environment.

    Regimes:
        A (0-99):   ResourceWorld, 5 resources, 3 hazards (standard)
        B (100-199): ResourceWorld, 3 resources, 4 hazards (harder)
        C (200-299): ChangingWorld, size=10, shift_interval=20 (novel)

    The env is deterministic given a fixed env_seed.
    """

    REGIME_BOUNDARIES = [0, 100, 200, 300]

    def __init__(self, env_seed: int = 42, privileged_obs: bool = True):
        self.env_seed = env_seed
        self.privileged_obs = privileged_obs
        self.step_count = 0
        self.current_regime = "A"
        self._env_a = SimpleResourceWorld(8, 8, seed=env_seed, n_resources=5, n_hazards=3, privileged_obs=privileged_obs)
        self._env_b = SimpleResourceWorld(8, 8, seed=env_seed + 1000, n_resources=3, n_hazards=4, privileged_obs=privileged_obs)
        self._env_c = SimpleChangingWorld(size=10, shift_interval=20, seed=env_seed + 2000, privileged_obs=privileged_obs)
        self._active_env = self._env_a
        self._active_env.reset()

    def reset(self) -> dict[str, Any]:
        self.step_count = 0
        self.current_regime = "A"
        self._active_env = self._env_a
        obs = self._active_env.reset()
        return self._augment_obs(obs)

    def observe(self) -> dict[str, Any]:
        return self._augment_obs(self._active_env.observe())

    def step(self, action: str) -> tuple[dict[str, Any], float, bool]:
        self.step_count += 1
        # Check for regime transition.
        if self.step_count == 100:
            self.current_regime = "B"
            self._active_env = self._env_b
            self._active_env.reset()
        elif self.step_count == 200:
            self.current_regime = "C"
            self._active_env = self._env_c
            self._active_env.reset()

        obs, reward, done = self._active_env.step(action)
        return self._augment_obs(obs), reward, done

    def _augment_obs(self, obs: dict[str, Any]) -> dict[str, Any]:
        """Add regime metadata to the observation."""
        obs = dict(obs)
        obs["regime"] = self.current_regime
        obs["global_step"] = self.step_count
        return obs

    @property
    def regime(self) -> str:
        return self.current_regime
