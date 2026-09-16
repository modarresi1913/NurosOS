"""
Integration tests for the Cognitive Metabolism module (Phase 12).
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


# ============================================================================
# Value-of-Information tests
# ============================================================================

class TestValueOfInformation:
    def test_returns_operation_cost_gain_and_worth_it(self):
        result = json.loads(_dev.evaluate_value_of_information("perceive", 0.1))
        assert "operation" in result
        assert "cost" in result
        assert "expected_info_gain" in result
        assert "worth_it" in result

    def test_high_gain_is_worth_it(self):
        result = json.loads(_dev.evaluate_value_of_information("perceive", 1.0))
        assert result["worth_it"] is True

    def test_low_gain_is_not_worth_it(self):
        result = json.loads(_dev.evaluate_value_of_information("perceive", 0.001))
        assert result["worth_it"] is False

    def test_cost_is_positive(self):
        for op in ["perceive", "predict", "memorize", "plan", "simulate", "act"]:
            result = json.loads(_dev.evaluate_value_of_information(op, 0.1))
            assert result["cost"] > 0

    def test_simulate_costs_more_than_perceive(self):
        sim = json.loads(_dev.evaluate_value_of_information("simulate", 0.1))
        per = json.loads(_dev.evaluate_value_of_information("perceive", 0.1))
        assert sim["cost"] > per["cost"]

    def test_unknown_operation_raises(self):
        with pytest.raises(Exception):
            _dev.evaluate_value_of_information("unknown_op", 0.1)


# ============================================================================
# Metabolism sweep tests
# ============================================================================

class TestMetabolismSweep:
    def test_returns_results_for_each_budget(self):
        result = json.loads(_dev.run_metabolism_sweep([0.05, 0.2, 1.0], n_steps=20))
        assert "results" in result
        assert len(result["results"]) == 3

    def test_each_result_has_expected_fields(self):
        result = json.loads(_dev.run_metabolism_sweep([0.1, 0.5], n_steps=20))
        for r in result["results"]:
            assert "energy_budget" in r
            assert "total_reward" in r
            assert "mean_reward" in r
            assert "refusals" in r
            assert "final_state_hash" in r

    def test_tighter_budget_has_more_refusals(self):
        result = json.loads(_dev.run_metabolism_sweep([0.05, 1.0], n_steps=30))
        tight = next(r for r in result["results"] if r["energy_budget"] == 0.05)
        loose = next(r for r in result["results"] if r["energy_budget"] == 1.0)
        assert tight["refusals"] >= loose["refusals"]

    def test_empty_budgets_returns_empty_results(self):
        result = json.loads(_dev.run_metabolism_sweep([], n_steps=10))
        assert result["results"] == []

    def test_has_genome_hash(self):
        result = json.loads(_dev.run_metabolism_sweep([0.1], n_steps=10))
        assert "genome_hash" in result
        assert len(result["genome_hash"]) == 64


# ============================================================================
# Metabolism demo integration test
# ============================================================================

class TestMetabolismDemo:
    def test_demo_runs_end_to_end(self, tmp_path):
        sys.path.insert(0, str(_REPO_ROOT / "experiments"))
        try:
            from metabolism_demo import run_metabolism_demo
        finally:
            sys.path.pop(0)
        result = run_metabolism_demo(
            steps=30,
            budgets=[0.05, 0.2, 1.0],
            out_dir=tmp_path,
        )
        assert result["experiment"] == "metabolism_demo"
        assert "sweep_results" in result
        assert len(result["sweep_results"]) == 3
        assert "value_of_information" in result
        assert len(result["value_of_information"]) > 0
        # Verify artifact was written.
        assert (tmp_path / "metabolism_result.json").exists()
