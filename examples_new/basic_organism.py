"""Example: Basic Organism Lifecycle.

Demonstrates creating, running, and inspecting a basic organism.
"""

from nuros.organism import Organism, OrganismConfig


def main():
    # Create organism
    config = OrganismConfig(name="demo-organism", genome_id="demo")
    organism = Organism(config)

    print(f"Organism created: {organism.name}")
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
    print(f"Forked: {child.name} (id: {child.organism_id[:8]}...)")

    # Terminate
    organism.terminate()
    print(f"After termination: {organism.state.name}")


if __name__ == "__main__":
    main()
