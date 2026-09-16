//! Artificial Aging.
//!
//! `AgingModel` models how accumulated computational history affects future
//! cognition. It has five configurable dimensions:
//!
//! 1. **Memory degradation** — memories become less accessible over time.
//! 2. **Plasticity changes** — plasticity decreases (or, rarely, increases)
//!    with age.
//! 3. **Processing constraints** — cognitive load increases, energy
//!    efficiency decreases.
//! 4. **Experience accumulation** — stability and prediction accuracy
//!    improve with experience (up to a ceiling).
//! 5. **Structural consolidation** — self-model stability increases as
//!    the organism's identity consolidates.
//!
//! ## Interpretation caveat
//!
//! Aging is **configurable**. Do not impose biological aging assumptions
//! without evidence. The purpose is to investigate: *How does accumulated
//! computational history affect future cognition?*

use serde::{Deserialize, Serialize};

use crate::hash;
use crate::state::DevelopmentalState;

/// The aging model.
///
/// Each field is a rate or threshold that controls how the corresponding
/// aging dimension affects the developmental state. All rates are per-tick.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgingModel {
    // --- Memory degradation ---
    /// Fraction of memory importance lost per tick (in [0, 1]).
    /// 0.0 = no degradation; 0.01 = 1% importance loss per tick.
    #[serde(default = "default_memory_degradation_rate")]
    pub memory_degradation_rate: f64,
    /// Age at which memory degradation begins (in ticks).
    #[serde(default = "default_memory_degradation_onset")]
    pub memory_degradation_onset: u64,

    // --- Plasticity changes ---
    /// Fraction of plasticity lost per tick after the onset age.
    /// Positive = plasticity decreases (typical); negative = plasticity
    /// increases (atypical).
    #[serde(default = "default_plasticity_decay_rate")]
    pub plasticity_decay_rate: f64,
    /// Age at which plasticity decay begins.
    #[serde(default = "default_plasticity_decay_onset")]
    pub plasticity_decay_onset: u64,
    /// Minimum plasticity floor (plasticity never drops below this).
    #[serde(default = "default_plasticity_floor")]
    pub plasticity_floor: f64,

    // --- Processing constraints ---
    /// Rate at which cognitive load increases per tick (in [0, 1]).
    #[serde(default = "default_cognitive_load_increase")]
    pub cognitive_load_increase: f64,
    /// Rate at which energy efficiency decreases per tick (in [0, 1]).
    #[serde(default = "default_energy_efficiency_decay")]
    pub energy_efficiency_decay: f64,
    /// Maximum cognitive load (ceiling).
    #[serde(default = "default_max_cognitive_load")]
    pub max_cognitive_load: f64,

    // --- Experience accumulation ---
    /// Rate at which stability improves per tick (in [0, 1]).
    #[serde(default = "default_stability_improvement_rate")]
    pub stability_improvement_rate: f64,
    /// Maximum stability (ceiling).
    #[serde(default = "default_max_stability")]
    pub max_stability: f64,
    /// Rate at which prediction accuracy improves per tick (in [0, 1]).
    #[serde(default = "default_prediction_accuracy_improvement")]
    pub prediction_accuracy_improvement: f64,

    // --- Structural consolidation ---
    /// Rate at which self-model stability increases per tick (in [0, 1]).
    #[serde(default = "default_self_model_consolidation_rate")]
    pub self_model_consolidation_rate: f64,
    /// Maximum self-model stability (ceiling).
    #[serde(default = "default_max_self_model_stability")]
    pub max_self_model_stability: f64,
}

fn default_memory_degradation_rate() -> f64 { 0.001 }
fn default_memory_degradation_onset() -> u64 { 100 }
fn default_plasticity_decay_rate() -> f64 { 0.0005 }
fn default_plasticity_decay_onset() -> u64 { 50 }
fn default_plasticity_floor() -> f64 { 0.05 }
fn default_cognitive_load_increase() -> f64 { 0.0001 }
fn default_energy_efficiency_decay() -> f64 { 0.0002 }
fn default_max_cognitive_load() -> f64 { 0.8 }
fn default_stability_improvement_rate() -> f64 { 0.001 }
fn default_max_stability() -> f64 { 0.95 }
fn default_prediction_accuracy_improvement() -> f64 { 0.0005 }
fn default_self_model_consolidation_rate() -> f64 { 0.0008 }
fn default_max_self_model_stability() -> f64 { 0.9 }

impl Default for AgingModel {
    fn default() -> Self {
        Self {
            memory_degradation_rate: default_memory_degradation_rate(),
            memory_degradation_onset: default_memory_degradation_onset(),
            plasticity_decay_rate: default_plasticity_decay_rate(),
            plasticity_decay_onset: default_plasticity_decay_onset(),
            plasticity_floor: default_plasticity_floor(),
            cognitive_load_increase: default_cognitive_load_increase(),
            energy_efficiency_decay: default_energy_efficiency_decay(),
            max_cognitive_load: default_max_cognitive_load(),
            stability_improvement_rate: default_stability_improvement_rate(),
            max_stability: default_max_stability(),
            prediction_accuracy_improvement: default_prediction_accuracy_improvement(),
            self_model_consolidation_rate: default_self_model_consolidation_rate(),
            max_self_model_stability: default_max_self_model_stability(),
        }
    }
}

impl AgingModel {
    /// Construct a model with no aging effects (all rates zero).
    pub fn no_aging() -> Self {
        Self {
            memory_degradation_rate: 0.0,
            memory_degradation_onset: u64::MAX,
            plasticity_decay_rate: 0.0,
            plasticity_decay_onset: u64::MAX,
            plasticity_floor: 0.0,
            cognitive_load_increase: 0.0,
            energy_efficiency_decay: 0.0,
            max_cognitive_load: 1.0,
            stability_improvement_rate: 0.0,
            max_stability: 1.0,
            prediction_accuracy_improvement: 0.0,
            self_model_consolidation_rate: 0.0,
            max_self_model_stability: 1.0,
        }
    }

    /// Construct a model with rapid aging (for testing).
    pub fn rapid_aging() -> Self {
        Self {
            memory_degradation_rate: 0.01,
            memory_degradation_onset: 10,
            plasticity_decay_rate: 0.005,
            plasticity_decay_onset: 10,
            plasticity_floor: 0.01,
            cognitive_load_increase: 0.005,
            energy_efficiency_decay: 0.005,
            max_cognitive_load: 0.9,
            stability_improvement_rate: 0.005,
            max_stability: 0.99,
            prediction_accuracy_improvement: 0.002,
            self_model_consolidation_rate: 0.005,
            max_self_model_stability: 0.95,
        }
    }

    /// Apply one tick of aging to a developmental state.
    ///
    /// This modifies the state in place according to the aging model's
    /// rates and thresholds. It should be called once per tick, after the
    /// organism's normal developmental update.
    pub fn apply(&self, state: &mut DevelopmentalState) -> AgingEffect {
        let age = state.age;
        let mut effect = AgingEffect::default();

        // 1. Memory degradation
        if age >= self.memory_degradation_onset {
            // Reduce memory_capacity by the degradation rate.
            let before = state.memory_capacity;
            state.memory_capacity = (state.memory_capacity - self.memory_degradation_rate).max(0.0);
            effect.memory_degradation = before - state.memory_capacity;
        }

        // 2. Plasticity decay
        if age >= self.plasticity_decay_onset {
            let before = state.plasticity;
            state.plasticity = (state.plasticity - self.plasticity_decay_rate).max(self.plasticity_floor);
            effect.plasticity_change = state.plasticity - before;
        }

        // 3. Processing constraints
        let before_load = state.cognitive_load;
        state.cognitive_load = (state.cognitive_load + self.cognitive_load_increase).min(self.max_cognitive_load);
        effect.cognitive_load_change = state.cognitive_load - before_load;

        let before_energy = state.energy_state;
        // Energy efficiency decay: the organism's max energy decreases slightly.
        // We model this as a small permanent reduction in energy_state.
        state.energy_state = (state.energy_state - self.energy_efficiency_decay).max(0.0);
        effect.energy_efficiency_change = state.energy_state - before_energy;

        // 4. Experience accumulation
        let before_stability = state.stability;
        state.stability = (state.stability + self.stability_improvement_rate).min(self.max_stability);
        effect.stability_change = state.stability - before_stability;

        let before_pred = state.prediction_accuracy;
        state.prediction_accuracy = (state.prediction_accuracy + self.prediction_accuracy_improvement).min(1.0);
        effect.prediction_accuracy_change = state.prediction_accuracy - before_pred;

        // 5. Structural consolidation
        let before_self = state.self_model_stability;
        state.self_model_stability = (state.self_model_stability + self.self_model_consolidation_rate).min(self.max_self_model_stability);
        effect.self_model_consolidation = state.self_model_stability - before_self;

        // Record an aging event
        state.record_event();

        effect
    }

    /// Canonical hash of the aging model (for provenance).
    pub fn hash(&self) -> String {
        hash::hash(self)
    }

    /// Render a human-readable summary.
    pub fn render(&self) -> String {
        let mut s = String::new();
        s.push_str("=== Aging Model ===\n");
        s.push_str("Memory degradation:\n");
        s.push_str(&format!("  rate:   {:.6} per tick\n", self.memory_degradation_rate));
        s.push_str(&format!("  onset:  {} ticks\n", self.memory_degradation_onset));
        s.push_str("Plasticity changes:\n");
        s.push_str(&format!("  decay_rate:  {:.6} per tick\n", self.plasticity_decay_rate));
        s.push_str(&format!("  onset:       {} ticks\n", self.plasticity_decay_onset));
        s.push_str(&format!("  floor:       {:.4}\n", self.plasticity_floor));
        s.push_str("Processing constraints:\n");
        s.push_str(&format!("  cognitive_load_increase: {:.6} per tick\n", self.cognitive_load_increase));
        s.push_str(&format!("  energy_efficiency_decay: {:.6} per tick\n", self.energy_efficiency_decay));
        s.push_str(&format!("  max_cognitive_load:      {:.4}\n", self.max_cognitive_load));
        s.push_str("Experience accumulation:\n");
        s.push_str(&format!("  stability_improvement_rate:       {:.6} per tick\n", self.stability_improvement_rate));
        s.push_str(&format!("  max_stability:                    {:.4}\n", self.max_stability));
        s.push_str(&format!("  prediction_accuracy_improvement:  {:.6} per tick\n", self.prediction_accuracy_improvement));
        s.push_str("Structural consolidation:\n");
        s.push_str(&format!("  self_model_consolidation_rate: {:.6} per tick\n", self.self_model_consolidation_rate));
        s.push_str(&format!("  max_self_model_stability:      {:.4}\n", self.max_self_model_stability));
        s
    }
}

/// The effect of one tick of aging on a developmental state.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct AgingEffect {
    /// How much memory_capacity decreased this tick.
    pub memory_degradation: f64,
    /// How much plasticity changed (negative = decay).
    pub plasticity_change: f64,
    /// How much cognitive_load increased.
    pub cognitive_load_change: f64,
    /// How much energy efficiency decreased.
    pub energy_efficiency_change: f64,
    /// How much stability improved.
    pub stability_change: f64,
    /// How much prediction accuracy improved.
    pub prediction_accuracy_change: f64,
    /// How much self-model stability increased (consolidation).
    pub self_model_consolidation: f64,
}

impl AgingEffect {
    /// Returns true if any aging effect was non-zero.
    pub fn has_any_effect(&self) -> bool {
        self.memory_degradation != 0.0
            || self.plasticity_change != 0.0
            || self.cognitive_load_change != 0.0
            || self.energy_efficiency_change != 0.0
            || self.stability_change != 0.0
            || self.prediction_accuracy_change != 0.0
            || self.self_model_consolidation != 0.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::DevelopmentalState;

    #[test]
    fn no_aging_model_has_zero_rates() {
        let m = AgingModel::no_aging();
        assert_eq!(m.memory_degradation_rate, 0.0);
        assert_eq!(m.plasticity_decay_rate, 0.0);
        assert_eq!(m.cognitive_load_increase, 0.0);
        assert_eq!(m.stability_improvement_rate, 0.0);
    }

    #[test]
    fn no_aging_does_not_modify_state() {
        let m = AgingModel::no_aging();
        let mut state = DevelopmentalState::default();
        state.age = 100;
        let original = state.clone();
        let effect = m.apply(&mut state);
        assert!(!effect.has_any_effect());
        assert_eq!(state.plasticity, original.plasticity);
        assert_eq!(state.stability, original.stability);
    }

    #[test]
    fn rapid_aging_reduces_plasticity() {
        let m = AgingModel::rapid_aging();
        let mut state = DevelopmentalState::default();
        state.age = 20; // past onset
        let original_plasticity = state.plasticity;
        m.apply(&mut state);
        assert!(state.plasticity < original_plasticity);
    }

    #[test]
    fn rapid_aging_reduces_memory_capacity_after_onset() {
        let m = AgingModel::rapid_aging();
        let mut state = DevelopmentalState::default();
        state.memory_capacity = 0.5;
        state.age = 20; // past onset of 10
        let original = state.memory_capacity;
        m.apply(&mut state);
        assert!(state.memory_capacity < original);
    }

    #[test]
    fn memory_degradation_does_not_occur_before_onset() {
        let m = AgingModel::rapid_aging();
        let mut state = DevelopmentalState::default();
        state.memory_capacity = 0.5;
        state.age = 5; // before onset of 10
        let original = state.memory_capacity;
        m.apply(&mut state);
        assert_eq!(state.memory_capacity, original);
    }

    #[test]
    fn plasticity_does_not_drop_below_floor() {
        let mut m = AgingModel::rapid_aging();
        m.plasticity_floor = 0.3;
        let mut state = DevelopmentalState::default();
        state.plasticity = 0.31;
        state.age = 100;
        m.apply(&mut state);
        assert!(state.plasticity >= 0.3 - 1e-9);
    }

    #[test]
    fn rapid_aging_increases_stability() {
        let m = AgingModel::rapid_aging();
        let mut state = DevelopmentalState::default();
        state.stability = 0.5;
        state.age = 20;
        let original = state.stability;
        m.apply(&mut state);
        assert!(state.stability > original);
    }

    #[test]
    fn stability_does_not_exceed_max() {
        let mut m = AgingModel::rapid_aging();
        m.max_stability = 0.6;
        let mut state = DevelopmentalState::default();
        state.stability = 0.59;
        state.age = 100;
        m.apply(&mut state);
        assert!(state.stability <= 0.6 + 1e-9);
    }

    #[test]
    fn rapid_aging_increases_cognitive_load() {
        let m = AgingModel::rapid_aging();
        let mut state = DevelopmentalState::default();
        state.cognitive_load = 0.1;
        state.age = 20;
        let original = state.cognitive_load;
        m.apply(&mut state);
        assert!(state.cognitive_load > original);
    }

    #[test]
    fn cognitive_load_does_not_exceed_max() {
        let mut m = AgingModel::rapid_aging();
        m.max_cognitive_load = 0.5;
        let mut state = DevelopmentalState::default();
        state.cognitive_load = 0.49;
        state.age = 100;
        m.apply(&mut state);
        assert!(state.cognitive_load <= 0.5 + 1e-9);
    }

    #[test]
    fn rapid_aging_increases_self_model_stability() {
        let m = AgingModel::rapid_aging();
        let mut state = DevelopmentalState::default();
        state.self_model_stability = 0.3;
        state.age = 20;
        let original = state.self_model_stability;
        m.apply(&mut state);
        assert!(state.self_model_stability > original);
    }

    #[test]
    fn render_contains_all_dimensions() {
        let m = AgingModel::default();
        let s = m.render();
        assert!(s.contains("Memory degradation"));
        assert!(s.contains("Plasticity changes"));
        assert!(s.contains("Processing constraints"));
        assert!(s.contains("Experience accumulation"));
        assert!(s.contains("Structural consolidation"));
    }

    #[test]
    fn hash_is_deterministic() {
        let m1 = AgingModel::default();
        let m2 = AgingModel::default();
        assert_eq!(m1.hash(), m2.hash());
    }

    #[test]
    fn hash_changes_with_parameters() {
        let m1 = AgingModel::default();
        let m2 = AgingModel::rapid_aging();
        assert_ne!(m1.hash(), m2.hash());
    }
}
