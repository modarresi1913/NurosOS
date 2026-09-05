//! # Synapse Types & Plasticity Rules
//!
//! This module defines the data structures used to represent synapses
//! in the kernel. The actual plasticity *algorithms* (STDP, Hebbian,
//! dopamine-modulated) live in `core/src/plasticity.rs`.
//!
//! ## Biological correspondence
//!
//! A biological synapse is a physical contact between two neurons. It
//! has:
//!
//! - A **pre-synaptic terminal** (the axon of the source neuron).
//! - A **post-synaptic density** (a dendritic spine on the target neuron).
//! - A **weight** — the strength of the connection, determined by the
//!   number of vesicles released per spike and the number of receptors
//!   on the post-synaptic side.
//! - A **neurotransmitter identity** — glutamate (excitatory), GABA
//!   (inhibitory), acetylcholine, dopamine, serotonin, etc.
//! - A **plasticity rule** — how the weight changes as a function of
//!   pre/post-synaptic activity (Hebbian, STDP, neuromodulated).

use half::f16;

/// A spike event traveling between two neurons.
///
/// This is the atomic unit of communication in NurosOS. It is small
/// (12 bytes) so that it fits in a single cache line alongside its
/// `SpikeHeader` (see `ipc.rs`).
#[derive(Clone, Copy, Debug)]
pub struct Spike {
    /// The emitting neuron's ID.
    pub src_neuron_id: u32,
    /// The tick at which the spike was emitted.
    pub timestamp: u32,
    /// Synaptic efficacy. Positive = excitatory, negative = inhibitory.
    /// Stored as `f16` for Loihi hardware compatibility.
    pub weight: f16,
    /// Index into the scheduler's plasticity-rule table.
    pub plasticity_id: u16,
}

/// A static synapse description (used during connectome loading).
#[derive(Clone, Copy, Debug)]
pub struct Synapse {
    /// Source neuron.
    pub source: crate::neuron::NeuronId,
    /// Target neuron.
    pub target: crate::neuron::NeuronId,
    /// Synaptic weight.
    pub weight: f16,
    /// Neurotransmitter identity.
    pub neurotransmitter: Neurotransmitter,
    /// Index into the plasticity-rule table.
    pub plasticity_id: u16,
    /// Biological synaptic delay, in ticks.
    pub delay_ticks: u32,
}

/// The neurotransmitter identity of a synapse.
///
/// This determines whether the synapse is excitatory or inhibitory,
/// and (in future versions) which plasticity rules are available.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Neurotransmitter {
    /// Glutamate — the primary excitatory neurotransmitter in the
    /// *Drosophila* CNS. Mimics AMPA/NMDA receptor activation.
    Glutamate,
    /// GABA — the primary inhibitory neurotransmitter. Mimics GABA-A
    /// (fast) and GABA-B (slow) receptor activation.
    Gaba,
    /// Acetylcholine — excitatory, used at the neuromuscular junction
    /// and in some central synapses.
    Acetylcholine,
    /// Dopamine — modulatory. Carries reward/aversion signals to the
    /// mushroom body, driving reinforcement learning.
    Dopamine,
    /// Serotonin — modulatory. Affects arousal, mood, and aggressive
    /// behavior in *Drosophila*.
    Serotonin,
    /// Octopamine — the invertebrate analog of noradrenaline. Drives
    /// the "fight or flight" response during stress.
    Octopamine,
}

impl Neurotransmitter {
    /// Returns `true` if this neurotransmitter is excitatory.
    pub fn is_excitatory(&self) -> bool {
        matches!(self, Self::Glutamate | Self::Acetylcholine)
    }

    /// Returns `true` if this neurotransmitter is inhibitory.
    pub fn is_inhibitory(&self) -> bool {
        matches!(self, Self::Gaba)
    }

    /// Returns `true` if this neurotransmitter is modulatory
    /// (i.e., it adjusts synaptic weights rather than carrying
    /// direct excitation/inhibition).
    pub fn is_modulatory(&self) -> bool {
        matches!(self, Self::Dopamine | Self::Serotonin | Self::Octopamine)
    }
}

/// A plasticity rule — how a synapse's weight changes over time.
///
/// The full algorithm implementations live in `core/src/plasticity.rs`.
/// This enum is just a tag carried by each synapse so the scheduler
/// knows which algorithm to invoke when a plasticity event fires.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PlasticityRule {
    /// No plasticity — the weight is fixed. Used for sensory afferents
    /// and other "hard-wired" connections.
    None,
    /// Hebbian: "cells that fire together wire together."
    /// Δw = η · pre · post
    Hebbian { learning_rate: f32 },
    /// Spike-Timing-Dependent Plasticity.
    /// Δw depends on the relative timing of pre- and post-synaptic spikes.
    /// Pre-before-post → potentiation; post-before-pre → depression.
    ///
    /// This is the dominant plasticity model in *Drosophila* and is
    /// believed to underlie associative learning in the mushroom body.
    Stdp {
        /// Learning rate for potentiation (LTP).
        eta_plus: f32,
        /// Learning rate for depression (LTD).
        eta_minus: f32,
        /// Time window for potentiation, in ms.
        tau_plus: f32,
        /// Time window for depression, in ms.
        tau_minus: f32,
    },
    /// Dopamine-modulated plasticity.
    ///
    /// Mimics the reward signal delivered to the mushroom body by
    /// dopaminergic PAM neurons during appetitive conditioning.
    DopamineModulated {
        /// Base learning rate.
        eta: f32,
        /// Dopamine concentration (0 = none, 1 = saturating).
        dopamine: f32,
    },
}

impl PlasticityRule {
    /// The default plasticity-rule table.
    ///
    /// Indexed by `plasticity_id` in `SpikeHeader`. The first entry
    /// (id 0) is always `None` — synapses with no plasticity rule.
    pub fn default_table() -> Vec<Self> {
        vec![
            Self::None,
            Self::Hebbian { learning_rate: 0.01 },
            Self::Stdp {
                eta_plus: 0.01,
                eta_minus: 0.01,
                tau_plus: 20.0,
                tau_minus: 20.0,
            },
            Self::DopamineModulated { eta: 0.02, dopamine: 0.0 },
        ]
    }
}
