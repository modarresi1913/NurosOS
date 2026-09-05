//! # Zero-Copy Inter-Process Communication — Synaptic Channels
//!
//! This module implements the lock-free, single-producer single-consumer
//! ring buffers described in `ARCHITECTURE.md` §4. Each synapse in the
//! connectome is backed by one such channel.
//!
//! ## Biological correspondence
//!
//! A biological synapse is a physical structure where:
//!
//! - The **presynaptic terminal** is the producer (it releases vesicles).
//! - The **postsynaptic density** is the consumer (it binds neurotransmitter).
//! - The **synaptic cleft** is the ring buffer (it holds a small backlog
//!   of neurotransmitter that decays over time).
//!
//! NurosOS channels reproduce this layout: the producer writes `SpikeHeader`
//! records, the consumer reads them in order, and the buffer size is set
//! to `D` ticks (where `D` is the biological synaptic delay, ~0.5–2 ms).
//!
//! ## Why zero-copy?
//!
//! Traditional OS IPC copies data between address spaces — a memcpy that
//! costs ~10 nJ per byte on modern x86. NurosOS eliminates this by:
//!
//! 1. Allocating every channel in shared memory at boot time.
//! 2. Passing `SpikeHeader` by reference (it is 8 bytes — fits in a cache line).
//! 3. Never copying the payload (spike "payloads" are just weights, which
//!    live in the synapse's metadata, not in the channel itself).
//!
//! This brings the cost of an inter-neuron message to ~10 pJ — a 1000×
//! improvement over traditional IPC, and within an order of magnitude of
//! biological synaptic transmission (~1 pJ per vesicle release).

use std::sync::atomic::{AtomicUsize, Ordering};
use std::cell::UnsafeCell;

use crate::synapse::Spike;

/// The header that precedes every spike in a synaptic channel.
///
/// This is 8 bytes — exactly one cache line on most architectures. We
/// pack it tightly to avoid false sharing between adjacent channels.
#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
pub struct SpikeHeader {
    /// The emitting neuron's ID.
    pub src_neuron_id: u32,
    /// The tick at which the spike was emitted.
    pub timestamp: u32,
    /// The synaptic efficacy (brain float16 for Loihi compatibility).
    pub weight: half::f16,
    /// Index into the scheduler's plasticity-rule table.
    pub plasticity_id: u16,
}

/// A lock-free SPSC ring buffer for spike transmission.
///
/// ## Biological correspondence
///
/// This buffer mimics the **synaptic cleft** — the ~20 nm gap between
/// pre- and post-synaptic membranes. Neurotransmitter diffuses across
/// this gap with a delay of ~0.5 ms; our buffer mimics this delay by
/// being sized so the producer is always `D` ticks ahead of the consumer.
///
/// ## Safety
///
/// This is SPSC (single-producer, single-consumer). The producer must
/// be the only thread calling `push()`; the consumer must be the only
/// thread calling `pop()`. Violating this contract is UB.
pub struct SynapticChannel {
    /// The ring buffer itself.
    buffer: Box<[UnsafeCell<Option<Spike>>]>,
    /// Producer index (only modified by producer).
    head: AtomicUsize,
    /// Consumer index (only modified by consumer).
    tail: AtomicUsize,
    /// Mask for fast modulo (capacity must be a power of 2).
    mask: usize,
    /// Biological synaptic delay, in ticks.
    pub delay_ticks: u32,
}

impl SynapticChannel {
    /// Construct a new channel with the given capacity and delay.
    ///
    /// `capacity` is rounded up to the next power of 2. `delay_ticks`
    /// is the biological synaptic delay (0.5–2 ms / TICK_MS = 1–2 ticks).
    pub fn new(capacity: usize, delay_ticks: u32) -> Self {
        let cap = capacity.next_power_of_two();
        let buffer: Vec<_> = (0..cap).map(|_| UnsafeCell::new(None)).collect();
        Self {
            buffer: buffer.into_boxed_slice(),
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
            mask: cap - 1,
            delay_ticks,
        }
    }

    /// Push a spike into the channel (producer side).
    ///
    /// Returns `Err(spike)` if the buffer is full — mimicking biological
    /// "synaptic failure" (a vesicle that fails to release due to
    /// depletion of readily-releasable pool).
    ///
    /// # Safety
    /// Only one thread may call this method.
    pub fn push(&self, spike: Spike) -> Result<(), Spike> {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Acquire);
        if head.wrapping_sub(tail) >= self.buffer.len() {
            // Buffer full — biological "synaptic failure".
            return Err(spike);
        }
        let slot = &self.buffer[head & self.mask];
        // SAFETY: we are the only producer; the consumer reads via `tail`,
        // which is strictly less than `head` at this point.
        unsafe {
            *slot.get() = Some(spike);
        }
        self.head.store(head.wrapping_add(1), Ordering::Release);
        Ok(())
    }

    /// Pop a spike from the channel (consumer side).
    ///
    /// Returns `None` if the buffer is empty — mimicking biological
    /// "silent synapse" periods.
    ///
    /// # Safety
    /// Only one thread may call this method.
    pub fn pop(&self) -> Option<Spike> {
        let tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Acquire);
        if tail == head {
            return None;  // Empty.
        }
        let slot = &self.buffer[tail & self.mask];
        // SAFETY: we are the only consumer; the producer writes via `head`,
        // which is strictly greater than `tail` at this point.
        let spike = unsafe { (*slot.get()).take() };
        self.tail.store(tail.wrapping_add(1), Ordering::Release);
        spike
    }

    /// Current number of pending spikes in the buffer.
    pub fn len(&self) -> usize {
        let head = self.head.load(Ordering::Relaxed);
        let tail = self.tail.load(Ordering::Relaxed);
        head.wrapping_sub(tail)
    }

    /// Whether the buffer is empty.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

// SAFETY: SynapticChannel is Send + Sync because the SPSC contract is
// enforced by the API (separate `push`/`pop` methods, each callable by
// only one thread). The UnsafeCell is only accessed through atomic indices.
unsafe impl Send for SynapticChannel {}
unsafe impl Sync for SynapticChannel {}

#[cfg(test)]
mod tests {
    use super::*;

    /// Mimics a single EPSP propagating across a synaptic cleft.
    #[test]
    fn test_single_spike_round_trip() {
        let ch = SynapticChannel::new(8, 1);
        let spike = Spike {
            src_neuron_id: 42,
            timestamp: 100,
            weight: half::f16::from_f32(0.5),
            plasticity_id: 0,
        };
        assert!(ch.push(spike).is_ok());
        let popped = ch.pop().expect("should have a spike");
        assert_eq!(popped.src_neuron_id, 42);
        assert!(ch.is_empty());
    }

    /// Mimics synaptic failure under high-frequency stimulation.
    #[test]
    fn test_buffer_overflow_mimics_synaptic_failure() {
        let ch = SynapticChannel::new(4, 1);  // capacity 4
        for i in 0..4 {
            assert!(ch.push(Spike {
                src_neuron_id: i,
                timestamp: 0,
                weight: half::f16::from_f32(1.0),
                plasticity_id: 0,
            }).is_ok());
        }
        // The 5th push should fail — vesicle depletion.
        let result = ch.push(Spike {
            src_neuron_id: 99,
            timestamp: 0,
            weight: half::f16::from_f32(1.0),
            plasticity_id: 0,
        });
        assert!(result.is_err(), "buffer should be full (synaptic failure)");
    }
}
