//! Environment API and the two flagship environments.
//!
//! Every environment in NurosOS exposes:
//!   - `reset()` — return to initial state
//!   - `observe()` — return current observation
//!   - `step(action)` — advance one timestep with the given action
//!   - `state()` — return full environment state
//!   - `hash()` — deterministic content hash of the current state
//!   - `snapshot()` — serializable full state for restore
//!   - `restore(snapshot)` — restore from a snapshot
//!
//! Optional methods:
//!   - `render()` — human-readable rendering
//!   - `causal_events()` — list of recent environment-side events
//!
//! Determinism contract: an environment constructed with a fixed seed and
//! reset to its initial state MUST produce identical observation/reward
//! sequences when given identical action sequences. This is verified by
//! [`tests::environment_determinism`].

use serde::{Deserialize, Serialize};

use crate::hash;

/// A serializable snapshot of an environment's state.
pub type EnvironmentSnapshot = serde_json::Value;

/// The action type used by all MVP environments. Each variant is a single
/// discrete action; richer environments can extend this enum.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Action {
    /// Move one step in the positive X direction.
    MoveRight,
    /// Move one step in the negative X direction.
    MoveLeft,
    /// Move one step in the positive Y direction.
    MoveUp,
    /// Move one step in the negative Y direction.
    MoveDown,
    /// Stay in place (skip a turn).
    Idle,
    /// Consume the resource at the current location (if any).
    Consume,
}

impl Action {
    /// All available actions.
    pub fn all() -> &'static [Action] {
        &[
            Action::MoveRight,
            Action::MoveLeft,
            Action::MoveUp,
            Action::MoveDown,
            Action::Idle,
            Action::Consume,
        ]
    }

    /// The (dx, dy) delta this action implies on a 2D grid.
    pub fn delta(self) -> (i32, i32) {
        match self {
            Action::MoveRight => (1, 0),
            Action::MoveLeft => (-1, 0),
            Action::MoveUp => (0, 1),
            Action::MoveDown => (0, -1),
            Action::Idle | Action::Consume => (0, 0),
        }
    }
}

impl std::fmt::Display for Action {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", serde_json::to_string(self).unwrap_or_default().trim_matches('"'))
    }
}

/// An observation returned by the environment. This is intentionally
/// generic: environments expose JSON-serializable observations so that any
/// cognitive engine can consume them.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Observation {
    /// Free-form observation payload.
    pub payload: serde_json::Value,
    /// Reward signal for this step (typically in [-1, 1]).
    pub reward: f64,
    /// True if the episode has terminated.
    pub done: bool,
    /// Step index of this observation.
    pub step: u64,
}

impl Observation {
    /// Construct a new observation.
    pub fn new(payload: serde_json::Value, reward: f64, done: bool, step: u64) -> Self {
        Self { payload, reward, done, step }
    }
}

/// Trait implemented by all NurosOS environments.
pub trait Environment: Send + Sync {
    /// Reset the environment to its initial state. Returns the first observation.
    fn reset(&mut self) -> Observation;

    /// Get the current observation without advancing the environment.
    fn observe(&self) -> Observation;

    /// Apply an action and advance one timestep. Returns the new observation.
    fn step(&mut self, action: Action) -> Observation;

    /// Return a serializable snapshot of the full environment state.
    fn snapshot(&self) -> EnvironmentSnapshot;

    /// Restore from a previously-taken snapshot.
    fn restore(&mut self, snapshot: &EnvironmentSnapshot) -> Result<(), String>;

    /// Deterministic content hash of the current state.
    fn hash(&self) -> String;

    /// Environment name (e.g. "resource_world", "changing_world").
    fn name(&self) -> &str;

    /// Optional: human-readable rendering of the current state.
    fn render(&self) -> String {
        format!("<{}: hash={}>", self.name(), hash::short_hash(&self.hash()))
    }
}

// ============================================================================
// Resource World
// ============================================================================

/// Resource World: a 2D grid where the organism must locate and consume
/// limited resources. Variables: energy gain from consumption, distance
/// traveled, risk from hazardous cells, resource availability.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceWorld {
    /// Grid width.
    pub width: u32,
    /// Grid height.
    pub height: u32,
    /// Current agent position.
    pub agent_pos: (u32, u32),
    /// Resource positions and remaining quantity (in [0, 1]).
    pub resources: Vec<((u32, u32), f64)>,
    /// Hazardous cell positions (entering these costs energy).
    pub hazards: Vec<(u32, u32)>,
    /// Current step index.
    pub step: u64,
    /// RNG seed (for deterministic resets).
    pub seed: u64,
    /// Initial agent position (for reset).
    pub initial_agent_pos: (u32, u32),
    /// Initial resources (for reset).
    pub initial_resources: Vec<((u32, u32), f64)>,
}

impl ResourceWorld {
    /// Create a new Resource World with the given dimensions and seed.
    pub fn new(width: u32, height: u32, seed: u64) -> Self {
        let agent_pos = (width / 2, height / 2);
        let resources = Self::generate_resources(width, height, seed, 5);
        let hazards = Self::generate_hazards(width, height, seed.wrapping_add(1), 3);
        Self {
            width,
            height,
            agent_pos,
            resources: resources.clone(),
            hazards,
            step: 0,
            seed,
            initial_agent_pos: agent_pos,
            initial_resources: resources,
        }
    }

    fn generate_resources(width: u32, height: u32, seed: u64, count: usize) -> Vec<((u32, u32), f64)> {
        let mut rng = SimpleRng::new(seed);
        let mut resources = Vec::with_capacity(count);
        let mut used = std::collections::HashSet::new();
        while resources.len() < count {
            let x = (rng.next_u32() % width.max(1)).max(0);
            let y = (rng.next_u32() % height.max(1)).max(0);
            if used.insert((x, y)) {
                let quantity = 0.5 + (rng.next_f64() * 0.5);
                resources.push(((x, y), quantity));
            }
        }
        resources
    }

    fn generate_hazards(width: u32, height: u32, seed: u64, count: usize) -> Vec<(u32, u32)> {
        let mut rng = SimpleRng::new(seed);
        let mut hazards = Vec::with_capacity(count);
        let mut used = std::collections::HashSet::new();
        while hazards.len() < count {
            let x = (rng.next_u32() % width.max(1)).max(0);
            let y = (rng.next_u32() % height.max(1)).max(0);
            if used.insert((x, y)) {
                hazards.push((x, y));
            }
        }
        hazards
    }

    fn is_hazard(&self, pos: (u32, u32)) -> bool {
        self.hazards.contains(&pos)
    }

    fn resource_at(&self, pos: (u32, u32)) -> Option<usize> {
        self.resources.iter().position(|(p, _)| *p == pos)
    }
}

impl Environment for ResourceWorld {
    fn reset(&mut self) -> Observation {
        self.agent_pos = self.initial_agent_pos;
        self.resources = self.initial_resources.clone();
        self.step = 0;
        self.observe()
    }

    fn observe(&self) -> Observation {
        let (ax, ay) = self.agent_pos;
        // Nearest resource distance + direction (Manhattan). Use fold to avoid Ord on f64.
        let nearest = self
            .resources
            .iter()
            .filter(|(_, q)| *q > 0.0)
            .map(|((rx, ry), _)| {
                let dx = *rx as i32 - ax as i32;
                let dy = *ry as i32 - ay as i32;
                ((dx.abs() + dy.abs()) as f64, dx, dy)
            })
            .fold(None::<(f64, i32, i32)>, |acc, x| {
                Some(match acc { None => x, Some(m) => if x.0 < m.0 { x } else { m } })
            });
        let (nearest_distance, dir_x, dir_y) = nearest.unwrap_or((-1.0, 0, 0));
        let on_resource = self.resource_at(self.agent_pos).is_some();
        let on_hazard = self.is_hazard(self.agent_pos);
        let total_resource_left: f64 = self.resources.iter().map(|(_, q)| *q).sum();
        let payload = serde_json::json!({
            "agent_pos": [ax, ay],
            "nearest_resource_distance": nearest_distance,
            "direction_to_resource": [dir_x, dir_y],
            "on_resource": on_resource,
            "on_hazard": on_hazard,
            "total_resource_left": total_resource_left,
            "resource_count": self.resources.iter().filter(|(_, q)| *q > 0.0).count(),
        });
        Observation::new(payload, 0.0, false, self.step)
    }

    fn step(&mut self, action: Action) -> Observation {
        self.step += 1;
        let (dx, dy) = action.delta();
        let new_x = (self.agent_pos.0 as i32 + dx).max(0).min(self.width as i32 - 1) as u32;
        let new_y = (self.agent_pos.1 as i32 + dy).max(0).min(self.height as i32 - 1) as u32;
        self.agent_pos = (new_x, new_y);

        let mut reward: f64 = -0.01; // small step cost

        if action == Action::Consume {
            if let Some(idx) = self.resource_at(self.agent_pos) {
                let qty = self.resources[idx].1;
                reward += qty;
                self.resources[idx].1 = 0.0;
            } else {
                reward -= 0.05; // penalty for wasted consume
            }
        }

        if self.is_hazard(self.agent_pos) {
            reward -= 0.2;
        }

        let done = self.resources.iter().all(|(_, q)| *q <= 0.0);
        let obs = self.observe();
        Observation::new(obs.payload, reward, done, self.step)
    }

    fn snapshot(&self) -> EnvironmentSnapshot {
        serde_json::to_value(self).unwrap_or(serde_json::Value::Null)
    }

    fn restore(&mut self, snapshot: &EnvironmentSnapshot) -> Result<(), String> {
        let restored: ResourceWorld = serde_json::from_value(snapshot.clone())
            .map_err(|e| format!("restore failed: {}", e))?;
        *self = restored;
        Ok(())
    }

    fn hash(&self) -> String {
        hash::hash(self)
    }

    fn name(&self) -> &str {
        "resource_world"
    }

    fn render(&self) -> String {
        let mut grid = String::new();
        for y in (0..self.height).rev() {
            for x in 0..self.width {
                let pos = (x, y);
                if pos == self.agent_pos {
                    grid.push('A');
                } else if self.resource_at(pos).map_or(false, |i| self.resources[i].1 > 0.0) {
                    grid.push('R');
                } else if self.is_hazard(pos) {
                    grid.push('H');
                } else {
                    grid.push('.');
                }
                grid.push(' ');
            }
            grid.push('\n');
        }
        grid
    }
}

// ============================================================================
// Changing World
// ============================================================================

/// Changing World: a 1D resource-tracking environment where the location
/// of the single resource shifts at fixed intervals. This tests adaptation
/// and plasticity: the organism must unlearn the old location and learn
/// the new one.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChangingWorld {
    /// Number of cells in the 1D world.
    pub size: u32,
    /// Current agent position.
    pub agent_pos: u32,
    /// Current resource position.
    pub resource_pos: u32,
    /// How often (in steps) the resource moves.
    pub shift_interval: u64,
    /// Current step index.
    pub step: u64,
    /// RNG seed.
    pub seed: u64,
    /// Initial agent position (for reset).
    pub initial_agent_pos: u32,
    /// Initial resource position (for reset).
    pub initial_resource_pos: u32,
    /// Number of times the resource has shifted so far.
    pub shifts: u64,
}

impl ChangingWorld {
    /// Create a new Changing World of the given size, with the resource
    /// shifting every `shift_interval` steps.
    pub fn new(size: u32, shift_interval: u64, seed: u64) -> Self {
        let agent_pos = 0;
        let resource_pos = size / 2;
        Self {
            size,
            agent_pos,
            resource_pos,
            shift_interval,
            step: 0,
            seed,
            initial_agent_pos: agent_pos,
            initial_resource_pos: resource_pos,
            shifts: 0,
        }
    }

    fn maybe_shift_resource(&mut self) {
        if self.step > 0 && self.step % self.shift_interval == 0 {
            let mut rng = SimpleRng::new(self.seed.wrapping_add(self.shifts));
            let new_pos = (rng.next_u32() % self.size.max(1)).max(0);
            if new_pos != self.resource_pos {
                self.resource_pos = new_pos;
                self.shifts += 1;
            }
        }
    }
}

impl Environment for ChangingWorld {
    fn reset(&mut self) -> Observation {
        self.agent_pos = self.initial_agent_pos;
        self.resource_pos = self.initial_resource_pos;
        self.step = 0;
        self.shifts = 0;
        self.observe()
    }

    fn observe(&self) -> Observation {
        let distance = (self.agent_pos as i32 - self.resource_pos as i32).abs() as f64;
        let on_resource = self.agent_pos == self.resource_pos;
        let payload = serde_json::json!({
            "agent_pos": self.agent_pos,
            "resource_pos": self.resource_pos,
            "distance_to_resource": distance,
            "on_resource": on_resource,
            "shifts": self.shifts,
        });
        Observation::new(payload, 0.0, false, self.step)
    }

    fn step(&mut self, action: Action) -> Observation {
        self.step += 1;
        let (dx, _) = action.delta();
        let new_pos = (self.agent_pos as i32 + dx).max(0).min(self.size as i32 - 1) as u32;
        self.agent_pos = new_pos;

        let mut reward: f64 = -0.01;
        if action == Action::Consume {
            if self.agent_pos == self.resource_pos {
                reward += 1.0;
            } else {
                reward -= 0.05;
            }
        }

        self.maybe_shift_resource();
        let obs = self.observe();
        Observation::new(obs.payload, reward, false, self.step)
    }

    fn snapshot(&self) -> EnvironmentSnapshot {
        serde_json::to_value(self).unwrap_or(serde_json::Value::Null)
    }

    fn restore(&mut self, snapshot: &EnvironmentSnapshot) -> Result<(), String> {
        let restored: ChangingWorld = serde_json::from_value(snapshot.clone())
            .map_err(|e| format!("restore failed: {}", e))?;
        *self = restored;
        Ok(())
    }

    fn hash(&self) -> String {
        hash::hash(self)
    }

    fn name(&self) -> &str {
        "changing_world"
    }

    fn render(&self) -> String {
        let mut line = String::with_capacity(self.size as usize + 1);
        for i in 0..self.size {
            if i == self.agent_pos && i == self.resource_pos {
                line.push('X');
            } else if i == self.agent_pos {
                line.push('A');
            } else if i == self.resource_pos {
                line.push('R');
            } else {
                line.push('.');
            }
        }
        line
    }
}

// ============================================================================
// Simple deterministic RNG (xorshift64*) — so we don't depend on the `rand`
// crate. Sufficient for environment generation; not cryptographically secure.
// ============================================================================

#[derive(Debug, Clone, Copy)]
struct SimpleRng {
    state: u64,
}

impl SimpleRng {
    fn new(seed: u64) -> Self {
        // Avoid the degenerate all-zero state.
        let s = if seed == 0 { 0x9E3779B97F4A7C15 } else { seed };
        Self { state: s }
    }

    fn next_u64(&mut self) -> u64 {
        // xorshift64* (Vigna, 2014).
        let mut x = self.state;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.state = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }

    fn next_u32(&mut self) -> u32 {
        (self.next_u64() & 0xFFFF_FFFF) as u32
    }

    fn next_f64(&mut self) -> f64 {
        // Convert to [0, 1) using the top 53 bits.
        let top = self.next_u64() >> 11;
        (top as f64) / ((1u64 << 53) as f64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn resource_world_determinism() {
        let mut a = ResourceWorld::new(8, 8, 42);
        let mut b = ResourceWorld::new(8, 8, 42);
        let _ = a.reset();
        let _ = b.reset();
        assert_eq!(a.hash(), b.hash());
        let actions = [
            Action::MoveRight, Action::Consume, Action::MoveUp, Action::Idle,
            Action::MoveLeft, Action::Consume, Action::MoveDown,
        ];
        for act in actions.iter() {
            let oa = a.step(*act);
            let ob = b.step(*act);
            assert_eq!(oa.payload, ob.payload);
            assert!((oa.reward - ob.reward).abs() < 1e-12);
        }
        assert_eq!(a.hash(), b.hash());
    }

    #[test]
    fn changing_world_determinism() {
        let mut a = ChangingWorld::new(10, 5, 7);
        let mut b = ChangingWorld::new(10, 5, 7);
        let _ = a.reset();
        let _ = b.reset();
        assert_eq!(a.hash(), b.hash());
        for i in 0..30 {
            let act = if i % 3 == 0 { Action::MoveRight } else if i % 3 == 1 { Action::Idle } else { Action::Consume };
            let oa = a.step(act);
            let ob = b.step(act);
            assert_eq!(oa.payload, ob.payload);
        }
    }

    #[test]
    fn snapshot_restore_round_trips() {
        let mut env = ResourceWorld::new(6, 6, 13);
        let _ = env.reset();
        env.step(Action::MoveRight);
        env.step(Action::Consume);
        let snap = env.snapshot();
        let hash_before = env.hash();

        // Mutate further.
        env.step(Action::MoveUp);
        env.step(Action::MoveLeft);
        assert_ne!(env.hash(), hash_before);

        // Restore.
        env.restore(&snap).unwrap();
        assert_eq!(env.hash(), hash_before);
    }

    #[test]
    fn changing_world_resource_shifts() {
        let mut env = ChangingWorld::new(10, 5, 99);
        let _ = env.reset();
        let initial_resource = env.resource_pos;
        for _ in 0..5 {
            env.step(Action::Idle);
        }
        // After 5 steps, a shift should have occurred.
        assert!(env.shifts >= 1 || env.resource_pos != initial_resource);
    }

    #[test]
    fn action_delta_correct() {
        assert_eq!(Action::MoveRight.delta(), (1, 0));
        assert_eq!(Action::MoveLeft.delta(), (-1, 0));
        assert_eq!(Action::MoveUp.delta(), (0, 1));
        assert_eq!(Action::MoveDown.delta(), (0, -1));
        assert_eq!(Action::Idle.delta(), (0, 0));
        assert_eq!(Action::Consume.delta(), (0, 0));
    }

    #[test]
    fn resource_world_render_shows_agent_and_resources() {
        let env = ResourceWorld::new(4, 4, 1);
        let s = env.render();
        assert!(s.contains('A'));
    }

    #[test]
    fn changing_world_render_shows_positions() {
        let env = ChangingWorld::new(8, 5, 1);
        let s = env.render();
        assert_eq!(s.len(), 8);
        assert!(s.contains('A') || s.contains('X'));
    }
}
