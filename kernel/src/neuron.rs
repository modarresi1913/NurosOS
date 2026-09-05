//! # Neuron Models
//!
//! This module defines the `NeuronModel` trait and a reference
//! implementation of the Leaky Integrate-and-Fire (LIF) model.
//!
//! ## Biological correspondence
//!
//! LIF is the simplest biologically-plausible spiking neuron model. It
//! captures three essential features of a real neuron:
//!
//! 1. **Integration** — incoming synaptic currents accumulate on the
//!    membrane capacitor.
//! 2. **Leak** — the membrane passively returns to rest via potassium
//!    leak channels.
//! 3. **Threshold** — when the membrane crosses a threshold, an
//!    all-or-nothing spike is emitted.
//!
//! LIF omits many biological details (ionic channel kinetics, dendritic
//! computation, axonal propagation delays). These are added in `core/`
//! as more sophisticated models (Izhikevich, Hodgkin-Huxley).

use crate::synapse::Spike;

/// A globally-unique neuron identifier.
///
/// This is the kernel's equivalent of a PID. It is stable for the
/// lifetime of the kernel (a neuron is never moved or deleted — it
/// can only be "lesioned", in which case the HAL remaps it).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct NeuronId(pub usize);

/// The result of one `step()` call on a neuron model.
#[derive(Clone, Copy, Debug)]
pub enum StepResult {
    /// The neuron did not fire.
    Silent,
    /// The neuron fired (emitted a spike).
    Fired,
}

/// Parameters for the Leaky Integrate-and-Fire model.
///
/// Defaults are the *Drosophila* mushroom-body Kenyon cell values
/// (Acerbo et al., 2012).
#[derive(Clone, Copy, Debug)]
pub struct LifParams {
    /// Membrane time constant, in ms. (KC: 18 ms)
    pub tau_m: f32,
    /// Synaptic time constant, in ms. (KC: 5.5 ms)
    pub tau_s: f32,
    /// Spike threshold, in mV. (KC: -55 mV)
    pub theta: f32,
    /// Resting potential, in mV. (KC: -70 mV)
    pub v_rest: f32,
    /// Reset potential, in mV. (KC: -80 mV — afterhyperpolarization)
    pub v_reset: f32,
    /// Refractory period, in ms. (KC: 2 ms)
    pub tau_refrac: f32,
}

/// Generic neuron parameter bundle, used by the HAL's `alloc_neuron`.
///
/// In v0.1.0 this is just an alias for `LifParams` (the only supported
/// model). In v0.2.0 it will become an enum covering LIF, Izhikevich,
/// and Hodgkin-Huxley.
pub type NeuronParams = LifParams;

impl Default for LifParams {
    fn default() -> Self {
        Self {
            tau_m: 18.0,
            tau_s: 5.5,
            theta: -55.0,
            v_rest: -70.0,
            v_reset: -80.0,
            tau_refrac: 2.0,
        }
    }
}

/// The Leaky Integrate-and-Fire neuron model.
///
/// ## Biological correspondence
///
/// This implements the standard LIF equation:
///
/// ```text
/// τ_m · dV/dt = -(V - V_rest) + R · I_syn(t)
/// ```
///
/// When `V > θ`, the neuron fires and `V` is reset to `V_reset`. A
/// refractory period of `τ_refrac` follows, during which the neuron
/// is insensitive to input.
pub struct LeakyIntegrateAndFire {
    /// Static parameters.
    pub params: LifParams,
    /// Current membrane potential, in mV.
    pub v_m: f32,
    /// Time since last spike, in ms. Used to enforce refractory period.
    pub t_since_last_spike: f32,
}

impl LeakyIntegrateAndFire {
    /// Construct a new LIF neuron with the given parameters.
    pub fn new(params: LifParams) -> Self {
        Self {
            params,
            v_m: params.v_rest,
            t_since_last_spike: f32::INFINITY,
        }
    }

    /// Construct a default LIF neuron (Kenyon cell parameters).
    pub fn kenyon_cell() -> Self {
        Self::new(LifParams::default())
    }

    /// Step the neuron forward by `dt` ms, given a list of incoming spikes.
    ///
    /// Each spike contributes a current pulse weighted by `spike.weight`.
    /// This is the biological EPSP/IPSP — the post-synaptic potential.
    pub fn step(&mut self, dt: f32, inputs: &[Spike]) -> StepResult {
        // Enforce refractory period — mimics the sodium-channel
        // inactivation that prevents a neuron from refiring immediately.
        if self.t_since_last_spike < self.params.tau_refrac {
            self.t_since_last_spike += dt;
            return StepResult::Silent;
        }

        // Sum the incoming synaptic currents.
        // This mimics the summation of EPSPs and IPSPs at the axon hillock.
        let i_syn: f32 = inputs.iter().map(|s| s.weight.to_f32()).sum();

        // Leaky integration — the membrane decays toward rest.
        // dv/dt = -(v - v_rest) / tau_m + i_syn / tau_m
        let decay = (-dt / self.params.tau_m).exp();
        self.v_m = self.v_m * decay
            + self.params.v_rest * (1.0 - decay)
            + i_syn * 10.0;  // Scale factor — mimics input resistance.

        // Threshold check.
        if self.v_m > self.params.theta {
            // Spike! Reset the membrane potential (afterhyperpolarization).
            self.v_m = self.params.v_reset;
            self.t_since_last_spike = 0.0;
            StepResult::Fired
        } else {
            self.t_since_last_spike += dt;
            StepResult::Silent
        }
    }
}

/// The trait that all neuron models must implement.
pub trait NeuronModel: Send + Sync {
    /// Update membrane potential given incoming spikes.
    fn step(&mut self, dt: f32, inputs: &[Spike]) -> StepResult;

    /// Return current membrane potential (in mV, biological scale).
    fn potential(&self) -> f32;
}

impl NeuronModel for LeakyIntegrateAndFire {
    fn step(&mut self, dt: f32, inputs: &[Spike]) -> StepResult {
        self.step(dt, inputs)
    }

    fn potential(&self) -> f32 {
        self.v_m
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use half::f16;

    /// A LIF neuron should fire when given sufficient excitatory input.
    ///
    /// This mimics the basic physiology: a Kenyon cell fires when its
    /// membrane is depolarized past threshold by summed EPSPs.
    #[test]
    fn test_lif_fires_on_strong_input() {
        let mut n = LeakyIntegrateAndFire::kenyon_cell();
        let spikes = vec![
            Spike { src_neuron_id: 0, timestamp: 0, weight: f16::from_f32(2.0), plasticity_id: 0 },
            Spike { src_neuron_id: 1, timestamp: 0, weight: f16::from_f32(2.0), plasticity_id: 0 },
            Spike { src_neuron_id: 2, timestamp: 0, weight: f16::from_f32(2.0), plasticity_id: 0 },
        ];
        let result = n.step(1.0, &spikes);
        assert!(matches!(result, StepResult::Fired));
    }

    /// A LIF neuron should not fire during its refractory period.
    #[test]
    fn test_lif_refractory_period() {
        let mut n = LeakyIntegrateAndFire::kenyon_cell();
        let strong_input = vec![
            Spike { src_neuron_id: 0, timestamp: 0, weight: f16::from_f32(3.0), plasticity_id: 0 },
        ];
        // First step: should fire.
        assert!(matches!(n.step(1.0, &strong_input), StepResult::Fired));
        // Second step (immediately after): refractory, should not fire.
        assert!(matches!(n.step(1.0, &strong_input), StepResult::Silent));
    }

    /// A LIF neuron should leak toward rest in the absence of input.
    #[test]
    fn test_lif_leak_to_rest() {
        let mut n = LeakyIntegrateAndFire::kenyon_cell();
        n.v_m = -50.0;  // Above rest, below threshold.
        for _ in 0..100 {
            n.step(1.0, &[]);
        }
        // Should have decayed back to near-rest.
        assert!((n.v_m - (-70.0)).abs() < 1.0);
    }
}
