//! # Region Graph — Topological Grouping of Neurons
//!
//! A `Region` is a cluster of neurons that form a biological neuropil
//! (e.g., the antennal lobe, mushroom body, central complex). The
//! `RegionGraph` holds the static wiring diagram + region membership.
//!
//! ## Biological correspondence
//!
//! *Drosophila* has ~40 identified neuropils. The major ones relevant
//! to NurosOS:
//!
//! | Region           | Function                                  | Neurons |
//! |------------------|-------------------------------------------|---------|
//! | Antennal lobe    | First olfactory relay (analog of olf. bulb) | ~200  |
//! | Mushroom body    | Associative memory, learning              | ~2,500  |
//! | Lateral horn     | Innate odor responses (innate valence)    | ~1,400  |
//! | Central complex  | Navigation, head-direction, spatial memory| ~3,000  |
//! | Ventral nerve cord | Motor pattern generation (locomotion)   | ~10,000 |
//!
//! Regions are critical for the Sparse Propagation Protocol — SPP
//! enforces the 5% sparsity cap *per region*, not globally, so that
//! small regions are not starved by large ones.

use std::collections::HashMap;

use crate::connectome::Connectome;
use crate::neuron::NeuronId;
use crate::synapse::Synapse;

/// A topologically-bounded cluster of neurons.
#[derive(Clone, Debug)]
pub struct Region {
    /// Human-readable name (e.g., "mushroom_body").
    pub name: String,
    /// Neuron IDs belonging to this region.
    pub neurons: Vec<NeuronId>,
    /// Outgoing inter-region synapses.
    ///
    /// Intra-region synapses are stored separately (in `RegionGraph::intra`).
    pub outgoing: Vec<Synapse>,
}

/// The global region graph.
///
/// Owns the full wiring diagram. The scheduler borrows this immutably
/// for the lifetime of the kernel.
pub struct RegionGraph {
    /// All regions, indexed by region ID.
    pub regions: Vec<Region>,
    /// Lookup: neuron ID → region ID.
    pub neuron_to_region: HashMap<NeuronId, usize>,
    /// All synapses in the system (both intra- and inter-region).
    /// Indexed by synapse ID (implicit: position in this Vec).
    pub all_synapses: Vec<Synapse>,
    /// For each neuron, the list of outgoing synapse IDs.
    pub outgoing_index: Vec<Vec<usize>>,
}

impl RegionGraph {
    /// Build a region graph from a loaded connectome.
    pub fn from_connectome(c: &Connectome) -> anyhow::Result<Self> {
        let mut regions: Vec<Region> = c
            .region_names()
            .iter()
            .map(|name| Region {
                name: name.clone(),
                neurons: Vec::new(),
                outgoing: Vec::new(),
            })
            .collect();

        let mut neuron_to_region = HashMap::new();
        for (neuron_id, region_id) in c.neuron_region_assignments() {
            regions[region_id].neurons.push(NeuronId(neuron_id));
            neuron_to_region.insert(NeuronId(neuron_id), region_id);
        }

        let mut all_synapses = Vec::with_capacity(c.synapse_count());
        let mut outgoing_index: Vec<Vec<usize>> = vec![Vec::new(); c.neuron_count()];

        for syn in c.synapses() {
            let id = all_synapses.len();
            all_synapses.push(syn);
            outgoing_index[syn.source.0].push(id);
            // Also add to the source region's outgoing list if the
            // target is in a different region (inter-region projection).
            if let (Some(src_r), Some(dst_r)) = (
                neuron_to_region.get(&syn.source),
                neuron_to_region.get(&syn.target),
            ) {
                if src_r != dst_r {
                    regions[*src_r].outgoing.push(syn);
                }
            }
        }

        Ok(Self {
            regions,
            neuron_to_region,
            all_synapses,
            outgoing_index,
        })
    }

    /// Iterate over the outgoing synapses of a neuron.
    pub fn outgoing(&self, n: NeuronId) -> impl Iterator<Item = Synapse> + '_ {
        self.outgoing_index
            .get(n.0)
            .into_iter()
            .flatten()
            .map(move |&i| self.all_synapses[i])
    }

    /// Total number of neurons in the system.
    pub fn total_neuron_count(&self) -> usize {
        self.outgoing_index.len()
    }

    /// Number of regions.
    pub fn region_count(&self) -> usize {
        self.regions.len()
    }
}
