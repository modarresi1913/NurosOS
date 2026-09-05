# ADR 0001: NurosOS has no filesystem

## Status
Accepted

## Context
Traditional operating systems organize persistent data as a tree of
files and directories (VFS — Virtual File System). This abstraction
is well-suited to human-authored documents and sequential data, but
it is poorly suited to neural data:

- **Path-based retrieval is wrong for memory.** Biological memory is
  *content-addressed* — a partial cue reactivates a stored pattern.
  Path-based retrieval requires knowing the path in advance, which
  defeats the purpose.
- **Hierarchical organization is wrong for associations.** Biological
  memories form cross-linked associative webs, not trees. A smell can
  trigger a visual memory, which can trigger an emotional memory.
  No tree can represent this.
- **File boundaries are arbitrary.** In a brain, there is no "file
  boundary" — activity flows continuously across circuits. Forcing
  the kernel to chunk data into files would introduce artificial
  serialization points.

## Decision
NurosOS will **not** implement a filesystem. Persistent data is stored
in the **Associative Memory Store (AMS)** — a content-addressed key-value
store backed by a Hopfield-like attractor network with sparse
connectivity. Retrieval is by stimulus, not by path.

The only on-disk artifacts are:

1. The connectome dataset (.h5) — read-only at boot.
2. NIR bytecode modules (.nir) — read-only at boot.
3. The AMS weight matrix snapshot (.nir) — written on shutdown, read on boot.

## Consequences
- **Pro:** Memory model matches biology. Content-addressed retrieval is
  O(log n) instead of O(path depth). Cross-modal associations are first-class.
- **Con:** Users cannot `ls` or `cat` to inspect state — they must use the
  `nuros-cli` shell, which speaks the AMS API.
- **Con:** Interop with traditional systems requires an explicit bridge
  (planned for v0.4.0: a FUSE filesystem that exposes AMS as a read-only
  virtual directory).

## References
- ARCHITECTURE.md §5 (Memory Model)
- AMS implementation: `kernel/src/mem.rs`
