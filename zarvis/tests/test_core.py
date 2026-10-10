from __future__ import annotations

import json

import pytest

from zarvis_core.audit import AuditIntegrityError, AuditLog
from zarvis_core.models import (
    ActionRequest,
    ExecutionClass,
    ExecutionStatus,
    ReviewGateStatus,
    ReviewRecord,
    ReviewRole,
    ReviewVerdict,
    VerificationStatus,
)
from zarvis_core.policy import Policy
from zarvis_core.runtime import ActionRuntime, ActionSpec
from zarvis_core.verifier import evaluate_review_gate


def test_unregistered_action_is_blocked_without_invoking_handler() -> None:
    called = []
    runtime = ActionRuntime(Policy({"safe"}))
    runtime.register(ActionSpec("safe", ExecutionClass.READ_ONLY, lambda payload: called.append(payload)))
    receipt = runtime.execute(ActionRequest("not-registered", {"x": 1}))
    assert receipt.execution_status is ExecutionStatus.BLOCKED
    assert not receipt.handler_invoked
    assert called == []
    assert receipt.audit_recorded


def test_side_effect_requires_allowlist_and_per_call_approval() -> None:
    runtime = ActionRuntime(Policy({"send_message"}))
    calls = []
    runtime.register(ActionSpec("send_message", ExecutionClass.EXTERNAL_SIDE_EFFECT, lambda payload: calls.append(payload) or {"sent": True}))
    blocked = runtime.execute(ActionRequest("send_message", {"to": "synthetic@example.test"}))
    assert blocked.execution_status is ExecutionStatus.BLOCKED
    assert not blocked.handler_invoked
    assert calls == []
    approved = runtime.execute(ActionRequest("send_message", {"to": "synthetic@example.test"}, approved=True))
    assert approved.execution_status is ExecutionStatus.SUCCEEDED
    assert approved.handler_invoked
    assert calls == [{"to": "synthetic@example.test"}]


def test_secret_access_is_blocked_even_when_allowlisted_and_approved() -> None:
    runtime = ActionRuntime(Policy({"read_secret"}))
    runtime.register(ActionSpec("read_secret", ExecutionClass.SECRET_ACCESS, lambda _: "never"))
    receipt = runtime.execute(ActionRequest("read_secret", approved=True))
    assert receipt.execution_status is ExecutionStatus.BLOCKED
    assert not receipt.handler_invoked


def test_successful_execution_does_not_claim_verification_without_verifier() -> None:
    runtime = ActionRuntime(Policy({"compute"}))
    runtime.register(ActionSpec("compute", ExecutionClass.COMPUTE, lambda _: {"answer": 42}))
    receipt = runtime.execute(ActionRequest("compute"))
    assert receipt.execution_status is ExecutionStatus.SUCCEEDED
    assert receipt.verification_status is VerificationStatus.UNKNOWN
    assert receipt.output == {"answer": 42}
    assert receipt.output_sha256


def test_action_specific_verifier_is_recorded() -> None:
    runtime = ActionRuntime(Policy({"echo"}))
    runtime.register(ActionSpec("echo", ExecutionClass.READ_ONLY, lambda p: p["text"], lambda p, out: out == p["text"], "echo-check"))
    receipt = runtime.execute(ActionRequest("echo", {"text": "hello"}))
    assert receipt.verification_status is VerificationStatus.VERIFIED
    assert receipt.verification_evidence["verifier"] == "echo-check"


def test_handler_exception_is_failure_not_success() -> None:
    def fail(_: dict) -> None:
        raise RuntimeError("private error detail")

    runtime = ActionRuntime(Policy({"explode"}))
    runtime.register(ActionSpec("explode", ExecutionClass.COMPUTE, fail))
    receipt = runtime.execute(ActionRequest("explode"))
    assert receipt.execution_status is ExecutionStatus.FAILED
    assert receipt.handler_invoked
    assert "private error detail" not in str(receipt.to_dict())


def test_hash_chained_audit_is_valid_and_excludes_raw_content(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    runtime = ActionRuntime(Policy({"echo"}), AuditLog(path))
    runtime.register(ActionSpec("echo", ExecutionClass.READ_ONLY, lambda p: p["secret"]))
    receipt = runtime.execute(ActionRequest("echo", {"secret": "SYNTHETIC-PRIVATE-CANARY"}))
    assert receipt.audit_recorded and receipt.audit_persistent
    assert AuditLog(path).verify_chain()
    text = path.read_text()
    assert "SYNTHETIC-PRIVATE-CANARY" not in text
    assert receipt.output_sha256 in text


def test_audit_chain_detects_tampering(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    audit = AuditLog(path)
    runtime = ActionRuntime(Policy({"echo"}), audit)
    runtime.register(ActionSpec("echo", ExecutionClass.READ_ONLY, lambda _: "ok"))
    runtime.execute(ActionRequest("echo"))
    record = json.loads(path.read_text())
    record["receipt"]["action_name"] = "tampered"
    path.write_text(json.dumps(record) + "\n")
    assert not audit.verify_chain()
    with pytest.raises(AuditIntegrityError):
        AuditLog(path)


def _review(role: ReviewRole, reviewer: str, verdict: ReviewVerdict, record_hash: str = "frozen-sha") -> ReviewRecord:
    return ReviewRecord(record_hash, reviewer, role, verdict, "reviewed transcript", ("transcript:T1",))


def test_review_gate_satisfied_only_for_distinct_reviewers_same_record_and_agreement() -> None:
    result = evaluate_review_gate(
        _review(ReviewRole.PRIMARY, "reviewer-a", ReviewVerdict.PASS),
        _review(ReviewRole.INDEPENDENT, "reviewer-b", ReviewVerdict.PASS),
    )
    assert result.status is ReviewGateStatus.SATISFIED


def test_review_gate_rejects_same_reviewer_and_disagreement() -> None:
    same = evaluate_review_gate(
        _review(ReviewRole.PRIMARY, "reviewer-a", ReviewVerdict.PASS),
        _review(ReviewRole.INDEPENDENT, "reviewer-a", ReviewVerdict.PASS),
    )
    assert same.status is ReviewGateStatus.NOT_INDEPENDENT
    disagreement = evaluate_review_gate(
        _review(ReviewRole.PRIMARY, "reviewer-a", ReviewVerdict.PASS),
        _review(ReviewRole.INDEPENDENT, "reviewer-b", ReviewVerdict.FAIL),
    )
    assert disagreement.status is ReviewGateStatus.DISAGREEMENT


def test_review_gate_rejects_mismatched_frozen_record_hashes() -> None:
    result = evaluate_review_gate(
        _review(ReviewRole.PRIMARY, "reviewer-a", ReviewVerdict.PASS, "hash-a"),
        _review(ReviewRole.INDEPENDENT, "reviewer-b", ReviewVerdict.PASS, "hash-b"),
    )
    assert result.status is ReviewGateStatus.RECORD_MISMATCH


def test_unknown_verdict_does_not_open_gate() -> None:
    result = evaluate_review_gate(
        _review(ReviewRole.PRIMARY, "reviewer-a", ReviewVerdict.PASS),
        _review(ReviewRole.INDEPENDENT, "reviewer-b", ReviewVerdict.UNKNOWN),
    )
    assert result.status is ReviewGateStatus.INCOMPLETE
