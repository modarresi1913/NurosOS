//! Developmental Causality Graph.
//!
//! This is NOT a claim of true philosophical causality. It is an explicit
//! computational provenance graph that records, for every cognitive
//! change, the chain of events that produced it.
//!
//! Vocabulary:
//!   - **causal trace** — a recorded sequence of events that led to a state change.
//!   - **candidate causal dependency** — an edge in the graph that suggests
//!     (but does not prove) one event caused another.
//!   - **provenance dependency** — a definite dependency (event X used the
//!     output of event Y).
//!
//! The graph is a DAG: events are added in chronological order and edges
//! only ever point from earlier events to later events.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// The kind of event recorded in the causality graph.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EventKind {
    /// An environment-side event (e.g. resource spawned, hazard moved).
    EnvironmentEvent,
    /// The organism observed the environment.
    SensoryObservation,
    /// The organism made a prediction about an action's reward.
    Prediction,
    /// The organism computed its prediction error.
    PredictionError,
    /// The organism updated its memory store.
    MemoryUpdate,
    /// The organism revised a belief in its self-model.
    BeliefRevision,
    /// The self-model was updated (rolling averages, capabilities).
    SelfModelChange,
    /// The organism selected an action.
    Decision,
    /// The organism executed an action in the environment.
    Action,
    /// The environment returned an outcome (reward, new state).
    Outcome,
    /// A developmental transition occurred (stage change, capability emergence).
    DevelopmentalChange,
}

impl std::fmt::Display for EventKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", serde_json::to_string(self).unwrap_or_default().trim_matches('"'))
    }
}

/// A single event in the causality graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CausalEvent {
    /// Monotonic event ID.
    pub id: u64,
    /// Step at which the event occurred.
    pub step: u64,
    /// Event kind.
    pub kind: EventKind,
    /// Free-form description.
    pub description: String,
    /// The event's payload (e.g. the observation, the action, the reward).
    pub payload: serde_json::Value,
    /// IDs of events that this event depends on (provenance dependencies).
    pub depends_on: Vec<u64>,
}

/// The causality graph.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DevelopmentalCausalityGraph {
    /// All events, indexed by ID.
    pub events: BTreeMap<u64, CausalEvent>,
    /// Next event ID to allocate.
    next_id: u64,
}

impl DevelopmentalCausalityGraph {
    /// Create an empty graph.
    pub fn new() -> Self {
        Self::default()
    }

    /// Record a new event with explicit dependencies. Returns its ID.
    pub fn record(
        &mut self,
        step: u64,
        kind: EventKind,
        description: impl Into<String>,
        payload: serde_json::Value,
        depends_on: Vec<u64>,
    ) -> u64 {
        let id = self.next_id;
        self.next_id += 1;
        let event = CausalEvent {
            id,
            step,
            kind,
            description: description.into(),
            payload,
            depends_on,
        };
        self.events.insert(id, event);
        id
    }

    /// Number of events in the graph.
    pub fn len(&self) -> usize {
        self.events.len()
    }

    /// True if the graph is empty.
    pub fn is_empty(&self) -> bool {
        self.events.is_empty()
    }

    /// Get an event by ID.
    pub fn get(&self, id: u64) -> Option<&CausalEvent> {
        self.events.get(&id)
    }

    /// Compute the **causal trace** leading up to a given event: the full
    /// set of events that directly or indirectly appear in its
    /// `depends_on` closure. Returned in chronological order (by ID).
    pub fn trace(&self, target_id: u64) -> Vec<&CausalEvent> {
        let mut visited = std::collections::BTreeSet::new();
        let mut stack = vec![target_id];
        while let Some(id) = stack.pop() {
            if visited.insert(id) {
                if let Some(ev) = self.events.get(&id) {
                    for dep in &ev.depends_on {
                        if !visited.contains(dep) {
                            stack.push(*dep);
                        }
                    }
                }
            }
        }
        visited
            .into_iter()
            .filter_map(|id| self.events.get(&id))
            .collect()
    }

    /// Return all events of a particular kind, in chronological order.
    pub fn events_of_kind(&self, kind: EventKind) -> Vec<&CausalEvent> {
        self.events
            .values()
            .filter(|e| e.kind == kind)
            .collect()
    }

    /// Render the graph as a human-readable list of events.
    pub fn render(&self, max_events: usize) -> String {
        let mut s = String::new();
        s.push_str(&format!("=== Developmental Causality Graph ({} events) ===\n", self.events.len()));
        for (i, ev) in self.events.values().take(max_events).enumerate() {
            let deps: Vec<String> = ev.depends_on.iter().map(|d| format!("#{}", d)).collect();
            s.push_str(&format!(
                "  #{:<4} step={:<4} {:<22} {:<30} deps=[{}]\n",
                ev.id, ev.step, ev.kind.to_string(),
                truncate(&ev.description, 30),
                deps.join(", "),
            ));
            let _ = i;
        }
        if self.events.len() > max_events {
            s.push_str(&format!("  ... ({} more events not shown)\n", self.events.len() - max_events));
        }
        s
    }

    /// Render the causal trace for a specific event.
    pub fn render_trace(&self, target_id: u64) -> String {
        let trace = self.trace(target_id);
        let mut s = String::new();
        s.push_str(&format!("=== Causal Trace for event #{} ===\n", target_id));
        for ev in trace {
            s.push_str(&format!(
                "  #{:<4} step={:<4} {:<22} {}\n",
                ev.id, ev.step, ev.kind.to_string(), ev.description,
            ));
        }
        s
    }

    /// Export as JSONL (one JSON object per line) for offline analysis.
    pub fn to_jsonl(&self) -> String {
        let mut s = String::new();
        for ev in self.events.values() {
            if let Ok(line) = serde_json::to_string(ev) {
                s.push_str(&line);
                s.push('\n');
            }
        }
        s
    }
}

fn truncate(s: &str, n: usize) -> String {
    if s.len() <= n {
        s.to_string()
    } else {
        format!("{}…", &s[..n])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn record_event_assigns_monotonic_ids() {
        let mut g = DevelopmentalCausalityGraph::new();
        let id1 = g.record(1, EventKind::SensoryObservation, "obs1", serde_json::json!({}), vec![]);
        let id2 = g.record(1, EventKind::Prediction, "pred1", serde_json::json!({}), vec![id1]);
        let id3 = g.record(2, EventKind::Action, "act1", serde_json::json!({}), vec![id2]);
        assert_eq!(id1, 0);
        assert_eq!(id2, 1);
        assert_eq!(id3, 2);
        assert_eq!(g.len(), 3);
    }

    #[test]
    fn trace_walks_dependency_closure() {
        let mut g = DevelopmentalCausalityGraph::new();
        let id1 = g.record(1, EventKind::SensoryObservation, "obs", serde_json::json!({}), vec![]);
        let id2 = g.record(1, EventKind::Prediction, "pred", serde_json::json!({}), vec![id1]);
        let id3 = g.record(1, EventKind::Decision, "dec", serde_json::json!({}), vec![id2]);
        let id4 = g.record(2, EventKind::Action, "act", serde_json::json!({}), vec![id3]);
        let trace = g.trace(id4);
        let trace_ids: Vec<u64> = trace.iter().map(|e| e.id).collect();
        assert!(trace_ids.contains(&id1));
        assert!(trace_ids.contains(&id2));
        assert!(trace_ids.contains(&id3));
        assert!(trace_ids.contains(&id4));
    }

    #[test]
    fn events_of_kind_filters_correctly() {
        let mut g = DevelopmentalCausalityGraph::new();
        g.record(1, EventKind::SensoryObservation, "a", serde_json::json!({}), vec![]);
        g.record(1, EventKind::Prediction, "b", serde_json::json!({}), vec![]);
        g.record(2, EventKind::SensoryObservation, "c", serde_json::json!({}), vec![]);
        assert_eq!(g.events_of_kind(EventKind::SensoryObservation).len(), 2);
        assert_eq!(g.events_of_kind(EventKind::Prediction).len(), 1);
    }

    #[test]
    fn jsonl_export_has_one_line_per_event() {
        let mut g = DevelopmentalCausalityGraph::new();
        g.record(1, EventKind::SensoryObservation, "a", serde_json::json!({}), vec![]);
        g.record(2, EventKind::Prediction, "b", serde_json::json!({}), vec![0]);
        let jsonl = g.to_jsonl();
        assert_eq!(jsonl.lines().count(), 2);
    }

    #[test]
    fn render_trace_works() {
        let mut g = DevelopmentalCausalityGraph::new();
        let id1 = g.record(1, EventKind::SensoryObservation, "obs", serde_json::json!({}), vec![]);
        let id2 = g.record(1, EventKind::Prediction, "pred", serde_json::json!({}), vec![id1]);
        let s = g.render_trace(id2);
        assert!(s.contains("Causal Trace"));
        assert!(s.contains("obs"));
        assert!(s.contains("pred"));
    }
}
