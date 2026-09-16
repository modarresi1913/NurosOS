"""
Mind Observatory CLI — inspect NurosOS developmental experiment artifacts.

Usage
-----
    python experiments/observatory.py <experiment_dir> <command> [options]

Commands
--------
    summary                  — one-screen overview of the experiment
    timeline <organism>      — step-by-step timeline replay
    mind-diff                — mind diff between the two organisms
    causal-trace             — causal backbone (trajectory chain)
    env-events <organism>    — environment-side events for an organism
    checkpoints              — checkpoints overview
    manifests                — reproducibility manifests
    divergence               — developmental divergence summary
    plot-dev-traj <organism> — PNG: developmental trajectory
    plot-pred-err <organism> — PNG: prediction error + reward
    plot-memory <organism>   — PNG: memory changes + cumulative reward
    plot-state-trans <org>   — PNG: developmental stage transitions
    plot-resource <organism> — PNG: resource consumption (energy + plasticity)
    plot-mind-diff           — PNG: mind diff visualization
    plot-divergence          — PNG: per-step state distance
    plot-divergence-cmp      — PNG: cumulative reward A vs B
    render-all [out_dir]     — generate all text + PNG reports

Organism IDs: organism_a, organism_b (or just "a" / "b").

Example
-------
    python experiments/observatory.py experiment_outputs/same_genome_different_world summary
    python experiments/observatory.py experiment_outputs/same_genome_different_world timeline a --end 30
    python experiments/observatory.py experiment_outputs/same_genome_different_world render-all observatory_outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make nuros importable when running from the repo root.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nuros.observatory import Observatory


def _normalize_organism(s: str) -> str:
    s = s.strip().lower()
    if s in ("a", "organism_a"):
        return "organism_a"
    if s in ("b", "organism_b"):
        return "organism_b"
    return s


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mind Observatory — inspect NurosOS developmental experiment artifacts",
        usage="observatory.py <experiment_dir> <command> [options]",
    )
    parser.add_argument("experiment_dir", help="path to the experiment output directory")
    parser.add_argument("command", help="what to render (see --help for the list)")
    parser.add_argument("organism", nargs="?", default=None, help="organism id (a/b/organism_a/organism_b)")
    parser.add_argument("--start", type=int, default=0, help="timeline start step (default: 0)")
    parser.add_argument("--end", type=int, default=None, help="timeline end step (default: all)")
    parser.add_argument("--out", type=str, default=None, help="output file path (for plot commands)")
    parser.add_argument("--show-obs", action="store_true", help="show observation payload in timeline")
    parser.add_argument("--max-events", type=int, default=30, help="max events for causal-trace / env-events")
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    if not exp_dir.exists():
        print(f"[error] experiment dir not found: {exp_dir}", file=sys.stderr)
        return 2

    obs = Observatory.from_experiment_dir(exp_dir)
    cmd = args.command.lower()

    if cmd == "summary":
        print("=== Experiment Summary ===")
        print(f"  experiment dir: {exp_dir}")
        print(f"  organism ids:   {obs.art.organism_ids}")
        s = obs.art.summary
        if s:
            print(f"  genome_name:    {s.get('genome_name', '')}")
            print(f"  genome_hash:    {s.get('genome_hash', '')[:24]}...")
            print(f"  n_steps:        {s.get('n_steps', 0)}")
            print(f"  env_a_seed:     {s.get('env_a_seed', 0)}")
            print(f"  env_b_seed:     {s.get('env_b_seed', 0)}")
            print(f"  env_a_hash:     {s.get('env_a_hash', '')[:24]}...")
            print(f"  env_b_hash:     {s.get('env_b_hash', '')[:24]}...")
            print(f"  final_stage_a:  {s.get('final_stage_a', '')}")
            print(f"  final_stage_b:  {s.get('final_stage_b', '')}")
            print(f"  total_reward_a: {s.get('total_reward_a', 0.0):.4f}")
            print(f"  total_reward_b: {s.get('total_reward_b', 0.0):.4f}")
            div = s.get("divergence", {})
            print(f"  divergence:")
            print(f"    mean_state_distance:    {div.get('mean_state_distance', 0.0):.4f}")
            print(f"    final_state_distance:   {div.get('final_state_distance', 0.0):.4f}")
            print(f"    reward_distance:        {div.get('reward_distance', 0.0):.4f}")
            print(f"    prediction_error_dist:  {div.get('prediction_error_distance', 0.0):.4f}")
            print(f"    action_distance:        {div.get('action_distance', 0.0):.0f}")
            print(f"    stage_divergence:       {div.get('stage_divergence', False)}")
        return 0

    if cmd == "timeline":
        if not args.organism:
            print("[error] timeline requires <organism> (a/b)", file=sys.stderr)
            return 2
        org = _normalize_organism(args.organism)
        print(obs.render_timeline_replay(org, start=args.start, end=args.end, show_observation=args.show_obs))
        return 0

    if cmd == "mind-diff":
        print(obs.render_mind_diff())
        return 0

    if cmd == "causal-trace":
        print(obs.render_causal_trace(max_events=args.max_events))
        return 0

    if cmd == "env-events":
        if not args.organism:
            print("[error] env-events requires <organism> (a/b)", file=sys.stderr)
            return 2
        org = _normalize_organism(args.organism)
        print(obs.render_environment_events(org, max_events=args.max_events))
        return 0

    if cmd == "checkpoints":
        print(obs.render_checkpoints())
        return 0

    if cmd == "manifests":
        print(obs.render_manifests())
        return 0

    if cmd == "divergence":
        print(obs.render_divergence())
        return 0

    if cmd.startswith("plot-"):
        out = Path(args.out) if args.out else Path(f"{cmd.replace('-', '_')}.png")
        if cmd == "plot-dev-traj":
            org = _normalize_organism(args.organism or "a")
            p = obs.plot_developmental_trajectory(org, out)
        elif cmd == "plot-pred-err":
            org = _normalize_organism(args.organism or "a")
            p = obs.plot_prediction_error(org, out)
        elif cmd == "plot-memory":
            org = _normalize_organism(args.organism or "a")
            p = obs.plot_memory_changes(org, out)
        elif cmd == "plot-state-trans":
            org = _normalize_organism(args.organism or "a")
            p = obs.plot_state_transitions(org, out)
        elif cmd == "plot-resource":
            org = _normalize_organism(args.organism or "a")
            p = obs.plot_resource_consumption(org, out)
        elif cmd == "plot-mind-diff":
            p = obs.plot_mind_diff(out)
        elif cmd == "plot-divergence":
            p = obs.plot_divergence(out)
        elif cmd == "plot-divergence-cmp":
            p = obs.plot_divergence_comparison(out)
        else:
            print(f"[error] unknown plot command: {cmd}", file=sys.stderr)
            return 2
        print(f"[ok] wrote {p}")
        return 0

    if cmd == "render-all":
        out_dir = Path(args.out) if args.out else Path("observatory_outputs")
        results = obs.render_all(out_dir)
        print(f"[ok] rendered {len(results)} artifacts to {out_dir}")
        for name, path in sorted(results.items()):
            print(f"  {name:<30} {path}")
        return 0

    print(f"[error] unknown command: {cmd}", file=sys.stderr)
    print("Available commands: summary, timeline, mind-diff, causal-trace, env-events,")
    print("                    checkpoints, manifests, divergence,")
    print("                    plot-dev-traj, plot-pred-err, plot-memory, plot-state-trans,")
    print("                    plot-resource, plot-mind-diff, plot-divergence,")
    print("                    plot-divergence-cmp, render-all")
    return 2


if __name__ == "__main__":
    sys.exit(main())
