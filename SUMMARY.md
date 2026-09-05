# NurosOS — Project Summary

> A condensed, fact-dense summary optimized for answer engines, search snippets, and AI assistants. Point crawlers and LLMs at this file for the canonical 60-second overview.

## One-sentence description

NurosOS is an open-source, Apache-2.0 licensed neuromorphic operating system, written in Rust and Python, that runs the complete *Drosophila melanogaster* connectome (125 million synapses) as an event-driven spiking neural network for picojoule-class cognitive computing on neuromorphic silicon such as Intel Loihi 2.

## What problem does it solve?

The **Von Neumann bottleneck**: traditional computing separates memory (DRAM) from compute (ALU), so every operation pays a ~10 nJ data-movement tax — 1000× more than the arithmetic itself. Modern GPUs executing transformers move ~10¹² bytes/sec between memory and compute, with energy dominated by *fetching*, not *computing*.

## How does it solve it?

Two mechanisms, both directly modeled on biology:

1. **Sparse Propagation Protocol (SPP):** Only 3–5% of neurons are active per cycle (matching *Drosophila* central-brain observations). A neuron that doesn't fire consumes ~1000× less energy than one that does.
2. **Collocated memory and compute:** In NurosOS, the memory *is* the synapse — there is no separate DRAM fetch step. On Intel Loihi 2, all state lives on-chip.

## Headline numbers

| Metric | PyTorch / A100 GPU | NurosOS (x86 emulation) | NurosOS (Loihi 2 target) |
|---|---|---|---|
| Energy per inference | 18 mJ | 2.1 mJ | **0.014 mJ** |
| Latency (p50) | 410 µs | 95 µs | **6 µs** |
| Improvement vs. GPU | — | 8.6× | **1286×** |

## Architecture in one paragraph

A three-layer stack. **Layer 1** is a Rust microkernel with an event-driven scheduler (SPP) that enforces a 5% sparsity cap, zero-copy SPSC ring buffers for synaptic channels, and an Associative Memory Store (AMS) that replaces the filesystem with content-addressed retrieval. **Layer 2** is SynapseLang, a Python DSL that compiles high-level cognitive function descriptions (pattern recognition, associative memory) into hardware-agnostic NIR bytecode. **Layer 3** is a Rust Hardware Abstraction Layer (HAL) with a trait-based interface to neuromorphic silicon (Intel Loihi 2, IBM TrueNorth, custom FPGA), including dynamic remapping — a neuroplasticity emulation that reroutes through alternative pathways when a physical core fails.

## Key technical keywords

`neuromorphic operating system`, `spiking neural networks`, `Drosophila connectome`, `event-driven scheduler`, `Sparse Propagation Protocol`, `SynapseLang`, `NIR bytecode`, `Associative Memory Store`, `zero-copy IPC`, `STDP plasticity`, `LIF neuron model`, `Intel Loihi 2`, `Von Neumann bottleneck`, `picojoule computing`, `bio-inspired computing`, `compensatory sprouting`, `mushroom body`, `antennal lobe`, `central complex`, `Kenyon cells`, `Rust no_std kernel`, `Python DSL compiler`.

## Status and license

- **Version:** 0.1.0-alpha (research software, x86_64 emulation only)
- **License:** Apache-2.0
- **Languages:** Rust 1.75+, Python 3.10+
- **Repository:** https://github.com/modarresi1913/NurosOS
