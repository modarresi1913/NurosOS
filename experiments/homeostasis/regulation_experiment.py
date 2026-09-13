"""Experiment: Homeostatic Regulation Convergence.

Study convergence properties of homeostatic regulation under
various perturbation patterns.
"""

from nuros.homeostasis import HomeostasisKernel


def run_regulation_experiment(
    n_ticks: int = 500,
    perturbation_interval: int = 50,
    perturbation_magnitude: float = 0.3,
) -> dict:
    """Run homeostatic regulation experiment."""
    hk = HomeostasisKernel()
    history = []

    for tick in range(n_ticks):
        # Apply perturbation periodically
        if tick % perturbation_interval == 0 and tick > 0:
            current = hk.get("energy")
            hk.set("energy", max(0, current - perturbation_magnitude))

        hk.tick()
        history.append({
            "tick": tick,
            "energy": hk.get("energy"),
            "uncertainty": hk.get("uncertainty"),
            "arousal": hk.get("arousal"),
        })

    # Analyze convergence
    final_energy = history[-1]["energy"]
    energy_variance = sum((h["energy"] - final_energy) ** 2 for h in history[-50:]) / 50

    return {
        "n_ticks": n_ticks,
        "perturbations": n_ticks // perturbation_interval,
        "final_energy": final_energy,
        "energy_variance_last_50": energy_variance,
        "converged": energy_variance < 0.01,
        "history": history,
    }


if __name__ == "__main__":
    result = run_regulation_experiment()
    print("Homeostatic Regulation Experiment")
    print("=" * 50)
    print(f"Ticks: {result['n_ticks']}")
    print(f"Perturbations: {result['perturbations']}")
    print(f"Final energy: {result['final_energy']:.4f}")
    print(f"Variance (last 50): {result['energy_variance_last_50']:.6f}")
    print(f"Converged: {result['converged']}")
