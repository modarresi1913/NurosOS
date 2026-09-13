# Mind Contract Specification

## Overview

The Mind Contract Layer (MCL) defines six contracts that every NurosOS organism must implement. These are not optional features — they are the structural invariants of a synthetic mind.

## Contract 1: Memory

**Interface**: `MemoryContract`

Operations:
- `remember(content, type, importance, context)` → MemoryEntry
- `retrieve(query, limit, type_filter)` → List[MemoryEntry]
- `associate(id_a, id_b, relationship_type)` → bool
- `reflect(query)` → List[MemoryEntry]  (meta-retrieval)
- `revise(entry_id, old_content, new_content, justification)` → MemoryEntry
- `reconsolidate(entry_id, reward)` → MemoryEntry
- `forget(entry_id, justification)` → bool
- `replay(from_tick, to_tick)` → List[MemoryEntry]
- `working_set()` → Dict  (working memory)

Memory Types:
| Type | Epistemic Default | Purpose |
|------|------------------|---------|
| EPISODIC | OBSERVED | Event sequences |
| SEMANTIC | INFERRED | Generalized knowledge |
| PROCEDURAL | ACTED | Skill/habit storage |
| WORKING | OBSERVED | Temporary active state |
| COUNTERFACTUAL | IMAGINED | What-if scenarios |

Invariants:
- Every memory has provenance (origin, timestamp, epistemic label)
- Every revision is auditable (old → new, justification, timestamp)
- Counterfactual memories MUST carry IMAGINED epistemic label
- Decay is continuous; importance modulates decay rate

## Contract 2: Self Model

**Interface**: `SelfModel`

Queries:
- CAPABILITIES: What can I do?
- LIMITATIONS: What can't I do?
- BELIEFS: What do I believe about the world?
- IDENTITY: Who am I?
- CURRENT_STATE: What is my current state?
- UNCERTAINTY: What am I uncertain about?

Invariants:
- Self-model MUST include uncertainty about self-knowledge
- Self-model updates MUST be auditable
- Self-model MUST NOT be directly writable by external systems without epistemic labeling

## Contract 3: Imagination

**Interface**: `ImaginationEngine`

Pipeline:
1. `hypothesize(state, actions)` → List[Counterfactual]
2. `simulate(counterfactual)` → Counterfactual (with simulated_outcome)
3. `evaluate(counterfactual)` → Score
4. `decide(counterfactuals)` → Decision (executed: bool)

Risk Levels: LOW, MEDIUM, HIGH, CRITICAL

Invariants:
- CRITICAL risk counterfactuals are NEVER executed
- Every simulation is labeled SIMULATED in epistemic kernel
- Simulated results MUST NOT be stored as OBSERVED
- Imagination MUST check safety kernel before proposing execution

## Contract 4: Values / Drives

**Interface**: `ValuesContract`

Three-tier hierarchy:
1. **Immutable Constraints** — Cannot be revoked (e.g., human_override, no_self_harm)
2. **Contextual Goals** — Can be added/revoked with justification
3. **Preferences** — Can be freely adjusted

Invariants:
- Immutable constraints CANNOT be revoked by any entity including the organism itself
- Value conflicts MUST be resolved through the hierarchy (constraints > goals > preferences)
- Every value change MUST be auditable

## Contract 5: Body

**Interface**: `BodyContract`

A Body may be:
- Physical robot (sensors + actuators)
- Virtual avatar (simulated environment)
- Software environment (API-connected)
- Simulation (sandbox)
- Game world
- Abstract (no physical presence)

Operations:
- `sense(channel)` → Observation
- `act(action)` → Result
- `available_channels()` → List[Channel]
- `body_type()` → BodyType

Invariants:
- Body abstraction MUST be portable (same mind, different body)
- All sensory input MUST be epistemically labeled as OBSERVED
- All motor output MUST be epistemically labeled as ACTED

## Contract 6: Responsibility

**Interface**: `ResponsibilityContract`

For every externally relevant action, maintain:
- What was observed
- What was inferred
- What was remembered
- What was imagined/simulated
- What values were active
- What decision was made
- What action was taken
- What the outcome was

Invariants:
- Every action has a complete causal chain
- Responsibility log is append-only (no deletion, only revision)
- Responsibility log is queryable by external auditors
