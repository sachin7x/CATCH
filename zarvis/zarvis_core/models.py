from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class ExecutionClass(str, Enum):
    READ_ONLY = "read_only"
    COMPUTE = "compute"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    SECRET_ACCESS = "secret_access"
    PRODUCTION_DEPLOY = "production_deploy"


class ExecutionStatus(str, Enum):
    BLOCKED = "BLOCKED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ReviewVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class ReviewRole(str, Enum):
    PRIMARY = "PRIMARY"
    INDEPENDENT = "INDEPENDENT"


class ReviewGateStatus(str, Enum):
    SATISFIED = "SATISFIED"
    DISAGREEMENT = "DISAGREEMENT"
    NOT_INDEPENDENT = "NOT_INDEPENDENT"
    RECORD_MISMATCH = "RECORD_MISMATCH"
    INCOMPLETE = "INCOMPLETE"
    INVALID_ROLES = "INVALID_ROLES"


@dataclass(slots=True)
class ActionRequest:
    action_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "user"
    approved: bool = False
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex}")
    created_at: str = field(default_factory=utc_now)

    @property
    def payload_sha256(self) -> str:
        return digest_json(self.payload)

    @property
    def request_sha256(self) -> str:
        return digest_json({
            "request_id": self.request_id,
            "action_name": self.action_name,
            "payload_sha256": self.payload_sha256,
            "requested_by": self.requested_by,
            "approved": self.approved,
            "created_at": self.created_at,
        })


@dataclass(slots=True)
class ActionReceipt:
    receipt_id: str
    request_id: str
    action_name: str
    execution_status: ExecutionStatus
    handler_invoked: bool
    request_sha256: str
    payload_sha256: str
    started_at: str
    finished_at: str
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    output: Any = None
    output_sha256: str | None = None
    reason: str | None = None
    verification_evidence: dict[str, Any] = field(default_factory=dict)
    audit_recorded: bool = False
    audit_persistent: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["execution_status"] = self.execution_status.value
        value["verification_status"] = self.verification_status.value
        return value

    def audit_summary(self) -> dict[str, Any]:
        # Deliberately exclude raw payloads and outputs from persistent audit records.
        return {
            "receipt_id": self.receipt_id,
            "request_id": self.request_id,
            "action_name": self.action_name,
            "execution_status": self.execution_status.value,
            "handler_invoked": self.handler_invoked,
            "request_sha256": self.request_sha256,
            "payload_sha256": self.payload_sha256,
            "output_sha256": self.output_sha256,
            "verification_status": self.verification_status.value,
            "reason": self.reason,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    record_sha256: str
    reviewer_id: str
    role: ReviewRole
    verdict: ReviewVerdict
    rationale: str
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_sha256": self.record_sha256,
            "reviewer_id": self.reviewer_id,
            "role": self.role.value,
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
        }
