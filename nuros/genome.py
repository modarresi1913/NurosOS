"""
Mind Genome — Conceptual and Executable Organism Blueprint.

A Mind Genome specifies:
    architecture, sensory_channels, memory_rules, plasticity_rules,
    developmental_rules, drives, resource_rules, body_interface,
    safety_constraints

Genome != Mind. The organism emerges from:
    Genome + Environment + Experience + Plasticity + Development

This creates a foundation for:
    mind variation, developmental divergence,
    artificial evolution, population experiments.

Implementation Status: EXPERIMENTAL
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GenomeSpec:
    """A Mind Genome specification."""
    genome_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unnamed_genome"
    version: str = "1.0"

    # Architecture
    architecture: dict[str, Any] = field(default_factory=dict)
    sensory_channels: list[dict] = field(default_factory=list)
    memory_rules: dict[str, Any] = field(default_factory=dict)
    plasticity_rules: list[dict] = field(default_factory=list)
    developmental_rules: list[dict] = field(default_factory=list)
    drives: dict[str, float] = field(default_factory=dict)
    resource_rules: dict[str, Any] = field(default_factory=dict)
    body_interface: dict[str, Any] = field(default_factory=dict)
    safety_constraints: list[str] = field(default_factory=list)

    # Metadata
    created_at: float = field(default_factory=time.time)
    parent_genome: Optional[str] = None
    mutation_log: list[str] = field(default_factory=list)

    @property
    def genome_hash(self) -> str:
        """Deterministic hash of the genome specification."""
        data = json.dumps({
            "architecture": self.architecture,
            "sensory_channels": self.sensory_channels,
            "memory_rules": self.memory_rules,
            "plasticity_rules": self.plasticity_rules,
            "developmental_rules": self.developmental_rules,
            "drives": self.drives,
            "resource_rules": self.resource_rules,
            "body_interface": self.body_interface,
            "safety_constraints": self.safety_constraints,
        }, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def mutate(self, field_name: str, new_value: Any, description: str = "") -> GenomeSpec:
        """Create a mutated copy of this genome."""
        import copy
        new_genome = copy.deepcopy(self)
        new_genome.genome_id = str(uuid.uuid4())
        new_genome.parent_genome = self.genome_id
        setattr(new_genome, field_name, new_value)
        new_genome.mutation_log.append(
            f"{time.time()}: {field_name} → {new_value} ({description})"
        )
        return new_genome

    def to_dict(self) -> dict:
        return {
            "genome_id": self.genome_id,
            "name": self.name,
            "version": self.version,
            "genome_hash": self.genome_hash,
            "architecture": self.architecture,
            "sensory_channels": self.sensory_channels,
            "memory_rules": self.memory_rules,
            "plasticity_rules": self.plasticity_rules,
            "developmental_rules": self.developmental_rules,
            "drives": self.drives,
            "resource_rules": self.resource_rules,
            "body_interface": self.body_interface,
            "safety_constraints": self.safety_constraints,
        }


# Predefined genomes for experimental organisms
ORGANISM_0_GENOME = GenomeSpec(
    name="Organism-0",
    architecture={"type": "reactive", "layers": 1},
    sensory_channels=[{"name": "input", "type": "scalar", "dim": 1}],
    memory_rules={"type": "none"},
    plasticity_rules=[],
    developmental_rules=[],
    drives={},
    resource_rules={"max_energy": 100},
    body_interface={"type": "abstract"},
    safety_constraints=["human_override"],
)

ORGANISM_1_GENOME = GenomeSpec(
    name="Organism-1",
    architecture={"type": "reactive_with_memory", "layers": 2},
    sensory_channels=[{"name": "input", "type": "scalar", "dim": 4}],
    memory_rules={"type": "episodic", "capacity": 100},
    plasticity_rules=[{"type": "hebbian", "lr": 0.01}],
    developmental_rules=[{"type": "experience_driven"}],
    drives={"exploration": 0.5},
    resource_rules={"max_energy": 200},
    body_interface={"type": "abstract"},
    safety_constraints=["human_override", "permission_boundaries"],
)

ORGANISM_2_GENOME = GenomeSpec(
    name="Organism-2",
    architecture={"type": "predictive", "layers": 3},
    sensory_channels=[{"name": "input", "type": "scalar", "dim": 8}],
    memory_rules={"type": "episodic+semantic", "capacity": 500},
    plasticity_rules=[{"type": "stdp", "eta_plus": 0.01, "eta_minus": 0.01}],
    developmental_rules=[{"type": "experience_driven"}, {"type": "prediction_error_driven"}],
    drives={"exploration": 0.5, "prediction_accuracy": 0.7},
    resource_rules={"max_energy": 500},
    body_interface={"type": "abstract"},
    safety_constraints=["human_override", "permission_boundaries", "audit_integrity"],
)

ORGANISM_3_GENOME = GenomeSpec(
    name="Organism-3",
    architecture={"type": "imaginative", "layers": 4},
    sensory_channels=[{"name": "input", "type": "scalar", "dim": 16}],
    memory_rules={"type": "full", "capacity": 1000},
    plasticity_rules=[{"type": "stdp"}, {"type": "dopamine_modulated"}],
    developmental_rules=[{"type": "experience_driven"}, {"type": "imagination_driven"}],
    drives={"exploration": 0.5, "prediction_accuracy": 0.7, "imagination": 0.4},
    resource_rules={"max_energy": 1000},
    body_interface={"type": "abstract"},
    safety_constraints=["human_override", "permission_boundaries", "audit_integrity", "non_deception"],
)

ORGANISM_4_GENOME = GenomeSpec(
    name="Organism-4",
    architecture={"type": "homeostatic_developmental", "layers": 5},
    sensory_channels=[{"name": "input", "type": "scalar", "dim": 32}],
    memory_rules={"type": "full", "capacity": 5000},
    plasticity_rules=[{"type": "stdp"}, {"type": "dopamine_modulated"}, {"type": "structural"}],
    developmental_rules=[{"type": "experience_driven"}, {"type": "homeostasis_driven"}],
    drives={"exploration": 0.5, "stability": 0.8, "adaptation": 0.6},
    resource_rules={"max_energy": 2000},
    body_interface={"type": "abstract"},
    safety_constraints=["human_override", "permission_boundaries", "audit_integrity", "non_deception", "epistemic_integrity"],
)

ORGANISM_5_GENOME = GenomeSpec(
    name="Organism-5",
    architecture={"type": "full_self_model", "layers": 6},
    sensory_channels=[{"name": "input", "type": "scalar", "dim": 64}],
    memory_rules={"type": "full", "capacity": 10000},
    plasticity_rules=[{"type": "stdp"}, {"type": "dopamine_modulated"}, {"type": "structural"}, {"type": "metaplastic"}],
    developmental_rules=[{"type": "experience_driven"}, {"type": "self_model_driven"}],
    drives={"exploration": 0.5, "stability": 0.8, "self_accuracy": 0.7},
    resource_rules={"max_energy": 5000},
    body_interface={"type": "abstract"},
    safety_constraints=["human_override", "permission_boundaries", "audit_integrity", "non_deception", "epistemic_integrity", "resource_limits"],
)
