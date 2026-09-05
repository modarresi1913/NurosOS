# NurosOS — The Bio-Inspired Neuromorphic Operating System

<p align="center">
  <em>"Decoupling intelligence from biological hardware."</em>
</p>

<p align="center">
  <a href="#status">Status</a> •
  <a href="#vision">Vision</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

---

## Status

| Layer            | Language | Stage               |
|------------------|----------|---------------------|
| Kernel           | Rust     | v0.1.0-alpha (stub) |
| SynapseLang      | Python   | v0.1.0-alpha (parser MVP) |
| HAL              | Rust     | x86 emulation only  |
| Core algorithms  | Rust     | LIF + STDP ready    |

> ⚠️ NurosOS is **research software**. It is not production-ready and currently runs only in **software emulation mode** on commodity x86_64 hardware. Do not deploy on neuromorphic silicon without reviewing `ARCHITECTURE.md`.

## Vision

NurosOS is a next-generation operating system and runtime environment architected upon the structural and functional principles derived from the complete connectome of *Drosophila melanogaster*. By translating the 125 million synaptic connections and sparse, feedback-driven neural topologies into software primitives, NurosOS provides a radical new paradigm for energy-efficient, highly parallel, and adaptive computing.

### Mission
Decouple intelligence from biological hardware by creating a software layer that natively runs on neuromorphic chips, simulating whole-brain dynamics with pico-joule efficiency.

### Long-term Vision
Establish the foundational infrastructure for **"Digital Biology"** — where consciousness, memory, and cognition are treated as executable system processes rather than emergent mysteries.

## Architecture

NurosOS is a three-layer stack:

```
┌──────────────────────────────────────────────────────────┐
│  External AI clients (PyTorch, TensorFlow, gRPC/REST)    │
└────────────────────────┬─────────────────────────────────┘
                         │  Hybrid API (REST/gRPC)
┌────────────────────────▼─────────────────────────────────┐
│  Layer 2 — SynapseLang Compiler                          │
│  • DSL → weighted graph bytecode                         │
│  • Connectome data loader (HDF5/SWCF format)             │
│  • Hardware-agnostic intermediate representation (NIR)   │
└────────────────────────┬─────────────────────────────────┘
                         │  Bytecode stream (zero-copy)
┌────────────────────────▼─────────────────────────────────┐
│  Layer 1 — Microkernel                                   │
│  • Event-driven spiking scheduler                        │
│  • Sparse Propagation Protocol (3–5% active per cycle)   │
│  • Zero-copy IPC (synaptic delay emulation)              │
└────────────────────────┬─────────────────────────────────┘
                         │  Neuromorphic instruction set
┌────────────────────────▼─────────────────────────────────┐
│  Layer 3 — Hardware Abstraction Layer (HAL)              │
│  • x86_64 (emulation)  • ARM  • Intel Loihi  • FPGA      │
│  • Dynamic remapping (neuroplasticity emulation)         │
└──────────────────────────────────────────────────────────┘
```

For the deep dive, see [`ARCHITECTURE.md`](./ARCHITECTURE.md). For the scientific rationale, see [`WHITEPAPER.md`](./WHITEPAPER.md).

## Quickstart

### Prerequisites

- **Rust** ≥ 1.75 (with `cargo`)
- **Python** ≥ 3.10
- **GNU Make** ≥ 4.0
- ~3 GB free disk (for the mini-connectome dataset)

### Install & Run

```bash
git clone https://github.com/[YourUsername]/NurosOS.git
cd NurosOS && make bootstrap
# This downloads the mini-connectome dataset (125M synapses compressed to ~2GB)

# Start the OS in software-emulation mode on the Drosophila connectome
./nuros-cli start --mode=emulation --target=drosophila

# In another terminal, attach to the running instance
./nuros-cli attach --port=8080
```

### Build from source

```bash
make build        # builds kernel (cargo) + compiler (pip wheel)
make test         # runs the "Fly Benchmark" suite
make bench        # runs performance benchmarks vs. GPU baseline
```

## Directory Structure

```
NurosOS/
├── kernel/          # Rust microkernel — scheduler, IPC, memory management
├── compiler/        # SynapseLang parser, AST, bytecode generator (Python)
├── hal/             # Hardware drivers — x86, ARM, Loihi, FPGA
├── core/            # Core neural network algorithms — STDP, LIF models
├── tools/           # Profiling, debugging, visualization tools
├── docs/            # Architectural Decision Records (ADR) and whitepapers
├── tests/           # Unit + integration tests (the "Fly Benchmark")
└── examples/        # Sample apps — object tracking, associative memory search
```

## Roadmap

| Version | Codename      | Milestone                                                                                  |
|---------|---------------|--------------------------------------------------------------------------------------------|
| v0.1.0  | Alpha         | Kernel boots on x86_64 using software-emulated spiking networks. Runs fly locomotion.      |
| v0.2.0  | Beta          | SynapseLang compiler stabilizes. Parses 10% of the full connectome dataset.                |
| v0.3.0  | RC            | FPGA HAL implemented. Demonstrates 1000× power reduction for pattern recognition vs. GPU.  |
| v1.0.0  | Stable        | Production SDK released, including "Digital Twin" library for pharmaceutical testing.      |

See the [GitHub Issues](https://github.com/[YourUsername]/NurosOS/issues) board for tracked milestones.

## Key Features

- **Connectome Emulation Mode** — A virtual sandbox that runs the exact male fruit fly connectome to verify system stability and benchmark performance against biological ground truth.
- **Memory as Synaptic Weights** — Replaces the hierarchical file system with an associative memory store (Key-Value + Hebbian learning). Data is retrieved not by path, but by *stimulus* (partial input).
- **Fault Tolerance** — Inherent redundancy; if a process crashes, neighboring "neurons" in the OS cluster compensate using a distributed consensus algorithm.
- **Hybrid API** — REST/gRPC endpoints allow external AI models (PyTorch, TensorFlow) to query the OS, letting traditional deep learning interface with the biological architecture.

## Contributing

All contributions must align with the principle of **"Biological Plausibility First, Performance Second."** Code must pass the [Fly Benchmark](./tests/README.md) — a suite of tests verifying the system's emergent behavior matches actual fruit fly responses (e.g., obstacle avoidance, phototaxis).

We use GitFlow. `main` is protected and requires **2 peer reviews + green CI**. See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full workflow.

## License

Released under the **Apache License 2.0**. See [`LICENSE`](./LICENSE).

## Citation

If you use NurosOS in academic work, please cite:

```bibtex
@software{nurosos2026,
  title  = {NurosOS: A Bio-Inspired Neuromorphic Operating System},
  year   = {2026},
  url    = {https://github.com/[YourUsername]/NurosOS}
}
```

## Acknowledgements

NurosOS is built on the shoulders of the open connectomics community. The structural and functional design of the kernel is directly inspired by the complete *Drosophila melanogaster* connectome dataset released in 2026.
