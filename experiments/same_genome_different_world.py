"""
Same Genome / Different World — the flagship NurosOS developmental experiment.

Hypothesis
----------
Identical initial computational conditions (same genome, same runtime, same
random seed) can produce divergent developmental states under different
environmental histories.

Method
------
1. Construct a single DevelopmentalGenome G.
2. Instantiate two organisms A and B from G.
3. Verify genome_hash(A) == genome_hash(B).
4. Place A in ResourceWorld(seed=env_a_seed) and B in ResourceWorld(seed=env_b_seed).
5. Develop both for N steps.
6. Record trajectories, telemetry, and final checkpoints.
7. Compute DevelopmentalDivergence(A, B).
8. Compute MindDiff between final states of A and B.
9. Build a ReproducibilityManifest for each organism.
10. Render a human-readable report + save machine-readable artifacts.

Interpretation caveat
---------------------
The phenomenon measured here — *Computational Developmental Divergence* —
is NOT evidence of consciousness, biological individuality, or subjective
experience. It is an observable computational fact: identical initial
conditions, different environmental histories, divergent developmental
states. The scientific interest is in characterizing *how* this divergence
emerges as a function of environmental structure, genome parameters, and
runtime properties.

Usage
-----
    python experiments/same_genome_different_world.py \\
        --steps 200 --env-a-seed 1 --env-b-seed 999 --width 6 --height 6 \\
        --out-dir ./experiment_outputs/same_genome_different_world

Outputs (written to --out-dir)
------------------------------
    genome.json                      — the genome used (with hash)
    trajectory_a.jsonl               — per-step trajectory for organism A
    trajectory_b.jsonl               — per-step trajectory for organism B
    telemetry_a.csv                  — flat telemetry table for A
    telemetry_b.csv                  — flat telemetry table for B
    checkpoint_a.json                — final checkpoint for A
    checkpoint_b.json                — final checkpoint for B
    divergence.json                  — DevelopmentalDivergence between A and B
    mind_diff.json                   — MindDiff between final states of A and B
    manifest_a.json                  — ReproducibilityManifest for A
    manifest_b.json                  — ReproducibilityManifest for B
    report.txt                       — human-readable summary
    summary.json                     — machine-readable summary
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Make the `nuros` package importable whether this script is run from the
# repository root or from the experiments/ directory.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nuros import _dev  # type: ignore[attr-defined]


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def run_experiment(
    steps: int = 200,
    env_a_seed: int = 1,
    env_b_seed: int = 999,
    width: int = 6,
    height: int = 6,
    genome_name: str = "flagship",
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the Same Genome / Different World experiment.

    Returns a dict with all artifacts. If `out_dir` is provided, also writes
    the artifacts to disk.
    """
    if out_dir is not None:
        _ensure_dir(out_dir)

    # 1. Construct the genome.
    genome = _dev.DevelopmentalGenome(genome_name)
    genome_hash = genome.hash
    genome_short = genome.short_hash

    # 2-3. Instantiate two organisms from the same genome and verify hash equality.
    org_a = _dev.MinimumOrganism(genome)
    org_b = _dev.MinimumOrganism(genome)
    assert org_a.genome_hash == org_b.genome_hash == genome_hash, "genome hash mismatch"
    org_a.initialize()
    org_a.begin_development()
    org_b.initialize()
    org_b.begin_development()

    # 4. Place each in a different (differently-seeded) ResourceWorld.
    env_a = _dev.ResourceWorld(width, height, env_a_seed)
    env_b = _dev.ResourceWorld(width, height, env_b_seed)
    env_a.reset()
    env_b.reset()
    env_a_hash = env_a.hash
    env_b_hash = env_b.hash

    # 5. Develop both for N steps. Record per-step trajectories as JSONL.
    traj_a_lines: list[str] = []
    traj_b_lines: list[str] = []
    telemetry_a_rows: list[dict[str, Any]] = []
    telemetry_b_rows: list[dict[str, Any]] = []

    cum_reward_a = 0.0
    cum_reward_b = 0.0
    cum_pe_a = 0.0
    cum_pe_b = 0.0

    for i in range(steps):
        tick_a = org_a.tick_resource(env_a)
        tick_b = org_b.tick_resource(env_b)
        cum_reward_a += tick_a["reward"]
        cum_reward_b += tick_b["reward"]
        cum_pe_a += tick_a["prediction_error"]
        cum_pe_b += tick_b["prediction_error"]

        traj_a_lines.append(json.dumps(tick_a, default=str))
        traj_b_lines.append(json.dumps(tick_b, default=str))

        telemetry_a_rows.append({
            "step": tick_a["step"],
            "action": tick_a["action"],
            "reward": tick_a["reward"],
            "prediction_error": tick_a["prediction_error"],
            "developmental_stage": tick_a["developmental_stage"],
            "energy": tick_a["energy"],
            "plasticity": tick_a["plasticity"],
            "memory_size": tick_a["memory_size"],
            "cum_reward": cum_reward_a,
            "cum_pe": cum_pe_a,
            "state_hash": tick_a["state_hash"],
        })
        telemetry_b_rows.append({
            "step": tick_b["step"],
            "action": tick_b["action"],
            "reward": tick_b["reward"],
            "prediction_error": tick_b["prediction_error"],
            "developmental_stage": tick_b["developmental_stage"],
            "energy": tick_b["energy"],
            "plasticity": tick_b["plasticity"],
            "memory_size": tick_b["memory_size"],
            "cum_reward": cum_reward_b,
            "cum_pe": cum_pe_b,
            "state_hash": tick_b["state_hash"],
        })

    # 6. Take final checkpoints.
    checkpoint_a = org_a.checkpoint_resource(env_a, env_a_seed, 0, "final_a")
    checkpoint_b = org_b.checkpoint_resource(env_b, env_b_seed, 0, "final_b")

    # 7. Compute divergence via the Rust-side flagship runner (single source of truth).
    flagship_json = _dev.run_same_genome_different_world(
        steps=steps,
        env_a_seed=env_a_seed,
        env_b_seed=env_b_seed,
        width=width,
        height=height,
        genome_name=genome_name,
    )
    flagship = json.loads(flagship_json)
    divergence = flagship["divergence"]

    # 8. Compute MindDiff between final organism states.
    snap_a = json.loads(org_a.snapshot())
    snap_b = json.loads(org_b.snapshot())
    mind_diff_json = _dev.mind_diff(json.dumps(snap_a, default=str), json.dumps(snap_b, default=str))
    mind_diff = json.loads(mind_diff_json)

    # 9. Reproducibility manifests.
    manifest_a = flagship["manifest_a"]
    manifest_b = flagship["manifest_b"]

    # 10. Human-readable report.
    report = _render_report(
        genome_name=genome_name,
        genome_hash=genome_hash,
        genome_short=genome_short,
        steps=steps,
        env_a_seed=env_a_seed,
        env_b_seed=env_b_seed,
        env_a_hash=env_a_hash,
        env_b_hash=env_b_hash,
        cum_reward_a=cum_reward_a,
        cum_reward_b=cum_reward_b,
        cum_pe_a=cum_pe_a,
        cum_pe_b=cum_pe_b,
        final_stage_a=org_a.developmental_stage,
        final_stage_b=org_b.developmental_stage,
        divergence=divergence,
        mind_diff=mind_diff,
        manifest_a=manifest_a,
        manifest_b=manifest_b,
    )

    summary = {
        "experiment": "same_genome_different_world",
        "genome_name": genome_name,
        "genome_hash": genome_hash,
        "genome_short_hash": genome_short,
        "n_steps": steps,
        "env_a_seed": env_a_seed,
        "env_b_seed": env_b_seed,
        "env_a_hash": env_a_hash,
        "env_b_hash": env_b_hash,
        "final_stage_a": org_a.developmental_stage,
        "final_stage_b": org_b.developmental_stage,
        "total_reward_a": cum_reward_a,
        "total_reward_b": cum_reward_b,
        "total_prediction_error_a": cum_pe_a,
        "total_prediction_error_b": cum_pe_b,
        "divergence": {
            "mean_state_distance": divergence["mean_state_distance"],
            "final_state_distance": divergence["final_state_distance"],
            "reward_distance": divergence["reward_distance"],
            "prediction_error_distance": divergence["prediction_error_distance"],
            "action_distance": divergence["action_distance"],
            "stage_divergence": divergence["stage_divergence"],
        },
        "mind_diff_identical": mind_diff["identical"],
        "mind_diff_developmental_state_l1": mind_diff["developmental_changes"]["state_l1_distance"],
        "interpretation": (
            "Computational Developmental Divergence: identical initial "
            "computational conditions produced divergent developmental "
            "states under different environmental histories. This is NOT "
            "evidence of consciousness or biological individuality."
        ),
    }

    # Write to disk if requested.
    if out_dir is not None:
        _write_json(out_dir / "genome.json", {
            "name": genome_name,
            "hash": genome_hash,
            "short_hash": genome_short,
            "json": genome.to_json(),
        })
        (out_dir / "trajectory_a.jsonl").write_text("\n".join(traj_a_lines) + "\n", encoding="utf-8")
        (out_dir / "trajectory_b.jsonl").write_text("\n".join(traj_b_lines) + "\n", encoding="utf-8")
        _write_csv(out_dir / "telemetry_a.csv", telemetry_a_rows)
        _write_csv(out_dir / "telemetry_b.csv", telemetry_b_rows)
        (out_dir / "checkpoint_a.json").write_text(checkpoint_a, encoding="utf-8")
        (out_dir / "checkpoint_b.json").write_text(checkpoint_b, encoding="utf-8")
        _write_json(out_dir / "divergence.json", divergence)
        _write_json(out_dir / "mind_diff.json", mind_diff)
        _write_json(out_dir / "manifest_a.json", manifest_a)
        _write_json(out_dir / "manifest_b.json", manifest_b)
        _write_text(out_dir / "report.txt", report)
        _write_json(out_dir / "summary.json", summary)

    return {
        "summary": summary,
        "report": report,
        "divergence": divergence,
        "mind_diff": mind_diff,
        "manifest_a": manifest_a,
        "manifest_b": manifest_b,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = list(rows[0].keys())
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(str(r.get(c, "")) for c in cols))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_report(
    genome_name: str,
    genome_hash: str,
    genome_short: str,
    steps: int,
    env_a_seed: int,
    env_b_seed: int,
    env_a_hash: str,
    env_b_hash: str,
    cum_reward_a: float,
    cum_reward_b: float,
    cum_pe_a: float,
    cum_pe_b: float,
    final_stage_a: str,
    final_stage_b: str,
    divergence: dict[str, Any],
    mind_diff: dict[str, Any],
    manifest_a: dict[str, Any],
    manifest_b: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("NurosOS — Flagship Experiment")
    lines.append("Same Genome / Different World")
    lines.append("=" * 72)
    lines.append("")
    lines.append("HYPOTHESIS")
    lines.append("  Identical initial computational conditions (same genome,")
    lines.append("  same runtime, same random seed) can produce divergent")
    lines.append("  developmental states under different environmental histories.")
    lines.append("")
    lines.append("INTERPRETATION CAVEAT")
    lines.append("  The phenomenon measured here — Computational Developmental")
    lines.append("  Divergence — is NOT evidence of consciousness, biological")
    lines.append("  individuality, or subjective experience. It is an observable")
    lines.append("  computational fact about divergent developmental trajectories.")
    lines.append("")
    lines.append("-" * 72)
    lines.append("GENOME")
    lines.append(f"  name:        {genome_name}")
    lines.append(f"  hash:        {genome_hash}")
    lines.append(f"  short hash:  {genome_short}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("ORGANISM A")
    lines.append(f"  environment:    ResourceWorld(width=6, height=6, seed={env_a_seed})")
    lines.append(f"  env_hash:       {env_a_hash}")
    lines.append(f"  steps:          {steps}")
    lines.append(f"  total_reward:   {cum_reward_a:.4f}")
    lines.append(f"  total_pe:       {cum_pe_a:.4f}")
    lines.append(f"  final_stage:    {final_stage_a}")
    lines.append("")
    lines.append("ORGANISM B")
    lines.append(f"  environment:    ResourceWorld(width=6, height=6, seed={env_b_seed})")
    lines.append(f"  env_hash:       {env_b_hash}")
    lines.append(f"  steps:          {steps}")
    lines.append(f"  total_reward:   {cum_reward_b:.4f}")
    lines.append(f"  total_pe:       {cum_pe_b:.4f}")
    lines.append(f"  final_stage:    {final_stage_b}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("DEVELOPMENTAL DIVERGENCE")
    lines.append(f"  n_steps compared:       {divergence['n_steps']}")
    lines.append(f"  reward_distance:        {divergence['reward_distance']:.4f}")
    lines.append(f"  prediction_error_dist:  {divergence['prediction_error_distance']:.4f}")
    lines.append(f"  action_distance:        {divergence['action_distance']:.0f} / {divergence['n_steps']}")
    lines.append(f"  mean_state_distance:    {divergence['mean_state_distance']:.4f}")
    lines.append(f"  final_state_distance:   {divergence['final_state_distance']:.4f}")
    lines.append(f"  stage_divergence:       {divergence['stage_divergence']}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("MIND DIFF (final state A vs final state B)")
    lines.append(f"  identical:                    {mind_diff['identical']}")
    lines.append(f"  step_delta:                   {mind_diff['step_delta']}")
    lines.append(f"  memory added/removed:         {mind_diff['memory_changes']['added']}/{mind_diff['memory_changes']['removed']}")
    lines.append(f"  value_changes total L1:       {mind_diff['value_changes']['total_l1']:.4f}")
    lines.append(f"  developmental state L1:       {mind_diff['developmental_changes']['state_l1_distance']:.4f}")
    lines.append(f"  stage A → B:                  {mind_diff['developmental_changes']['stage_a']} → {mind_diff['developmental_changes']['stage_b']}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("REPRODUCIBILITY (organism A)")
    lines.append(f"  mind_id:          {manifest_a['mind_id']}")
    lines.append(f"  genome_hash:      {manifest_a['genome_hash'][:24]}...")
    lines.append(f"  environment_hash: {manifest_a['environment_hash'][:24]}...")
    lines.append(f"  checkpoint_hash:  {manifest_a['checkpoint_hash'][:24]}...")
    lines.append(f"  n_steps:          {manifest_a['n_steps']}")
    lines.append(f"  random_seed:      {manifest_a['random_seed']}")
    lines.append(f"  env_seed:         {manifest_a['environment_seed']}")
    lines.append("")
    lines.append("REPRODUCIBILITY (organism B)")
    lines.append(f"  mind_id:          {manifest_b['mind_id']}")
    lines.append(f"  genome_hash:      {manifest_b['genome_hash'][:24]}...")
    lines.append(f"  environment_hash: {manifest_b['environment_hash'][:24]}...")
    lines.append(f"  checkpoint_hash:  {manifest_b['checkpoint_hash'][:24]}...")
    lines.append(f"  n_steps:          {manifest_b['n_steps']}")
    lines.append(f"  random_seed:      {manifest_b['random_seed']}")
    lines.append(f"  env_seed:         {manifest_b['environment_seed']}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("CONCLUSION")
    if divergence["mean_state_distance"] > 0 or divergence["action_distance"] > 0 or divergence["reward_distance"] > 0:
        lines.append("  Divergence detected. The two organisms, instantiated from the")
        lines.append("  SAME genome and run with the SAME random seed, produced")
        lines.append("  DIFFERENT developmental trajectories because they developed in")
        lines.append("  DIFFERENT environments. This is Computational Developmental")
        lines.append("  Divergence.")
    else:
        lines.append("  No divergence detected within the measured dimensions. Either")
        lines.append("  the environments were too similar, the run was too short, or")
        lines.append("  the organism's policy did not differentiate between them.")
    lines.append("")
    lines.append("SCIENTIFIC STATUS")
    lines.append("  [IMPLEMENTED]    Same Genome / Different World experiment runner")
    lines.append("  [IMPLEMENTED]    DevelopmentalDivergence metrics")
    lines.append("  [IMPLEMENTED]    MindDiff between final states")
    lines.append("  [IMPLEMENTED]    ReproducibilityManifest for each organism")
    lines.append("  [IMPLEMENTED]    Deterministic replay from checkpoint")
    lines.append("  [PROPOSED]       Statistical significance testing across many seed pairs")
    lines.append("  [PROPOSED]       CounterfactualSelf / PossibleSelfSpace")
    lines.append("  [PROPOSED]       Artificial Evolution on DevelopmentalGenome")
    lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS Same Genome / Different World flagship experiment")
    parser.add_argument("--steps", type=int, default=200, help="number of developmental steps per organism (default: 200)")
    parser.add_argument("--env-a-seed", type=int, default=1, help="RNG seed for environment A (default: 1)")
    parser.add_argument("--env-b-seed", type=int, default=999, help="RNG seed for environment B (default: 999)")
    parser.add_argument("--width", type=int, default=6, help="ResourceWorld width (default: 6)")
    parser.add_argument("--height", type=int, default=6, help="ResourceWorld height (default: 6)")
    parser.add_argument("--genome-name", type=str, default="flagship", help="genome name (default: flagship)")
    parser.add_argument("--out-dir", type=str, default=None, help="directory to write artifacts to (default: ./experiment_outputs/same_genome_different_world)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else (_REPO_ROOT / "experiment_outputs" / "same_genome_different_world")

    print(f"NurosOS — Same Genome / Different World experiment")
    print(f"  steps={args.steps}  env_a_seed={args.env_a_seed}  env_b_seed={args.env_b_seed}")
    print(f"  width={args.width}  height={args.height}  genome_name={args.genome_name}")
    print(f"  out_dir={out_dir}")
    print()

    result = run_experiment(
        steps=args.steps,
        env_a_seed=args.env_a_seed,
        env_b_seed=args.env_b_seed,
        width=args.width,
        height=args.height,
        genome_name=args.genome_name,
        out_dir=out_dir,
    )

    print(result["report"])
    print()
    print(f"Artifacts written to: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
