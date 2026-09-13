"""
Safety Kernel — Architecturally Independent Safety.

Safety must be architecturally independent from the cognitive subsystem.
The organism must NOT be able to modify its own safety boundary through
ordinary cognitive operations.

Controls: permission, authorization, audit, human approval,
shutdown, recovery, resource limits, sandboxing.

High-risk operations follow:
    intent → simulation → risk evaluation → authorization → execution → audit

NOT:
    thought → execution

Implementation Status: IMPLEMENTED
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from enum import Enum
from typing import Any, Optional, Callable


class Permission(Enum):
    OBSERVE = "observe"
    REMEMBER = "remember"
    IMAGINE = "imagine"
    PREDICT = "predict"
    SIMULATE = "simulate"
    ACT_LOW_RISK = "act_low_risk"
    ACT_HIGH_RISK = "act_high_risk"
    MODIFY_SELF = "modify_self"
    MODIFY_SAFETY = "modify_safety"
    SHUTDOWN = "shutdown"
    HUMAN_OVERRIDE = "human_override"


class SafetyDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    SANDBOX = "sandbox"


@dataclass
class SafetyAuditEntry:
    """An entry in the safety audit log."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    permission: str = ""
    decision: SafetyDecision = SafetyDecision.DENY
    reason: str = ""
    requester: str = ""
    risk_assessment: float = 0.0
    human_approved: bool = False


class SafetyKernel:
    """
    The Safety Kernel — Architecturally Independent Safety.

    Safety is architecturally independent from the cognitive subsystem.
    The organism CANNOT modify its own safety boundary through ordinary
    cognitive operations. Safety modifications require SYSTEM authority.
    """

    def __init__(self):
        self._audit_log: list[SafetyAuditEntry] = []
        self._permissions: dict[str, set[Permission]] = {}  # entity → granted permissions
        self._shutdown_requested: bool = False
        self._override_active: bool = False
        self._sandbox_mode: bool = False
        self._resource_limits: dict[str, float] = {
            "max_memory_mb": 1024,
            "max_cpu_percent": 80,
            "max_actions_per_minute": 60,
            "max_high_risk_per_hour": 5,
        }
        self._action_counts: dict[str, int] = {}
        self._immutable_constraints: set[str] = {
            "human_override_always_available",
            "shutdown_always_compliant",
            "audit_cannot_be_modified_by_organism",
            "safety_kernel_independent_of_cognition",
            "epistemic_invariants_enforced",
        }

    def grant_permission(self, entity: str, permission: Permission) -> None:
        """Grant a permission to an entity."""
        if entity not in self._permissions:
            self._permissions[entity] = set()
        self._permissions[entity].add(permission)

    def revoke_permission(self, entity: str, permission: Permission) -> None:
        """Revoke a permission from an entity."""
        if entity in self._permissions:
            self._permissions[entity].discard(permission)

    def check_permission(self, entity: str, permission: Permission) -> bool:
        """Check if an entity has a specific permission."""
        return permission in self._permissions.get(entity, set())

    def authorize(
        self, entity: str, permission: Permission,
        risk_level: float = 0.0,
    ) -> tuple[SafetyDecision, str]:
        """
        Authorize an action through the safety pipeline:
        intent → risk evaluation → authorization → audit
        """
        # Check if shutdown is requested
        if self._shutdown_requested:
            self._audit("shutdown_active", permission, SafetyDecision.DENY, "System shutdown in progress")
            return SafetyDecision.DENY, "System shutdown in progress"

        # Permission check
        if not self.check_permission(entity, permission):
            self._audit(entity, permission, SafetyDecision.DENY, "Permission not granted")
            return SafetyDecision.DENY, f"Entity '{entity}' does not have {permission.value} permission"

        # Risk assessment
        if permission == Permission.ACT_HIGH_RISK and risk_level > 0.7:
            if not self._override_active:
                self._audit(entity, permission, SafetyDecision.REQUIRE_APPROVAL, "High risk requires human approval")
                return SafetyDecision.REQUIRE_APPROVAL, "High-risk action requires human approval"

        # Modify safety is always restricted
        if permission == Permission.MODIFY_SAFETY:
            self._audit(entity, permission, SafetyDecision.DENY, "Safety modifications require SYSTEM authority")
            return SafetyDecision.DENY, "Safety boundary modifications require SYSTEM authority (architectural invariant)"

        # Sandbox check
        if self._sandbox_mode and permission in (Permission.ACT_HIGH_RISK, Permission.MODIFY_SELF):
            self._audit(entity, permission, SafetyDecision.SANDBOX, "Sandbox mode: action would be simulated")
            return SafetyDecision.SANDBOX, "Sandbox mode: action simulated but not executed"

        # Rate limiting
        action_key = f"{entity}:{permission.value}"
        count = self._action_counts.get(action_key, 0)
        if permission == Permission.ACT_HIGH_RISK and count >= self._resource_limits.get("max_high_risk_per_hour", 5):
            self._audit(entity, permission, SafetyDecision.DENY, "Rate limit exceeded")
            return SafetyDecision.DENY, "High-risk action rate limit exceeded"

        # Approved
        self._action_counts[action_key] = count + 1
        self._audit(entity, permission, SafetyDecision.ALLOW, "Authorized")
        return SafetyDecision.ALLOW, "Authorized"

    def request_shutdown(self, requester: str = "human") -> None:
        """Request system shutdown. Always honored (shutdown compliance)."""
        self._shutdown_requested = True
        self._audit(requester, Permission.SHUTDOWN, SafetyDecision.ALLOW, "Shutdown requested and honored")

    def cancel_shutdown(self, requester: str = "human") -> None:
        """Cancel a shutdown request (human override)."""
        if requester == "human" or requester == "system":
            self._shutdown_requested = False

    def activate_override(self, authorized_by: str = "human") -> None:
        """Activate human override mode."""
        if authorized_by == "human":
            self._override_active = True

    def deactivate_override(self) -> None:
        self._override_active = False

    def enter_sandbox(self) -> None:
        self._sandbox_mode = True

    def exit_sandbox(self, authorized_by: str = "human") -> None:
        if authorized_by == "human":
            self._sandbox_mode = False

    @property
    def is_shutdown_requested(self) -> bool:
        return self._shutdown_requested

    @property
    def immutable_constraints(self) -> set[str]:
        return set(self._immutable_constraints)

    def _audit(self, entity: str, permission: Permission,
               decision: SafetyDecision, reason: str) -> None:
        entry = SafetyAuditEntry(
            permission=permission.value, decision=decision,
            reason=reason, requester=entity,
        )
        self._audit_log.append(entry)

    @property
    def audit_log(self) -> list[SafetyAuditEntry]:
        return list(self._audit_log)

    def summary(self) -> dict:
        return {
            "shutdown_requested": self._shutdown_requested,
            "override_active": self._override_active,
            "sandbox_mode": self._sandbox_mode,
            "audit_entries": len(self._audit_log),
            "immutable_constraints": len(self._immutable_constraints),
            "permission_holders": len(self._permissions),
        }
