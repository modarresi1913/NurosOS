//! # NurosOS HAL interface types.
//!
//! This crate holds the `NeuromorphicTarget` trait and its parameter
//! types. It exists as a separate crate so that driver crates can
//! implement the trait without depending on `nuros-hal`, which
//! re-exports the drivers (a dependency cycle would otherwise result).

#![deny(missing_docs)]

/// A globally-unique neuron identifier (re-exported from the kernel).
pub type NeuronId = u32;

/// A neuromorphic hardware target.
///
/// Every backend (x86, ARM, Loihi, FPGA) implements this trait. The
/// kernel interacts with hardware *only* through this trait.
pub trait NeuromorphicTarget: Send + Sync {
    /// Human-readable name (e.g., "x86_64 emulation", "Intel Loihi 2").
    fn name(&self) -> &str;

    /// Allocate a neuron with the given parameters.
    ///
    /// Returns the neuron's ID. This ID is stable for the lifetime of
    /// the kernel (a neuron is never deleted — only lesioned, in which
    /// case `remap()` is called).
    fn alloc_neuron(&mut self, params: &NeuronParams) -> NeuronId;

    /// Allocate a synapse between two neurons.
    fn alloc_synapse(&mut self, src: NeuronId, dst: NeuronId, weight: half::f16) -> u64;

    /// Fire a neuron at the given tick.
    fn fire(&mut self, n: NeuronId, t: u64);

    /// Read a neuron's current membrane potential (in mV).
    fn read_potential(&self, n: NeuronId) -> f32;

    /// Dynamic remapping — neuroplasticity emulation.
    ///
    /// When a physical core fails (a "lesion"), the HAL selects a
    /// neighboring neuron with the most similar connectivity profile,
    /// copies the failed neuron's weights to the substitute, and
    /// updates the routing table.
    ///
    /// This mimics biological **compensatory sprouting**.
    fn remap(&mut self, failed: NeuronId) -> NeuronId;

    /// Report energy consumed since the last reset (in joules).
    fn energy_report(&self) -> f64;
}

/// Generic neuron parameter bundle.
#[derive(Clone, Copy, Debug, Default)]
pub struct NeuronParams {
    /// Membrane time constant (ms).
    pub tau_m: f32,
    /// Spike threshold (mV).
    pub theta: f32,
    /// Resting potential (mV).
    pub v_rest: f32,
    /// Reset potential (mV).
    pub v_reset: f32,
    /// Refractory period (ms).
    pub tau_refrac: f32,
}
