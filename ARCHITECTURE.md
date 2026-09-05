# Architecture — NurosOS Microkernel & Sparse Propagation Protocol

This document is the canonical reference for the internal design of NurosOS. It is intended for kernel hackers, SynapseLang compiler engineers, and HAL driver authors. For a higher-level overview, see [`README.md`](./README.md). For the scientific rationale, see [`WHITEPAPER.md`](./WHITEPAPER.md).

---

## 1. Design Philosophy

NurosOS is **not** a Unix-compatible kernel. It does not expose `fork`, `exec`, or a POSIX file system. Instead, it provides three primitives:

1. **Neuron** — a schedulable unit of computation that fires when its membrane potential crosses threshold.
2. **Synapse** — a typed, directional, zero-copy channel between two neurons.
3. **Region** — a topologically-bounded cluster of neurons (analogous to a biological neuropil, e.g., the mushroom body).

Every other OS concept (processes, files, sockets, signals) is **emulated** on top of these three primitives.

### 1.1 Biological Plausibility First

When there is a conflict between biological plausibility and engineering performance, biological plausibility wins. This is enforced by the [Fly Benchmark](../tests/README.md) — any PR that degrades the system's similarity to *Drosophila* behavioral data is rejected, even if it improves throughput.

### 1.2 The Three Invariants

- **I1 — Sparsity.** At any given cycle, at most 5% of all neurons may be in the `Firing` state. This mirrors the observed ~3–5% active fraction in the fruit fly brain and is the single largest source of energy efficiency.
- **I2 — Locality.** A neuron may only communicate with neurons within its *fan-out radius* (default: 1 mm biological-equivalent). Long-range projections require explicit `RegionBridge` channels.
- **I3 — Plasticity.** Every synapse carries a `PlasticityRule` tag. Synapses with no rule are read-only (sensory afferents); all others must update their weight on every spike.

---

## 2. The Microkernel

The kernel is written in Rust and runs in `no_std` mode. It has four subsystems:

| Subsystem     | Crate path                | Responsibility                                            |
|---------------|---------------------------|-----------------------------------------------------------|
| Scheduler     | `kernel/src/sched/`       | Event-driven neuron firing                                |
| IPC           | `kernel/src/ipc/`         | Zero-copy synaptic channels                               |
| Memory        | `kernel/src/mem/`         | Synaptic weight store + associative memory                 |
| HAL bridge    | `kernel/src/hal/`         | Translation from NIR to hardware-specific instructions    |

### 2.1 Boot Sequence

```
1. HAL init          (probe CPU, set up page tables)
2. Load connectome   (parse NIR bytecode → build Neuron graph in memory)
3. Spawn sensory regions   (vision, olfaction, mechanosensation)
4. Spawn motor regions     (locomotion, grooming, courtship)
5. Enter main loop   (Sparse Propagation Protocol)
```

### 2.2 The Main Loop

The main loop is **not** time-driven. There is no `sleep(1ms)` between cycles. Instead, the kernel waits on an event queue populated by:

- External stimuli (sensors, gRPC requests)
- Internal firing events (a neuron crossing threshold)
- Plasticity timers (e.g., STDP eligibility traces)

This event-driven design eliminates the idle-wake cycles that dominate traditional OS power consumption.

---

## 3. The Sparse Propagation Protocol (SPP)

SPP is the heart of NurosOS. It is the algorithm that decides *which* neurons to evaluate on any given cycle, given the constraint that only 3–5% may be active.

### 3.1 Algorithm

```
SPP_Tick():
    1. Collect all pending events from the global event queue (E).
    2. For each event e in E:
         a. Identify the target neuron n.
         b. Add n to the "active set" A (if not already present).
         c. Propagate e's effect to n's membrane potential V_m(n).
    3. If |A| > 0.05 * |N|:
         a. Sort A by |ΔV_m| descending.
         b. Keep only the top 5%; defer the rest to the next tick.
    4. For each neuron n in A:
         a. If V_m(n) > θ(n):  fire.
            i.  Emit spikes to all outgoing synapses (zero-copy).
            ii. Schedule plasticity updates for affected synapses.
         b. Apply leaky integration: V_m(n) *= exp(-Δt/τ(n)).
    5. Clear E. Sleep until next event (or HAL timer interrupt).
```

### 3.2 Why this is biologically plausible

The 3–5% sparsity constraint is not arbitrary. It matches:

- **Energy budget** — biological neurons consume ~10⁹ ATP per spike; the brain limits firing to stay within mitochondrial supply.
- **Information content** — At 5% activity, the entropy of the population code is near-maximal for a 10⁵-neuron region (perLaughlin & Sejnowski 2003).
- **Observed data** — Two-photon calcium imaging of *Drosophila* central complex shows ~4.2% simultaneous activation during walking.

### 3.3 Performance implications

SPP gives NurosOS its headline numbers:

| Metric                          | Traditional OS | NurosOS (emulation) | NurosOS (Loihi target) |
|---------------------------------|----------------|---------------------|------------------------|
| Active compute fraction         | 100%           | 5%                  | 5%                     |
| Energy per inference (10⁶ syn)  | ~120 mJ (GPU)  | ~8 mJ               | ~12 µJ                 |
| Latency (1-region spike)        | ~50 µs         | ~12 µs              | ~0.8 µs                |

---

## 4. Zero-Copy IPC (Synaptic Channels)

Traditional OS IPC copies data between address spaces. NurosOS eliminates this by treating every synapse as a **lock-free, single-producer single-consumer ring buffer** allocated in shared memory.

### 4.1 Channel layout

```
+-----------------+-----------------+-----------------+
| SpikeHeader     | Payload (0-64B) | SpikeHeader     | ...
+-----------------+-----------------+-----------------+
   8 bytes              variable          8 bytes
```

`SpikeHeader` is:
```rust
struct SpikeHeader {
    src_neuron_id: u32,    // emitting neuron
    timestamp:     u32,    // tick at emission
    weight:        f16,    // synaptic efficacy (brain float16)
    plasticity_id: u16,    // index into plasticity rule table
}
```

### 4.2 Synaptic delay emulation

The ring buffer is sized so that the producer is always `D` ticks ahead of the consumer, where `D` is the biological synaptic delay (typically 0.5–2 ms). This naturally throttles producers and prevents runaway feedback loops.

---

## 5. Memory Model — Associative Memory Store

NurosOS has no filesystem. Instead, it exposes an **Associative Memory Store (AMS)** that retrieves data by stimulus rather than by path.

### 5.1 API

```
AMS.store(stimulus: Tensor, payload: Bytes) -> Handle
AMS.query(partial_stimulus: Tensor, k: usize) -> [(Handle, similarity: f32)]
AMS.reinforce(handle: Handle, reward: f32)   // Hebbian update
```

### 5.2 Implementation

AMS is backed by a **Hopfield-like attractor network** with sparse connectivity. Every `store` operation distributes the payload across ~10³ synapses using locality-sensitive hashing. A `query` triggers a relaxation cycle that converges to the nearest stored attractor.

### 5.3 Persistence

On shutdown, AMS snapshots its synaptic weight matrix to disk in the **NIR (Neuromorphic Intermediate Representation)** format. On boot, the matrix is memory-mapped — there is no deserialization cost.

---

## 6. Hardware Abstraction Layer (HAL)

The HAL is a trait-based Rust interface. Every hardware target implements:

```rust
trait NeuromorphicTarget {
    fn alloc_neuron(&mut self, params: &NeuronParams) -> NeuronId;
    fn alloc_synapse(&mut self, src: NeuronId, dst: NeuronId, w: f16) -> SynapseId;
    fn fire(&mut self, n: NeuronId, t: Tick);
    fn read_potential(&self, n: NeuronId) -> f32;
    fn remap(&mut self, failed: NeuronId) -> NeuronId;  // neuroplasticity
}
```

### 6.1 Dynamic remapping (neuroplasticity)

When a physical core fails (a "lesion"), the HAL:

1. Detects the failure via a watchdog.
2. Selects a neighboring neuron with the most similar connectivity profile.
3. Copies the failed neuron's weights to the substitute.
4. Updates the routing table.

This process mimics biological **compensatory sprouting** and is what gives NurosOS its fault tolerance.

---

## 7. ADRs

Architectural decisions are recorded as ADRs in [`docs/adr/`](./adr). The current set:

- [ADR-0001](./adr/0001-no-filesystem.md) — Why NurosOS has no filesystem
- [ADR-0002](./adr/0002-rust-over-cpp.md) — Why Rust over C++ for the kernel
- [ADR-0003](./adr/0003-spp-sparsity-threshold.md) — Why the sparsity threshold is 5%
- [ADR-0004](./adr/0004-ams-over-vfs.md) — Why AMS replaces VFS

---

## 8. Open Questions

These are unresolved research questions tracked as GitHub Discussions:

- **Q1.** Should SPP's sparsity threshold adapt region-by-region, or be globally fixed?
- **Q2.** How do we represent neuromodulators (dopamine, serotonin) in the scheduler?
- **Q3.** Can we prove formal liveness guarantees for SPP, given its event-driven nature?

Contributions on these are welcome — but bring data, not opinions.
