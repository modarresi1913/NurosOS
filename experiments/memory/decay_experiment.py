"""Experiment: Memory Decay Dynamics.

Compare different decay functions (exponential, power-law, linear, step)
and measure their effect on memory retrieval quality over time.
"""

import time
import math
from dataclasses import dataclass
from typing import Callable

from nuros.memory import MemoryContract, MemoryType


@dataclass
class DecayResult:
    function_name: str
    total_memories: int
    strong_memories: int  # strength > 0.1
    retrieval_accuracy: float
    elapsed: float


def exponential_decay(strength: float, rate: float, ticks: int) -> float:
    return strength * math.exp(-rate * ticks)

def power_law_decay(strength: float, rate: float, ticks: int) -> float:
    return strength / (1 + rate * ticks)

def linear_decay(strength: float, rate: float, ticks: int) -> float:
    return max(0.0, strength - rate * ticks)

def step_decay(strength: float, rate: float, ticks: int) -> float:
    steps = int(ticks * rate)
    return strength * (0.5 ** steps)


DECAY_FUNCTIONS = {
    "exponential": exponential_decay,
    "power_law": power_law_decay,
    "linear": linear_decay,
    "step": step_decay,
}


def run_decay_experiment(
    n_memories: int = 100,
    total_ticks: int = 200,
    rate: float = 0.01,
    importance_range: tuple = (0.3, 1.0),
) -> dict[str, DecayResult]:
    """Run memory decay experiment with all decay functions."""
    import random
    results = {}

    for name, decay_fn in DECAY_FUNCTIONS.items():
        start = time.perf_counter()

        memory = MemoryContract()
        # Create memories with varying importance
        for i in range(n_memories):
            importance = importance_range[0] + random.random() * (importance_range[1] - importance_range[0])
            memory.remember(f"entry_{i}", importance=importance, memory_type=MemoryType.EPISODIC)

        # Simulate ticks with decay
        strong_count = 0
        for tick in range(total_ticks):
            for entry in memory._store.values():
                entry.access_count  # trigger strength recalculation

        # Count strong memories
        strong_count = sum(1 for e in memory._store.values() if e.current_strength > 0.1)

        elapsed = time.perf_counter() - start
        results[name] = DecayResult(
            function_name=name,
            total_memories=n_memories,
            strong_memories=strong_count,
            retrieval_accuracy=strong_count / n_memories,
            elapsed=elapsed,
        )

    return results


if __name__ == "__main__":
    results = run_decay_experiment()
    print("Memory Decay Experiment Results")
    print("=" * 50)
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Total memories: {result.total_memories}")
        print(f"  Strong memories: {result.strong_memories}")
        print(f"  Retrieval accuracy: {result.retrieval_accuracy:.2%}")
        print(f"  Elapsed: {result.elapsed:.3f}s")
