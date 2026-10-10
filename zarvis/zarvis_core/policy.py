from __future__ import annotations

from dataclasses import dataclass

from .models import ExecutionClass


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


class Policy:
    """Fail-closed policy: allowlisted action plus per-call approval for side effects."""

    _approval_required = {
        ExecutionClass.EXTERNAL_SIDE_EFFECT,
        ExecutionClass.PRODUCTION_DEPLOY,
    }

    def __init__(self, allowed_actions: set[str] | frozenset[str] | None = None) -> None:
        self.allowed_actions = frozenset(allowed_actions or set())

    def evaluate(
        self,
        action_name: str,
        execution_class: ExecutionClass,
        *,
        approved: bool,
    ) -> PolicyDecision:
        if action_name not in self.allowed_actions:
            return PolicyDecision(False, "action_not_allowlisted")
        if execution_class is ExecutionClass.SECRET_ACCESS:
            return PolicyDecision(False, "secret_access_disabled_in_mvp")
        if execution_class in self._approval_required and not approved:
            return PolicyDecision(False, "explicit_one_time_approval_required")
        return PolicyDecision(True, "allowlisted_and_authorized")
