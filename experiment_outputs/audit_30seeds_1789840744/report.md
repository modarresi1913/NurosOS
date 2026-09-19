# Experiment Report — audit_30seeds_1789840744

- **Seeds**: 30
- **Steps per run**: 300
- **Total runs**: 360

## Results: Cumulative Reward (mean ± std)

| Condition | Mode | Mean | Std | n | Min | Max | Cohen's d vs B |
|-----------|------|------|-----|---|-----|-----|-----------------|
| A_q_learning | priv | -3.0279 | 6.9394 | 30 | -7.4600 | 22.5200 | -0.640 |
| A_q_learning | raw | 1.8671 | 10.1409 | 30 | -7.7700 | 25.9300 | +0.540 |
| B_nurosos_baseline | priv | 1.7327 | 7.8994 | 30 | -9.0290 | 21.7139 | — |
| B_nurosos_baseline | raw | -2.3626 | 4.4376 | 30 | -4.9600 | 15.6300 | — |
| C_no_maturation | priv | 1.7327 | 7.8994 | 30 | -9.0290 | 21.7139 | +0.000 |
| C_no_maturation | raw | -2.3626 | 4.4376 | 30 | -4.9600 | 15.6300 | +0.000 |
| D_no_plasticity_decay | priv | 2.5023 | 7.1786 | 30 | -6.1955 | 19.4908 | +0.102 |
| D_no_plasticity_decay | raw | -2.1353 | 3.9955 | 30 | -5.2700 | 9.4500 | +0.054 |
| E_no_self_model | priv | 1.7327 | 7.8994 | 30 | -9.0290 | 21.7139 | +0.000 |
| E_no_self_model | raw | -2.3626 | 4.4376 | 30 | -4.9600 | 15.6300 | +0.000 |
| F_no_heuristic_bias | priv | -0.5655 | 8.1148 | 30 | -6.7600 | 28.6900 | -0.287 |
| F_no_heuristic_bias | raw | -2.3626 | 4.4376 | 30 | -4.9600 | 15.6300 | +0.000 |

## Interpretation

- **Positive Cohen's d** means the condition performed BETTER than B (NurosOS baseline).
- **Negative Cohen's d** means the condition performed WORSE than B.
- **|d| > 0.3** is a practically significant effect size.
- **Condition F (no heuristic bias)** is the CRITICAL ablation: if F << B, the bias carries the performance.
- **Condition A (Q-learning)** vs B: if A >= B, NurosOS provides no measurable value.