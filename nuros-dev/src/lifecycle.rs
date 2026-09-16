//! Organism lifecycle state machine.
//!
//! Every organism transitions through an explicit set of lifecycle states.
//! Transitions are observable and auditable: the only way to change state
//! is through [`LifecycleMachine::transition`], which records the previous
//! state, the new state, and the step at which the transition occurred.

use serde::{Deserialize, Serialize};

/// The complete set of organism lifecycle states.
///
/// These are intentionally distinct from developmental stages (which describe
/// the *cognitive maturity* of the organism). Lifecycle states describe the
/// *operational state* of the organism in the runtime.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum LifecycleState {
    /// Genome loaded but no organism instantiated yet.
    Created,
    /// Organism constructed, initial state applied, ready to develop.
    Initialized,
    /// Actively developing — experiencing the environment.
    Developing,
    /// Steady-state operation between developmental transitions.
    Active,
    /// In the middle of an adaptation event.
    Adapting,
    /// Recovering from a perturbation or instability.
    Recovering,
    /// A checkpoint has been taken; the organism is paused.
    Checkpointed,
    /// The organism has been forked; this instance continues independently.
    Forked,
    /// Suspended by an external observer; can be resumed.
    Suspended,
    /// Terminated — no further transitions are possible.
    Terminated,
}

impl LifecycleState {
    /// All valid states in declaration order.
    pub fn all() -> &'static [LifecycleState] {
        &[
            LifecycleState::Created,
            LifecycleState::Initialized,
            LifecycleState::Developing,
            LifecycleState::Active,
            LifecycleState::Adapting,
            LifecycleState::Recovering,
            LifecycleState::Checkpointed,
            LifecycleState::Forked,
            LifecycleState::Suspended,
            LifecycleState::Terminated,
        ]
    }

    /// Returns `true` if this is a terminal state (no further transitions).
    pub fn is_terminal(self) -> bool {
        matches!(self, LifecycleState::Terminated)
    }
}

impl std::fmt::Display for LifecycleState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", serde_json::to_string(self).unwrap_or_default().trim_matches('"'))
    }
}

/// A single recorded lifecycle transition.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LifecycleTransition {
    /// The state we transitioned from.
    pub from: LifecycleState,
    /// The state we transitioned to.
    pub to: LifecycleState,
    /// The step index at which the transition occurred.
    pub step: u64,
    /// Free-form reason for the transition (e.g. "experience_count >= 10").
    pub reason: String,
}

/// A lifecycle state machine. Tracks current state + full transition history.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LifecycleMachine {
    current: LifecycleState,
    history: Vec<LifecycleTransition>,
}

impl LifecycleMachine {
    /// Create a new machine in the [`Created`] state.
    pub fn new() -> Self {
        Self {
            current: LifecycleState::Created,
            history: Vec::new(),
        }
    }

    /// Current state.
    pub fn current(&self) -> LifecycleState {
        self.current
    }

    /// Full transition history (chronological).
    pub fn history(&self) -> &[LifecycleTransition] {
        &self.history
    }

    /// Transition to a new state. Returns `Err` if the transition is invalid
    /// (e.g. transitioning out of [`Terminated`]) or if `target == current`.
    pub fn transition(
        &mut self,
        target: LifecycleState,
        step: u64,
        reason: impl Into<String>,
    ) -> Result<(), String> {
        if self.current.is_terminal() {
            return Err(format!(
                "cannot transition from terminal state {}",
                self.current
            ));
        }
        if target == self.current {
            return Err(format!(
                "cannot transition to the same state {}",
                target
            ));
        }
        self.history.push(LifecycleTransition {
            from: self.current,
            to: target,
            step,
            reason: reason.into(),
        });
        self.current = target;
        Ok(())
    }

    /// Number of transitions recorded.
    pub fn transition_count(&self) -> usize {
        self.history.len()
    }
}

impl Default for LifecycleMachine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn starts_in_created_state() {
        let m = LifecycleMachine::new();
        assert_eq!(m.current(), LifecycleState::Created);
        assert_eq!(m.transition_count(), 0);
    }

    #[test]
    fn records_transitions() {
        let mut m = LifecycleMachine::new();
        m.transition(LifecycleState::Initialized, 0, "constructed").unwrap();
        m.transition(LifecycleState::Developing, 1, "birth").unwrap();
        assert_eq!(m.current(), LifecycleState::Developing);
        assert_eq!(m.transition_count(), 2);
        assert_eq!(m.history()[0].from, LifecycleState::Created);
        assert_eq!(m.history()[1].to, LifecycleState::Developing);
    }

    #[test]
    fn cannot_transition_from_terminated() {
        let mut m = LifecycleMachine::new();
        m.transition(LifecycleState::Terminated, 5, "shutdown").unwrap();
        let err = m.transition(LifecycleState::Active, 6, "wake").unwrap_err();
        assert!(err.contains("terminal"));
    }

    #[test]
    fn cannot_transition_to_same_state() {
        let mut m = LifecycleMachine::new();
        let err = m.transition(LifecycleState::Created, 1, "noop").unwrap_err();
        assert!(err.contains("same state"));
    }
}
