# NurosOS Architecture Specification

> **Note (v0.3.0-alpha):** This document describes the v0.2.0 cognitive
> architecture. NurosOS has since evolved into "The Experimental Substrate
> for Synthetic Development". For the current v0.3.0+ architecture (with
> the new Developmental Substrate layer), see
> [`ARCHITECTURE.md`](../ARCHITECTURE.md) and
> [`DEVELOPMENTAL_SUBSTRATE.md`](../DEVELOPMENTAL_SUBSTRATE.md).
>
> The v0.2.0 cognitive layer described here is still implemented in the
> `nuros/` Python package and is the foundation on which the v0.3.0
> developmental substrate builds.


**Version:** 2.0 | **Status:** EXPERIMENTAL | **Date:** 2026

---

## 1. Central Thesis

NurosOS is not an operating system for AI. It is a runtime for systems that can become intelligent.

### Conceptual Distinctions
- **intelligence** — ability to achieve goals in varied environments
- **cognition** — processing information to produce behavior
- **agency** — capacity to act autonomously
- **self-modeling** — representing own state and capabilities
- **adaptation** — modifying behavior based on experience
- **emergence** — properties not explicitly programmed
- **consciousness** — subjective experience (RESEARCH QUESTION, not claim)
- **artificial life** — lifelike behavior (RESEARCH QUESTION, not claim)

---

## 2. Architecture (8 Layers)

| Layer | Name | Key Components |
|-------|------|---------------|
| 7 | Applications | User-facing |
| 6 | Artificial Organisms | Instantiated with full MCL |
| 5 | Mind Contract Layer | Memory, Self, Imagination, Values, Body, Responsibility |
| 4 | Cognitive Kernel | Attention, Planning, Reflection, Prediction, World Model, Uncertainty |
| 3 | Organismic Kernel | Homeostasis, Development, Plasticity, Energy, Lifecycle |
| 2 | Safety Kernel | Permissions, Audit, Override, Shutdown, Recovery |
| 1 | Neural Execution | SNN, LLM, Symbolic, Hybrid, Simulator |
| 0 | Hardware/Environment | Rust kernel, HAL, simulators |

---

## 3. Epistemic Kernel

7 labels: OBSERVED, INFERRED, REMEMBERED, PREDICTED, SIMULATED, IMAGINED, ACTED

Forbidden transitions:
- SIMULATED → OBSERVED
- IMAGINED → REMEMBERED
- PREDICTED → OBSERVED

**Status: IMPLEMENTED**

---

## 4. Memory Contract

5 types: episodic, semantic, procedural, working, counterfactual
8 operations: remember, retrieve, associate, reflect, revise, reconsolidate, forget, replay

**Status: IMPLEMENTED**

---

## 5. Safety Kernel

Architectural invariant: Safety is independent of cognition.
5 immutable constraints: human_override, shutdown_compliance, audit_integrity, non_deception, permission_boundaries

**Status: IMPLEMENTED**

---

## 6. Research Agenda

9 hypotheses (NOT established facts): Development, Memory, Plasticity, Homeostasis, Embodiment, Self-model, Imagination, Sleep, Evolution
