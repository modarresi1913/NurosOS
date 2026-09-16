"""
Integration tests for the Artificial Aging module (Phase 13).
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

RAPID_AGING = {
    "memory_degradation_rate": 0.01,
    "memory_degradation_onset": 10,
    "plasticity_decay_rate": 0.005,
    "plasticity_decay_onset": 10,
    "plasticity_floor": 0.01,
    "cognitive_load_increase": 0.005,
    "energy_efficiency_decay": 0.005,
    "max_cognitive_load": 0.9,
    "stability_improvement_rate": 0.005,
    "max_stability": 0.99,
    "prediction_accuracy_improvement": 0.002,
    "self_model_consolidation_rate": 0.005,
    "max_self_model_stability": 0.95,
}


class TestAgingComparison:
    def test_returns_no_aging_and_with_aging(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=50))
        assert "no_aging" in result
        assert "with_aging" in result
        assert "deltas" in result

    def test_has_expected_fields(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=50))
        for org_key in ["no_aging", "with_aging"]:
            org = result[org_key]
            for field in ["plasticity", "stability", "energy_state", "cognitive_load", "memory_capacity", "prediction_accuracy", "self_model_stability", "state_hash"]:
                assert field in org, f"missing {field} in {org_key}"

    def test_aging_reduces_plasticity(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=80))
        assert result["deltas"]["plasticity"] < 0

    def test_aging_increases_self_model_stability(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=80))
        assert result["deltas"]["self_model_stability"] > 0

    def test_aging_reduces_memory_capacity(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=80))
        assert result["deltas"]["memory_capacity"] < 0

    def test_state_hashes_differ(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=50))
        assert result["no_aging"]["state_hash"] != result["with_aging"]["state_hash"]

    def test_has_genome_hash_and_model_hash(self):
        result = json.loads(_dev.run_aging_comparison(json.dumps(RAPID_AGING), n_steps=30))
        assert "genome_hash" in result
        assert "aging_model_hash" in result
        assert len(result["genome_hash"]) == 64

    def test_empty_model_uses_defaults(self):
        result = json.loads(_dev.run_aging_comparison("{}", n_steps=30))
        assert "no_aging" in result
        assert "with_aging" in result

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            _dev.run_aging_comparison("not json", n_steps=30)


class TestAgingDemo:
    def test_demo_runs_end_to_end(self, tmp_path):
        sys.path.insert(0, str(_REPO_ROOT / "experiments"))
        try:
            from aging_demo import run_aging_demo
        finally:
            sys.path.pop(0)
        result = run_aging_demo(steps=50, model_name="rapid", out_dir=tmp_path)
        assert "no_aging" in result
        assert "with_aging" in result
        assert (tmp_path / "aging_result.json").exists()

    def test_demo_rejects_unknown_model(self):
        sys.path.insert(0, str(_REPO_ROOT / "experiments"))
        try:
            from aging_demo import run_aging_demo
        finally:
            sys.path.pop(0)
        with pytest.raises(ValueError):
            run_aging_demo(steps=20, model_name="unknown")
