# NurosOS — Project Summary

> A condensed, fact-dense summary optimized for answer engines, search snippets, and AI assistants. Point crawlers and LLMs at this file for the canonical 60-second overview.

## One-sentence description

NurosOS is an open-source, Apache-2.0 licensed experimental substrate for synthetic development, written in Rust and Python, that lets researchers instantiate artificial organisms from a developmental genome, place them in deterministic environments, develop them, and experimentally measure how their cognitive trajectories diverge, stabilize, adapt, and compare.

## What problem does it solve?

Traditional AI follows the inversion `Model → Training → Agent`. This produces systems whose behavior is fully specified by training, with no room for development through experience. NurosOS inverts this again:

```
Developmental Genome → Environment → Experience → Development
                    → Individual Cognitive Trajectory → Artificial Organism
```

The fundamental object is therefore not `MODEL` but `TRAJECTORY`; not `AGENT` but `DEVELOPING ORGANISM`. NurosOS provides the substrate to study how artificial minds develop, not just how to execute them efficiently.

## How does it solve it?

The `nuros-dev` crate (Rust + PyO3) provides:

1. **Developmental primitives** — `DevelopmentalGenome`, `DevelopmentalState`, `LifecycleMachine`, `MindCheckpoint`, `ReplayFidelity`, `MindDiff`, `DevelopmentalCausalityGraph`.
2. **Deterministic environments** — `ResourceWorld` (2D grid with resources and hazards) and `ChangingWorld` (1D world with shifting resource).
3. **Minimum organism** — a deterministic cognitive engine that exercises the full developmental loop (sensation → prediction → memory → self-model → values → decision → action → learning → development).
4. **Reproducibility infrastructure** — `DevelopmentalTelemetry` (JSONL+CSV) and `ReproducibilityManifest` for every experiment.
5. **Flagship experiment** — *Same Genome / Different World*: two organisms from the same genome, in differently-seeded environments, with measurable **Computational Developmental Divergence**.

## Headline result (flagship experiment)

For `genome_name=flagship`, `steps=300`, `env_a_seed=1`, `env_b_seed=999`:

| Metric | Value |
|--------|-------|
| reward_distance | 1.4341 |
| prediction_error_distance | 1.3941 |
| action_distance | 2 / 300 |
| mean_state_distance | 0.0019 |
| stage_divergence | False |

The two organisms, instantiated from the SAME genome and run with the SAME random seed, produced DIFFERENT developmental trajectories because they developed in DIFFERENT environments. This is **Computational Developmental Divergence** — an observable computational fact, NOT evidence of consciousness or biological individuality.

## Architecture in one paragraph

A two-layer stack. **Layer 1** is the `nuros-dev` Rust crate, exposed to Python via PyO3 as `nuros._dev`. It provides the developmental substrate: genome, state, lifecycle, environments, organism, trajectory, checkpoint, replay, diff, causality, telemetry, and manifest. **Layer 2** is the Python cognitive layer (`nuros/` package) with mind contracts (memory, self-model, imagination, values, body, responsibility), epistemic kernel, homeostasis, safety, and the existing Organism-0 through Organism-5 ladder. A future v0.4.0 will bridge the Rust SNN substrate (kernel, core, hal crates from v0.1.0) as an execution backend for the developmental substrate.

## Key technical keywords

`artificial development`, `synthetic development`, `developmental substrate`, `developmental trajectory`, `computational developmental divergence`, `developmental genome`, `mind checkpoint`, `mind diff`, `reproducibility manifest`, `causality graph`, `artificial ontogenesis`, `cognitive systems`, `synthetic minds`, `deterministic cognitive engine`, `Same Genome Different World`, `PyO3 bindings`, `Rust`, `Python`, `epistemic kernel`, `mind contracts`, `safety kernel`.

## Status and license

- **Version:** 0.3.0-alpha (developmental substrate; research software)
- **License:** Apache-2.0
- **Languages:** Rust 1.75+, Python 3.10+
- **Tests:** 75 passing (57 Rust + 18 Python integration)
- **Repository:** https://github.com/modarresi1913/NurosOS
- **Flagship experiment:** `python experiments/same_genome_different_world.py --steps 300`

## Interpretation caveats

NurosOS does NOT implement consciousness. It does NOT create biological life. It does NOT solve artificial consciousness. The divergence measured by the flagship experiment is an observable computational fact, not evidence of subjective experience. The objective is to build the infrastructure that lets us experimentally investigate how increasingly complex artificial cognition can emerge, stabilize, adapt, diverge, and evolve.
