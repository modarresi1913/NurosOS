//! Cognitive Metabolism + Epistemic Metabolism.
//!
//! The metabolism modules model computational resource expenditure. At minimum:
//!
//! - **Cognitive budgets** — finite per-tick budgets for each cognitive operation:
//!   `attention`, `inference`, `memory`, `exploration`, `uncertainty`, `risk`, `energy`.
//! - **Cost model** — per-operation costs: `perception_cost`, `prediction_cost`,
//!   `memory_cost`, `planning_cost`, `simulation_cost`, `action_cost`.
//! - **Spending tracker** — how much of each budget has been spent this tick.
//! - **Value-of-information decision rule** — "Is this information worth the
//!   cognitive cost?"
//!
//! ## Interpretation caveat
//!
//! This is a computational abstraction inspired by resource-constrained
//! organisms. It does NOT reproduce biological metabolism. It is a research
//! tool for studying how resource constraints shape developmental trajectories.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::hash;

/// The cognitive budgets for one tick.
///
/// Each budget is a non-negative number. A budget of `0.0` means the
/// corresponding operation is forbidden; a budget of `f64::INFINITY` means
/// unlimited. Sensible defaults are finite.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CognitiveBudget {
    /// Attention budget — limits perception + observation processing.
    #[serde(default = "default_attention")]
    pub attention: f64,
    /// Inference budget — limits prediction + belief update.
    #[serde(default = "default_inference")]
    pub inference: f64,
    /// Memory budget — limits memory formation + retrieval.
    #[serde(default = "default_memory")]
    pub memory: f64,
    /// Exploration budget — limits random/exploratory actions.
    #[serde(default = "default_exploration")]
    pub exploration: f64,
    /// Uncertainty budget — limits uncertainty-reduction operations.
    #[serde(default = "default_uncertainty")]
    pub uncertainty: f64,
    /// Risk budget — limits risk-taking actions.
    #[serde(default = "default_risk")]
    pub risk: f64,
    /// Energy budget — limits total energy expenditure per tick.
    #[serde(default = "default_energy")]
    pub energy: f64,
}

fn default_attention() -> f64 { 1.0 }
fn default_inference() -> f64 { 1.0 }
fn default_memory() -> f64 { 1.0 }
fn default_exploration() -> f64 { 0.5 }
fn default_uncertainty() -> f64 { 0.5 }
fn default_risk() -> f64 { 0.3 }
fn default_energy() -> f64 { 0.2 }

impl Default for CognitiveBudget {
    fn default() -> Self {
        Self {
            attention: default_attention(),
            inference: default_inference(),
            memory: default_memory(),
            exploration: default_exploration(),
            uncertainty: default_uncertainty(),
            risk: default_risk(),
            energy: default_energy(),
        }
    }
}

impl CognitiveBudget {
    /// Construct a budget with all fields set to the same value.
    pub fn uniform(value: f64) -> Self {
        Self {
            attention: value,
            inference: value,
            memory: value,
            exploration: value,
            uncertainty: value,
            risk: value,
            energy: value,
        }
    }

    /// Construct a budget with zero for all fields (forbids everything).
    pub fn zero() -> Self {
        Self::uniform(0.0)
    }

    /// Construct a budget with infinity for all fields (unlimited).
    pub fn unlimited() -> Self {
        Self::uniform(f64::INFINITY)
    }
}

/// The cost model for cognitive operations.
///
/// Each operation has a non-negative cost. When an operation is performed,
/// its cost is deducted from the corresponding budget.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CognitiveCostModel {
    #[serde(default = "default_perceive_cost")]
    pub perception: f64,
    #[serde(default = "default_predict_cost")]
    pub prediction: f64,
    #[serde(default = "default_memory_cost")]
    pub memory_formation: f64,
    #[serde(default = "default_planning_cost")]
    pub planning: f64,
    #[serde(default = "default_simulation_cost")]
    pub simulation: f64,
    #[serde(default = "default_action_cost")]
    pub action: f64,
}

fn default_perceive_cost() -> f64 { 0.05 }
fn default_predict_cost() -> f64 { 0.05 }
fn default_memory_cost() -> f64 { 0.03 }
fn default_planning_cost() -> f64 { 0.1 }
fn default_simulation_cost() -> f64 { 0.15 }
fn default_action_cost() -> f64 { 0.05 }

impl Default for CognitiveCostModel {
    fn default() -> Self {
        Self {
            perception: default_perceive_cost(),
            prediction: default_predict_cost(),
            memory_formation: default_memory_cost(),
            planning: default_planning_cost(),
            simulation: default_simulation_cost(),
            action: default_action_cost(),
        }
    }
}

/// A snapshot of how much of each budget has been spent in the current tick.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BudgetSpending {
    pub attention_spent: f64,
    pub inference_spent: f64,
    pub memory_spent: f64,
    pub exploration_spent: f64,
    pub uncertainty_spent: f64,
    pub risk_spent: f64,
    pub energy_spent: f64,
}

impl BudgetSpending {
    /// Reset all spending to zero (called at the start of each tick).
    pub fn reset(&mut self) {
        *self = Self::default();
    }
}

/// The kind of cognitive operation. Used to map operations to budgets + costs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CognitiveOperation {
    /// Perceiving / observing the environment.
    Perceive,
    /// Predicting the outcome of an action.
    Predict,
    /// Forming a new memory.
    Memorize,
    /// Planning (looking ahead).
    Plan,
    /// Simulating a counterfactual.
    Simulate,
    /// Taking an action in the environment.
    Act,
    /// Exploratory action (random).
    Explore,
    /// Uncertainty-reduction action.
    ReduceUncertainty,
    /// Risk-taking action.
    TakeRisk,
}

impl CognitiveOperation {
    /// All operations.
    pub fn all() -> &'static [CognitiveOperation] {
        &[
            CognitiveOperation::Perceive,
            CognitiveOperation::Predict,
            CognitiveOperation::Memorize,
            CognitiveOperation::Plan,
            CognitiveOperation::Simulate,
            CognitiveOperation::Act,
            CognitiveOperation::Explore,
            CognitiveOperation::ReduceUncertainty,
            CognitiveOperation::TakeRisk,
        ]
    }
}

/// The Cognitive Metabolism.
///
/// Holds the budgets, the cost model, and the current spending. Provides
/// methods to check whether an operation is affordable and to spend budget.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CognitiveMetabolism {
    pub budget: CognitiveBudget,
    pub costs: CognitiveCostModel,
    pub spending: BudgetSpending,
    /// Total spending accumulated across all ticks (for telemetry).
    #[serde(default)]
    pub total_spending: BudgetSpending,
    /// Number of operations refused due to insufficient budget.
    #[serde(default)]
    pub refusals: u64,
}

impl Default for CognitiveMetabolism {
    fn default() -> Self {
        Self::new(CognitiveBudget::default(), CognitiveCostModel::default())
    }
}

impl CognitiveMetabolism {
    /// Construct a metabolism with the given budgets and costs.
    pub fn new(budget: CognitiveBudget, costs: CognitiveCostModel) -> Self {
        Self {
            budget,
            costs,
            spending: BudgetSpending::default(),
            total_spending: BudgetSpending::default(),
            refusals: 0,
        }
    }

    /// Reset per-tick spending (call at the start of each tick).
    pub fn reset_tick(&mut self) {
        self.spending.reset();
    }

    /// Returns the cost of an operation.
    pub fn cost_of(&self, op: CognitiveOperation) -> f64 {
        match op {
            CognitiveOperation::Perceive => self.costs.perception,
            CognitiveOperation::Predict => self.costs.prediction,
            CognitiveOperation::Memorize => self.costs.memory_formation,
            CognitiveOperation::Plan => self.costs.planning,
            CognitiveOperation::Simulate => self.costs.simulation,
            CognitiveOperation::Act => self.costs.action,
            CognitiveOperation::Explore => self.costs.action + 0.02,
            CognitiveOperation::ReduceUncertainty => self.costs.prediction + 0.02,
            CognitiveOperation::TakeRisk => self.costs.action + 0.05,
        }
    }

    /// Check whether an operation is affordable under the current budgets.
    ///
    /// An operation is affordable iff, for every budget it consumes, the
    /// remaining budget is >= the operation's cost on that budget.
    pub fn can_afford(&self, op: CognitiveOperation) -> bool {
        let cost = self.cost_of(op);
        // Map operation to budgets it consumes.
        match op {
            CognitiveOperation::Perceive => {
                self.spending.attention_spent + cost <= self.budget.attention
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::Predict => {
                self.spending.inference_spent + cost <= self.budget.inference
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::Memorize => {
                self.spending.memory_spent + cost <= self.budget.memory
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::Plan => {
                self.spending.inference_spent + cost <= self.budget.inference
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::Simulate => {
                self.spending.inference_spent + cost <= self.budget.inference
                    && self.spending.memory_spent + cost <= self.budget.memory
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::Act => {
                self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::Explore => {
                self.spending.exploration_spent + cost <= self.budget.exploration
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::ReduceUncertainty => {
                self.spending.uncertainty_spent + cost <= self.budget.uncertainty
                    && self.spending.inference_spent + cost <= self.budget.inference
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
            CognitiveOperation::TakeRisk => {
                self.spending.risk_spent + cost <= self.budget.risk
                    && self.spending.energy_spent + cost <= self.budget.energy
            }
        }
    }

    /// Spend budget for an operation. Returns `true` if the operation was
    /// affordable and the budget was spent; `false` if refused (and increments
    /// the refusal counter).
    pub fn spend(&mut self, op: CognitiveOperation) -> bool {
        if !self.can_afford(op) {
            self.refusals += 1;
            return false;
        }
        let cost = self.cost_of(op);
        match op {
            CognitiveOperation::Perceive => {
                self.spending.attention_spent += cost;
                self.total_spending.attention_spent += cost;
            }
            CognitiveOperation::Predict | CognitiveOperation::Plan => {
                self.spending.inference_spent += cost;
                self.total_spending.inference_spent += cost;
            }
            CognitiveOperation::Memorize => {
                self.spending.memory_spent += cost;
                self.total_spending.memory_spent += cost;
            }
            CognitiveOperation::Simulate => {
                self.spending.inference_spent += cost;
                self.spending.memory_spent += cost;
                self.total_spending.inference_spent += cost;
                self.total_spending.memory_spent += cost;
            }
            CognitiveOperation::Act => {
                // Action only costs energy.
            }
            CognitiveOperation::Explore => {
                self.spending.exploration_spent += cost;
                self.total_spending.exploration_spent += cost;
            }
            CognitiveOperation::ReduceUncertainty => {
                self.spending.uncertainty_spent += cost;
                self.spending.inference_spent += cost;
                self.total_spending.uncertainty_spent += cost;
                self.total_spending.inference_spent += cost;
            }
            CognitiveOperation::TakeRisk => {
                self.spending.risk_spent += cost;
                self.total_spending.risk_spent += cost;
            }
        }
        // Energy is consumed by all operations.
        self.spending.energy_spent += cost;
        self.total_spending.energy_spent += cost;
        true
    }

    /// Value-of-information decision rule.
    ///
    /// Estimates whether performing an operation is "worth it" given the
    /// expected information gain and the cognitive cost.
    ///
    /// Returns `true` iff the expected information gain exceeds the cost.
    /// `expected_info_gain` is in [0, 1] (a heuristic estimate); `cost` is
    /// the operation's cost in the same units.
    pub fn is_worth_it(&self, expected_info_gain: f64, op: CognitiveOperation) -> bool {
        let cost = self.cost_of(op);
        expected_info_gain >= cost
    }

    /// Remaining fraction of each budget (in [0, 1]).
    pub fn remaining_fractions(&self) -> BTreeMap<String, f64> {
        let mut m = BTreeMap::new();
        m.insert("attention".to_string(), ((self.budget.attention - self.spending.attention_spent) / self.budget.attention).max(0.0));
        m.insert("inference".to_string(), ((self.budget.inference - self.spending.inference_spent) / self.budget.inference).max(0.0));
        m.insert("memory".to_string(), ((self.budget.memory - self.spending.memory_spent) / self.budget.memory).max(0.0));
        m.insert("exploration".to_string(), ((self.budget.exploration - self.spending.exploration_spent) / self.budget.exploration).max(0.0));
        m.insert("uncertainty".to_string(), ((self.budget.uncertainty - self.spending.uncertainty_spent) / self.budget.uncertainty).max(0.0));
        m.insert("risk".to_string(), ((self.budget.risk - self.spending.risk_spent) / self.budget.risk).max(0.0));
        m.insert("energy".to_string(), ((self.budget.energy - self.spending.energy_spent) / self.budget.energy).max(0.0));
        m
    }

    /// Canonical hash of the metabolism (for provenance).
    pub fn hash(&self) -> String {
        hash::hash(self)
    }

    /// Render a human-readable summary.
    pub fn render(&self) -> String {
        let mut s = String::new();
        s.push_str("=== Cognitive Metabolism ===\n");
        s.push_str("Budgets (per tick):\n");
        s.push_str(&format!("  attention:   {:.4}\n", self.budget.attention));
        s.push_str(&format!("  inference:   {:.4}\n", self.budget.inference));
        s.push_str(&format!("  memory:      {:.4}\n", self.budget.memory));
        s.push_str(&format!("  exploration: {:.4}\n", self.budget.exploration));
        s.push_str(&format!("  uncertainty: {:.4}\n", self.budget.uncertainty));
        s.push_str(&format!("  risk:        {:.4}\n", self.budget.risk));
        s.push_str(&format!("  energy:      {:.4}\n", self.budget.energy));
        s.push_str("Spending (this tick):\n");
        s.push_str(&format!("  attention:   {:.4}\n", self.spending.attention_spent));
        s.push_str(&format!("  inference:   {:.4}\n", self.spending.inference_spent));
        s.push_str(&format!("  memory:      {:.4}\n", self.spending.memory_spent));
        s.push_str(&format!("  exploration: {:.4}\n", self.spending.exploration_spent));
        s.push_str(&format!("  uncertainty: {:.4}\n", self.spending.uncertainty_spent));
        s.push_str(&format!("  risk:        {:.4}\n", self.spending.risk_spent));
        s.push_str(&format!("  energy:      {:.4}\n", self.spending.energy_spent));
        s.push_str(&format!("Refusals (insufficient budget): {}\n", self.refusals));
        s
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_budget_is_finite() {
        let b = CognitiveBudget::default();
        assert!(b.attention.is_finite());
        assert!(b.inference.is_finite());
        assert!(b.energy.is_finite());
    }

    #[test]
    fn unlimited_budget_allows_anything() {
        let m = CognitiveMetabolism::new(CognitiveBudget::unlimited(), CognitiveCostModel::default());
        for op in CognitiveOperation::all() {
            assert!(m.can_afford(*op), "unlimited budget should afford {:?}", op);
        }
    }

    #[test]
    fn zero_budget_forbids_everything() {
        let m = CognitiveMetabolism::new(CognitiveBudget::zero(), CognitiveCostModel::default());
        for op in CognitiveOperation::all() {
            assert!(!m.can_afford(*op), "zero budget should not afford {:?}", op);
        }
    }

    #[test]
    fn spend_increments_spending() {
        let mut m = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        let cost = m.cost_of(CognitiveOperation::Perceive);
        let spent = m.spend(CognitiveOperation::Perceive);
        assert!(spent);
        assert!((m.spending.attention_spent - cost).abs() < 1e-9);
        assert!((m.spending.energy_spent - cost).abs() < 1e-9);
    }

    #[test]
    fn refusal_increments_counter() {
        let mut m = CognitiveMetabolism::new(CognitiveBudget::zero(), CognitiveCostModel::default());
        let spent = m.spend(CognitiveOperation::Perceive);
        assert!(!spent);
        assert_eq!(m.refusals, 1);
    }

    #[test]
    fn reset_tick_clears_spending() {
        let mut m = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        m.spend(CognitiveOperation::Perceive);
        assert!(m.spending.attention_spent > 0.0);
        m.reset_tick();
        assert_eq!(m.spending.attention_spent, 0.0);
    }

    #[test]
    fn is_worth_it_returns_true_when_gain_exceeds_cost() {
        let m = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        let cost = m.cost_of(CognitiveOperation::Perceive);
        assert!(m.is_worth_it(cost + 0.01, CognitiveOperation::Perceive));
        assert!(!m.is_worth_it(cost - 0.01, CognitiveOperation::Perceive));
    }

    #[test]
    fn remaining_fractions_decrease_with_spending() {
        let mut m = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        let before = m.remaining_fractions();
        m.spend(CognitiveOperation::Perceive);
        let after = m.remaining_fractions();
        assert!(after["attention"] <= before["attention"]);
        assert!(after["energy"] <= before["energy"]);
    }

    #[test]
    fn render_contains_all_budgets() {
        let m = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        let s = m.render();
        assert!(s.contains("attention"));
        assert!(s.contains("inference"));
        assert!(s.contains("memory"));
        assert!(s.contains("energy"));
        assert!(s.contains("Refusals"));
    }

    #[test]
    fn hash_is_deterministic() {
        let m1 = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        let m2 = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        assert_eq!(m1.hash(), m2.hash());
    }

    #[test]
    fn total_spending_accumulates_across_ticks() {
        let mut m = CognitiveMetabolism::new(CognitiveBudget::default(), CognitiveCostModel::default());
        m.spend(CognitiveOperation::Perceive);
        m.reset_tick();
        m.spend(CognitiveOperation::Perceive);
        // total_spending should have 2x the cost; spending should have 1x.
        assert!(m.total_spending.attention_spent > m.spending.attention_spent);
    }
}
