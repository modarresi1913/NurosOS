# NurosOS Quickstart

## Installation

```bash
git clone https://github.com/modarresi1913/NurosOS.git
cd NurosOS
pip install -e .
```

## Your First Organism

```python
from nuros.organism import Organism, OrganismConfig, OrganismState

# Create a minimal organism
config = OrganismConfig(name="my-first-organism")
organism = Organism(config)

# Give it life
organism.birth()
print(f"State: {organism.state}")  # ALIVE

# Run a cognitive tick
result = organism.tick()
print(f"Tick: {result}")

# Observe the organism's state
print(f"Memories: {organism.memory.memory_count}")
print(f"Homeostasis: {organism.homeostasis.summary()}")
```

## Using the Epistemic Kernel

```python
from nuros.epistemic import EpistemicKernel, EpistemicLabel, EpistemicViolation

ek = EpistemicKernel()

# Create grounded observations
observation = ek.observe({"sensor_reading": 42.0})

# Infer from observations
inference = ek.infer({"pattern": "increasing"})

# Predict future states
prediction = ek.predict({"next_value": 45.0})

# Simulate alternatives
simulation = ek.simulate({"if_action_x": "outcome_y"})

# Imagine counterfactuals
imagination = ek.imagine({"what_if": "scenario_z"})

# FORBIDDEN: Simulated → Observed (raises EpistemicViolation)
try:
    simulation.as_observed("verification")
except EpistemicViolation as e:
    print(f"Safety violation caught: {e}")
```

## Working with Memory

```python
from nuros.memory import MemoryContract, MemoryType

memory = MemoryContract()

# Store episodic memory
ep1 = memory.remember("I saw a red object", 
                       memory_type=MemoryType.EPISODIC,
                       importance=0.8)

# Store semantic memory
ep2 = memory.remember("Red objects are often hot",
                       memory_type=MemoryType.SEMANTIC,
                       importance=0.6)

# Associate memories
memory.associate(ep1.memory_id, ep2.memory_id, "supports")

# Retrieve with query
results = memory.retrieve(limit=10)
for entry in results:
    print(f"[{entry.memory_type.name}] {entry.content}")

# Revise with audit trail
revised = memory.revise(ep2.memory_id, "content", 
                        "Red objects can be cool too",
                        "New observation corrected belief")
```

## Running Experiments

```python
from nuros.organism import Organism, OrganismConfig
from nuros.genome import ORGANISM_0_GENOME

# Create organism from genome
organism = Organism(OrganismConfig(name="experiment-1"))
organism.birth()

# Run experimental loop
for tick in range(100):
    observation = {"tick": tick, "value": tick * 0.1}
    result = organism.tick()
    
    if tick % 20 == 0:
        print(f"Tick {tick}: {organism.homeostasis.summary()}")

# Take snapshot for reproducibility
snapshot = organism.snapshot()
print(f"State hash: {organism.state_hash()}")
```

## Running Tests

```bash
python -m pytest nuros/tests/ -v
```

## Running Benchmarks

```bash
python -m benchmarks.benchmark_suite
```
