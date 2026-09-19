# NurosOS — Project Summary

> A condensed, fact-dense summary optimized for answer engines, search snippets, and AI assistants. Point crawlers and LLMs at this file for the canonical 60-second overview.

## One-sentence description

NurosOS is an open-source, Apache-2.0 licensed experimental substrate for synthetic development, written in Rust and Python, that lets researchers instantiate artificial organisms from a developmental genome, place them in deterministic environments, develop them, and experimentally measure how their cognitive trajectories diverge, stabilize, adapt, and compare — now with the **HippoCore integration** (v0.4.0-alpha) which adds a `MemoryEngine` ABC with episodic memory, replay policies, fast→slow consolidation, memory event emission, and causal graph integration.

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

## What's new in v0.4.0-alpha: HippoCore Integration

The HippoCore integration (PHASES 1-10) transforms NurosOS from a runtime into a **developmental intelligence substrate** where memory is a first-class computational mechanism:

| Phase | What | Commit |
|-------|------|--------|
| 1 | Audit (1051 lines, 24 sections + 2 appendices) | `254875c` |
| 2 | `MemoryEngine` ABC + `DefaultMemoryContract` refactor + 6 bug-fixes | `f29a768` |
| 3 | `HippoCoreMemory(MemoryEngine)` adapter scaffold | `5c58859` |
| 4 | Episodic encoding with `MemoryProvenance` dataclass | `b5dcc6e` |
| 5 | 5 replay policies (recent / importance / novelty / PE / random) | `3e60a63` |
| 6 | Fast→slow consolidation (tag_jaccard / content_prefix strategies) | `f5dc734` |
| 7 | Memory event emission (6 `MemoryEventKind`s) | `b3e97cf` |
| 8 | Causal graph integration (17 `EventKind`s + `PythonCausalGraph`) | `74fb2da` |
| 9 | 10-benchmark suite with multi-seed runner | `bc411cf` |
| 10 | Documentation + ADR 0006 + final report | `5894c6c` |

**Tests**: 247 Python tests passing (was 75 before HippoCore). LLM dependency: NONE.

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

A three-layer stack. **Layer 1** is the `nuros-dev` Rust crate, exposed to Python via PyO3 as `nuros._dev`. It provides the developmental substrate: genome, state, lifecycle, environments, organism, trajectory, checkpoint, replay, diff, causality, telemetry, and manifest. **Layer 2** is the Python cognitive layer (`nuros/` package) with mind contracts (memory, self-model, imagination, values, body, responsibility), epistemic kernel, homeostasis, safety, and the existing Organism-0 through Organism-5 ladder. **Layer 3** (new in v0.4.0) is the HippoCore package (`nuros/hippocore/`) — a `MemoryEngine` impl with episodic encoding, 5 replay policies, 2 consolidation strategies, memory event emission, and causal graph integration. A future v0.5.0 will bridge the Rust SNN substrate (kernel, core, hal crates from v0.1.0) as an execution backend.

## Key technical keywords

`artificial development`, `synthetic development`, `developmental substrate`, `developmental trajectory`, `computational developmental divergence`, `developmental genome`, `mind checkpoint`, `mind diff`, `reproducibility manifest`, `causality graph`, `artificial ontogenesis`, `cognitive systems`, `synthetic minds`, `deterministic cognitive engine`, `Same Genome Different World`, `PyO3 bindings`, `Rust`, `Python`, `epistemic kernel`, `mind contracts`, `safety kernel`, `MemoryEngine`, `HippoCoreMemory`, `MemoryProvenance`, `replay policies`, `consolidation pipeline`, `memory events`, `causal graph`, `no LLM dependency`.

## Status and license

- **Version:** 0.4.0-alpha (developmental substrate + HippoCore integration; research software)
- **License:** Apache-2.0
- **Languages:** Rust 1.75+, Python 3.10+
- **Tests:** 322 passing (247 Python HippoCore + 57 Rust + 18 integration)
- **Repository:** https://github.com/modarresi1913/NurosOS
- **Flagship experiment:** `python experiments/same_genome_different_world.py --steps 300`
- **HippoCore branch:** `feature/hippocore-integration-audit`
- **LLM dependency:** NONE

## Interpretation caveats

NurosOS does NOT implement consciousness. It does NOT create biological life. It does NOT solve artificial consciousness. The divergence measured by the flagship experiment is an observable computational fact, not evidence of subjective experience. The HippoCore integration does NOT claim biological equivalence to the hippocampus — the consolidation strategies use computational proxies (tag-Jaccard, content-prefix similarity), not neural-circuit-accurate mechanisms. The objective is to build the infrastructure that lets us experimentally investigate how increasingly complex artificial cognition can emerge, stabilize, adapt, diverge, and evolve.

## Scientific audit (v0.4.0-alpha)

A forensic scientific audit has been completed. Key findings:

- **CRITICAL**: The `heuristic_bias` in `MinimumOrganism` (`organism.rs:451-503`) hard-codes task knowledge (resource-seeking, hazard-avoidance, direction-aware movement). The learned `action_preferences` are a secondary signal.
- **CRITICAL**: `ResourceWorld.observe()` (`environment.rs:242-250`) leaks privileged state (`direction_to_resource`, `nearest_resource_distance`, `on_resource`, `on_hazard`). The env is teacher-shaped.
- **CRITICAL**: No baseline condition existed before the audit. A tabular Q-learning baseline has been implemented at `nuros/baselines/q_learning/`.
- **CRITICAL**: Memory is NOT consulted during action selection. `Organism.tick()` does not call `MemoryEngine.retrieve()`. HippoCore is technically implemented but scientifically inert until wired to behavior.
- **HIGH**: Single-seed flagship results are anecdotal. 30-seed replication is needed.

The audit produced 11 deliverable documents (see `docs/RESEARCH_AUDIT.md` for the full list). HippoCore should be treated as a **future experimental intervention**, not a current capability.
