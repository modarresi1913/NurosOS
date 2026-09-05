//! # Neuron models.
//!
//! Implements biologically-detailed spiking neuron models. The kernel
//! invokes these on every SPP tick for every active neuron.

use half::f16;

/// The result of one `step()` call on a neuron model.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StepResult {
    /// The neuron did not fire.
    Silent,
    /// The neuron fired (emitted a spike).
    Fired,
}

/// Parameters for the Leaky Integrate-and-Fire model.
#[derive(Clone, Copy, Debug)]
pub struct LifParams {
    /// Membrane time constant, in ms. Default: 18 ms (Kenyon cell).
    pub tau_m: f32,
    /// Spike threshold, in mV. Default: -55 mV.
    pub theta: f32,
    /// Resting potential, in mV. Default: -70 mV.
    pub v_rest: f32,
    /// Reset potential, in mV. Default: -80 mV (afterhyperpolarization).
    pub v_reset: f32,
    /// Refractory period, in ms. Default: 2 ms.
    pub tau_refrac: f32,
}

impl Default for LifParams {
    fn default() -> Self {
        Self {
            tau_m: 18.0,
            theta: -55.0,
            v_rest: -70.0,
            v_reset: -80.0,
            tau_refrac: 2.0,
        }
    }
}

/// A spike event — the atomic unit of inter-neuron communication.
#[derive(Clone, Copy, Debug)]
pub struct Spike {
    /// Source neuron ID.
    pub src: u32,
    /// Synaptic weight.
    pub weight: f16,
    /// Tick at which the spike was emitted.
    pub timestamp: u32,
}

/// The Leaky Integrate-and-Fire neuron model.
///
/// Implements:
/// ```text
/// τ_m · dV/dt = -(V - V_rest) + R · I_syn(t)
/// ```
/// When `V > θ`, fire and reset to `V_reset`.
pub struct LeakyIntegrateAndFire {
    /// Static parameters.
    pub params: LifParams,
    /// Current membrane potential (mV).
    pub v_m: f32,
    /// Time since last spike (ms).
    pub t_since_last_spike: f32,
}

impl LeakyIntegrateAndFire {
    /// Construct with the given parameters, starting at rest.
    pub fn new(params: LifParams) -> Self {
        Self { params, v_m: params.v_rest, t_since_last_spike: f32::INFINITY }
    }

    /// Construct with default Kenyon-cell parameters.
    pub fn kenyon_cell() -> Self { Self::new(LifParams::default()) }
}

/// The trait that all neuron models implement.
pub trait NeuronModel: Send + Sync {
    /// Step the model forward by `dt` ms.
    fn step(&mut self, dt: f32, inputs: &[Spike]) -> StepResult;
    /// Current membrane potential (mV).
    fn potential(&self) -> f32;
}

impl NeuronModel for LeakyIntegrateAndFire {
    fn step(&mut self, dt: f32, inputs: &[Spike]) -> StepResult {
        // Refractory period — mimics Na⁺ channel inactivation.
        if self.t_since_last_spike < self.params.tau_refrac {
            self.t_since_last_spike += dt;
            return StepResult::Silent;
        }

        // Sum EPSPs and IPSPs at the axon hillock.
        let i_syn: f32 = inputs.iter().map(|s| s.weight.to_f32()).sum();

        // Leaky integration toward rest.
        let decay = (-dt / self.params.tau_m).exp();
        self.v_m = self.v_m * decay
            + self.params.v_rest * (1.0 - decay)
            + i_syn * 10.0;

        if self.v_m > self.params.theta {
            self.v_m = self.params.v_reset;
            self.t_since_last_spike = 0.0;
            StepResult::Fired
        } else {
            self.t_since_last_spike += dt;
            StepResult::Silent
        }
    }

    fn potential(&self) -> f32 { self.v_m }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lif_fires_on_strong_input() {
        let mut n = LeakyIntegrateAndFire::kenyon_cell();
        let spikes = vec![
            Spike { src: 0, weight: f16::from_f32(2.0), timestamp: 0 },
            Spike { src: 1, weight: f16::from_f32(2.0), timestamp: 0 },
        ];
        assert_eq!(n.step(1.0, &spikes), StepResult::Fired);
    }

    #[test]
    fn test_lif_leaks_to_rest() {
        let mut n = LeakyIntegrateAndFire::kenyon_cell();
        n.v_m = -50.0;
        for _ in 0..200 { n.step(1.0, &[]); }
        assert!((n.v_m - (-70.0)).abs() < 1.0);
    }
}
