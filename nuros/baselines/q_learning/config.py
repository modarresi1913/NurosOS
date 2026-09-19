"""Q-learning configuration for the NurosOS baseline audit.

Per docs/BASELINE_SPEC.md:
  - alpha = 0.1 (learning rate; matches NurosOS genome.plasticity_rules.learning_rate)
  - gamma = 0.95 (discount factor; standard for episodic tasks)
  - epsilon = 0.1 (exploration rate; standard eps-greedy)
  - q_table_capacity = 200 (matches Rust MinimumOrganism::MemoryRecord cap)
  - privileged_obs = True (whether to use the env's privileged observation fields)
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QLearningConfig:
    """Configuration for the Q-learning baseline.

    All hyperparameters are frozen for the experiment per the preregistration
    (experiments/EXPERIMENTS.md). Do NOT modify after observing results.
    """
    alpha: float = 0.1
    gamma: float = 0.95
    epsilon: float = 0.1
    q_table_capacity: int = 200  # matches Rust organism.rs:233 cap
    privileged_obs: bool = True   # if False, use raw_obs (only agent_pos + reward)
    seed: int = 42
    n_steps: int = 300

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "q_table_capacity": self.q_table_capacity,
            "privileged_obs": self.privileged_obs,
            "seed": self.seed,
            "n_steps": self.n_steps,
        }


DEFAULT_CONFIG = QLearningConfig()
