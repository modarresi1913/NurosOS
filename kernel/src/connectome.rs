//! # Connectome Loader
//!
//! This module loads the *Drosophila* connectome dataset (FlyWire .h5
//! format) into memory. The loaded data is then handed to
//! `RegionGraph::from_connectome()` to build the runtime wiring diagram.
//!
//! ## Biological correspondence
//!
//! This is the software equivalent of **neurogenesis** — the process
//! by which neurons are born, extend axons and dendrites, and form
//! synaptic connections. In *Drosophila* this happens during pupal
//! development (~100 hours). In NurosOS it happens once, at boot.
//!
//! ## Dataset format
//!
//! The .h5 file contains three datasets:
//!
//! - `neurons/`     — neuron metadata (ID, type, region)
//! - `synapses/`    — synaptic connections (pre, post, weight, neurotransmitter)
//! - `regions/`     — region metadata (name, neuron count, function)
//!
//! For v0.1.0 we support a *mini* version of the dataset (125M synapses
//! compressed to ~2 GB). The full dataset (~500 GB) will be supported
//! in v0.3.0 via memory-mapped access.

use std::path::Path;

use crate::neuron::NeuronId;
use crate::synapse::{Neurotransmitter, Synapse};

/// A loaded connectome.
///
/// Owns the neuron/synapse/region tables in memory. This is a large
/// structure (~10 GB when fully loaded) — once it is handed to
/// `RegionGraph::from_connectome()`, the graph takes ownership and
/// this struct can be dropped.
pub struct Connectome {
    /// Neuron → region assignment.
    neuron_regions: Vec<usize>,
    /// Region names, indexed by region ID.
    region_names: Vec<String>,
    /// All synapses.
    synapses: Vec<Synapse>,
}

impl Connectome {
    /// Load a connectome from a .h5 file.
    ///
    /// In v0.1.0 this is a stub that returns synthetic data — the
    /// actual HDF5 parsing is implemented in v0.2.0. The synthetic
    /// data is enough to boot the kernel and run the Fly Benchmark
    /// smoke tests.
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        if !path.exists() {
            log::warn!("Connectome file not found at {}; using synthetic data", path.display());
            return Self::synthetic();
        }

        // TODO(v0.2.0): real HDF5 parsing.
        log::info!("Loading connectome from {} (HDF5 parsing not yet implemented)", path.display());
        Self::synthetic()
    }

    /// Generate a small synthetic connectome for testing.
    ///
    /// Mimics the topology (not the scale) of the *Drosophila* brain:
    /// 3 regions (antennal lobe, mushroom body, lateral horn),
    /// 100 neurons, 1000 synapses.
    fn synthetic() -> anyhow::Result<Self> {
        let region_names = vec![
            "antennal_lobe".to_string(),
            "mushroom_body".to_string(),
            "lateral_horn".to_string(),
        ];

        // 100 neurons, distributed across the 3 regions.
        let mut neuron_regions = Vec::with_capacity(100);
        for i in 0..100 {
            let region = match i {
                0..=19   => 0,  // Antennal lobe (sensory)
                20..=69  => 1,  // Mushroom body (memory)
                _        => 2,  // Lateral horn (innate)
            };
            neuron_regions.push(region);
        }

        // 1000 synapses with random (deterministic) connectivity.
        // Mimics sparse connectivity: ~1% of possible connections.
        let mut synapses = Vec::with_capacity(1000);
        let mut rng_state: u32 = 42;
        for _ in 0..1000 {
            // Simple LCG for reproducibility.
            rng_state = rng_state.wrapping_mul(1103515245).wrapping_add(12345);
            let src = (rng_state >> 16) as usize % 100;
            rng_state = rng_state.wrapping_mul(1103515245).wrapping_add(12345);
            let dst = (rng_state >> 16) as usize % 100;

            let nt = if src < 20 { Neurotransmitter::Acetylcholine }
                     else if src < 70 { Neurotransmitter::Glutamate }
                     else { Neurotransmitter::Gaba };

            synapses.push(Synapse {
                source: NeuronId(src),
                target: NeuronId(dst),
                weight: half::f16::from_f32(0.5),
                neurotransmitter: nt,
                plasticity_id: 1,  // Hebbian by default.
                delay_ticks: 1,
            });
        }

        Ok(Self { neuron_regions, region_names, synapses })
    }

    /// Number of neurons in the connectome.
    pub fn neuron_count(&self) -> usize { self.neuron_regions.len() }

    /// Number of synapses in the connectome.
    pub fn synapse_count(&self) -> usize { self.synapses.len() }

    /// Region names.
    pub fn region_names(&self) -> &[String] { &self.region_names }

    /// Neuron → region assignments (as (neuron_id, region_id) pairs).
    pub fn neuron_region_assignments(&self) -> impl Iterator<Item = (usize, usize)> + '_ {
        self.neuron_regions.iter().enumerate().map(|(n, r)| (n, *r))
    }

    /// Iterator over synapses.
    pub fn synapses(&self) -> &[Synapse] { &self.synapses }
}
