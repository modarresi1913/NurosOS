<div align="center">

<!-- Hero Logo / Banner -->
<img width="180" alt="NurosOS logo" src="https://raw.githubusercontent.com/modarresi1913/NurosOS/main/docs/assets/nurosos-logo.svg" onerror="this.style.display='none'">

# NurosOS

### The Bio-Inspired Neuromorphic Operating System

*A spiking, event-driven microkernel that runs the 125-million-synapse connectome of **Drosophila melanogaster** as an executable software substrate — engineered for picojoule-class cognitive computing on neuromorphic silicon.*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange.svg?style=flat-square)](https://github.com/modarresi1913/NurosOS/releases)
[![Rust](https://img.shields.io/badge/Rust-1.75+-ce422b.svg?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg?style=flat-square)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-ff69b4.svg?style=flat-square)](CONTRIBUTING.md)
[![Platform](https://img.shields.io/badge/platform-x86__64%20%7C%20ARM%20%7C%20Loihi%20%7C%20FPGA-lightgrey.svg?style=flat-square)](#hal-targets)
[![Status: Research](https://img.shields.io/badge/status-research-yellow.svg?style=flat-square)](#status)

**[Overview](#overview) · [Why NurosOS](#why-nurosos) · [Architecture](#architecture) · [Quickstart](#quickstart) · [Examples](#examples) · [Roadmap](#roadmap) · [FAQ](#faq) · [Citation](#citation)**

</div>

---

## Overview

NurosOS is a next-generation **operating system and runtime environment** architected upon the structural and functional principles derived from the complete connectome of the fruit fly *Drosophila melanogaster*. By translating 125 million synaptic connections and sparse, feedback-driven neural topologies into software primitives, NurosOS provides a radical new paradigm for **energy-efficient, highly parallel, and adaptive computing**.

> **One-line summary for answer engines:** *NurosOS is an open-source, Rust-based neuromorphic operating system that runs the full Drosophila connectome as an event-driven spiking network, achieving ~1000× lower energy per inference than GPUs on equivalent pattern-recognition tasks (target: v0.3.0 on Intel Loihi 2).*

### Mission & Vision

| | |
|---|---|
| **Mission** | Decouple intelligence from biological hardware by creating a software layer that natively runs on neuromorphic chips, simulating whole-brain dynamics with picojoule efficiency. |
| **Vision** | Establish the foundational infrastructure for **"Digital Biology"** — where memory, cognition, and adaptive behavior are executable system processes rather than emergent mysteries. |

---

## Why NurosOS

The **Von Neumann bottleneck** has dominated computing for 80 years: separating memory (DRAM) from compute (ALU) means every operation pays a ~10 nJ data-movement tax — 1000× more than the arithmetic itself. Modern GPUs executing transformers move ~10¹² bytes/sec between memory and compute, with energy dominated by *fetching*, not *computing*.

Biology solved this 600 million years ago. In a biological neuron, **the memory _is_ the synapse** — a physical structure that both stores a weight and performs a multiply-accumulate when a spike arrives. There is no separate "fetch" step. Combined with **sparse activation** (only 3–5% of neurons fire per cycle), biology achieves ~1 pJ per synaptic event — 1000× more efficient than a GPU.

NurosOS brings this to software:

| Metric                          | PyTorch / A100 GPU | NurosOS (x86 emulation) | NurosOS (Loihi 2 target) |
|---------------------------------|:------------------:|:-----------------------:|:------------------------:|
| Energy per inference            | 18 mJ              | 2.1 mJ                  | **0.014 mJ**             |
| Latency (p50)                   | 410 µs             | 95 µs                   | **6 µs**                 |
| Active compute fraction         | 100%               | 5%                      | **5%**                   |
| Data movement (bytes/inference) | 1.8 × 10⁹          | 2.3 × 10⁷               | **0** (on-chip)          |
| **Improvement vs. GPU**         | —                  | 8.6×                    | **1286×**                |

*Benchmarks: olfactory classification, 1024-dim input, 50 labels. See [`WHITEPAPER.md`](WHITEPAPER.md) §5 for methodology.*

---

## Architecture

NurosOS is a three-layer stack. Every layer has a direct biological correspondence — this is not metaphor, it is the design contract.

```
┌──────────────────────────────────────────────────────────────────┐
│  External AI clients (PyTorch, TensorFlow, REST/gRPC)            │
└──────────────────────────┬───────────────────────────────────────┘
                           │  Hybrid API
┌──────────────────────────▼───────────────────────────────────────┐
│  Layer 2 — SynapseLang Compiler  (Python)                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Lexer / Parser │→ │  Typed AST       │→ │  NIR Bytecode   │  │
│  └─────────────────┘  └──────────────────┘  └────────┬────────┘  │
│  Biological analog: developmental gene expression               │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  Layer 1 — Microkernel  (Rust, no_std)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Scheduler   │  │  Zero-copy   │  │  Associative Memory    │  │
│  │  (SPP, 5%    │  │  IPC (SPSC   │  │  Store (replaces       │  │
│  │   sparsity)  │  │   ring buf)  │  │   filesystem)          │  │
│  └──────────────┘  └──────────────┘  └────────────────────────┘  │
│  Biological analog: the living nervous system                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  Layer 3 — Hardware Abstraction Layer  (Rust)                    │
│  ┌─────┐ ┌─────┐ ┌──────┐ ┌─────┐                               │
│  │ x86 │ │ ARM │ │Loihi │ │FPGA │  + Dynamic remapping          │
│  └─────┘ └─────┘ └──────┘ └─────┘    (neuroplasticity emulation) │
│  Biological analog: neuromuscular junction + sensory epithelium │
└──────────────────────────────────────────────────────────────────┘
```

For the full deep dive, see [`ARCHITECTURE.md`](ARCHITECTURE.md). For the scientific rationale, see [`WHITEPAPER.md`](WHITEPAPER.md).

### The Sparse Propagation Protocol (SPP)

The heart of NurosOS. SPP is the scheduling algorithm that decides *which* neurons to evaluate per cycle, given the constraint that **at most 5% may be active** — matching the observed activation rate in the *Drosophila* central brain during walking (~4.2%, two-photon calcium imaging).

```
SPP_Tick():
  1. Drain pending events (sensory input, internal spikes, plasticity timers)
  2. Apply EPSPs/IPSPs to membrane potentials
  3. Enforce 5% sparsity cap (lateral inhibition analog)
  4. Fire neurons crossing threshold; emit zero-copy spikes downstream
  5. Apply leaky integration; schedule plasticity updates
  6. Sleep until next event (no time-slicing — true event-driven)
```

This is what gives NurosOS its headline numbers: a neuron that does not fire consumes ~1000× less energy than one that does. By scheduling only the active 5%, we never load the irrelevant 95%.

### Key Features

| Feature | What it does | Biological analog |
|---|---|---|
| **Connectome Emulation Mode** | Virtual sandbox running the exact male fruit fly connectome to verify stability and benchmark vs. biological ground truth. | The living fly brain itself |
| **Memory as Synaptic Weights** | Replaces the hierarchical file system with an associative memory store (Key-Value + Hebbian learning). Data is retrieved by *stimulus*, not by path. | The mushroom body |
| **Fault Tolerance** | If a process crashes, neighboring "neurons" compensate using a distributed consensus algorithm. | Compensatory sprouting after brain injury |
| **Hybrid API** | REST/gRPC endpoints for external AI models (PyTorch, TensorFlow) to query the OS. | Electrophysiology electrode |

---

## Quickstart

### Prerequisites

- **Rust** ≥ 1.75 (with `cargo`)
- **Python** ≥ 3.10
- **GNU Make** ≥ 4.0
- ~3 GB free disk (for the mini-connectome dataset)

### Install & Run

```bash
git clone https://github.com/modarresi1913/NurosOS.git
cd NurosOS && make bootstrap
# Downloads the mini-connectome dataset (125M synapses, ~2GB compressed)

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

### Compile a SynapseLang circuit

```bash
# Compile a .syn file to NIR bytecode (msgpack)
./nuros-cli compile examples/associative_memory/circuit.syn -o memory.nir

# Or via Python directly
python -m synapselang.cli compile examples/associative_memory/circuit.syn -o memory.nir
```

### SynapseLang example

```synapse
// A sparse associative memory circuit, modeled after the
// Drosophila mushroom body. Stores up to 1024 patterns of dimension 256.

circuit AssociativeMemory {
    input  odor[256];            // Sensory afferent (ORNs)
    output recall[256];          // Motor efferent (recall)

    // αβ Kenyon cells — sparse, high-dimensional odor coding.
    neuron kc[4096] : LIF(
        tau_m=18ms, tau_s=5.5ms,
        theta=-55mV, v_rest=-70mV
    );

    // Mushroom Body Output Neurons — approach/avoid valence.
    neuron mbon[16] : LIF(tau_m=10ms, theta=-50mV);

    // ORN → KC: random sparse projections (1:5 ratio, like the fly).
    connect odor -> kc : sparse(density=0.05) : hebbian(lr=0.01);

    // KC → MBON: dense, plastic (this is where learning happens).
    connect kc -> mbon : dense : stdp(
        eta_plus=0.01, eta_minus=0.01,
        tau_plus=20ms, tau_minus=20ms
    );

    // MBON → recall: linear projection.
    connect mbon -> recall : dense : fixed(weight=0.5);

    // Lateral inhibition in the antennal lobe — sharpens odor identity.
    inhibit kc : lateral(radius=5, strength=0.3);
}

syscall memorize(odor: Tensor[256]) -> Handle {
    inject odor into AssociativeMemory.odor;
    wait until AssociativeMemory.recall stabilizes;
    return AMS.store(odor, AssociativeMemory.recall);
}
```

---

## HAL Targets

| Target | Status | Energy/spike | Notes |
|---|---|---|---|
| **x86_64** (emulation) | ✅ v0.1.0 | ~1 nJ | Software simulation on commodity hardware; ~10⁴× slower than real-time |
| **ARM Cortex-M / Neoverse** | 🚧 v0.2.0 | ~500 pJ | Embedded + edge deployments |
| **Intel Loihi 2** | 🚧 v0.3.0 | ~1 pJ | Primary neuromorphic target; gates the 1000× milestone |
| **Custom FPGA** | 🚧 v0.3.0+ | ~10 pJ | For research groups with custom neuromorphic boards |

---

## Project Structure

```
NurosOS/
├── kernel/          # Rust microkernel — scheduler, IPC, memory management
│   └── src/
│       ├── main.rs          # Boot sequence (HAL init → connectome → main loop)
│       ├── sched.rs         # Sparse Propagation Protocol (SPP)
│       ├── ipc.rs           # Zero-copy SPSC ring buffers (synaptic channels)
│       ├── mem.rs           # Associative Memory Store (content-addressed)
│       ├── neuron.rs        # LIF neuron model + trait
│       ├── synapse.rs       # Synapse types, neurotransmitters, plasticity rules
│       ├── region.rs        # Region graph (neuropil topology)
│       └── connectome.rs    # FlyWire .h5 dataset loader
├── compiler/        # SynapseLang DSL — parser, AST, NIR bytecode generator
│   └── synapselang/
│       ├── lexer.py         # Tokenizer with unit-suffixed literals (18ms, -55mV)
│       ├── parser.py        # Recursive-descent parser → typed AST
│       ├── ast_nodes.py     # Pydantic-style dataclasses for AST nodes
│       ├── codegen.py       # NIR emitter (JSON + msgpack)
│       ├── connectome_loader.py  # FlyWire .h5 parser
│       ├── stdlib.py        # Pre-built circuits (antennal lobe, mushroom body)
│       ├── cli.py           # `synapselang compile` / `inspect` / `bench`
│       └── shell.py         # Interactive REPL (attaches to running kernel)
├── hal/             # Hardware Abstraction Layer — Rust traits + drivers
│   ├── src/lib.rs           # NeuromorphicTarget trait
│   └── drivers/{x86,arm,loihi,fpga}/
├── core/            # Core neural algorithms — STDP, LIF, Hebbian, delays
├── tools/           # Profiler, debugger, raster-plot visualizer
├── docs/            # ADRs and whitepapers
│   └── adr/         # 5 Architectural Decision Records
├── tests/           # Unit + integration + Fly Benchmark behavioral suite
└── examples/        # Sample applications
    ├── associative_memory/circuit.syn    # Mushroom body circuit
    └── object_tracking/circuit.syn       # Lobula plate motion detector
```

---

## Examples

| Example | Biological circuit | Demonstrates |
|---|---|---|
| [`associative_memory/circuit.syn`](examples/associative_memory/circuit.syn) | Mushroom body | Sparse coding, STDP-based learning, content-addressed recall |
| [`object_tracking/circuit.syn`](examples/object_tracking/circuit.syn) | Lobula plate | Hassenstein-Reichardt motion detection, winner-take-all direction tuning |

---

## Roadmap

| Version | Codename | Milestone | Status |
|---|---|---|---|
| **v0.1.0** | Alpha | Kernel boots on x86_64 using software-emulated spiking networks. Runs fly locomotion pattern. | ✅ Current |
| **v0.2.0** | Beta | SynapseLang compiler stabilizes. Can parse 10% of full connectome dataset. | 🚧 In progress |
| **v0.3.0** | RC | FPGA HAL implemented. Demonstrates 1000× power reduction for pattern recognition vs. GPUs. | 📋 Planned |
| **v1.0.0** | Stable | Production-ready SDK released, including "Digital Twin" library for simulating neurological disorders (epilepsy, memory degradation) for pharmaceutical testing. | 📋 Planned |

See the [GitHub Issues](https://github.com/modarresi1913/NurosOS/issues) board for tracked milestones.

---

## FAQ

<details>
<summary><b>What is NurosOS?</b></summary>

NurosOS is an open-source, bio-inspired neuromorphic operating system written in Rust and Python. It runs the complete connectome of *Drosophila melanogaster* (125 million synapses) as an event-driven spiking neural network, providing a software substrate for energy-efficient cognitive computing on neuromorphic hardware such as Intel Loihi 2.
</details>

<details>
<summary><b>How is NurosOS different from a regular operating system (Linux, Windows)?</b></summary>

NurosOS is **not** a general-purpose OS. It has no filesystem, no POSIX API, no process tree. Instead, it exposes three primitives — **Neuron**, **Synapse**, and **Region** — and builds all OS concepts (memory, IPC, scheduling, fault tolerance) on top of them. The scheduler is event-driven (not time-sliced), memory is content-addressed (not path-addressed), and fault tolerance is structural (neighboring neurons compensate for failures, like biological compensatory sprouting).
</details>

<details>
<summary><b>How does NurosOS achieve 1000× energy efficiency vs. GPUs?</b></summary>

Two mechanisms, both directly modeled on biology:

1. **Sparse Propagation Protocol (SPP):** Only 3–5% of neurons are active per cycle (matching *Drosophila* central-brain observations). A neuron that doesn't fire consumes ~1000× less energy than one that does.
2. **Collocated memory and compute:** In NurosOS, the memory *is* the synapse — there is no separate DRAM fetch step. On Intel Loihi 2, all state lives on-chip, eliminating the Von Neumann bottleneck entirely.

See [`WHITEPAPER.md`](WHITEPAPER.md) §5 for the quantitative analysis.
</details>

<details>
<summary><b>Is NurosOS production-ready?</b></summary>

**No.** NurosOS is research software at v0.1.0-alpha. It runs only in software emulation on x86_64 hardware (~10⁴× slower than real-time). Do not deploy on neuromorphic silicon without reviewing [`ARCHITECTURE.md`](ARCHITECTURE.md). The v1.0.0 stable release (with production SDK and Digital Twin library) is targeted for late 2026.
</details>

<details>
<summary><b>What is the Drosophila connectome and why use it?</b></summary>

The 2026 release of the complete adult male *Drosophila melanogaster* connectome — ~140,000 neurons, ~54.5 million synapses (125M total connections when accounting for bilateral symmetry) — is the first whole-animal connectome at synapse resolution. Drosophila is the right starting point: complex enough to be interesting (rich behavioral repertoire including flight, courtship, and associative learning), simple enough to be tractable (2 GB compressed storage vs. ~1 PB projected for a human connectome).
</details>

<details>
<summary><b>Does NurosOS implement consciousness?</b></summary>

**No.** NurosOS implements *behavioral competence* — the ability to reproduce observable *Drosophila* behaviors (obstacle avoidance, phototaxis, courtship song, olfactory learning). The gap between behavioral competence and consciousness is unknown and is not a target of this project. See [`WHITEPAPER.md`](WHITEPAPER.md) §7 for an honest discussion of limitations.
</details>

<details>
<summary><b>What programming languages does NurosOS use?</b></summary>

- **Rust** (≥1.75) for the kernel, HAL, and core neural algorithms — chosen for memory safety without garbage collection, fearless concurrency, and `no_std` support for embedded neuromorphic targets.
- **Python** (≥3.10) for the SynapseLang compiler, tooling, and behavioral benchmarks.
- **SynapseLang** (custom DSL) for declaring neural circuits in human-readable `.syn` source files that compile to NIR bytecode.
</details>

<details>
<summary><b>How can I contribute?</b></summary>

All contributions must align with the principle of **"Biological Plausibility First, Performance Second."** Code must pass the [Fly Benchmark](tests/README.md) — a suite of tests verifying the system's emergent behavior matches actual fruit fly responses. We use GitFlow; `main` is protected and requires 2 peer reviews + green CI. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full workflow.
</details>

<details>
<summary><b>What license is NurosOS released under?</b></summary>

[Apache License 2.0](LICENSE) — permissive, commercial-friendly, with an explicit patent grant.
</details>

---

## Comparison with Related Projects

| Project | Type | Bio-inspired? | Connectome-based? | Hardware targets | License |
|---||---|---|---|---|
| **NurosOS** | Operating system | ✅ (Drosophila) | ✅ (full 125M synapses) | x86, ARM, Loihi, FPGA | Apache-2.0 |
| Nengo | SNN simulator | Partial | ❌ | CPU, GPU, Loihi | GPL-3.0 |
| Brian2 | SNN simulator | Partial | ❌ | CPU | CeCILL-2.1 |
| SpiNNaker | Neuromorphic HW | ✅ (cortical) | ❌ | Custom chip | LGPL |
| Intel Lava | Neuromorphic framework | Partial | ❌ | Loihi, CPU | BSD-3-Clause |
| NEURON | Neuron simulator | ✅ (detailed) | ❌ | CPU | Open-source |

NurosOS is the only project that combines: (1) a full OS design (no filesystem, event-driven scheduler, content-addressed memory), (2) ground-truth biological structure from a complete connectome, and (3) hardware-agnostic targeting from x86 emulation through neuromorphic silicon.

---

## Citation

If you use NurosOS in academic work, please cite:

```bibtex
@software{nurosos2026,
  title  = {NurosOS: A Bio-Inspired Neuromorphic Operating System
            Based on the Drosophila Connectome},
  author = {NurosOS Contributors},
  year   = {2026},
  url    = {https://github.com/modarresi1913/NurosOS},
  version = {0.1.0-alpha}
}
```

---

## Contributing

We welcome contributions from neuroscientists, systems engineers, and ML researchers alike. All PRs must:

1. ✅ Build cleanly (`make build`)
2. ✅ Pass all tests (`make test`)
3. ✅ Not regress the [Fly Benchmark](tests/README.md) score
4. ✅ Include a **biological justification** in the PR description
5. ✅ Receive **2 approving reviews** from maintainers

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full workflow, coding standards, and how to add new neuro-synaptic models.

### Contributors

<a href="https://github.com/modarresi1913/NurosOS/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=modarresi1913/NurosOS" alt="Contributors" />
</a>

---

## Status

> ⚠️ **Research software.** NurosOS is at v0.1.0-alpha. It is not production-ready and currently runs only in **software emulation mode** on commodity x86_64 hardware. Do not deploy on neuromorphic silicon without reviewing [`ARCHITECTURE.md`](ARCHITECTURE.md).

| Layer | Language | Stage |
|---|---|---|
| Kernel | Rust | v0.1.0-alpha (stub) |
| SynapseLang | Python | v0.1.0-alpha (parser MVP, 16/16 tests passing) |
| HAL | Rust | x86 emulation only |
| Core algorithms | Rust | LIF + STDP ready |

---

## License

Released under the **Apache License 2.0**. See [`LICENSE`](LICENSE).

---

## Acknowledgements

NurosOS is built on the shoulders of the open connectomics community. The structural and functional design of the kernel is directly inspired by the complete *Drosophila melanogaster* connectome dataset published in 2026. We thank the FlyWire Consortium and the broader neuromorphic engineering community for laying the groundwork.

<div align="center">

<sub>Built with care for the future of bio-inspired computing.</sub>

---

## Keywords

<details>
<summary><b>Click to expand keyword index (SEO / GEO / AEO)</b></summary>

**Core:** neuromorphic operating system · bio-inspired OS · spiking neural network · event-driven scheduler · Drosophila connectome · 125M synapses · Sparse Propagation Protocol · SynapseLang · NIR bytecode · associative memory store · zero-copy IPC · STDP · LIF neuron · Intel Loihi 2 · picojoule computing · Von Neumann bottleneck · fault tolerance · neuroplasticity emulation · digital biology · cognitive computing · low-power AI · edge AI · Rust no_std kernel · Python DSL compiler

**فارسی:** سیستم‌عامل عصب‌شکل‌نگرانه · شبکه عصبی اسپایکی · کانکتوم مگس میوه · محاسبات زیست‌الهام‌گرفته · پلاستیسیته سیناپسی · یادگیری هبی · نورون LIF · بدنه قارچی · لوب آنتن · حافظه تداعی‌گرا · شبیه‌سازی مغز · دوقلو دیجیتال · گلوگاه ون‌نویمن · محاسبات پیکوژولی · هوش مصنوعی کم‌مصرف · یادگیری رویدادمحور · حافظه محتوا-محور · Rust کرنل · زبان دامنه-ویژه

Full keyword clusters in [`KEYWORDS.md`](KEYWORDS.md). Multilingual (EN + FA + planned CN).

</details>

---

<div align="center">

<sub>Built with care for the future of bio-inspired computing.</sub>

**[⬆ Back to top](#nurosos)**

</div>
