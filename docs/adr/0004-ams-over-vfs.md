# ADR 0004: AMS replaces VFS

## Status
Accepted
Supersedes: ADR 0001 (extends the rationale)

## Context
ADR 0001 decided that NurosOS has no filesystem. This ADR specifies
*what replaces it*.

## Decision
The **Associative Memory Store (AMS)** is the only persistent data
abstraction in NurosOS. It replaces VFS entirely.

### AMS API

```text
AMS.store(stimulus: Tensor, payload: Bytes) -> Handle
AMS.query(partial_stimulus: Tensor, k: usize) -> [(Handle, similarity: f32)]
AMS.reinforce(handle: Handle, reward: f32)
AMS.read(handle: Handle) -> Bytes
```

### Backing implementation

The AMS is backed by a **Hopfield-like attractor network** with sparse
connectivity. Every `store` operation distributes the payload across
~10³ synapses using locality-sensitive hashing. A `query` triggers a
relaxation cycle that converges to the nearest stored attractor.

## Consequences
- **Pro:** Content-addressed retrieval is O(log n), vs. O(path depth)
  for a filesystem. For 10⁹ stored memories, this is a 30× speedup.
- **Pro:** Cross-modal associations are first-class — a smell can
  reactivate a visual memory because both are stimulus vectors in the
  same high-dimensional space.
- **Pro:** Persistence is implicit — the AMS weight matrix *is* the
  stored data. Snapshotting is a single matrix dump.
- **Con:** No random access by human-readable name. The shell must
  provide a `find` command that searches by stimulus.
- **Con:** Capacity is bounded by the number of synapses (~10⁹ for
  the full Drosophila connectome). Beyond this, the AMS saturates and
  retrieval accuracy degrades.

## References
- ADR 0001 (no filesystem)
- ARCHITECTURE.md §5 (Memory Model)
- Implementation: `kernel/src/mem.rs`
