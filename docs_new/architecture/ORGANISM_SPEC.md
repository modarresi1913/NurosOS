# Organism Specification

## Definition

An **Organism** in NurosOS is an integrated system that implements all six Mind Contracts and operates within the constraints of the Safety Kernel.

## Lifecycle

```
UNBORN → birth() → ALIVE → terminate() → TERMINATED
                     │
                     ├── tick() → cognitive cycle
                     ├── fork() → new organism
                     ├── snapshot() → state capture
                     └── state_hash() → reproducibility hash
```

## Organism Ladder

### Organism-0: Minimal Viable Organism
- **Capabilities**: Observe, remember (episodic), homeostasis, react
- **Incapable**: Prediction, imagination, self-model, planning
- **Use case**: Reactive agent, simple sensorimotor loop
- **Epistemic range**: OBSERVED, ACTED only

### Organism-1: Predictive Organism
- **Adds**: Prediction, prediction error tracking, semantic memory
- **Incapable**: Imagination, self-model, planning
- **Use case**: Anticipatory agent, error-driven learning
- **Epistemic range**: + PREDICTED, INFERRED

### Organism-2: Imaginative Organism
- **Adds**: Counterfactual reasoning, simulation, risk assessment
- **Incapable**: Self-model, planning
- **Use case**: Decision-making agent, what-if reasoning
- **Epistemic range**: + SIMULATED, IMAGINED

### Organism-3: Self-Modeling Organism
- **Adds**: Metacognition, self-assessment, capability/limitation modeling
- **Incapable**: Social reasoning, full autonomy
- **Use case**: Reflective agent, self-improving systems
- **Epistemic range**: Full seven labels

### Organism-4: Social Organism
- **Adds**: Theory of mind, communication, social reasoning
- **Incapable**: Full autonomous goal-setting
- **Use case**: Multi-agent systems, cooperative/competitive agents
- **Epistemic range**: Full + social context

### Organism-5: Full Autonomous Organism
- **Adds**: Goal-setting, planning, value-driven decisions, developmental progression
- **Incapable**: Nothing (within safety bounds)
- **Use case**: Autonomous research, creative problem solving
- **Epistemic range**: Full + developmental context

## Mind Genome

Each organism is specified by a **Mind Genome** — a YAML-like blueprint:

```yaml
organism:
  id: organism-5
  version: "0.2.0"
  
  architecture:
    cognitive_modules: [attention, planning, reflection, prediction]
    organismic_modules: [homeostasis, development, plasticity]
    
  sensory_channels:
    - name: vision
      type: spatial
      dimensions: [224, 224, 3]
    - name: language
      type: symbolic
      vocabulary: 50000
      
  memory:
    types: [episodic, semantic, procedural, working, counterfactual]
    default_decay: exponential
    capacity: 10000
    
  plasticity:
    rules: [hebbian, reward_modulated, predictive]
    learning_rate: 0.01
    
  drives:
    - name: curiosity
      weight: 0.7
      trigger: uncertainty > 0.5
    - name: efficiency
      weight: 0.5
      trigger: energy < 0.3
      
  safety:
    immutable_constraints: [no_self_harm, human_override, shutdown_compliance]
    max_action_risk: MEDIUM
    audit_all: true
```

## Reproducibility

State is captured via:
```
ReproducibilityHash = GenomeHash + ExperienceHash + MemoryHash + SynapticStateHash + EnvironmentVersion + RuntimeVersion
```

This guarantees that identical conditions produce identical behavior.
