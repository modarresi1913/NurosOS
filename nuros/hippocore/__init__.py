"""
HippoCore — episodic memory & continual-learning engine for NurosOS.

PHASE 3 of the master prompt's 10-phase migration strategy (audit §21).

This package provides an alternative ``MemoryEngine`` implementation that
*will* (in PHASES 4-6) deliver:
  - genuine pattern separation (PHASE 4)
  - fast episodic ↔ slow consolidated dual-store (PHASE 6)
  - policy-driven generative replay (PHASE 5)

In PHASE 3, ``HippoCoreMemory`` is a **thin wrapper** around
``DefaultMemoryContract`` — it produces byte-identical behavior so that:
  - the integration surface (Organism, OrganismConfig, tests) is exercised
    end-to-end against a non-default MemoryEngine class.
  - PHASE 4 can swap in real episodic encoding + pattern separation
    behind the same ABC, without touching any caller.
  - a golden-file smoke test (``test_hippocore_smoke.py``) confirms
    behavioral equivalence today, so any divergence in PHASE 4+ is
    *intentional* and *measured*.

Status: [IMPLEMENTED] — adapter scaffold + smoke test.
        [PROPOSED]    — real HippoCore mechanisms (PHASES 4-6).

LLM dependency: NONE. The HippoCore package is fully local and
deterministic, satisfying master prompt §23.
"""

from nuros.hippocore.memory_engine import HippoCoreMemory, HippoCoreMemoryConfig

__all__ = ["HippoCoreMemory", "HippoCoreMemoryConfig"]
