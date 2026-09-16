# NurosOS Architecture Overview

> **Note (v0.3.0-alpha):** This document describes the v0.2.0 cognitive
> architecture. NurosOS has since evolved into "The Experimental Substrate
> for Synthetic Development". For the current v0.3.0+ architecture (with
> the new Developmental Substrate layer), see
> [../../ARCHITECTURE.md](../../ARCHITECTURE.md) and
> [../../DEVELOPMENTAL_SUBSTRATE.md](../../DEVELOPMENTAL_SUBSTRATE.md).

## The Central Thesis (v0.2.0 — preserved)

We don't want to merely build larger models. We want to explore the **computational conditions** under which artificial systems can develop memory, agency, prediction, adaptation, self-modeling, and embodied behavior.

NurosOS is not an operating system for AI. It is a **runtime for systems that can become intelligent** — a substrate where artificial cognitive organisms can instantiate, develop through experience, maintain internal state, interact with environments, undergo plasticity, construct memories, model themselves, simulate futures, and remain observable and corrigible.

## Layer Architecture

```
┌─────────────────────────────────────────────────┐
│                   Applications                   │
├─────────────────────────────────────────────────┤
│              Artificial Organisms                 │
│         (Organism-0 → Organism-5 Ladder)         │
├─────────────────────────────────────────────────┤
│           Mind Contract Layer (MCL)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐     │
│  │  Memory  │ │ SelfModel│ │ Imagination  │     │
│  ├──────────┤ ├──────────┤ ├──────────────┤     │
│  │ Values   │ │  Body    │ │Responsibility│     │
│  └──────────┘ └──────────┘ └──────────────┘     │
├─────────────────────────────────────────────────┤
│              Cognitive Kernel                     │
│   Attention │ Planning │ Reflection │ Prediction │
│   WorldModel│ Uncertainty                        │
├─────────────────────────────────────────────────┤
│            Organismic Kernel                      │
│   Homeostasis │ Development │ Plasticity          │
│   Energy │ Lifecycle │ Self-organization          │
├─────────────────────────────────────────────────┤
│        Safety Kernel (architecturally independent)│
│   Permissions │ Audit │ Human Override │ Shutdown │
│   Recovery │ Immutable Constraints               │
├─────────────────────────────────────────────────┤
│        Neural / Cognitive Execution Layer         │
│   SNN │ LLM │ Symbolic │ Hybrid                  │
├─────────────────────────────────────────────────┤
│              Hardware Abstraction (HAL)           │
│   x86 │ ARM │ FPGA │ Loihi │ GPU                 │
└─────────────────────────────────────────────────┘
```

## Design Principles

1. **Epistemic Hygiene**: Every internal representation carries an epistemic label identifying its origin
2. **Architectural Independence of Safety**: Safety kernel cannot be modified by cognitive subsystems
3. **Developmental, not Pre-Specified**: Organisms develop through experience, not static configuration
4. **Observable and Corrigible**: Every action has an auditable causal chain
5. **Reproducible**: Genome + Experience + Runtime = Deterministic replay
6. **Embodiment-Portable**: Same mind can inhabit different bodies

## The Organism Ladder

| Level | Organism | Capabilities |
|-------|----------|-------------|
| 0 | Minimal Viable | Sensory loop, episodic memory, homeostasis |
| 1 | Predictive | + Prediction, prediction error, semantic memory |
| 2 | Imaginative | + Counterfactual reasoning, simulation, risk assessment |
| 3 | Self-Modeling | + Metacognition, self-assessment, capability modeling |
| 4 | Social | + Theory of mind, communication, social reasoning |
| 5 | Full Autonomous | + Goal-setting, planning, value-driven decisions |
