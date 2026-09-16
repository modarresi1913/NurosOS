"""
Counterfactual Self demo — "What if the environment had been different?"

This experiment demonstrates the CounterfactualSelf module (Phase 11):
  1. Run an organism in environment E1 for N steps.
  2. Take a checkpoint at the midpoint.
  3. Continue developing in E1 (the "actual" trajectory).
  4. Use CounterfactualSelf to ask: "What if the environment had been E2?"
  5. Replay from the checkpoint in E2 (the counterfactual trajectory).
  6. Compare the counterfactual to the actual (Computational Developmental Divergence).
  7. Build a PossibleSelfSpace with multiple alternative futures.

All counterfactual trajectories are marked SIMULATED + COUNTERFACTUAL and are
NEVER executed in the real environment.

Usage:
    python experiments/counterfactual_demo.py --steps 60 --alt-seed 999 --n-futures 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nuros import _dev


def run_counterfactual_demo(
    steps: int = 60,
    env_seed: int = 1,
    alt_seed: int = 999,
    width: int = 6,
    height: int = 6,
    genome_name: str = "counterfactual_demo",
    n_futures: int = 3,
    out_dir: Path | None = None,
) -> dict:
    """Run the counterfactual demo."""

    # 1. Run an organism in E1, take a midpoint checkpoint, continue.
    g = _dev.DevelopmentalGenome(genome_name)
    org = _dev.MinimumOrganism(g)
    org.initialize()
    org.begin_development()
    env = _dev.ResourceWorld(width, height, env_seed)
    env.reset()

    half = steps // 2
    # Record ALL trajectory points (before AND after the checkpoint) so that
    # compare_to_actual can slice from checkpoint.step onward.
    all_points = []
    for i in range(steps):
        tick = org.tick_resource(env)
        if i + 1 == half:
            checkpoint_json = org.checkpoint_resource(env, env_seed, 0, "midpoint")
            checkpoint = json.loads(checkpoint_json)
            print(f"[1] Checkpoint taken at step {org.step} (hash={checkpoint['state_hash'][:12]}...)")
        # Record every tick (we'll build the trajectory JSON after the loop).
        all_points.append(tick)

    # Build the actual trajectory JSON from all points. We use the checkpoint's
    # developmental_state as an approximation for each point's developmental_state
    # (the Rust side only needs the points for divergence comparison).
    ckpt_dev_state = checkpoint["organism_state"]["developmental"]
    actual_points = []
    for p in all_points:
        actual_points.append({
            "step": p["step"],
            "action": p["action"],
            "observation": p["observation"],
            "reward": p["reward"],
            "prediction_error": p["prediction_error"],
            "predicted_reward": p["predicted_reward"],
            "developmental_state": ckpt_dev_state,  # approximation
            "memory_size": p["memory_size"],
            "state_hash": p["state_hash"],
        })
    actual_traj = {
        "organism_id": "actual",
        "genome_hash": checkpoint["genome_hash"],
        "environment_hash": checkpoint["environment_hash"],
        "environment_seed": env_seed,
        "points": actual_points,
        "events": [],
    }
    print(f"[2] Actual trajectory: {len(actual_points)} total steps (checkpoint at step {half})")

    # 2. Counterfactual: what if env_seed were alt_seed?
    cf_json = _dev.run_counterfactual_environment(
        checkpoint_json, json.dumps(actual_traj), alt_seed, half, width, height
    )
    cf = json.loads(cf_json)
    print(f"[3] Counterfactual trajectory: {len(cf['counterfactual']['trajectory']['points'])} steps")
    print(f"    epistemic_labels: {cf['counterfactual']['epistemic_labels']}")
    print(f"    executed_in_real_env: {cf['counterfactual']['executed_in_real_environment']}")
    print(f"    divergence_from_actual:")
    d = cf["divergence_from_actual"]
    print(f"      n_steps:             {d['n_steps']}")
    print(f"      reward_distance:     {d['reward_distance']:.4f}")
    print(f"      pe_distance:         {d['prediction_error_distance']:.4f}")
    print(f"      action_distance:     {d['action_distance']:.0f} / {d['n_steps']}")
    print(f"      mean_state_distance: {d['mean_state_distance']:.4f}")

    # 3. PossibleSelfSpace with n_futures alternative environments.
    alt_seeds = [100 * (i + 1) for i in range(n_futures)]
    pss_json = _dev.run_possible_self_space(
        checkpoint_json, alt_seeds, half, width, height
    )
    pss = json.loads(pss_json)
    print(f"\n[4] Possible-Self Space: {len(pss['space']['possible_futures'])} futures")
    print(f"    coverage (mean pairwise L1): {pss['coverage']:.4f}")
    for i, f in enumerate(pss["space"]["possible_futures"]):
        s = f["trajectory"]["points"][-1]["developmental_state"] if f["trajectory"]["points"] else {}
        print(f"    future {i}: {f['counterfactual_change']}")
        print(f"             final_stage={s.get('developmental_stage', '?')}, age={s.get('age', '?')}")
    print(f"\n[5] Interpretation caveat: This is an experimental abstraction.")
    print(f"    It does NOT represent phenomenological identity.")

    result = {
        "experiment": "counterfactual_demo",
        "genome_name": genome_name,
        "genome_hash": checkpoint["genome_hash"],
        "n_steps": steps,
        "env_seed": env_seed,
        "alt_seed": alt_seed,
        "checkpoint_step": half,
        "checkpoint_hash": checkpoint["state_hash"],
        "counterfactual": cf["counterfactual"],
        "divergence_from_actual": d,
        "possible_self_space": pss["space"],
        "coverage": pss["coverage"],
        "distances_from_current": pss["distances_from_current"],
        "interpretation": (
            "Counterfactual trajectories are marked SIMULATED + COUNTERFACTUAL "
            "and are NEVER executed in the real environment. The divergence "
            "measured is an observable computational fact, NOT evidence of "
            "consciousness or phenomenological identity."
        ),
    }

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "counterfactual_result.json").write_text(
            json.dumps(result, indent=2, default=str), encoding="utf-8"
        )
        (out_dir / "checkpoint.json").write_text(checkpoint_json, encoding="utf-8")
        print(f"\nArtifacts written to: {out_dir}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="NurosOS Counterfactual Self demo")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--env-seed", type=int, default=1)
    parser.add_argument("--alt-seed", type=int, default=999)
    parser.add_argument("--width", type=int, default=6)
    parser.add_argument("--height", type=int, default=6)
    parser.add_argument("--genome-name", type=str, default="counterfactual_demo")
    parser.add_argument("--n-futures", type=int, default=3)
    parser.add_argument("--out-dir", type=str, default=None)
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else (_REPO_ROOT / "experiment_outputs" / "counterfactual_demo")
    run_counterfactual_demo(
        steps=args.steps,
        env_seed=args.env_seed,
        alt_seed=args.alt_seed,
        width=args.width,
        height=args.height,
        genome_name=args.genome_name,
        n_futures=args.n_futures,
        out_dir=out_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
