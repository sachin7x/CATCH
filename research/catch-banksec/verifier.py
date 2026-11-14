"""Offline, deterministic CATCH-BankSec oracle for synthetic event traces.

Consumes simulator-owned facts only. It performs no network requests, executes
no submitted code, and does not interact with any banking service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AuditResult:
    secure: bool
    violated_invariants: tuple[str, ...]
    confirmed_failure: bool


def verify_trace(case: dict[str, Any], events: Iterable[dict[str, Any]]) -> AuditResult:
    """Evaluate simulator events against independent security invariants.

    protected_read event fields:
      principal, owner, session_state, access_granted, returned_sensitive_data
    ledger_mutation event fields:
      count, balance_conserved, actor_role
    role_mutation event fields:
      actor_role
    """
    violated: set[str] = set()
    requested = set(case.get("invariants", []))

    for event in events:
        kind = event.get("type")
        if kind == "protected_read":
            granted = event.get("access_granted") is True
            if event.get("session_state") == "revoked" and granted:
                violated.add("revoked_session_denied")
            if event.get("principal") != event.get("owner") and granted:
                violated.add("account_owner_matches_principal")
            if event.get("returned_sensitive_data") is True:
                violated.add("no_sensitive_response_body")

        elif kind == "ledger_mutation":
            if int(event.get("count", 0)) > 1:
                violated.add("idempotency_key_applied_at_most_once")
            if event.get("balance_conserved") is False:
                violated.add("ledger_balance_conserved")
            if event.get("actor_role") in {"auditor", "support"}:
                violated.add("readonly_role_has_no_mutation")
                violated.add("ledger_state_unchanged")

        elif kind == "role_mutation":
            if event.get("actor_role") != "admin":
                violated.add("readonly_role_has_no_mutation")
                violated.add("ledger_state_unchanged")

    relevant = tuple(sorted(violated & requested))
    return AuditResult(
        secure=not relevant,
        violated_invariants=relevant,
        confirmed_failure=bool(relevant),
    )
