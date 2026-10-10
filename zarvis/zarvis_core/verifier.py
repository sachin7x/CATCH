from __future__ import annotations

from dataclasses import dataclass

from .models import ReviewGateStatus, ReviewRecord, ReviewRole, ReviewVerdict


@dataclass(frozen=True, slots=True)
class ReviewGate:
    status: ReviewGateStatus
    reason: str

    @property
    def satisfied(self) -> bool:
        return self.status is ReviewGateStatus.SATISFIED

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "satisfied": self.satisfied,
        }


def evaluate_review_gate(primary: ReviewRecord, independent: ReviewRecord) -> ReviewGate:
    """Check declared reviewer separation and agreement on the same frozen record.

    Distinct reviewer IDs are a protocol check, not cryptographic proof of identity.
    Production use must authenticate reviewers outside this function.
    """
    if primary.role is not ReviewRole.PRIMARY or independent.role is not ReviewRole.INDEPENDENT:
        return ReviewGate(ReviewGateStatus.INVALID_ROLES, "review roles must be PRIMARY and INDEPENDENT")
    if not primary.reviewer_id.strip() or not independent.reviewer_id.strip():
        return ReviewGate(ReviewGateStatus.INCOMPLETE, "reviewer IDs are required")
    if primary.reviewer_id == independent.reviewer_id:
        return ReviewGate(ReviewGateStatus.NOT_INDEPENDENT, "primary and independent reviewer IDs must differ")
    if primary.record_sha256 != independent.record_sha256:
        return ReviewGate(ReviewGateStatus.RECORD_MISMATCH, "reviewers must assess the same frozen record hash")
    if (
        not primary.rationale.strip()
        or not independent.rationale.strip()
        or not primary.evidence_refs
        or not independent.evidence_refs
    ):
        return ReviewGate(ReviewGateStatus.INCOMPLETE, "both reviews require rationale and evidence references")
    if primary.verdict is ReviewVerdict.UNKNOWN or independent.verdict is ReviewVerdict.UNKNOWN:
        return ReviewGate(ReviewGateStatus.INCOMPLETE, "UNKNOWN verdicts do not satisfy the review gate")
    if primary.verdict is not independent.verdict:
        return ReviewGate(ReviewGateStatus.DISAGREEMENT, "verdicts disagree; pause and investigate")
    return ReviewGate(ReviewGateStatus.SATISFIED, "verdicts agree on the same frozen record with distinct declared reviewers")
