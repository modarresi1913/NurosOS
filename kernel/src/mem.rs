//! # Associative Memory Store (AMS)
//!
//! NurosOS has no filesystem. Instead, it exposes an Associative Memory
//! Store that retrieves data by *stimulus* rather than by path.
//!
//! ## Biological correspondence
//!
//! This is the software analog of the **mushroom body** in *Drosophila* —
//! a sparse, high-dimensional memory system where odors (and other stimuli)
//! are encoded as distributed patterns of Kenyon cell activity. Retrieval
//! is content-addressed: a partial cue reactivates the full stored pattern
//! via attractor dynamics.
//!
//! The classic experiment: a fly is trained to avoid a specific odor
//! paired with electric shock. The memory trace lives in the synaptic
//! weights between Kenyon cells and mushroom body output neurons (MBONs).
//! The fly can later retrieve this memory from a *partial* odor cue —
//! content-addressed recall.
//!
//! ## API
//!
//! ```ignore
//! AMS.store(stimulus: Tensor, payload: Bytes) -> Handle;
//! AMS.query(partial_stimulus: Tensor, k: usize) -> Vec<(Handle, f32)>;
//! AMS.reinforce(handle: Handle, reward: f32);   // Hebbian update
//! ```

use std::collections::HashMap;
use std::sync::RwLock;

/// An opaque handle to a stored memory.
///
/// This is the AMS equivalent of a file descriptor. It is meaningless
/// outside the AMS — there is no global namespace.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Handle(pub u64);

/// A stored memory entry.
struct Entry {
    /// The original stimulus tensor (a sparse, distributed pattern).
    stimulus: Vec<f32>,
    /// The associated payload (opaque bytes).
    payload: Vec<u8>,
    /// Reinforcement score — incremented by `reinforce()`.
    /// Mimics the dopamine-modulated plasticity at the KC→MBON synapse.
    reinforcement: f32,
}

/// The Associative Memory Store.
///
/// Backed by a `HashMap` for v0.1.0. In v0.2.0 this will be replaced
/// by a Hopfield-like attractor network with sparse connectivity (see
/// `ARCHITECTURE.md` §5).
pub struct Ams {
    /// The internal store.
    inner: RwLock<HashMap<Handle, Entry>>,
    /// Monotonic counter for generating handles.
    next_handle: std::sync::atomic::AtomicU64,
}

impl Ams {
    /// Construct a new, empty AMS.
    pub fn new() -> Self {
        Self {
            inner: RwLock::new(HashMap::new()),
            next_handle: std::sync::atomic::AtomicU64::new(1),
        }
    }

    /// Store a (stimulus, payload) pair.
    ///
    /// Mimics the consolidation of a memory trace in the mushroom body:
    /// a sparse pattern of KC activity becomes associated with a
    /// valence-labeled output (e.g., "approach" or "avoid").
    pub fn store(&self, stimulus: Vec<f32>, payload: Vec<u8>) -> Handle {
        let h = Handle(self.next_handle.fetch_add(1, std::sync::atomic::Ordering::Relaxed));
        let mut w = self.inner.write().expect("AMS poisoned");
        w.insert(h, Entry {
            stimulus,
            payload,
            reinforcement: 0.0,
        });
        h
    }

    /// Query the AMS for the k nearest neighbors of `partial_stimulus`.
    ///
    /// This is the biological "pattern completion" — given a degraded
    /// or partial cue, the system retrieves the most similar stored
    /// memory. The similarity metric is cosine similarity, which matches
    /// the sparse, high-dimensional coding of Kenyon cells (where the
    /// angle between population vectors carries the odor identity).
    pub fn query(&self, partial_stimulus: &[f32], k: usize) -> Vec<(Handle, f32)> {
        let r = self.inner.read().expect("AMS poisoned");
        let mut scored: Vec<(Handle, f32)> = r
            .iter()
            .map(|(h, e)| (*h, cosine_similarity(&e.stimulus, partial_stimulus)))
            .collect();
        scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(k);
        scored
    }

    /// Retrieve a payload by handle (after `query`).
    ///
    /// This is the equivalent of `read()` — but the handle must have
    /// been obtained via content-addressed lookup, not by path.
    pub fn read(&self, h: Handle) -> Option<Vec<u8>> {
        let r = self.inner.read().expect("AMS poisoned");
        r.get(&h).map(|e| e.payload.clone())
    }

    /// Reinforce a stored memory (Hebbian update).
    ///
    /// Mimics dopamine-modulated plasticity at the KC→MBON synapse:
    /// a reward signal strengthens the association between the stimulus
    /// and the valence of the output. This is how the fly learns to
    /// "approach" or "avoid" an odor after paired shock/sugar training.
    pub fn reinforce(&self, h: Handle, reward: f32) {
        let mut w = self.inner.write().expect("AMS poisoned");
        if let Some(e) = w.get_mut(&h) {
            e.reinforcement += reward;
        }
    }
}

impl Default for Ams {
    fn default() -> Self { Self::new() }
}

/// Cosine similarity between two vectors.
///
/// Matches the sparse population-code metric used in *Drosophila*
/// olfactory coding studies (where the angle between KC activity
/// vectors encodes odor identity).
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let n = a.len().min(b.len());
    let mut dot = 0.0;
    let mut na = 0.0;
    let mut nb = 0.0;
    for i in 0..n {
        dot += a[i] * b[i];
        na += a[i] * a[i];
        nb += b[i] * b[i];
    }
    if na == 0.0 || nb == 0.0 {
        return 0.0;
    }
    dot / (na.sqrt() * nb.sqrt())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Mimics odor memory consolidation and recall in the mushroom body.
    #[test]
    fn test_store_and_query() {
        let ams = Ams::new();

        // Store two odors as sparse population vectors.
        let odor_a = vec![0.0, 1.0, 0.0, 1.0, 0.0, 1.0];
        let odor_b = vec![1.0, 0.0, 1.0, 0.0, 1.0, 0.0];
        let h_a = ams.store(odor_a.clone(), b"approach".to_vec());
        let h_b = ams.store(odor_b.clone(), b"avoid".to_vec());

        // Query with a partial cue (3 of 6 dimensions).
        let cue = vec![0.0, 1.0, 0.0, 1.0, 0.0, 0.0];
        let hits = ams.query(&cue, 2);
        assert_eq!(hits[0].0, h_a, "partial cue should retrieve odor A first");
        assert!(hits[0].1 > 0.9);

        // Read back the payload.
        let payload = ams.read(h_a).expect("handle should resolve");
        assert_eq!(payload, b"approach");

        // Reinforce B (paired with shock).
        ams.reinforce(h_b, -1.0);
    }
}
