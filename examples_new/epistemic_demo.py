"""Example: Epistemic Kernel Demo.

Shows how the epistemic kernel prevents knowledge corruption.
"""

import sys
sys.path.insert(0, '/home/z/my-project/NurosOS')

from nuros.epistemic import EpistemicKernel, EpistemicLabel, EpistemicViolation


def main():
    ek = EpistemicKernel()

    print("=== Epistemic Kernel Demo ===\n")

    # Grounded knowledge
    obs = ek.observe({"temperature": 22.5, "location": "lab"})
    print(f"Observation: label={obs.label.name}, confidence={obs.confidence}")

    inf = ek.infer({"comfort_level": "moderate"})
    print(f"Inference: label={inf.label.name}, confidence={inf.confidence}")

    pred = ek.predict({"temperature_in_1h": 23.0})
    print(f"Prediction: label={pred.label.name}, confidence={pred.confidence}")

    sim = ek.simulate({"if_ac_on": 20.0})
    print(f"Simulation: label={sim.label.name}, confidence={sim.confidence}")

    img = ek.imagine({"if_heatwave": 35.0})
    print(f"Imagination: label={img.label.name}, confidence={img.confidence}")

    print("\n--- Forbidden Transitions ---\n")

    # Try forbidden: SIMULATED → OBSERVED
    try:
        sim.as_observed("I verified it")
        print("ERROR: Should have been blocked!")
    except EpistemicViolation as e:
        print(f"✓ Blocked: SIMULATED → OBSERVED ({e})")

    # Try forbidden: IMAGINED → REMEMBERED
    try:
        img.as_remembered("I remember imagining this")
        print("ERROR: Should have been blocked!")
    except EpistemicViolation as e:
        print(f"✓ Blocked: IMAGINED → REMEMBERED ({e})")

    # Allowed transition
    new_rep = obs.as_inferred("Processed observation")
    print(f"\n✓ Allowed: OBSERVED → INFERRED (label={new_rep.label.name})")

    # Override
    override_rep = sim.transition_to(
        EpistemicLabel.OBSERVED,
        "EPISTEMIC_OVERRIDE: Sensor confirmed simulation result"
    )
    print(f"✓ Override: SIMULATED → OBSERVED (label={override_rep.label.name})")

    print(f"\nAudit log entries: {len(ek._audit_log)}")


if __name__ == "__main__":
    main()
