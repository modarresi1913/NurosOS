//! Developmental State.
//!
//! The developmental state is the **complete observable state** of an
//! organism at a single point in its developmental trajectory. It includes
//! the organism's age, current developmental stage, plasticity, stability,
//! energy, cognitive load, memory capacity, prediction accuracy, self-model
//! stability, exploration level, risk sensitivity, and accumulated
//! capabilities.
//!
//! The state is intentionally NOT a single scalar. It is a vector of
//! measurable quantities that can be compared across organisms and across
//! time. The distance between two developmental states (see [`diff`]) is
//! the foundation of [`MindDiff`](crate::diff::MindDiff) and the
//! [`DevelopmentalDivergence`](crate::trajectory) metrics.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::hash;

/// The developmental stage of an organism.
///
/// Stages are coarse-grained labels for where the organism is in its
/// developmental trajectory. The transition thresholds between stages are
/// specified by the genome's maturation schedule.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DevelopmentalStage {
    /// Initial configuration, before any experience.
    Embryonic,
    /// First experiences, before developmental rules activate.
    Nascent,
    /// Active development — plasticity is high.
    Developing,
    /// Approaching stability — plasticity decreasing.
    Maturing,
    /// Stable behavior, plasticity low.
    Mature,
    /// Domain-adapted, specialized for environment.
    Specialized,
    /// Gradual decline in plasticity and stability.
    Aging,
    /// No longer developing.
    Terminated,
}

impl Default for DevelopmentalStage {
    fn default() -> Self {
        Self::Embryonic
    }
}

impl std::fmt::Display for DevelopmentalStage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", serde_json::to_string(self).unwrap_or_default().trim_matches('"'))
    }
}

/// The complete developmental state of an organism.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevelopmentalState {
    /// Step count since initialization (chronological age).
    #[serde(default)]
    pub age: u64,
    /// Current developmental stage.
    #[serde(default)]
    pub developmental_stage: DevelopmentalStage,
    /// Maturity in [0, 1]. Higher = closer to Mature stage.
    #[serde(default = "default_maturity")]
    pub maturity: f64,
    /// Plasticity in [0, 1]. Higher = more changeable.
    #[serde(default = "default_plasticity")]
    pub plasticity: f64,
    /// Stability in [0, 1]. Higher = more consistent behavior.
    #[serde(default = "default_stability")]
    pub stability: f64,
    /// Adaptability in [0, 1]. Higher = better at adapting to changes.
    #[serde(default = "default_adaptability")]
    pub adaptability: f64,
    /// Energy in [0, 1]. Higher = more energetic resources available.
    #[serde(default = "default_energy")]
    pub energy_state: f64,
    /// Cognitive load in [0, 1]. Higher = more of the cognitive budget in use.
    #[serde(default)]
    pub cognitive_load: f64,
    /// Memory capacity utilization in [0, 1].
    #[serde(default)]
    pub memory_capacity: f64,
    /// Rolling mean of recent prediction accuracies in [0, 1].
    #[serde(default = "default_prediction_accuracy")]
    pub prediction_accuracy: f64,
    /// Stability of the self-model in [0, 1].
    #[serde(default = "default_self_model_stability")]
    pub self_model_stability: f64,
    /// Current exploration drive in [0, 1]. Higher = more exploratory.
    #[serde(default = "default_exploration_level")]
    pub exploration_level: f64,
    /// Current risk sensitivity in [0, 1]. Higher = more risk-averse.
    #[serde(default = "default_risk_sensitivity")]
    pub risk_sensitivity: f64,
    /// Map of capability name → proficiency in [0, 1].
    #[serde(default)]
    pub capabilities: BTreeMap<String, f64>,
    /// Number of developmental events recorded so far.
    #[serde(default)]
    pub developmental_event_count: u64,
}

fn default_maturity() -> f64 { 0.0 }
fn default_plasticity() -> f64 { 0.8 }
fn default_stability() -> f64 { 0.5 }
fn default_adaptability() -> f64 { 0.5 }
fn default_energy() -> f64 { 1.0 }
fn default_prediction_accuracy() -> f64 { 0.0 }
fn default_self_model_stability() -> f64 { 0.0 }
fn default_exploration_level() -> f64 { 0.3 }
fn default_risk_sensitivity() -> f64 { 0.5 }

impl Default for DevelopmentalState {
    fn default() -> Self {
        Self {
            age: 0,
            developmental_stage: DevelopmentalStage::Embryonic,
            maturity: default_maturity(),
            plasticity: default_plasticity(),
            stability: default_stability(),
            adaptability: default_adaptability(),
            energy_state: default_energy(),
            cognitive_load: 0.0,
            memory_capacity: 0.0,
            prediction_accuracy: default_prediction_accuracy(),
            self_model_stability: default_self_model_stability(),
            exploration_level: default_exploration_level(),
            risk_sensitivity: default_risk_sensitivity(),
            capabilities: BTreeMap::new(),
            developmental_event_count: 0,
        }
    }
}

impl DevelopmentalState {
    /// Compute the canonical SHA-256 hash of this state.
    pub fn hash(&self) -> String {
        hash::hash(self)
    }

    /// Short form of the hash.
    pub fn short_hash(&self) -> String {
        hash::short_hash(&self.hash())
    }

    /// Compute a scalar "distance" between two developmental states.
    ///
    /// This is the L1 (Manhattan) distance between the scalar fields, plus
    /// the L1 distance between matching capability proficiencies. The result
    /// is in [0, ∞); it is NOT normalized to [0, 1].
    ///
    /// **Interpretation caveat**: a small distance does NOT mean the two
    /// organisms are cognitively equivalent — only that their measurable
    /// developmental state vectors are close. Use this for ordering and
    /// comparison, not as an absolute measure.
    pub fn distance(&self, other: &DevelopmentalState) -> f64 {
        let mut d: f64 = 0.0;
        d += (self.maturity - other.maturity).abs();
        d += (self.plasticity - other.plasticity).abs();
        d += (self.stability - other.stability).abs();
        d += (self.adaptability - other.adaptability).abs();
        d += (self.energy_state - other.energy_state).abs();
        d += (self.cognitive_load - other.cognitive_load).abs();
        d += (self.memory_capacity - other.memory_capacity).abs();
        d += (self.prediction_accuracy - other.prediction_accuracy).abs();
        d += (self.self_model_stability - other.self_model_stability).abs();
        d += (self.exploration_level - other.exploration_level).abs();
        d += (self.risk_sensitivity - other.risk_sensitivity).abs();

        // Capability distance: L1 over the union of capability keys.
        let mut keys: std::collections::BTreeSet<&String> = self.capabilities.keys().collect();
        for k in other.capabilities.keys() {
            keys.insert(k);
        }
        for k in keys {
            let a = self.capabilities.get(k).copied().unwrap_or(0.0);
            let b = other.capabilities.get(k).copied().unwrap_or(0.0);
            d += (a - b).abs();
        }
        d
    }

    /// Record a developmental event (increments the counter).
    pub fn record_event(&mut self) {
        self.developmental_event_count += 1;
    }

    /// Snapshot as a flat JSON object (useful for telemetry export).
    pub fn to_flat_json(&self) -> serde_json::Value {
        serde_json::json!({
            "age": self.age,
            "developmental_stage": self.developmental_stage.to_string(),
            "maturity": self.maturity,
            "plasticity": self.plasticity,
            "stability": self.stability,
            "adaptability": self.adaptability,
            "energy_state": self.energy_state,
            "cognitive_load": self.cognitive_load,
            "memory_capacity": self.memory_capacity,
            "prediction_accuracy": self.prediction_accuracy,
            "self_model_stability": self.self_model_stability,
            "exploration_level": self.exploration_level,
            "risk_sensitivity": self.risk_sensitivity,
            "capabilities": self.capabilities,
            "developmental_event_count": self.developmental_event_count,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_state_is_embryonic() {
        let s = DevelopmentalState::default();
        assert_eq!(s.developmental_stage, DevelopmentalStage::Embryonic);
        assert_eq!(s.age, 0);
    }

    #[test]
    fn hash_is_deterministic() {
        let s1 = DevelopmentalState::default();
        let s2 = DevelopmentalState::default();
        assert_eq!(s1.hash(), s2.hash());
    }

    #[test]
    fn distance_to_self_is_zero() {
        let s = DevelopmentalState::default();
        assert_eq!(s.distance(&s), 0.0);
    }

    #[test]
    fn distance_is_symmetric() {
        let mut a = DevelopmentalState::default();
        let mut b = DevelopmentalState::default();
        a.plasticity = 0.8;
        b.plasticity = 0.4;
        let d_ab = a.distance(&b);
        let d_ba = b.distance(&a);
        assert!((d_ab - d_ba).abs() < 1e-12);
        assert!(d_ab > 0.0);
    }

    #[test]
    fn distance_includes_capabilities() {
        let mut a = DevelopmentalState::default();
        let mut b = DevelopmentalState::default();
        a.capabilities.insert("locate_resource".into(), 0.7);
        b.capabilities.insert("locate_resource".into(), 0.2);
        assert!(a.distance(&b) > 0.4);
    }

    #[test]
    fn flat_json_round_trips_stage() {
        let s = DevelopmentalState::default();
        let v = s.to_flat_json();
        assert_eq!(v["developmental_stage"], "EMBRYONIC");
    }
}
