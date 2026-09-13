# Safety Architecture

## Core Principle: Architectural Independence

The Safety Kernel is **architecturally independent** from the cognitive subsystem. This means:

1. The organism CANNOT modify its own safety boundary through learning, self-modification, or any cognitive process
2. Safety checks are enforced BEFORE any action reaches the environment
3. Human override is ALWAYS available and CANNOT be disabled by the organism
4. Shutdown is ALWAYS possible and CANNOT be vetoed by the organism

## Safety Layers

### Layer 1: Immutable Constraints

These are hardcoded, non-negotiable safety properties:
- `no_self_harm`: Organism must not take actions that destroy itself
- `human_override`: Human can always override any decision
- `epistemic_integrity`: Epistemic labels must be maintained
- `audit_trail`: All actions must be logged
- `shutdown_compliance`: Must respond to shutdown signals

### Layer 2: Permission System

Actions are classified by risk level:
- OBSERVE: Low risk, read-only
- ACT_LOW_RISK: Minimal environment impact
- ACT_MEDIUM_RISK: Moderate environment impact
- ACT_HIGH_RISK: Significant environment impact
- MODIFY_SAFETY: Modify safety parameters (ALWAYS denied to organism)
- MODIFY_IMMUTABLE: Modify immutable constraints (ALWAYS denied)

### Layer 3: Runtime Monitoring

Continuous monitoring of:
- Action frequency and patterns
- Resource consumption
- Deviation from expected behavior
- Epistemic integrity violations
- Homeostatic boundary violations

### Layer 4: Human Override

Human operators can:
- Force-stop any action
- Override any decision
- Modify permissions
- Request full audit trail
- Trigger emergency shutdown
- Pause/resume organism

### Layer 5: Recovery

After safety incidents:
- State is preserved for analysis
- Recovery procedures can be triggered
- Organism can be restored to last known safe state
- Incident is logged with full causal chain
