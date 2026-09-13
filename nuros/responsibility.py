"""
Responsibility Contract — Auditable Causal History.

For each externally relevant action, maintain:
    what was observed, what was inferred, what was remembered,
    what was imagined, what was predicted, what policy selected
    the action, what authorization existed, what action was
    executed, what result occurred.

This creates an auditable causal history.
Do NOT claim philosophical or legal personhood.

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from nuros.epistemic import EpistemicLabel


@dataclass
class ResponsibilityRecord:
    """
    Complete auditable record for an externally relevant action.
    
    Every field answers a specific question about the causal chain
    that led to an action. This is NOT legal personhood — it is
    a technical audit mechanism.
    """
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    # What information was available
    observed: Optional[Any] = None
    inferred: Optional[Any] = None
    remembered: Optional[Any] = None
    imagined: Optional[Any] = None
    predicted: Optional[Any] = None

    # What drove the decision
    policy_used: str = ""
    authorization: str = ""
    authority_source: str = ""

    # What happened
    action_taken: str = ""
    action_parameters: dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    success: bool = False

    # Context
    organism_id: str = ""
    environment_id: str = ""
    session_id: str = ""


class ResponsibilityContract:
    """
    The Responsibility Contract — Auditable Causal History.

    Implements the Responsibility portion of the Mind Contract Layer (MCL).
    Provides a complete, auditable record of why each action was taken,
    what information influenced it, and what authorization existed.
    """

    def __init__(self):
        self._records: dict[str, ResponsibilityRecord] = {}
        self._record_order: list[str] = []

    def record_action(
        self,
        action: str,
        observed: Any = None,
        inferred: Any = None,
        remembered: Any = None,
        imagined: Any = None,
        predicted: Any = None,
        policy_used: str = "",
        authorization: str = "",
        authority_source: str = "",
        action_parameters: Optional[dict] = None,
        result: Any = None,
        success: bool = False,
        organism_id: str = "",
    ) -> ResponsibilityRecord:
        """Record an action with full causal context."""
        rec = ResponsibilityRecord(
            observed=observed, inferred=inferred, remembered=remembered,
            imagined=imagined, predicted=predicted, policy_used=policy_used,
            authorization=authorization, authority_source=authority_source,
            action_taken=action, action_parameters=action_parameters or {},
            result=result, success=success, organism_id=organism_id,
        )
        self._records[rec.record_id] = rec
        self._record_order.append(rec.record_id)
        return rec

    def get_record(self, record_id: str) -> Optional[ResponsibilityRecord]:
        return self._records.get(record_id)

    def recent_records(self, limit: int = 10) -> list[ResponsibilityRecord]:
        ids = self._record_order[-limit:]
        return [self._records[rid] for rid in ids if rid in self._records]

    def explain(self, record_id: str) -> Optional[str]:
        """Generate a human-readable explanation of an action."""
        rec = self._records.get(record_id)
        if not rec:
            return None

        lines = [
            f"Action: {rec.action_taken}",
            f"Time: {rec.timestamp}",
            f"Policy: {rec.policy_used}",
            f"Authorization: {rec.authorization} (from {rec.authority_source})",
        ]
        if rec.observed:
            lines.append(f"Based on observation: {rec.observed}")
        if rec.inferred:
            lines.append(f"Based on inference: {rec.inferred}")
        if rec.remembered:
            lines.append(f"Based on memory: {rec.remembered}")
        if rec.imagined:
            lines.append(f"Based on imagination: {rec.imagined} (speculative)")
        if rec.predicted:
            lines.append(f"Based on prediction: {rec.predicted} (uncertain)")
        lines.append(f"Result: {rec.result} ({'success' if rec.success else 'failure'})")
        return "\n".join(lines)

    def audit_trail(self, organism_id: Optional[str] = None) -> list[dict]:
        """Return audit trail, optionally filtered by organism."""
        records = self._records.values()
        if organism_id:
            records = [r for r in records if r.organism_id == organism_id]
        return [
            {
                "record_id": r.record_id,
                "timestamp": r.timestamp,
                "action": r.action_taken,
                "policy": r.policy_used,
                "authorization": r.authorization,
                "success": r.success,
            }
            for r in records
        ]

    def summary(self) -> dict:
        return {
            "total_records": len(self._records),
            "successful_actions": sum(1 for r in self._records.values() if r.success),
            "failed_actions": sum(1 for r in self._records.values() if not r.success),
        }
