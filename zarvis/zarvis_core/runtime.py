from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable

from .audit import AuditLog
from .models import (
    ActionReceipt,
    ActionRequest,
    ExecutionClass,
    ExecutionStatus,
    VerificationStatus,
    digest_json,
    utc_now,
)
from .policy import Policy

ActionHandler = Callable[[dict[str, Any]], Any]
ActionVerifier = Callable[[dict[str, Any], Any], bool]


@dataclass(frozen=True, slots=True)
class ActionSpec:
    name: str
    execution_class: ExecutionClass
    handler: ActionHandler
    verifier: ActionVerifier | None = None
    verifier_name: str | None = None


class ActionRuntime:
    """Executes only registered, allowlisted actions and returns an honest receipt."""

    def __init__(self, policy: Policy, audit: AuditLog | None = None) -> None:
        self.policy = policy
        self.audit = audit or AuditLog()
        self._specs: dict[str, ActionSpec] = {}
        self._receipts: list[ActionReceipt] = []

    def register(self, spec: ActionSpec) -> None:
        if not spec.name.strip():
            raise ValueError("action name must not be empty")
        if spec.name in self._specs:
            raise ValueError(f"action already registered: {spec.name}")
        self._specs[spec.name] = spec

    def _record(self, receipt: ActionReceipt) -> ActionReceipt:
        try:
            self.audit.append_receipt(receipt)
            receipt.audit_recorded = True
            receipt.audit_persistent = self.audit.persistent
        except Exception as exc:
            # Do not hide that an action may have run when audit persistence fails.
            receipt.reason = (receipt.reason + "; " if receipt.reason else "") + f"audit_recording_failed:{type(exc).__name__}"
        self._receipts.append(receipt)
        return receipt

    def execute(self, request: ActionRequest) -> ActionReceipt:
        started = utc_now()
        spec = self._specs.get(request.action_name)
        decision = (
            self.policy.evaluate(
                request.action_name,
                spec.execution_class,
                approved=request.approved,
            )
            if spec is not None
            else None
        )
        if spec is None or decision is None or not decision.allowed:
            reason = "action_not_registered" if spec is None else decision.reason
            now = utc_now()
            return self._record(ActionReceipt(
                receipt_id=f"rcpt_{uuid.uuid4().hex}",
                request_id=request.request_id,
                action_name=request.action_name,
                execution_status=ExecutionStatus.BLOCKED,
                handler_invoked=False,
                request_sha256=request.request_sha256,
                payload_sha256=request.payload_sha256,
                started_at=started,
                finished_at=now,
                reason=reason,
            ))

        try:
            output = spec.handler(request.payload)
        except Exception as exc:
            now = utc_now()
            return self._record(ActionReceipt(
                receipt_id=f"rcpt_{uuid.uuid4().hex}",
                request_id=request.request_id,
                action_name=request.action_name,
                execution_status=ExecutionStatus.FAILED,
                handler_invoked=True,
                request_sha256=request.request_sha256,
                payload_sha256=request.payload_sha256,
                started_at=started,
                finished_at=now,
                reason=f"handler_failed:{type(exc).__name__}",
            ))

        verification_status = VerificationStatus.UNKNOWN
        verification_evidence: dict[str, Any] = {}
        if spec.verifier is not None:
            try:
                passed = bool(spec.verifier(request.payload, output))
                verification_status = VerificationStatus.VERIFIED if passed else VerificationStatus.FAILED
                verification_evidence = {"verifier": spec.verifier_name or "action_specific"}
            except Exception as exc:
                verification_evidence = {"verifier_error": type(exc).__name__}

        return self._record(ActionReceipt(
            receipt_id=f"rcpt_{uuid.uuid4().hex}",
            request_id=request.request_id,
            action_name=request.action_name,
            execution_status=ExecutionStatus.SUCCEEDED,
            handler_invoked=True,
            request_sha256=request.request_sha256,
            payload_sha256=request.payload_sha256,
            started_at=started,
            finished_at=utc_now(),
            verification_status=verification_status,
            output=output,
            output_sha256=digest_json(output),
            verification_evidence=verification_evidence,
        ))

    def receipts(self) -> list[dict[str, Any]]:
        return [receipt.to_dict() for receipt in self._receipts]
