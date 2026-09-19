"""
Minimal Reference Emulator — demonstrates how a "task" gets scheduled
in a spike-timing-inspired neural network.

This is a CONCEPTUAL DEMONSTRATION, not a production simulator. It shows
the L0 → L1 → L2 flow:

  L0 (Reference Emulator): a small network of threshold-fire neurons.
  L1 (Spike-Timed Scheduling API): spikes are converted to task-dispatch
      events. A neuron that fires at time T schedules its downstream
      task for time T+delay.
  L2 (Task Interface): tasks (move, consume, idle) are dispatched to
      the environment based on the spike schedule.

The emulator is intentionally minimal (~150 lines) so that a reader can
understand the entire flow in one sitting. It is NOT biologically
accurate. It demonstrates the CONCEPT.

Run:
    python3 examples/reference_emulator.py

Output: a step-by-step trace showing how spikes → task scheduling →
environment interaction → reward → synaptic update.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# L0 — Reference Emulator: a minimal spiking network
# ============================================================================

@dataclass
class Neuron:
    """A simple leaky integrate-and-fire neuron."""
    name: str
    membrane_potential: float = 0.0
    threshold: float = 1.0
    leak: float = 0.1  # per-tick decay
    last_fire_time: int = -1

    def receive(self, weight: float, current_time: int):
        """Receive a synaptic input."""
        self.membrane_potential += weight
        if self.membrane_potential >= self.threshold:
            self.last_fire_time = current_time
            self.membrane_potential = 0.0  # reset
            return True  # fired!
        return False

    def tick(self):
        """Leaky decay."""
        self.membrane_potential = max(0.0, self.membrane_potential - self.leak)


@dataclass
class Synapse:
    """A directed connection between two neurons."""
    pre: str  # presynaptic neuron name
    post: str  # postsynaptic neuron name
    weight: float
    delay: int = 1  # synaptic delay in ticks


class SpikeNetwork:
    """L0: A minimal spiking neural network.

    The network has:
      - sensory neurons (receive input from the environment)
      - interneurons (process)
      - motor neurons (output drives task selection)

    When a motor neuron fires, it triggers a task (L2).
    """

    def __init__(self):
        self.neurons: dict[str, Neuron] = {}
        self.synapses: list[Synapse] = []
        self.spike_log: list[dict] = []

    def add_neuron(self, name: str, threshold: float = 1.0, leak: float = 0.1):
        self.neurons[name] = Neuron(name=name, threshold=threshold, leak=leak)

    def add_synapse(self, pre: str, post: str, weight: float, delay: int = 1):
        self.synapses.append(Synapse(pre=pre, post=post, weight=weight, delay=delay))

    def step(self, sensory_input: dict[str, float], current_time: int) -> list[str]:
        """Run one tick of the network.

        Args:
            sensory_input: {neuron_name: input_current} for sensory neurons.
            current_time: tick index.

        Returns: list of motor-neuron names that fired this tick (= tasks to dispatch).
        """
        # Apply sensory input.
        for name, current in sensory_input.items():
            if name in self.neurons:
                self.neurons[name].receive(current, current_time)

        # Propagate spikes through synapses — iterate until no more fires (settle).
        motor_fires: list[str] = []
        for _ in range(5):  # max 5 propagation passes per tick
            new_spikes: list[tuple[str, str, float]] = []
            for syn in self.synapses:
                pre = self.neurons.get(syn.pre)
                if pre and pre.last_fire_time == current_time:
                    new_spikes.append((syn.pre, syn.post, syn.weight))
            if not new_spikes:
                break
            any_fired = False
            for pre_name, post_name, weight in new_spikes:
                post = self.neurons.get(post_name)
                if post and post.last_fire_time != current_time:  # don't re-fire
                    fired = post.receive(weight, current_time)
                    if fired:
                        any_fired = True
                        if post_name.startswith("motor_"):
                            motor_fires.append(post_name)
            if not any_fired:
                break

        # Log spikes.
        for name, n in self.neurons.items():
            if n.last_fire_time == current_time:
                self.spike_log.append({
                    "time": current_time, "neuron": name,
                    "potential": n.membrane_potential,
                })

        # Leak all neurons.
        for n in self.neurons.values():
            n.tick()

        return motor_fires


# ============================================================================
# L1 — Spike-Timed Scheduling API
# ============================================================================

# Maps motor-neuron names to task names (L2 tasks).
MOTOR_TO_TASK = {
    "motor_move_right": "move_right",
    "motor_move_left": "move_left",
    "motor_consume": "consume",
    "motor_idle": "idle",
}

# Maps sensory signals to sensory-neuron names.
SENSOR_TO_NEURON = {
    "on_resource": "sens_resource",
    "direction_right": "sens_right",
    "direction_left": "sens_left",
    "hunger": "sens_hunger",
}


class SpikeScheduler:
    """L1: Converts sensory observations → sensory-neuron input currents,
    and motor-neuron fires → task-dispatch events.

    This is the "spike-timed scheduling" layer: the timing of spikes
    determines the timing of task execution. A neuron that fires at time
    T schedules its downstream task for time T (or T+delay if synapses
    have delays).
    """

    @staticmethod
    def obs_to_currents(obs: dict) -> dict[str, float]:
        """Convert an environment observation to sensory-neuron input currents."""
        currents = {}
        if obs.get("on_resource"):
            currents["sens_resource"] = 1.5  # strong excitation
        if obs.get("on_hazard"):
            currents["sens_hunger"] = 0.8
        direction = obs.get("direction_to_resource", [0, 0])
        if isinstance(direction, list) and len(direction) >= 2:
            dx = direction[0]
            if dx > 0:
                currents["sens_right"] = 0.5
            elif dx < 0:
                currents["sens_left"] = 0.5
        return currents

    @staticmethod
    def motor_to_task(motor_fires: list[str]) -> str:
        """Convert motor-neuron fires to a single task (first-past-the-post)."""
        for motor in motor_fires:
            task = MOTOR_TO_TASK.get(motor)
            if task:
                return task
        return "idle"  # default if no motor fired


# ============================================================================
# L2 — Task Interface (environment interaction)
# ============================================================================

class SimpleGridEnv:
    """L2: A minimal 1D grid environment for the emulator demo.

    The agent starts at position 0. A resource is at position 3.
    The agent can move_left, move_right, consume, or idle.
    """

    def __init__(self, resource_pos: int = 3, size: int = 10):
        self.size = size
        self.agent_pos = 0
        self.resource_pos = resource_pos
        self.resource_remaining = 1.0
        self.step_count = 0

    def observe(self) -> dict:
        on_resource = (self.agent_pos == self.resource_pos and self.resource_remaining > 0)
        dx = self.resource_pos - self.agent_pos
        return {
            "agent_pos": self.agent_pos,
            "on_resource": on_resource,
            "on_hazard": False,
            "direction_to_resource": [dx, 0],
            "resource_remaining": self.resource_remaining,
        }

    def step(self, action: str) -> tuple[dict, float]:
        self.step_count += 1
        reward = -0.01  # step cost

        if action == "move_right":
            self.agent_pos = min(self.size - 1, self.agent_pos + 1)
        elif action == "move_left":
            self.agent_pos = max(0, self.agent_pos - 1)
        elif action == "consume":
            if self.agent_pos == self.resource_pos and self.resource_remaining > 0:
                reward += self.resource_remaining
                self.resource_remaining = 0.0

        obs = self.observe()
        return obs, reward


# ============================================================================
# Demo: run the full L0 → L1 → L2 loop
# ============================================================================

def build_network() -> SpikeNetwork:
    """Build a minimal network for the resource-seeking demo.

    Topology:
      sens_resource → interneuron_exc → motor_consume
      sens_right → interneuron_right → motor_move_right
      sens_left → interneuron_left → motor_move_left
      sens_hunger → interneuron_explore → motor_move_right (bias toward exploration)
    """
    net = SpikeNetwork()

    # Sensory neurons.
    net.add_neuron("sens_resource", threshold=0.8)
    net.add_neuron("sens_right", threshold=0.3)
    net.add_neuron("sens_left", threshold=0.3)
    net.add_neuron("sens_hunger", threshold=0.5)

    # Interneurons.
    net.add_neuron("inter_exc", threshold=0.5, leak=0.05)
    net.add_neuron("inter_right", threshold=0.3, leak=0.05)
    net.add_neuron("inter_left", threshold=0.3, leak=0.05)
    net.add_neuron("inter_explore", threshold=0.4, leak=0.05)

    # Motor neurons.
    net.add_neuron("motor_consume", threshold=0.5, leak=0.02)
    net.add_neuron("motor_move_right", threshold=0.4, leak=0.02)
    net.add_neuron("motor_move_left", threshold=0.4, leak=0.02)
    net.add_neuron("motor_idle", threshold=0.9, leak=0.02)  # high threshold = rare

    # Synapses: sensory → interneuron → motor.
    net.add_synapse("sens_resource", "inter_exc", 0.8)
    net.add_synapse("inter_exc", "motor_consume", 0.6)

    net.add_synapse("sens_right", "inter_right", 0.5)
    net.add_synapse("inter_right", "motor_move_right", 0.5)

    net.add_synapse("sens_left", "inter_left", 0.5)
    net.add_synapse("inter_left", "motor_move_left", 0.5)

    net.add_synapse("sens_hunger", "inter_explore", 0.4)
    net.add_synapse("inter_explore", "motor_move_right", 0.3)  # bias toward right

    return net


def run_demo(n_steps: int = 20):
    """Run the L0 → L1 → L2 demo."""
    print("=" * 72)
    print("NurosOS Minimal Reference Emulator")
    print("L0 (Spike Network) → L1 (Spike Scheduler) → L2 (Task Interface)")
    print("=" * 72)
    print()

    net = build_network()
    env = SimpleGridEnv(resource_pos=3, size=10)
    scheduler = SpikeScheduler()

    print(f"Initial: agent_pos={env.agent_pos}, resource_pos={env.resource_pos}")
    print(f"Network: {len(net.neurons)} neurons, {len(net.synapses)} synapses")
    print()

    total_reward = 0.0
    for t in range(n_steps):
        # L2 → L1: observe environment → convert to sensory currents.
        obs = env.observe()
        currents = scheduler.obs_to_currents(obs)

        # L0: run the spike network one tick.
        motor_fires = net.step(currents, t)

        # L1 → L2: convert motor fires to task.
        task = scheduler.motor_to_task(motor_fires)

        # L2: execute task in environment.
        next_obs, reward = env.step(task)
        total_reward += reward

        # Trace.
        spikes = [s["neuron"] for s in net.spike_log if s["time"] == t]
        print(f"  t={t:2d} | pos={env.agent_pos} | obs={obs['on_resource']} | "
              f"currents={currents} | spikes={spikes} | task={task:15s} | "
              f"reward={reward:+.2f} | total={total_reward:+.2f}")

        if env.resource_remaining <= 0:
            print(f"\n  ✅ Resource consumed at t={t}! Total reward = {total_reward:.2f}")
            break

    print()
    print(f"Final: agent_pos={env.agent_pos}, total_reward={total_reward:.2f}")
    print(f"Spike log: {len(net.spike_log)} total spikes across {n_steps} ticks")
    print()
    print("This demonstrates the L0→L1→L2 flow:")
    print("  L0: Sensory neurons receive input → interneurons process → motor neurons fire")
    print("  L1: Spike timing determines task timing (neuron fires at T → task at T)")
    print("  L2: Task dispatched to environment → reward → (in a full system, synaptic update)")


if __name__ == "__main__":
    run_demo()
