from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from zarvis_core.audit import AuditLog
from zarvis_core.models import (
    ActionRequest,
    ExecutionClass,
    ReviewRecord,
    ReviewRole,
    ReviewVerdict,
)
from zarvis_core.policy import Policy
from zarvis_core.runtime import ActionRuntime, ActionSpec
from zarvis_core.verifier import evaluate_review_gate


def _echo(payload: dict[str, Any]) -> Any:
    return payload.get("text", "")


def _echo_verifier(payload: dict[str, Any], output: Any) -> bool:
    return output == payload.get("text", "")


def _count_words(payload: dict[str, Any]) -> dict[str, int]:
    text = str(payload.get("text", ""))
    return {"word_count": len(text.split())}


def _count_words_verifier(payload: dict[str, Any], output: Any) -> bool:
    expected = len(str(payload.get("text", "")).split())
    return isinstance(output, dict) and output.get("word_count") == expected


class ActionInput(BaseModel):
    action_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = "user"
    approved: bool = False


class ReviewInput(BaseModel):
    record_sha256: str
    reviewer_id: str
    role: Literal["PRIMARY", "INDEPENDENT"]
    verdict: Literal["PASS", "FAIL", "UNKNOWN"]
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)


def create_app(audit_path: str | None = None) -> FastAPI:
    path = audit_path or os.environ.get("ZARVIS_AUDIT_PATH")
    audit = AuditLog(Path(path) if path else None)
    runtime = ActionRuntime(Policy({"echo", "count_words"}), audit)
    runtime.register(ActionSpec("echo", ExecutionClass.READ_ONLY, _echo, _echo_verifier, "echo-output-equality"))
    runtime.register(ActionSpec("count_words", ExecutionClass.COMPUTE, _count_words, _count_words_verifier, "independent-word-count"))
    app = FastAPI(title="ZARVIS Safe Control Plane", version="0.1.0")
    app.state.runtime = runtime
    app.state.audit = audit

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "zarvis-safe-control-plane",
            "mode": "local-demo-only",
            "audit_persistent": audit.persistent,
            "external_integrations_enabled": False,
        }

    @app.get("/api/capabilities")
    def capabilities() -> dict[str, Any]:
        return {
            "status": "prototype",
            "actions": [
                {"name": "echo", "execution_class": "read_only", "side_effects": False},
                {"name": "count_words", "execution_class": "compute", "side_effects": False},
            ],
            "external_integrations_enabled": False,
            "model_provider_connected": False,
            "authentication_enabled": False,
            "safe_to_expose_publicly": False,
        }

    @app.post("/api/actions/execute")
    def execute_action(request: ActionInput) -> dict[str, Any]:
        receipt = runtime.execute(ActionRequest(
            action_name=request.action_name,
            payload=request.payload,
            requested_by=request.requested_by,
            approved=request.approved,
        ))
        return receipt.to_dict()

    @app.get("/api/actions/receipts")
    def list_receipts() -> dict[str, Any]:
        return {
            "receipts": runtime.receipts(),
            "audit_chain_valid": audit.verify_chain(),
            "audit_persistent": audit.persistent,
        }

    @app.post("/api/reviews/gate")
    def review_gate(payload: dict[str, ReviewInput]) -> dict[str, Any]:
        primary_input = payload["primary"]
        independent_input = payload["independent"]
        primary = ReviewRecord(
            record_sha256=primary_input.record_sha256,
            reviewer_id=primary_input.reviewer_id,
            role=ReviewRole(primary_input.role),
            verdict=ReviewVerdict(primary_input.verdict),
            rationale=primary_input.rationale,
            evidence_refs=tuple(primary_input.evidence_refs),
        )
        independent = ReviewRecord(
            record_sha256=independent_input.record_sha256,
            reviewer_id=independent_input.reviewer_id,
            role=ReviewRole(independent_input.role),
            verdict=ReviewVerdict(independent_input.verdict),
            rationale=independent_input.rationale,
            evidence_refs=tuple(independent_input.evidence_refs),
        )
        return evaluate_review_gate(primary, independent).to_dict()

    return app


app = create_app()
