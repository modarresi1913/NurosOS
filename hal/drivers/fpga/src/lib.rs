//! # Custom FPGA HAL driver.
//!
//! Targets custom FPGA arrays (Xilinx Versal, Intel Stratix). Used
//! when neither x86 emulation nor Loihi is suitable — e.g., for
//! research groups that have built their own neuromorphic boards.
//!
//! ## Biological correspondence
//!
//! An FPGA is the equivalent of a **cultured organoid** — a custom-grown
//! piece of neural tissue that does not match any naturally-occurring
//! brain but is useful for controlled experiments.
//!
//! ## Status
//!
//! v0.1.0: stub. Real FPGA integration is scheduled for v0.3.0+.

use nuros_hal::{NeuronId, NeuronParams, NeuromorphicTarget};

pub struct FpgaTarget {
    neuron_count: usize,
    energy: f64,
}

impl FpgaTarget {
    pub fn new() -> Self {
        Self { neuron_count: 0, energy: 0.0 }
    }
}

impl Default for FpgaTarget {
    fn default() -> Self { Self::new() }
}

impl NeuromorphicTarget for FpgaTarget {
    fn name(&self) -> &str { "FPGA (v0.3.0 stub)" }

    fn alloc_neuron(&mut self, _: &NeuronParams) -> NeuronId {
        let id = self.neuron_count as NeuronId;
        self.neuron_count += 1;
        id
    }

    fn alloc_synapse(&mut self, _: NeuronId, _: NeuronId, _: half::f16) -> u64 { 0 }
    fn fire(&mut self, _: NeuronId, _: u64) { self.energy += 1e-11; }
    fn read_potential(&self, _: NeuronId) -> f32 { -70.0 }
    fn remap(&mut self, failed: NeuronId) -> NeuronId { (failed + 1) % self.neuron_count.max(1) as NeuronId }
    fn energy_report(&self) -> f64 { self.energy }
}
