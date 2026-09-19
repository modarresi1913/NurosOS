# BASELINE SPEC — Tabular Q-Learning

> **Master prompt PHASE 3**: implement a minimal baseline using the SAME environment and evaluation harness.
> **Status**: SPECIFICATION + IMPLEMENTATION (the implementation is in `benchmarks/baselines/q_learning/`).
> **Companion to**: `experiments/EXPERIMENTS.md` (preregistration), `experiments/ABLATION_MATRIX.md` (matrix).

---

## Purpose

The Q-learning baseline is the audit's **falsifier**. It establishes whether the NurosOS developmental substrate provides measurable behavioral value beyond a conventional simple learning system. The purpose is **NOT** to make Q-learning look weak. The purpose is to **falsify** the claim "NurosOS provides measurable value."

If Q-learning outperforms NurosOS, the result is "NurosOS does not provide value on this env" — that is a valid scientific finding.

---

## Implementation constraints (master prompt PHASE 3)

The baseline MUST use:

- **Same environment**: the non-stationary 3-regime env from `experiments/EXPERIMENTS.md` §7 (Regime A: ResourceWorld 0-99, Regime B: harder ResourceWorld 100-199, Regime C: ChangingWorld 200-299).
- **Same episode structure**: 300 steps per run.
- **Comparable action space**: the same 6 actions (MoveRight/Left/Up/Down/Idle/Consume).
- **Same evaluation seeds**: 30 seeds (42..71).
- **Clearly documented hyperparameters**: α=0.1, γ=0.95, ε=0.1 (see `benchmarks/baselines/q_learning/config.json`).
- **No access to NurosOS-specific privileged information**: in privileged mode, the Q-learner uses the same observation payload as the NurosOS organism (including `direction_to_resource` etc.); in raw mode, it uses only `agent_pos` + reward. **The Q-learner does NOT get any extra information beyond what NurosOS gets.**

The Q-learner also gets the same memory budget (200 entries) as the NurosOS organism — implemented as a tabular Q-table with an LRU eviction policy when the table exceeds 200 entries.

---

## Hyperparameters

| Hyperparameter | Value | Justification |
|----------------|-------|---------------|
| Learning rate α | 0.1 | Standard tabular Q-learning default; matches NurosOS `genome.plasticity_rules.learning_rate`. |
| Discount factor γ | 0.95 | Standard for episodic tasks; gives a horizon of ~20 steps. |
| Exploration ε | 0.1 | Standard ε-greedy; matches NurosOS `genome.biases.exploration_bias` of 0.3 (NurosOS has higher exploration). |
| Q-table capacity | 200 entries | Matches the Rust `MinimumOrganism::MemoryRecord` cap (`organism.rs:233`). LRU eviction when exceeded. |
| Random seed | per-run (42..71) | Same seed set as NurosOS. |

These hyperparameters are documented in `benchmarks/baselines/q_learning/config.json` and are frozen for the experiment per the preregistration.

---

## Q-table state representation

The Q-table is keyed by `(state_signature, action)` pairs. The state signature is derived from the observation payload:

### Privileged mode (matches NurosOS organism)

- `state_signature = (agent_pos, on_resource, on_hazard, direction_to_resource_quantized)`
- Where `direction_to_resource_quantized` collapses the (dx, dy) vector to one of 9 buckets (8 compass directions + "on resource").

This matches the information available to `MinimumOrganism::heuristic_bias` (`organism.rs:451-503`).

### Raw mode

- `state_signature = (agent_pos)` only.
- The Q-learner must learn the value of (position, action) pairs from reward alone — no direction hint, no on_resource hint.

This is the "fair" comparison: both NurosOS and Q-learner are deprived of the privileged fields.

---

## Q-update rule

Standard tabular Q-learning:

```
Q(s, a) ← Q(s, a) + α [r + γ max_a' Q(s', a') - Q(s, a)]
```

Where:
- `s` = current state signature
- `a` = action taken
- `r` = reward received
- `s'` = next state signature (after taking `a`)
- `α` = 0.1 (learning rate)
- `γ` = 0.95 (discount factor)
- `max_a' Q(s', a')` = the best estimated Q-value at the next state

This is a **full Bellman backup** — distinct from NurosOS's `action_preferences` update (`organism.rs:206-213`), which is a single-step Rescorla-Wagner / TD(0) update WITHOUT the max_a' term. This is a meaningful difference: the Q-learner bootstraps, NurosOS does not.

---

## ε-greedy action selection

```
With probability ε (default 0.1):
    action = uniform_random_choice(Action::all())
Otherwise:
    action = argmax_a Q(s, a)
```

The randomness is **deterministic given a seed** — uses the same `deterministic_random`-style hash as the Rust `MinimumOrganism` (`organism.rs:573-584`), seeded by `(step, state_signature)`.

This ensures reproducibility: same seed + same observation sequence → same action sequence.

---

## LRU eviction policy

When the Q-table exceeds 200 entries, the **least-recently-used** (state, action) pair is evicted. The "recently used" timestamp is updated on every `Q(s, a)` lookup or update.

This matches the Rust `MinimumOrganism::MemoryRecord` cap (`organism.rs:233-236`), which caps at 200 entries and drops the lowest-importance record when exceeded. The NurosOS cap is importance-based; the Q-learner cap is LRU-based. The audit considers this an acceptable difference (both are 200-entry caps; the eviction policy difference is documented).

---

## Result serialization

Per master prompt PHASE 10 (Experiment harness), each Q-learning run produces:

```
experiment_outputs/<experiment_id>/
    config.json              # hyperparameters + env config + seed
    manifest.json            # ReproducibilityManifest (genome_hash analog = config_hash)
    raw/
        per_step.jsonl       # {step, action, reward, q_table_size, ...}
    metrics/
        primary.json         # {cumulative_reward, ...}
        secondary.json       # {adaptation_latency, post_shift_recovery, ...}
    trajectories/
        trajectory.jsonl     # one TickRecord-like entry per step
    checkpoints/
        final_q_table.json   # the final 200-entry Q-table
    plots/
        reward_curve.png     # cumulative reward over 300 steps
    report.md                # human-readable summary
```

---

## Tests

`benchmarks/baselines/q_learning/test_q_learning.py` (new) verifies:

1. The Q-learner deterministically reproduces a trajectory given a fixed seed.
2. The Q-table cap of 200 is enforced (LRU eviction triggers when exceeded).
3. The Q-update rule is mathematically correct (single-step numerical test).
4. The state signature is correctly derived from the observation payload (privileged mode + raw mode).
5. The ε-greedy policy is deterministic given a seed.
6. The result serialization round-trips (config + manifest + raw + metrics load correctly).

---

## What the Q-learning baseline is NOT

- It is **NOT** a deep RL baseline (no neural network, no function approximation). The audit's purpose is to test against the simplest conventional learning system per master prompt PHASE 3.
- It is **NOT** given privileged access to NurosOS internals. It uses the same observation the env provides to any organism.
- It is **NOT** configured to make NurosOS look good. The hyperparameters are standard tabular Q-learning defaults.
- It is **NOT** a HippoCore condition. HippoCore is a future intervention per `docs/HIPPOCORE_INTEGRATION_PLAN.md`.

**End of BASELINE_SPEC.md.**
