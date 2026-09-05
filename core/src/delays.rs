//! # Axonal delay modeling.
//!
//! Biological neurons do not communicate instantaneously — action
//! potentials travel down axons at 0.1–100 m/s, introducing delays of
//! 0.1–10 ms. This module models those delays.
//!
//! ## Biological correspondence
//!
//! Axonal delay is not a bug — it is a feature. The brain uses delays
//! for temporal processing: sound localization in the barn owl, for
//! example, relies on sub-millisecond inter-aural time differences.
//! In *Drosophila*, delays in the courtship song circuit produce the
//! species-specific pulse rhythm.

/// A simple delay-line buffer.
///
/// Holds spikes for `delay_ticks` ticks before releasing them.
/// This mimics the axonal propagation delay.
pub struct DelayLine {
    /// Per-tick buffer of spikes.
    buffer: Vec<Vec<u32>>,
    /// Index of the current tick (mod buffer.len()).
    head: usize,
    /// Delay in ticks.
    delay_ticks: usize,
}

impl DelayLine {
    /// Construct a new delay line with the given delay (in ticks).
    pub fn new(delay_ticks: usize) -> Self {
        Self {
            buffer: vec![Vec::new(); delay_ticks.max(1)],
            head: 0,
            delay_ticks: delay_ticks.max(1),
        }
    }

    /// Push a spike into the delay line.
    pub fn push(&mut self, spike_src: u32) {
        self.buffer[self.head].push(spike_src);
    }

    /// Advance one tick and return the spikes that have finished delaying.
    pub fn tick(&mut self) -> Vec<u32> {
        self.head = (self.head + 1) % self.delay_ticks;
        std::mem::take(&mut self.buffer[self.head])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_delay_line_holds_spikes() {
        let mut dl = DelayLine::new(3);
        dl.push(42);
        // Should not appear before 3 ticks.
        assert!(dl.tick().is_empty());
        assert!(dl.tick().is_empty());
        let out = dl.tick();
        assert_eq!(out, vec![42]);
    }
}
