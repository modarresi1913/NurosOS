"""
Connectome Mapping Example — demonstrates how a simple graph maps to a
spike-timing structure.

This is the "compile connectome → timing" concept made concrete. Given a
small graph (e.g., 5 neurons from a connectome fragment), we show how
each edge becomes a synapse with a weight + delay, and how the graph's
topology determines the spike-timing schedule.

This is NOT the full Drosophila connectome. It is a minimal example
showing the CONCEPT of "compiling a connectome into a timing structure."
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field


# ============================================================================
# Input: a simple connectome fragment (adjacency list with weights)
# ============================================================================

EXAMPLE_CONNECTOME = {
    "neurons": [
        {"name": "KC_001", "type": "Kenyon_cell", "region": "mushroom_body"},
        {"name": "KC_002", "type": "Kenyon_cell", "region": "mushroom_body"},
        {"name": "MBON_001", "type": "MB_output_neuron", "region": "mushroom_body"},
        {"name": "DAN_001", "type": "dopaminergic_neuron", "region": "mushroom_body"},
        {"name": "OAN_001", "type": "octopaminergic_neuron", "region": "mushroom_body"},
    ],
    "connections": [
        {"pre": "KC_001", "post": "MBON_001", "weight": 0.8, "delay": 1, "neurotransmitter": "acetylcholine"},
        {"pre": "KC_002", "post": "MBON_001", "weight": 0.6, "delay": 1, "neurotransmitter": "acetylcholine"},
        {"pre": "DAN_001", "post": "KC_001", "weight": -0.3, "delay": 2, "neurotransmitter": "dopamine"},
        {"pre": "DAN_001", "post": "KC_002", "weight": -0.3, "delay": 2, "neurotransmitter": "dopamine"},
        {"pre": "OAN_001", "post": "MBON_001", "weight": 0.4, "delay": 1, "neurotransmitter": "octopamine"},
        {"pre": "MBON_001", "post": "DAN_001", "weight": 0.5, "delay": 3, "neurotransmitter": "acetylcholine"},
    ],
}


# ============================================================================
# Compiler: connectome graph → spike-timing schedule
# ============================================================================

@dataclass
class CompiledSynapse:
    pre: str
    post: str
    weight: float
    delay: int
    neurotransmitter: str


@dataclass
class SpikeSchedule:
    """A compiled spike-timing schedule derived from a connectome."""
    neurons: dict[str, dict] = field(default_factory=dict)
    synapses: list[CompiledSynapse] = field(default_factory=dict) if False else field(default_factory=list)
    timing_matrix: dict[str, dict[str, int]] = field(default_factory=dict)
    """timing_matrix[pre][post] = delay (ticks)."""

    def summary(self) -> str:
        lines = [
            f"Compiled Connectome → Spike Schedule",
            f"  Neurons: {len(self.neurons)}",
            f"  Synapses: {len(self.synapses)}",
            f"  Timing matrix: {len(self.timing_matrix)} pre-synaptic entries",
        ]
        if self.synapses:
            delays = [s.delay for s in self.synapses]
            weights = [s.weight for s in self.synapses]
            lines.append(f"  Delay range: {min(delays)}-{max(delays)} ticks")
            lines.append(f"  Weight range: {min(weights):.1f}-{max(weights):.1f}")
            nts = set(s.neurotransmitter for s in self.synapses)
            lines.append(f"  Neurotransmitters: {', '.join(sorted(nts))}")
        return "\n".join(lines)

    def trace_path(self, start: str, max_hops: int = 5) -> list[list[str]]:
        """Trace all paths from a starting neuron (up to max_hops)."""
        paths = [[start]]
        for _ in range(max_hops):
            new_paths = []
            for p in paths:
                last = p[-1]
                for syn in self.synapses:
                    if syn.pre == last and syn.post not in p:
                        new_paths.append(p + [syn.post])
            paths = new_paths if new_paths else paths
        return paths


def compile_connectome(connectome: dict) -> SpikeSchedule:
    """Compile a connectome graph into a spike-timing schedule.

    This is the core "connectome → timing" mapping:
      1. Each neuron becomes a node in the timing network.
      2. Each connection becomes a synapse with (weight, delay).
      3. The delay determines WHEN the postsynaptic neuron receives the spike.
      4. The timing matrix records all (pre, post, delay) triples.

    In a full implementation (future work), the connectome would be the
    complete Drosophila connectome (~140K neurons, ~50M synapses). The
    compiler would map it to a hardware-executable spike schedule for a
    neuromorphic chip (Loihi, SpiNNaker, etc.).

    Here we demonstrate the concept with 5 neurons.
    """
    schedule = SpikeSchedule()

    # Step 1: Register neurons.
    for n in connectome["neurons"]:
        schedule.neurons[n["name"]] = n

    # Step 2: Compile connections → synapses.
    for conn in connectome["connections"]:
        syn = CompiledSynapse(
            pre=conn["pre"], post=conn["post"],
            weight=conn["weight"], delay=conn["delay"],
            neurotransmitter=conn.get("neurotransmitter", "unknown"),
        )
        schedule.synapses.append(syn)

        # Step 3: Build the timing matrix.
        if conn["pre"] not in schedule.timing_matrix:
            schedule.timing_matrix[conn["pre"]] = {}
        schedule.timing_matrix[conn["pre"]][conn["post"]] = conn["delay"]

    return schedule


# ============================================================================
# Demo
# ============================================================================

def run_demo():
    print("=" * 72)
    print("NurosOS Connectome Mapping Example")
    print("Compile a simple graph → spike-timing structure")
    print("=" * 72)
    print()

    # Show the input connectome.
    print("Input: Connectome fragment (5 neurons, 6 connections)")
    print("-" * 72)
    for n in EXAMPLE_CONNECTOME["neurons"]:
        print(f"  Neuron: {n['name']:12s} | type: {n['type']:25s} | region: {n['region']}")
    print()
    for c in EXAMPLE_CONNECTOME["connections"]:
        print(f"  {c['pre']:12s} → {c['post']:12s} | w={c['weight']:+.1f} | delay={c['delay']}t | nt={c['neurotransmitter']}")
    print()

    # Compile.
    schedule = compile_connectome(EXAMPLE_CONNECTOME)

    # Show the compiled schedule.
    print("Output: Compiled spike-timing schedule")
    print("-" * 72)
    print(schedule.summary())
    print()

    # Show the timing matrix.
    print("Timing matrix (pre → post: delay in ticks):")
    for pre, posts in schedule.timing_matrix.items():
        for post, delay in posts.items():
            print(f"  {pre:12s} → {post:12s}: delay = {delay} tick(s)")
    print()

    # Trace paths from KC_001.
    print("Path trace from KC_001 (max 3 hops):")
    paths = schedule.trace_path("KC_001", max_hops=3)
    for p in paths[:5]:
        print(f"  {' → '.join(p)}")
    print()

    # Show how this maps to hardware execution.
    print("Hardware mapping (conceptual):")
    print("  KC_001 fires at T=0")
    print("  → MBON_001 receives spike at T=0+1=1 (delay=1)")
    print("  → DAN_001 receives spike at T=1+3=4 (delay=3 from MBON_001)")
    print("  → DAN_001 inhibits KC_001 at T=4+2=6 (delay=2, negative weight)")
    print()
    print("This is the 'compile connectome → timing' concept:")
    print("  Graph topology → synaptic delays → temporal schedule")
    print("  The schedule is what a neuromorphic chip (Loihi, SpiNNaker) would execute.")


if __name__ == "__main__":
    run_demo()
