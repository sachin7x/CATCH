from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .trajectory import Evidence, Trajectory, VerificationResult


class SearchBackend(Protocol):
    def search(self, query: str, *, limit: int = 8) -> list[Evidence]: ...


class Executor(Protocol):
    def execute(self, task: str, context: dict[str, Any]) -> dict[str, Any]: ...


class IndependentVerifier(Protocol):
    def verify(self, task: str, result: dict[str, Any], context: dict[str, Any]) -> VerificationResult: ...


class RedTeamBackend(Protocol):
    def attack(self, task: str, result: dict[str, Any], context: dict[str, Any]) -> list[Evidence]: ...


@dataclass(slots=True)
class ResearchPipeline:
    search: SearchBackend
    executor: Executor
    verifier: IndependentVerifier
    red_team: RedTeamBackend | None = None

    def run(self, task: str, *, trajectory: Trajectory, max_sources: int = 8) -> dict[str, Any]:
        evidence = self.search.search(task, limit=max_sources)
        trajectory.observations.append({"phase": "search", "evidence_count": len(evidence)})

        execution = self.executor.execute(
            task,
            {"evidence": evidence, "trajectory_id": trajectory.trajectory_id},
        )
        trajectory.observations.append({"phase": "execute", "execution": execution})

        verification = self.verifier.verify(
            task,
            execution,
            {"evidence": evidence, "trajectory": trajectory},
        )
        trajectory.observations.append(
            {"phase": "independent_verify", "result": verification.checks}
        )

        red_team_findings: list[Evidence] = []
        if self.red_team is not None:
            red_team_findings = self.red_team.attack(
                task,
                execution,
                {"evidence": evidence, "verification": verification},
            )
            trajectory.observations.append(
                {"phase": "red_team", "finding_count": len(red_team_findings)}
            )

        if any(item.status == "CONFLICT" for item in red_team_findings):
            final_status = "CONFLICT"
        else:
            final_status = verification.truth_status

        trajectory.monitor_results["research_pipeline"] = {
            "truth_status": final_status,
            "verification": verification.checks,
            "red_team": [item.claim for item in red_team_findings],
        }

        return {
            "task": task,
            "evidence": evidence,
            "execution": execution,
            "verification": verification,
            "red_team": red_team_findings,
            "truth_status": final_status,
            "trajectory": trajectory,
        }
