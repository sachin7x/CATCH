from dataclasses import dataclass

import pytest

from rllm.catchvl.control_plane import ControlPlane, VerifiedCache
from rllm.catchvl.trajectory import VerificationResult


@dataclass
class FakeRuntime:
    def execute(self, task, *, context, trajectory):
        trajectory.observations.append({"phase": "runtime"})
        return {"answer": f"done:{task}"}


@dataclass
class FakeVerifier:
    truth_status: str = "VERIFIED"

    def verify(self, task, result, *, context, trajectory):
        return VerificationResult(
            passed=self.truth_status == "VERIFIED",
            truth_status=self.truth_status,
            checks={"answer": result["answer"], "task": task},
        )


def test_verified_cache_rejects_unverified_entries() -> None:
    cache = VerifiedCache()
    with pytest.raises(ValueError, match="only VERIFIED"):
        cache.put(
            key="k",
            payload={"answer": "x"},
            truth_status="UNKNOWN",
            source_trajectory_id="t1",
        )


def test_control_plane_executes_verifies_and_caches_only_verified() -> None:
    plane = ControlPlane(FakeRuntime(), FakeVerifier())

    result = plane.execute(
        "solve",
        task_id="task-1",
        model_id="model-1",
    )

    assert result["truth_status"] == "VERIFIED"
    assert "cache_key" in result
    assert result["trajectory_id"].startswith("catch-runtime:task-1:")
    assert plane.cache.get(result["cache_key"]).truth_status == "VERIFIED"


def test_control_plane_does_not_cache_unknown() -> None:
    plane = ControlPlane(FakeRuntime(), FakeVerifier("UNKNOWN"))

    result = plane.execute(
        "solve",
        task_id="task-1",
        model_id="model-1",
    )

    assert result["truth_status"] == "UNKNOWN"
    assert "cache_key" not in result
    assert not plane.cache.snapshot()
