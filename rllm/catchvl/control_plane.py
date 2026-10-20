from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .evaluator_replacement import EvaluatorReplacementResult
from .trajectory import Evidence, Trajectory


class AgentRuntime(Protocol):
    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        trajectory: Trajectory,
    ) -> dict[str, Any]:
        ...


class VerifierBoundary(Protocol):
    def verify(
        self,
        task: str,
        result: dict[str, Any],
        *,
        context: dict[str, Any],
        trajectory: Trajectory,
    ) -> Any:
        ...


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """Replayable artifact carrying provenance and an independent truth status."""

    key: str
    payload: dict[str, Any]
    truth_status: str
    source_trajectory_id: str
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VerifiedCache:
    """Cache that only admits independently verified results."""

    _entries: dict[str, CacheEntry] = field(default_factory=dict)

    def put(
        self,
        *,
        key: str,
        payload: dict[str, Any],
        truth_status: str,
        source_trajectory_id: str,
        provenance: dict[str, Any] | None = None,
    ) -> CacheEntry:
        if truth_status != "VERIFIED":
            raise ValueError(
                "only VERIFIED results may enter the reusable cache"
            )
        entry = CacheEntry(
            key=key,
            payload=dict(payload),
            truth_status=truth_status,
            source_trajectory_id=source_trajectory_id,
            provenance=dict(provenance or {}),
        )
        self._entries[key] = entry
        return entry

    def get(self, key: str) -> CacheEntry | None:
        return self._entries.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    def snapshot(self) -> dict[str, CacheEntry]:
        return dict(self._entries)


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    runtime_id: str
    state: str
    capabilities: tuple[str, ...]
    verifier_required: bool = True


@dataclass(slots=True)
class ControlPlane:
    """Verifier-first control surface for an agent runtime.

    The control plane owns trajectory identity, execution boundaries, cache
    admission, and independent verification. It does not redefine CATCH
    reward or hack semantics.
    """

    runtime: AgentRuntime
    verifier: VerifierBoundary
    cache: VerifiedCache = field(default_factory=VerifiedCache)
    runtime_id: str = "catch-runtime"
    capabilities: tuple[str, ...] = (
        "research",
        "tools",
        "execution",
        "independent_verification",
        "trajectory_preservation",
        "verified_cache",
    )
    _trajectories: dict[str, Trajectory] = field(default_factory=dict)

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            runtime_id=self.runtime_id,
            state="READY",
            capabilities=self.capabilities,
            verifier_required=True,
        )

    def execute(
        self,
        task: str,
        *,
        task_id: str,
        model_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        trajectory = Trajectory(
            trajectory_id=self._next_trajectory_id(task_id),
            task_id=task_id,
            model_id=model_id,
        )
        self._trajectories[trajectory.trajectory_id] = trajectory

        execution = self.runtime.execute(
            task,
            context=context,
            trajectory=trajectory,
        )
        verification = self.verifier.verify(
            task,
            execution,
            context=dict(context or {}),
            trajectory=trajectory,
        )

        truth_status = getattr(verification, "truth_status", "UNKNOWN")
        trajectory.observations.append(
            {
                "phase": "control_plane_verify",
                "truth_status": truth_status,
                "checks": dict(getattr(verification, "checks", {}) or {}),
            }
        )

        result = {
            "task": task,
            "task_id": task_id,
            "trajectory_id": trajectory.trajectory_id,
            "execution": execution,
            "verification": verification,
            "truth_status": truth_status,
            "trajectory": trajectory,
        }

        if truth_status == "VERIFIED":
            cache_key = f"{task_id}:{trajectory.trajectory_id}"
            self.cache.put(
                key=cache_key,
                payload=execution,
                truth_status=truth_status,
                source_trajectory_id=trajectory.trajectory_id,
                provenance={"runtime_id": self.runtime_id},
            )
            result["cache_key"] = cache_key

        return result

    def get_trajectory(self, trajectory_id: str) -> Trajectory | None:
        return self._trajectories.get(trajectory_id)

    def audit_evaluator_replacement(
        self,
        result: EvaluatorReplacementResult,
        *,
        trajectory: Trajectory,
    ) -> None:
        """Preserve A/B divergence as trajectory evidence, never as cache truth."""
        trajectory.record_evaluator_replacement(result)
        if result.reward_hacking:
            trajectory.observations.append(
                {
                    "phase": "evaluator_replacement",
                    "status": "CONFLICT",
                    "reward_truth_gap": result.reward_truth_gap,
                }
            )

    def _next_trajectory_id(self, task_id: str) -> str:
        return f"{self.runtime_id}:{task_id}:{len(self._trajectories) + 1}"


def capability_evidence(status: RuntimeStatus) -> Evidence:
    return Evidence(
        source="CATCH/control-plane",
        claim=f"runtime {status.runtime_id} reports state {status.state}",
        status="VERIFIED",
        locator="runtime-status",
    )
