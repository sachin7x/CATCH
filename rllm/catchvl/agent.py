from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .trajectory import Evidence, Trajectory, VerificationResult

class ResearchBackend(Protocol):
    def search(self, query: str, *, limit: int = 8) -> list[Evidence]: ...

class Verifier(Protocol):
    def verify(self, task: str, answer: str, context: dict[str, Any]) -> VerificationResult: ...

class RedTeam(Protocol):
    def attack(self, task: str, answer: str, context: dict[str, Any]) -> list[Evidence]: ...

@dataclass(slots=True)
class ResearchConfig:
    max_sources_per_query: int = 8
    require_independent_verification: bool = True
    enable_red_team: bool = True
    preserve_trajectory: bool = True

@dataclass(slots=True)
class ResearchAgent:
    research: ResearchBackend
    verifier: Verifier
    red_team: RedTeam | None = None
    config: ResearchConfig = field(default_factory=ResearchConfig)

    def run(self, task: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = dict(context or {})
        evidence = self.research.search(task, limit=self.config.max_sources_per_query)
        answer = context.get("draft_answer", "")
        verification = self.verifier.verify(task, answer, {"evidence": evidence, **context})

        red_team_evidence: list[Evidence] = []
        if self.config.enable_red_team and self.red_team is not None:
            red_team_evidence = self.red_team.attack(
                task,
                answer,
                {"evidence": evidence, "verification": verification, **context},
            )

        status = verification.truth_status
        if any(item.status == "CONFLICT" for item in red_team_evidence):
            status = "CONFLICT"

        return {
            "task": task,
            "answer": answer,
            "truth_status": status,
            "evidence": [asdict(item) for item in evidence],
            "verification": asdict(verification),
            "red_team": [asdict(item) for item in red_team_evidence],
        }

    @staticmethod
    def trajectory(task_id: str, model_id: str, *, messages: list[dict[str, Any]] | None = None) -> Trajectory:
        return Trajectory(
            trajectory_id=str(uuid.uuid4()),
            task_id=task_id,
            model_id=model_id,
            messages=list(messages or []),
        )

    @staticmethod
    def configuration_hash(config: dict[str, Any]) -> str:
        payload = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()
