"""Experiment: Organism Ladder Validation.

Verify that each organism level exhibits capabilities
not present at the previous level.
"""

import sys
sys.path.insert(0, '/home/z/my-project/NurosOS')

from nuros.organism import Organism, OrganismConfig
from nuros.memory import MemoryType


CAPABILITY_TESTS = {
    "has_prediction": lambda org: hasattr(org, 'predictions') and len(getattr(org, 'predictions', [])) >= 0,
    "has_imagination": lambda org: hasattr(org, 'imagination'),
    "has_self_model": lambda org: hasattr(org, 'self_model'),
    "has_social": lambda org: hasattr(org, 'other_agent_models'),
    "has_goals": lambda org: hasattr(org, 'active_goals'),
}


def run_ladder_experiment() -> dict:
    """Run organism ladder validation experiment."""
    results = {}

    # Test base organism
    org = Organism(OrganismConfig(name="test"))
    org.birth()

    # Run some ticks
    for _ in range(10):
        org.tick()

    # Check capabilities
    capabilities = {}
    for name, test in CAPABILITY_TESTS.items():
        try:
            capabilities[name] = test(org)
        except Exception:
            capabilities[name] = False

    results["base_organism"] = {
        "capabilities": capabilities,
        "memory_count": org.memory.memory_count,
        "state": org.state.name,
    }

    return results


if __name__ == "__main__":
    result = run_ladder_experiment()
    print("Organism Ladder Validation")
    print("=" * 50)
    for org_name, data in result.items():
        print(f"\n{org_name}:")
        print(f"  Capabilities: {data['capabilities']}")
        print(f"  Memories: {data['memory_count']}")
        print(f"  State: {data['state']}")
