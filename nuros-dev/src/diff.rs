//! Mind Diff.
//!
//! Inspired conceptually by version-control diffs, but designed for
//! cognitive state. A `MindDiff` describes the structured difference
//! between two organism states — what changed in memory, in the
//! self-model, in capabilities, in values, in prediction, in behavior,
//! and in the developmental state.
//!
//! The output is machine-readable JSON. A human-readable rendering is
//! provided by [`MindDiff::render`].

use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

use crate::organism::OrganismState;
use crate::state::DevelopmentalState;

/// A structured diff between two organism states.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MindDiff {
    /// Hash of state A.
    pub state_a_hash: String,
    /// Hash of state B.
    pub state_b_hash: String,
    /// Step difference (B.step - A.step).
    pub step_delta: i64,
    /// Changes in memory.
    pub memory_changes: MemoryDiff,
    /// Changes in the self-model.
    pub self_model_changes: SelfModelDiff,
    /// Changes in action preferences (the "values" of the MVP organism).
    pub value_changes: ValueDiff,
    /// Changes in capability proficiencies.
    pub capability_changes: CapabilityDiff,
    /// Changes in prediction metrics.
    pub prediction_changes: PredictionDiff,
    /// Changes in recent behavior (action distribution).
    pub behavioral_changes: BehavioralDiff,
    /// Changes in the developmental state vector.
    pub developmental_changes: DevelopmentalStateDiff,
    /// True if the two states are byte-for-byte identical.
    pub identical: bool,
}

/// Changes in memory between two states.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MemoryDiff {
    /// Number of memories added (present in B but not in A).
    pub added: usize,
    /// Number of memories removed (present in A but not in B).
    pub removed: usize,
    /// Number of memories whose importance changed.
    pub importance_changed: usize,
    /// Total memory size in A.
    pub size_a: usize,
    /// Total memory size in B.
    pub size_b: usize,
}

/// Changes in the self-model.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SelfModelDiff {
    /// Change in expected reward.
    pub expected_reward_delta: f64,
    /// Change in expected prediction error.
    pub expected_prediction_error_delta: f64,
    /// Number of self-model updates between A and B.
    pub update_count_delta: i64,
}

/// Changes in action preferences (the MVP organism's "values").
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ValueDiff {
    /// Per-action change in preference score.
    pub per_action: std::collections::BTreeMap<String, f64>,
    /// L1 norm of the change vector.
    pub total_l1: f64,
}

/// Changes in capability proficiencies.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CapabilityDiff {
    /// Per-capability change in proficiency.
    pub per_capability: std::collections::BTreeMap<String, f64>,
    /// Capabilities that appeared in B but not in A.
    pub gained: Vec<String>,
    /// Capabilities that were in A but not in B.
    pub lost: Vec<String>,
}

/// Changes in prediction metrics.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PredictionDiff {
    /// Change in rolling prediction accuracy.
    pub accuracy_delta: f64,
    /// Change in total prediction error accumulated.
    pub total_error_delta: f64,
}

/// Changes in recent behavior (action distribution).
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BehavioralDiff {
    /// Most recent action in A (if any).
    pub last_action_a: Option<String>,
    /// Most recent action in B (if any).
    pub last_action_b: Option<String>,
    /// True if the last action differs.
    pub last_action_changed: bool,
}

/// Changes in the developmental state vector.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DevelopmentalStateDiff {
    /// Change in age.
    pub age_delta: i64,
    /// Change in maturity.
    pub maturity_delta: f64,
    /// Change in plasticity.
    pub plasticity_delta: f64,
    /// Change in stability.
    pub stability_delta: f64,
    /// Change in energy.
    pub energy_delta: f64,
    /// Change in prediction accuracy.
    pub prediction_accuracy_delta: f64,
    /// Change in self-model stability.
    pub self_model_stability_delta: f64,
    /// Change in exploration level.
    pub exploration_level_delta: f64,
    /// L1 distance between the two developmental state vectors.
    pub state_l1_distance: f64,
    /// True if the developmental stage changed.
    pub stage_changed: bool,
    /// Stage in A.
    pub stage_a: String,
    /// Stage in B.
    pub stage_b: String,
}

impl MindDiff {
    /// Compute the diff between two organism states.
    pub fn between(a: &OrganismState, b: &OrganismState) -> Self {
        let identical = a.hash() == b.hash();

        // Memory diff: compare by key.
        let keys_a: std::collections::BTreeSet<&String> = a.memory.iter().map(|m| &m.key).collect();
        let keys_b: std::collections::BTreeSet<&String> = b.memory.iter().map(|m| &m.key).collect();
        let added = keys_b.difference(&keys_a).count();
        let removed = keys_a.difference(&keys_b).count();
        let importance_changed = a.memory.iter().zip(b.memory.iter())
            .filter(|(ma, mb)| ma.key == mb.key && (ma.importance - mb.importance).abs() > 1e-9)
            .count();

        // Self-model diff.
        let self_model_changes = SelfModelDiff {
            expected_reward_delta: b.self_model.expected_reward - a.self_model.expected_reward,
            expected_prediction_error_delta: b.self_model.expected_prediction_error - a.self_model.expected_prediction_error,
            update_count_delta: b.self_model.update_count as i64 - a.self_model.update_count as i64,
        };

        // Value (action preference) diff.
        let mut per_action = std::collections::BTreeMap::new();
        let mut total_l1 = 0.0;
        let mut all_keys: BTreeSet<&String> = a.action_preferences.keys().collect();
        all_keys.extend(b.action_preferences.keys());
        for k in all_keys {
            let va = a.action_preferences.get(k).copied().unwrap_or(0.0);
            let vb = b.action_preferences.get(k).copied().unwrap_or(0.0);
            let delta = vb - va;
            per_action.insert(k.clone(), delta);
            total_l1 += delta.abs();
        }
        let value_changes = ValueDiff { per_action, total_l1 };

        // Capability diff.
        let mut per_capability = std::collections::BTreeMap::new();
        let mut gained = Vec::new();
        let mut lost = Vec::new();
        let mut all_caps: BTreeSet<&String> = a.developmental.capabilities.keys().collect();
        all_caps.extend(b.developmental.capabilities.keys());
        for k in all_caps {
            let ca = a.developmental.capabilities.get(k).copied().unwrap_or(0.0);
            let cb = b.developmental.capabilities.get(k).copied().unwrap_or(0.0);
            if !a.developmental.capabilities.contains_key(k) && b.developmental.capabilities.contains_key(k) {
                gained.push(k.clone());
            } else if a.developmental.capabilities.contains_key(k) && !b.developmental.capabilities.contains_key(k) {
                lost.push(k.clone());
            }
            per_capability.insert(k.clone(), cb - ca);
        }
        let capability_changes = CapabilityDiff { per_capability, gained, lost };

        // Prediction diff.
        let prediction_changes = PredictionDiff {
            accuracy_delta: b.developmental.prediction_accuracy - a.developmental.prediction_accuracy,
            total_error_delta: b.total_prediction_error - a.total_prediction_error,
        };

        // Behavioral diff.
        let last_action_a = a.last_action.map(|x| x.to_string());
        let last_action_b = b.last_action.map(|x| x.to_string());
        let last_action_changed = last_action_a != last_action_b;
        let behavioral_changes = BehavioralDiff {
            last_action_a: last_action_a.clone(),
            last_action_b: last_action_b.clone(),
            last_action_changed,
        };

        // Developmental state diff.
        let dev_a = &a.developmental;
        let dev_b = &b.developmental;
        let developmental_changes = DevelopmentalStateDiff {
            age_delta: dev_b.age as i64 - dev_a.age as i64,
            maturity_delta: dev_b.maturity - dev_a.maturity,
            plasticity_delta: dev_b.plasticity - dev_a.plasticity,
            stability_delta: dev_b.stability - dev_a.stability,
            energy_delta: dev_b.energy_state - dev_a.energy_state,
            prediction_accuracy_delta: dev_b.prediction_accuracy - dev_a.prediction_accuracy,
            self_model_stability_delta: dev_b.self_model_stability - dev_a.self_model_stability,
            exploration_level_delta: dev_b.exploration_level - dev_a.exploration_level,
            state_l1_distance: dev_a.distance(dev_b),
            stage_changed: dev_a.developmental_stage != dev_b.developmental_stage,
            stage_a: dev_a.developmental_stage.to_string(),
            stage_b: dev_b.developmental_stage.to_string(),
        };

        Self {
            state_a_hash: a.short_hash(),
            state_b_hash: b.short_hash(),
            step_delta: b.step as i64 - a.step as i64,
            memory_changes: MemoryDiff {
                added,
                removed,
                importance_changed,
                size_a: a.memory.len(),
                size_b: b.memory.len(),
            },
            self_model_changes,
            value_changes,
            capability_changes,
            prediction_changes,
            behavioral_changes,
            developmental_changes,
            identical,
        }
    }

    /// Render a human-readable summary.
    pub fn render(&self) -> String {
        let mut s = String::new();
        s.push_str("=== Mind Diff ===\n");
        s.push_str(&format!("  State A:        {}...\n", &self.state_a_hash[..12.min(self.state_a_hash.len())]));
        s.push_str(&format!("  State B:        {}...\n", &self.state_b_hash[..12.min(self.state_b_hash.len())]));
        s.push_str(&format!("  Step delta:     {}\n", self.step_delta));
        s.push_str(&format!("  Identical:      {}\n", self.identical));
        s.push_str("\n");
        s.push_str("-- Memory --\n");
        s.push_str(&format!("  added={}, removed={}, importance_changed={}, size {}→{}\n",
            self.memory_changes.added, self.memory_changes.removed,
            self.memory_changes.importance_changed,
            self.memory_changes.size_a, self.memory_changes.size_b));
        s.push_str("\n-- Self-model --\n");
        s.push_str(&format!("  expected_reward:        {:+.4}\n", self.self_model_changes.expected_reward_delta));
        s.push_str(&format!("  expected_prediction_err: {:+.4}\n", self.self_model_changes.expected_prediction_error_delta));
        s.push_str(&format!("  update_count:           {:+}\n", self.self_model_changes.update_count_delta));
        s.push_str("\n-- Values (action preferences) --\n");
        s.push_str(&format!("  total L1 change: {:.4}\n", self.value_changes.total_l1));
        for (k, v) in &self.value_changes.per_action {
            s.push_str(&format!("    {:<10} {:+.4}\n", k, v));
        }
        s.push_str("\n-- Capabilities --\n");
        for (k, v) in &self.capability_changes.per_capability {
            s.push_str(&format!("    {:<20} {:+.4}\n", k, v));
        }
        if !self.capability_changes.gained.is_empty() {
            s.push_str(&format!("  gained: {:?}\n", self.capability_changes.gained));
        }
        if !self.capability_changes.lost.is_empty() {
            s.push_str(&format!("  lost:   {:?}\n", self.capability_changes.lost));
        }
        s.push_str("\n-- Prediction --\n");
        s.push_str(&format!("  accuracy:      {:+.4}\n", self.prediction_changes.accuracy_delta));
        s.push_str(&format!("  total error:   {:+.4}\n", self.prediction_changes.total_error_delta));
        s.push_str("\n-- Behavior --\n");
        s.push_str(&format!("  last action: {} → {}\n",
            self.behavioral_changes.last_action_a.as_deref().unwrap_or("—"),
            self.behavioral_changes.last_action_b.as_deref().unwrap_or("—")));
        s.push_str("\n-- Developmental state --\n");
        s.push_str(&format!("  stage: {} → {}\n",
            self.developmental_changes.stage_a, self.developmental_changes.stage_b));
        s.push_str(&format!("  age:                  {:+}\n", self.developmental_changes.age_delta));
        s.push_str(&format!("  plasticity:           {:+.4}\n", self.developmental_changes.plasticity_delta));
        s.push_str(&format!("  stability:            {:+.4}\n", self.developmental_changes.stability_delta));
        s.push_str(&format!("  energy:               {:+.4}\n", self.developmental_changes.energy_delta));
        s.push_str(&format!("  prediction_accuracy:  {:+.4}\n", self.developmental_changes.prediction_accuracy_delta));
        s.push_str(&format!("  self_model_stability: {:+.4}\n", self.developmental_changes.self_model_stability_delta));
        s.push_str(&format!("  exploration_level:    {:+.4}\n", self.developmental_changes.exploration_level_delta));
        s.push_str(&format!("  state L1 distance:    {:.4}\n", self.developmental_changes.state_l1_distance));
        s
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::environment::{ResourceWorld, Environment};
    use crate::genome::DevelopmentalGenome;
    use crate::organism::MinimumOrganism;

    #[test]
    fn diff_of_identical_states_is_marked_identical() {
        let g = DevelopmentalGenome::named("diff");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let snap1 = org.state.clone();
        let snap2 = org.state.clone();
        let diff = MindDiff::between(&snap1, &snap2);
        assert!(diff.identical);
    }

    #[test]
    fn diff_of_different_states_is_not_identical() {
        let g = DevelopmentalGenome::named("diff");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let snap1 = org.state.clone();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        for _ in 0..5 {
            org.tick(&mut env);
        }
        let snap2 = org.state.clone();
        let diff = MindDiff::between(&snap1, &snap2);
        assert!(!diff.identical);
        assert_eq!(diff.step_delta, 5);
    }

    #[test]
    fn diff_renders_human_readable_summary() {
        let g = DevelopmentalGenome::named("diff");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let snap1 = org.state.clone();
        let mut env = ResourceWorld::new(6, 6, 1);
        env.reset();
        for _ in 0..3 {
            org.tick(&mut env);
        }
        let snap2 = org.state.clone();
        let diff = MindDiff::between(&snap1, &snap2);
        let s = diff.render();
        assert!(s.contains("Mind Diff"));
        assert!(s.contains("Memory"));
        assert!(s.contains("Values"));
        assert!(s.contains("Developmental state"));
    }

    #[test]
    fn diff_detects_action_preference_changes() {
        let g = DevelopmentalGenome::named("diff");
        let mut org = MinimumOrganism::instantiate(g);
        org.initialize().unwrap();
        org.begin_development().unwrap();
        let snap1 = org.state.clone();
        // Manually mutate an action preference to verify detection.
        org.state.action_preferences.insert("move_right".to_string(), 0.5);
        let snap2 = org.state.clone();
        let diff = MindDiff::between(&snap1, &snap2);
        assert!(diff.value_changes.total_l1 > 0.0);
    }
}
