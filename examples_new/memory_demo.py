"""Example: Memory Contract Demo.

Shows the living memory system with provenance, decay, and audit.
"""

from nuros.memory import MemoryContract, MemoryType


def main():
    memory = MemoryContract()

    print("=== Memory Contract Demo ===\n")

    # Store different types of memories
    e1 = memory.remember("Saw a red car at intersection",
                          memory_type=MemoryType.EPISODIC, importance=0.7)
    print(f"Episodic: {e1.content} [type={e1.memory_type.name}, label={e1.epistemic_label.name}]")

    e2 = memory.remember("Red means stop in traffic",
                          memory_type=MemoryType.SEMANTIC, importance=0.9)
    print(f"Semantic: {e2.content} [type={e2.memory_type.name}, label={e2.epistemic_label.name}]")

    e3 = memory.remember("If I had gone left instead...",
                          memory_type=MemoryType.COUNTERFACTUAL, importance=0.4)
    print(f"Counterfactual: {e3.content} [type={e3.memory_type.name}, label={e3.epistemic_label.name}]")

    # Associate memories
    memory.associate(e1.memory_id, e2.memory_id, "supports")
    print(f"\n✓ Associated: {e1.memory_id[:8]}... → {e2.memory_id[:8]}...")

    # Revise with audit
    revised = memory.revise(e2.memory_id, "content",
                           "Red usually means stop, but context matters",
                           "Nuanced understanding after experience")
    print(f"✓ Revised: '{revised.content}'")
    print(f"  Revision history: {len(revised.revision_history)} entries")

    # Reflect (meta-retrieval over a single memory)
    reflection = memory.reflect(e2.memory_id)
    print(f"\nReflection on {e2.memory_id[:8]}...: {reflection}")

    # Summary
    summary = memory.summary()
    print(f"\nMemory Summary: {summary}")


if __name__ == "__main__":
    main()
