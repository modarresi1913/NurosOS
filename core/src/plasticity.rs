//! # Synaptic plasticity rules.
//!
//! Implements the algorithms that update synaptic weights as a function
//! of pre/post-synaptic activity.
//!
//! ## Biological correspondence
//!
//! Plasticity is the biological basis of **learning and memory**. In
//! *Drosophila*, the dominant form is **STDP** at the Kenyon cell →
//! mushroom body output neuron (MBON) synapse, modulated by dopamine
//! signaling during associative conditioning.

use crate::models::Spike;

/// Generic plasticity rule trait.
pub trait PlasticityRule: Send + Sync {
    /// Update the weight given recent pre/post spikes.
    ///
    /// Returns the new weight.
    fn update(&self, current_weight: f32, pre_spikes: &[Spike], post_spikes: &[Spike]) -> f32;
}

/// Hebbian rule: "cells that fire together wire together."
///
/// Δw = η · pre · post
pub struct HebbianRule {
    /// Learning rate.
    pub eta: f32,
}

impl PlasticityRule for HebbianRule {
    fn update(&self, w: f32, pre: &[Spike], post: &[Spike]) -> f32 {
        // Mimics Hebbian co-activation: if both pre and post fired
        // recently, strengthen the synapse.
        let pre_active = !pre.is_empty();
        let post_active = !post.is_empty();
        let delta = if pre_active && post_active { self.eta } else { 0.0 };
        w + delta
    }
}

/// Spike-Timing-Dependent Plasticity.
///
/// Δw depends on the relative timing of pre and post spikes:
/// - Pre before post → LTP (long-term potentiation).
/// - Post before pre → LTD (long-term depression).
///
/// This is the dominant plasticity model in *Drosophila* associative
/// learning. Mimics the STDP curve measured at the KC→MBON synapse.
pub struct StdpRule {
    /// LTP learning rate.
    pub eta_plus: f32,
    /// LTD learning rate.
    pub eta_minus: f32,
    /// LTP time window (ms).
    pub tau_plus: f32,
    /// LTD time window (ms).
    pub tau_minus: f32,
}

impl Default for StdpRule {
    fn default() -> Self {
        Self {
            eta_plus: 0.01,
            eta_minus: 0.01,
            tau_plus: 20.0,
            tau_minus: 20.0,
        }
    }
}

impl PlasticityRule for StdpRule {
    fn update(&self, w: f32, pre: &[Spike], post: &[Spike]) -> f32 {
        // Pair each pre spike with each post spike and sum the weight change.
        let mut delta = 0.0;
        for p in pre {
            for q in post {
                let dt = q.timestamp as f32 - p.timestamp as f32;
                if dt > 0.0 {
                    // Pre before post → LTP.
                    delta += self.eta_plus * (-dt / self.tau_plus).exp();
                } else {
                    // Post before pre → LTD.
                    let dt = -dt;
                    delta -= self.eta_minus * (-dt / self.tau_minus).exp();
                }
            }
        }
        w + delta
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use half::f16;

    #[test]
    fn test_hebbian_strengthens_on_coactivation() {
        let rule = HebbianRule { eta: 0.1 };
        let pre = vec![Spike { src: 0, weight: f16::from_f32(1.0), timestamp: 0 }];
        let post = vec![Spike { src: 1, weight: f16::from_f32(1.0), timestamp: 1 }];
        let new_w = rule.update(0.5, &pre, &post);
        assert!(new_w > 0.5, "Hebbian should strengthen on coactivation");
    }

    #[test]
    fn test_stdp_ltp_on_pre_before_post() {
        let rule = StdpRule::default();
        let pre = vec![Spike { src: 0, weight: f16::from_f32(1.0), timestamp: 0 }];
        let post = vec![Spike { src: 1, weight: f16::from_f32(1.0), timestamp: 10 }];
        let new_w = rule.update(0.5, &pre, &post);
        assert!(new_w > 0.5, "Pre-before-post should potentiate (LTP)");
    }

    #[test]
    fn test_stdp_ltd_on_post_before_pre() {
        let rule = StdpRule::default();
        let pre = vec![Spike { src: 0, weight: f16::from_f32(1.0), timestamp: 10 }];
        let post = vec![Spike { src: 1, weight: f16::from_f32(1.0), timestamp: 0 }];
        let new_w = rule.update(0.5, &pre, &post);
        assert!(new_w < 0.5, "Post-before-pre should depress (LTD)");
    }
}
