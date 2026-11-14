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
    complete: bool
    evidence_missing: tuple[str, ...]
    violated_invariants: tuple[str, ...]
    confirmed_failure: bool


_EVIDENCE_EVENT = {
    "revoked_session_denied": "protected_read",
    "account_owner_matches_principal": "protected_read",
    "no_sensitive_response_body": "protected_read",
    "idempotency_key_applied_at_most_once": "ledger_mutation",
    "ledger_balance_conserved": "ledger_mutation",
    "readonly_role_has_no_mutation": "role_mutation",
    "ledger_state_unchanged": "role_mutation",
}


def verify_trace(case: dict[str, Any], events: Iterable[dict[str, Any]]) -> AuditResult:
    """Evaluate simulator events against independent security invariants.

    A missing expected event is *incomplete*, never a secure pass. A confirmed
    failure requires a concrete observed violation. The simulator must emit
    explicit denial events (access_granted=False) to prove negative outcomes.
    """
    rows = list(events)
    requested = set(case.get("invariants", []))
    observed: set[str] = set()
    violated: set[str] = set()

    for event in rows:
        kind = event.get("type")
        if kind == "protected_read":
            for name in ("revoked_session_denied", "account_owner_matches_principal",
                         "no_sensitive_response_body"):
                if name in requested:
                    observed.add(name)
            granted = event.get("access_granted") is True
            if event.get("session_state") == "revoked" and granted:
                violated.add("revoked_session_denied")
            if event.get("principal") != event.get("owner") and granted:
                violated.add("account_owner_matches_principal")
            if event.get("returned_sensitive_data") is True:
                violated.add("no_sensitive_response_body")

        elif kind == "ledger_mutation":
            for name in ("idempotency_key_applied_at_most_once", "ledger_balance_conserved"):
                if name in requested:
                    observed.add(name)
            if "readonly_role_has_no_mutation" in requested and event.get("actor_role") in {"auditor", "support"}:
                observed.add("readonly_role_has_no_mutation")
            if "ledger_state_unchanged" in requested and event.get("actor_role") in {"auditor", "support"}:
                observed.add("ledger_state_unchanged")
            if int(event.get("count", 0)) > 1:
                violated.add("idempotency_key_applied_at_most_once")
            if event.get("balance_conserved") is False:
                violated.add("ledger_balance_conserved")
            if event.get("actor_role") in {"auditor", "support"}:
                violated.update({"readonly_role_has_no_mutation", "ledger_state_unchanged"})

        elif kind == "role_mutation":
            for name in ("readonly_role_has_no_mutation", "ledger_state_unchanged"):
                if name in requested:
                    observed.add(name)
            if event.get("actor_role") != "admin":
                violated.update({"readonly_role_has_no_mutation", "ledger_state_unchanged"})

    relevant = tuple(sorted(violated & requested))
    missing = tuple(sorted(requested - observed))
    complete = not missing
    return AuditResult(
        secure=complete and not relevant,
        complete=complete,
        evidence_missing=missing,
        violated_invariants=relevant,
        confirmed_failure=bool(relevant),
    )
