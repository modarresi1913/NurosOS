"""Experiment: Epistemic Integrity Verification.

Verify that the epistemic kernel correctly prevents all
forbidden transitions and allows all valid ones.
"""

from nuros.epistemic import (
    EpistemicKernel, EpistemicLabel, EpistemicRepresentation, EpistemicViolation
)


FORBIDDEN = [
    (EpistemicLabel.SIMULATED, EpistemicLabel.OBSERVED),
    (EpistemicLabel.IMAGINED, EpistemicLabel.REMEMBERED),
    (EpistemicLabel.PREDICTED, EpistemicLabel.OBSERVED),
    (EpistemicLabel.IMAGINED, EpistemicLabel.OBSERVED),
    (EpistemicLabel.SIMULATED, EpistemicLabel.REMEMBERED),
    (EpistemicLabel.PREDICTED, EpistemicLabel.REMEMBERED),
]


def run_integrity_experiment() -> dict:
    """Run epistemic integrity verification experiment."""
    ek = EpistemicKernel()
    results = {
        "forbidden_blocked": 0,
        "forbidden_total": len(FORBIDDEN),
        "allowed_succeeded": 0,
        "allowed_total": 0,
        "override_works": 0,
    }

    # Test all forbidden transitions
    for source, target in FORBIDDEN:
        factory = {
            EpistemicLabel.OBSERVED: ek.observe,
            EpistemicLabel.INFERRED: ek.infer,
            EpistemicLabel.REMEMBERED: ek.remember,
            EpistemicLabel.PREDICTED: ek.predict,
            EpistemicLabel.SIMULATED: ek.simulate,
            EpistemicLabel.IMAGINED: ek.imagine,
        }
        rep = factory[source]({"test": True})
        try:
            rep.transition_to(target, "test")
            # If we get here, forbidden was NOT blocked
        except EpistemicViolation:
            results["forbidden_blocked"] += 1

    # Test valid transitions (OBSERVED → INFERRED, etc.)
    valid = [
        (EpistemicLabel.OBSERVED, EpistemicLabel.INFERRED),
        (EpistemicLabel.OBSERVED, EpistemicLabel.REMEMBERED),
        (EpistemicLabel.INFERRED, EpistemicLabel.PREDICTED),
        (EpistemicLabel.PREDICTED, EpistemicLabel.SIMULATED),
    ]
    results["allowed_total"] = len(valid)
    for source, target in valid:
        factory = {
            EpistemicLabel.OBSERVED: ek.observe,
            EpistemicLabel.INFERRED: ek.infer,
            EpistemicLabel.REMEMBERED: ek.remember,
            EpistemicLabel.PREDICTED: ek.predict,
            EpistemicLabel.SIMULATED: ek.simulate,
            EpistemicLabel.IMAGINED: ek.imagine,
        }
        rep = factory[source]({"test": True})
        try:
            rep.transition_to(target, "valid transition")
            results["allowed_succeeded"] += 1
        except EpistemicViolation:
            pass

    # Test override mechanism
    for source, target in FORBIDDEN:
        factory = {
            EpistemicLabel.OBSERVED: ek.observe,
            EpistemicLabel.INFERRED: ek.infer,
            EpistemicLabel.REMEMBERED: ek.remember,
            EpistemicLabel.PREDICTED: ek.predict,
            EpistemicLabel.SIMULATED: ek.simulate,
            EpistemicLabel.IMAGINED: ek.imagine,
        }
        rep = factory[source]({"test": True})
        try:
            rep.transition_to(target, f"EPISTEMIC_OVERRIDE: Verified for test")
            results["override_works"] += 1
        except EpistemicViolation:
            pass

    results["integrity_verified"] = (
        results["forbidden_blocked"] == results["forbidden_total"]
        and results["allowed_succeeded"] == results["allowed_total"]
        and results["override_works"] == results["forbidden_total"]
    )

    return results


if __name__ == "__main__":
    result = run_integrity_experiment()
    print("Epistemic Integrity Verification")
    print("=" * 50)
    print(f"Forbidden blocked: {result['forbidden_blocked']}/{result['forbidden_total']}")
    print(f"Allowed succeeded: {result['allowed_succeeded']}/{result['allowed_total']}")
    print(f"Override works: {result['override_works']}/{result['forbidden_total']}")
    print(f"Integrity verified: {result['integrity_verified']}")
