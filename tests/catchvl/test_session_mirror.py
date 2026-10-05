import pytest

from rllm.catchvl.session import SessionMirror
from rllm.catchvl.trajectory import Trajectory


def test_session_mirror_round_trip():
    mirror = SessionMirror(project_state={"branch": "feat/catch-vl-research-agent"})
    mirror.add_trajectory(Trajectory("t1", "task1", "model"))
    restored = SessionMirror.restore(mirror.export())
    assert restored.project_state == mirror.project_state
    assert restored.trajectories == mirror.trajectories
    assert restored.fingerprint() == mirror.fingerprint()


def test_session_mirror_rejects_tampered_payload():
    mirror = SessionMirror(project_state={"branch": "feat/catch-vl-research-agent"})
    exported = mirror.export()
    exported["project_state"]["branch"] = "tampered"

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        SessionMirror.restore(exported)


def test_session_mirror_requires_fingerprint():
    mirror = SessionMirror(project_state={"branch": "feat/catch-vl-research-agent"})

    with pytest.raises(ValueError, match="missing its fingerprint"):
        SessionMirror.restore({
            "schema_version": mirror.schema_version,
            "system_name": mirror.system_name,
            "capability_contract": list(mirror.capability_contract),
            "truth_policy": list(mirror.truth_policy),
            "project_state": dict(mirror.project_state),
            "durable_facts": dict(mirror.durable_facts),
            "tool_registry": dict(mirror.tool_registry),
            "trajectories": list(mirror.trajectories),
        })
