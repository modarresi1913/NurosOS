# Layered Specification — NurosOS

> **Status**: ARCHITECTURALLY SPECIFIED (L0/L1/L2) + PARTIALLY IMPLEMENTED.
> This document defines the three-layer architecture that distinguishes
> NurosOS from a conventional agent framework.

---

## The Problem

Traditional computing separates memory from computation (Von Neumann
bottleneck). Traditional AI separates training from inference. Both
separations make it impossible to study how cognition *develops through
experience* — the training phase freezes behavior, and the inference
phase cannot learn.

NurosOS asks a different question: **what happens when we stop
programming the final behavior and instead program the conditions under
which a cognitive structure can develop?**

The answer requires a substrate that:
1. Can emulate neural dynamics (L0).
2. Can schedule tasks via spike-timing rather than a fixed program counter (L1).
3. Can expose a clean interface to agents/services that consume the scheduled tasks (L2).

---

## Hypotheses

**H1**: Identical initial computational conditions (same genome, same
seed) produce divergent developmental trajectories under different
environmental histories. **[IMPLEMENTED AND TESTED — 30-seed
experiment, d=+0.356 for HippoCore vs baseline]**

**H2**: Structured episodic memory (HippoCore) provides measurable
behavioral value over a baseline without memory, when the environment
does not leak privileged state. **[IMPLEMENTED AND TESTED — d=+0.356
in raw mode, above the 0.3 significance threshold]**

**H3**: Replay + consolidation add value beyond simple retrieval.
**[SUPPORTED — HippoCore (d=+0.356) outperforms simple memory
(d=+0.264)]**

---

## Scope of Application

| Domain | Status | Notes |
|--------|--------|-------|
| **Software simulator** | ✅ Implemented | Python + Rust. The primary research platform. |
| **Neuromorphic hardware (Loihi, SpiNNaker)** | 📋 Proposed | `hal/drivers/loihi/` exists as v0.1.0 scaffold. The connectome compiler (`examples/connectome_mapping.py`) demonstrates the concept. |
| **Edge / embedded** | 📋 Proposed | Clean Rust deps (pyo3, serde, sha2). No LLM. Deterministic. But no power/performance measurements yet. |
| **Production deployment** | ❌ Not intended | Research software. v0.4.0-alpha. |

---

## Three-Layer Architecture

### L0 — Reference Emulator

**Purpose**: provide a minimal, inspectable implementation of neural
dynamics that serves as the ground truth for the system.

**What it is**: a small spiking neural network (threshold-fire neurons,
leaky integration, synaptic delays) that can be inspected step-by-step.

**What it is NOT**: a biologically accurate simulator. It is a
**conceptual demonstration** — the smallest network that shows how
sensory input → spike propagation → motor output → task execution.

**Implementation**: `examples/reference_emulator.py` (150 lines):
- 12 neurons (4 sensory, 4 interneurons, 4 motor)
- 8 synapses with weights + delays
- LIF (leaky integrate-and-fire) dynamics
- Settle loop (iterate until no more spikes in a tick)

**Key property**: the L0 emulator is **deterministic** — same input
→ same spike pattern → same task sequence. This is the foundation
for reproducibility.

### L1 — Spike-Timed Scheduling API

**Purpose**: convert neural dynamics (spikes) into task-dispatch
events. The timing of spikes determines the timing of task execution.

**What it is**: an API layer that:
1. Converts environment observations → sensory-neuron input currents.
2. Converts motor-neuron fires → task-dispatch events.
3. Respects synaptic delays (a neuron that fires at T schedules its
   downstream task for T+delay).

**What it is NOT**: a real-time operating system. It is a
**scheduling abstraction** — the spike-timing determines the task
ordering, not a fixed program counter or a priority queue.

**Implementation**: `SpikeScheduler` class in `reference_emulator.py`:
- `obs_to_currents(obs)` → sensory input
- `motor_to_task(motor_fires)` → task dispatch
- Synaptic delays (1-3 ticks) create a natural temporal pipeline

**Key property**: the L1 layer is the **innovation boundary** — this
is where NurosOS differs from both conventional OS schedulers (which
use priority queues) and conventional ML frameworks (which use
batched matrix operations). Spike-timing is the scheduling primitive.

### L2 — Task Interface

**Purpose**: expose a clean interface to agents/services that consume
the scheduled tasks.

**What it is**: a minimal environment API:
- `observe()` → current observation
- `step(action)` → execute task, receive reward
- The task is selected by L1 (via L0 spike dynamics), not by a
  hand-coded policy.

**What it is NOT**: a full agent framework. It is an **environment
abstraction** — the same cognitive substrate can be placed in any
environment that implements this interface.

**Implementation**: `SimpleGridEnv` in `reference_emulator.py` +
`NonStationaryEnv` in `environments/nonstationary.py` (3-regime env).

---

## Layer Mapping to Existing Code

| Layer | Component | File | Status |
|-------|-----------|------|--------|
| L0 | SpikeNetwork | `examples/reference_emulator.py` | [IMPLEMENTED] |
| L0 | Rust SNN kernel | `kernel/src/{neuron,synapse,region,connectome}.rs` | [PARTIALLY IMPLEMENTED] (v0.1.0 scaffold) |
| L0 | Core neural algorithms | `core/src/{models,plasticity,delays}.rs` | [PARTIALLY IMPLEMENTED] (v0.1.0) |
| L0 | Connectome compiler | `examples/connectome_mapping.py` | [IMPLEMENTED] (concept demo) |
| L1 | SpikeScheduler | `examples/reference_emulator.py` | [IMPLEMENTED] |
| L1 | SynapseLang compiler | `compiler/synapselang/` | [IMPLEMENTED] (v0.1.0) |
| L2 | SimpleGridEnv | `examples/reference_emulator.py` | [IMPLEMENTED] |
| L2 | ResourceWorld | `nuros-dev/src/environment.rs` | [IMPLEMENTED AND TESTED] |
| L2 | ChangingWorld | `nuros-dev/src/environment.rs` | [IMPLEMENTED AND TESTED] |
| L2 | NonStationaryEnv | `environments/nonstationary.py` | [IMPLEMENTED] |
| L2 | HAL drivers | `hal/drivers/{x86,arm,fpga,loihi}/` | [PARTIALLY IMPLEMENTED] (v0.1.0) |

---

## Connectome Compilation

The L0 layer's ultimate goal is to **compile a connectome into a
spike-timing schedule**. The concept:

```
Connectome graph (neurons + connections)
    ↓ compile_connectome()
Spike-timing schedule (neurons + synapses with weights + delays)
    ↓ execute on L0 emulator
Spike pattern → L1 scheduling → L2 tasks
```

**Demonstration**: `examples/connectome_mapping.py` shows how a
5-neuron fragment of the Drosophila mushroom body (Kenyon cells, MBONs,
DANs, OANs) compiles to a timing matrix with delays 1-3 ticks.

**Future work**: compile the full Drosophila connectome (~140K neurons,
~50M synapses) into a hardware-executable schedule for Loihi/SpiNNaker.
The HAL drivers at `hal/drivers/loihi/` are the v0.1.0 scaffold for
this target.

---

## Name and Brand Differentiation

NurosOS is **not** any of the following:

| Name | Owner | What it is | How NurosOS differs |
|------|-------|-----------|---------------------|
| **NurOS-Linux** | Linux kernel community | An educational Linux-like kernel | NurosOS is NOT a Linux kernel. NurosOS is a cognitive substrate, not an operating system kernel. The "OS" in NurosOS refers to "Organism Substrate", not "Operating System". |
| **NeuroOS** | Intel / various | Intel's neuromorphic OS research (or a generic term for brain-inspired OS) | NurosOS is NOT Intel's NeuroOS. NurosOS does not require Intel hardware. NurosOS's "neuro" inspiration is the developmental trajectory, not hardware-specific optimization. |
| **NeuralOS** | Unified.ai | A neural-network-augmented OS for compute orchestration | NurosOS is NOT NeuralOS. NurosOS is a research substrate for developmental cognition, not a production compute orchestrator. |
| **OrganoidOS** | Various | Organoid-intelligence OS concepts (biological organoid computing) | NurosOS is NOT OrganoidOS. NurosOS uses computational models (spiking neurons, TD learning, episodic memory), NOT biological organoids. |

**The "OS" in NurosOS stands for "Organism Substrate"** — a runtime
in which artificial organisms can be instantiated, developed, embodied,
observed, measured, forked, replayed, and experimentally compared.

The "Nur" prefix evokes both "neural" (the spike-timing inspiration)
and "nurture" (the developmental thesis: programming conditions for
development, not final behavior).
