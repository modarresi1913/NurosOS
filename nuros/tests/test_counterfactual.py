"""
Integration tests for the CounterfactualSelf + PossibleSelfSpace module (Phase 11).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _dev_available() -> bool:
    try:
        from nuros import _dev  # noqa: F401
        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(
    not _dev_available(),
    reason="nuros._dev Rust extension is not installed",
)

from nuros import _dev  # noqa: E402


def _make_checkpoint(steps: int = 20, seed: int = 1) -> tuple[str, dict]:
    """Run an organism for `steps` ticks and return (checkpoint_json, checkpoint_dict)."""
    g = _dev.DevelopmentalGenome("cf_test")
    org = _dev.MinimumOrganism(g)
    org.initialize()
    org.begin_development()
    env = _dev.ResourceWorld(6, 6, seed)
    env.reset()
    for _ in range(steps):
        org.tick_resource(env)
    ck_json = org.checkpoint_resource(env, seed, 0, "midpoint")
    return ck_json, json.loads(ck_json)


def _make_actual_trajectory(checkpoint: dict, n_steps: int = 20, seed: int = 1) -> str:
    """Build a minimal actual trajectory JSON for counterfactual comparison.

    The trajectory must have at least checkpoint.step + n_steps points so that
    compare_to_actual can slice points[checkpoint.step .. checkpoint.step + n_steps].
    """
    ckpt_dev = checkpoint["organism_state"]["developmental"]
    ckpt_step = checkpoint["step"]
    total_needed = ckpt_step + n_steps
    points = []
    for i in range(total_needed):
        points.append({
            "step": i + 1,
            "action": "idle",
            "observation": {},
            "reward": -0.01,
            "prediction_error": 0.01,
            "predicted_reward": 0.0,
            "developmental_state": ckpt_dev,
            "memory_size": i + 1,
            "state_hash": f"hash{i}",
        })
    return json.dumps({
        "organism_id": "actual",
        "genome_hash": checkpoint["genome_hash"],
        "environment_hash": checkpoint["environment_hash"],
        "environment_seed": seed,
        "points": points,
        "events": [],
    })


# ============================================================================
# CounterfactualSelf tests
# ============================================================================

class TestCounterfactualEnvironment:
    def test_returns_counterfactual_trajectory(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result_json = _dev.run_counterfactual_environment(ck_json, actual, 999, 10, 6, 6)
        result = json.loads(result_json)
        assert "counterfactual" in result
        assert "divergence_from_actual" in result

    def test_counterfactual_has_correct_epistemic_labels(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result = json.loads(_dev.run_counterfactual_environment(ck_json, actual, 999, 10, 6, 6))
        labels = result["counterfactual"]["epistemic_labels"]
        assert "SIMULATED" in labels
        assert "COUNTERFACTUAL" in labels

    def test_counterfactual_never_executed_in_real_env(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result = json.loads(_dev.run_counterfactual_environment(ck_json, actual, 999, 10, 6, 6))
        assert result["counterfactual"]["executed_in_real_environment"] is False

    def test_counterfactual_has_correct_change_description(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result = json.loads(_dev.run_counterfactual_environment(ck_json, actual, 999, 10, 6, 6))
        change = result["counterfactual"]["counterfactual_change"]
        assert "environment" in change
        assert "999" in change

    def test_counterfactual_trajectory_has_correct_length(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result = json.loads(_dev.run_counterfactual_environment(ck_json, actual, 999, 15, 6, 6))
        points = result["counterfactual"]["trajectory"]["points"]
        assert len(points) == 15

    def test_divergence_has_correct_n_steps(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result = json.loads(_dev.run_counterfactual_environment(ck_json, actual, 999, 10, 6, 6))
        assert result["divergence_from_actual"]["n_steps"] == 10

    def test_divergence_metrics_are_non_negative(self):
        ck_json, ck = _make_checkpoint(steps=20, seed=1)
        actual = _make_actual_trajectory(ck, n_steps=20, seed=1)
        result = json.loads(_dev.run_counterfactual_environment(ck_json, actual, 999, 10, 6, 6))
        d = result["divergence_from_actual"]
        assert d["reward_distance"] >= 0
        assert d["prediction_error_distance"] >= 0
        assert d["action_distance"] >= 0
        assert d["mean_state_distance"] >= 0

    def test_invalid_checkpoint_json_raises(self):
        with pytest.raises(Exception):
            _dev.run_counterfactual_environment("not json", "[]", 999, 10, 6, 6)


# ============================================================================
# PossibleSelfSpace tests
# ============================================================================

class TestPossibleSelfSpace:
    def test_returns_space_with_futures(self):
        ck_json, _ = _make_checkpoint(steps=20, seed=1)
        result = json.loads(_dev.run_possible_self_space(ck_json, [100, 200, 300], 10, 6, 6))
        assert "space" in result
        assert "coverage" in result
        assert "distances_from_current" in result
        assert len(result["space"]["possible_futures"]) == 3

    def test_all_futures_have_counterfactual_labels(self):
        ck_json, _ = _make_checkpoint(steps=20, seed=1)
        result = json.loads(_dev.run_possible_self_space(ck_json, [100, 200], 10, 6, 6))
        for f in result["space"]["possible_futures"]:
            assert "SIMULATED" in f["epistemic_labels"]
            assert "COUNTERFACTUAL" in f["epistemic_labels"]
            assert f["executed_in_real_environment"] is False

    def test_coverage_is_zero_with_one_future(self):
        ck_json, _ = _make_checkpoint(steps=20, seed=1)
        result = json.loads(_dev.run_possible_self_space(ck_json, [100], 10, 6, 6))
        assert result["coverage"] == 0.0

    def test_coverage_is_non_negative_with_multiple_futures(self):
        ck_json, _ = _make_checkpoint(steps=20, seed=1)
        result = json.loads(_dev.run_possible_self_space(ck_json, [100, 200, 300], 10, 6, 6))
        assert result["coverage"] >= 0.0

    def test_distances_from_current_has_one_entry_per_future(self):
        ck_json, _ = _make_checkpoint(steps=20, seed=1)
        result = json.loads(_dev.run_possible_self_space(ck_json, [100, 200, 300], 10, 6, 6))
        dists = result["distances_from_current"]
        assert len(dists) == 3
        for entry in dists:
            assert len(entry) == 2  # [index, distance]
            assert entry[1] >= 0.0

    def test_empty_alt_seeds_produces_empty_space(self):
        ck_json, _ = _make_checkpoint(steps=20, seed=1)
        result = json.loads(_dev.run_possible_self_space(ck_json, [], 10, 6, 6))
        assert len(result["space"]["possible_futures"]) == 0
        assert result["coverage"] == 0.0


# ============================================================================
# Counterfactual demo integration test
# ============================================================================

class TestCounterfactualDemo:
    def test_demo_runs_end_to_end(self, tmp_path):
        sys.path.insert(0, str(_REPO_ROOT / "experiments"))
        try:
            from counterfactual_demo import run_counterfactual_demo
        finally:
            sys.path.pop(0)
        result = run_counterfactual_demo(
            steps=40,
            env_seed=1,
            alt_seed=999,
            n_futures=2,
            out_dir=tmp_path,
        )
        assert result["experiment"] == "counterfactual_demo"
        assert "counterfactual" in result
        assert "divergence_from_actual" in result
        assert "possible_self_space" in result
        assert len(result["possible_self_space"]["possible_futures"]) == 2
        # Verify artifacts were written.
        assert (tmp_path / "counterfactual_result.json").exists()
        assert (tmp_path / "checkpoint.json").exists()
