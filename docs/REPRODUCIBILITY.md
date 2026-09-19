# Reproducibility

> Master prompt §36: "Can the system now demonstrate EXPERIENCE →
> EPISODIC MEMORY → REPLAY → CONSOLIDATION → MEMORY-DEPENDENT BEHAVIOR
> → DEVELOPMENTAL CHANGE → MEASURABLE TRAJECTORY"?
>
> Master prompt §27: "Every claim must be categorized as IMPLEMENTED /
> EXPERIMENTAL / PROPOSED / NOT VALIDATED."

---

## Reproducibility invariants

### 1. Determinism given a fixed seed

Every HippoCore operation is deterministic given a fixed seed. The PHASE 9
benchmark suite verifies this with multi-seed runs (>= 5 seeds per
condition, mean ± std reported).

The `HippoCoreMemoryConfig.replay_seed` knob controls RNG-based policy
selection. Pass `replay_seed=42` for reproducibility.

### 2. Checkpoint/restore round-trips

`MemoryEngine.checkpoint()` returns a JSON-native dict that
`MemoryEngine.restore(payload)` accepts. The PHASE 9 benchmark 10
verifies:

- `hash_match = 1.0` — memory count preserved.
- `content_match = 1.0` — sorted content lists match.
- Idempotency: restoring twice yields the same state as restoring once.

Cross-engine restore is supported: a `DefaultMemoryContract` can restore
a `HippoCoreMemory`-produced checkpoint (the entries/working_memory/
operation_log layout is identical in PHASE 3-8).

### 3. Replay fidelity (master prompt §19)

The PHASE 9 benchmark 10 + the existing Rust
`replay_from_checkpoint_is_exact_for_deterministic_engine` test
(`nuros-dev/src/checkpoint.rs:282-301`) confirm:

- For the deterministic numeric engine (`MinimumOrganism`): exact
  replay from checkpoint (action + reward match byte-for-byte).
- For the HippoCoreMemory Python side: content match + count match
  (PHASE 9 benchmark 10).

---

## Master prompt §36 final architectural test

| Stage | Status | Evidence |
|-------|--------|----------|
| EXPERIENCE | ✅ `[IMPLEMENTED]` | `HippoCoreMemory.encode_episode()` PHASE 4 |
| EPISODIC MEMORY | ✅ `[IMPLEMENTED]` | `MemoryEntry` with PHASE 4 schema + `MemoryProvenance` |
| REPLAY | ✅ `[IMPLEMENTED]` | 5 policies PHASE 5 |
| CONSOLIDATION | ✅ `[IMPLEMENTED]` | 2 strategies PHASE 6 |
| MEMORY-DEPENDENT BEHAVIOR | ⚠️ `[PARTIAL]` | `Organism.tick()` does not yet consult memory during action selection. **Highest-priority PHASE 10+ item.** |
| DEVELOPMENTAL CHANGE | ✅ `[IMPLEMENTED]` (separately) | `DevelopmentalState` evolves with ticks; PHASE 7 memory events feed the trajectory |
| MEASURABLE TRAJECTORY | ✅ `[IMPLEMENTED]` | `DevelopmentalTrajectory` (Rust) + PHASE 7 `MemoryEvent` emission + PHASE 9 benchmark 08 |

**Verdict**: PARTIAL → MOSTLY YES. The single explicit gap is
stage 5 (memory-dependent behavior), which is a PHASE 10+ follow-up
item.

---

## Manifest (master prompt §35)

The existing Rust `ReproducibilityManifest` (`nuros-dev/src/telemetry.rs:168-197`)
records hashes of genome, environment, checkpoint, configuration, and
dependencies. PHASE 10 follow-up: add `memory_state_hash` to the
manifest so two organisms with the same genome/env but different memory
contents get different manifests (audit Appendix B.9 fix at the
manifest level — currently the organism-level `state_hash()` is fixed
but the Rust manifest is not).

---

## Statistical validity (master prompt §27)

The PHASE 9 benchmark suite reports mean ± std across >= 5 seeds. No
single-seed results are presented as conclusions. The `n_seeds=5`
default follows master prompt §27 — "a 4-condition comparison without
multiple seeds is anecdotal, not scientific".

The benchmark outputs (JSON/CSV/Markdown) carry per-seed raw values so
downstream analysis can recompute statistics if needed.

---

## What is NOT validated (master prompt §27 "NOT VALIDATED")

- We do NOT claim "biologically equivalent to hippocampus" — we have
  no measurement comparing to neural data.
- We do NOT claim "conscious" — subjective experience is not measured.
- We do NOT claim "AGI" — this is research infrastructure, not a
  deployed system.
- We do NOT claim the PHASE 6 consolidation is "the same as biological
  memory consolidation" — we use computational proxies (tag-Jaccard,
  content-prefix), not neural-circuit-accurate mechanisms.
- We do NOT claim energy-efficiency measurements on real hardware
  (master prompt §24 explicitly forbids: "Do NOT claim specific wattage
  until measured on real hardware"). The PHASE 9 benchmarks report
  wall-clock latency in milliseconds, not wattage.

---

## How to reproduce the PHASE 9 benchmark results

```bash
# Clone + install (master prompt §24 — clean deps).
git clone https://github.com/modarresi1913/NurosOS.git
cd NurosOS

# Run the PHASE 9 benchmark suite (Python-only; no Rust build required).
python3 -c "from benchmarks.memory import run_all_benchmarks; from pathlib import Path; run_all_benchmarks(Path('./benchmarks/memory/results'), n_seeds=5)"

# Inspect results.
ls benchmarks/memory/results/
cat benchmarks/memory/results/01_pattern_separation/summary.md
cat benchmarks/memory/results/10_checkpoint_reproducibility/summary.md
```

For the Rust-side flagship experiment (`experiments/same_genome_different_world.py`),
the user needs to first build the Rust extension:

```bash
cd nuros-dev && maturin build --release && pip install --force-reinstall target/wheels/nuros_dev-*.whl && cd ..
python experiments/same_genome_different_world.py --steps 200
```

(The Rust build is not available in the PHASE 10 authoring environment
but is documented for downstream researchers.)
