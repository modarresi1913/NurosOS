//! # ARM HAL driver.
//!
//! Targets ARM Cortex-M microcontrollers (embedded) and ARM Neoverse
//! (edge servers). Useful for IoT-scale NurosOS deployments.
//!
//! ## Biological correspondence
//!
//! An ARM Cortex-M is the equivalent of a **small ganglion** — a
//! compact, low-power processing node that handles local reflexes
//! without consulting the full brain.

use nuros_hal::{NeuronId, NeuronParams, NeuromorphicTarget};

pub struct ArmTarget {
    neuron_count: usize,
    energy: f64,
}

impl ArmTarget {
    pub fn new() -> Self {
        Self { neuron_count: 0, energy: 0.0 }
    }
}

impl Default for ArmTarget {
    fn default() -> Self { Self::new() }
}

impl NeuromorphicTarget for ArmTarget {
    fn name(&self) -> &str { "ARM Cortex-M (v0.1.0 stub)" }

    fn alloc_neuron(&mut self, _: &NeuronParams) -> NeuronId {
        let id = self.neuron_count as NeuronId;
        self.neuron_count += 1;
        id
    }

    fn alloc_synapse(&mut self, _: NeuronId, _: NeuronId, _: half::f16) -> u64 { 0 }
    fn fire(&mut self, _: NeuronId, _: u64) { self.energy += 5e-10; }
    fn read_potential(&self, _: NeuronId) -> f32 { -70.0 }
    fn remap(&mut self, failed: NeuronId) -> NeuronId { (failed + 1) % self.neuron_count.max(1) as NeuronId }
    fn energy_report(&self) -> f64 { self.energy }
}
