"""NurosOS Organism Library.

Pre-built organisms at different levels of capability:
    Organism-0: Minimal viable (sensory loop only)
    Organism-1: Predictive (adds prediction)
    Organism-2: Imaginative (adds counterfactual reasoning)
    Organism-3: Self-modeling (adds metacognition)
    Organism-4: Social (adds theory of mind)
    Organism-5: Full autonomous (all capabilities)
"""

from organisms.organism_0 import Organism0
from organisms.organism_1 import Organism1
from organisms.organism_2 import Organism2
from organisms.organism_3 import Organism3
from organisms.organism_4 import Organism4
from organisms.organism_5 import Organism5

ORGANISM_LADDER = {
    0: Organism0,
    1: Organism1,
    2: Organism2,
    3: Organism3,
    4: Organism4,
    5: Organism5,
}

__all__ = [
    "Organism0", "Organism1", "Organism2",
    "Organism3", "Organism4", "Organism5",
    "ORGANISM_LADDER",
]
