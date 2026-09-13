"""Example: Basic Organism Lifecycle.

Demonstrates creating, running, and inspecting a basic organism.
"""

import sys
sys.path.insert(0, '/home/z/my-project/NurosOS')

from nuros.organism import Organism, OrganismConfig, OrganismState
from nuros.epistemic import EpistemicLabel


def main():
    # Create organism
    config = OrganismConfig(
        name="demo-organism",
        description="A basic demonstration organism",
    )
    organism = Organism(config)

    print(f"Organism created: {organism.config.name}")
    print(f"State: {organism.state.name}")

    # Birth
    organism.birth()
    print(f"After birth: {organism.state.name}")

    # Run cognitive ticks
    for i in range(10):
        result = organism.tick()
        if i % 3 == 0:
            print(f"  Tick {i+1}: memories={organism.memory.memory_count}, "
                  f"energy={organism.homeostasis.get('energy'):.3f}")

    # Take snapshot
    snap = organism.snapshot()
    print(f"\nSnapshot taken: {list(snap.keys())}")
    print(f"State hash: {organism.state_hash()}")

    # Fork
    child = organism.fork(name="child-organism")
    print(f"Forked: {child.config.name} (id: {child.organism_id[:8]}...)")

    # Terminate
    organism.terminate()
    print(f"After termination: {organism.state.name}")


if __name__ == "__main__":
    main()
