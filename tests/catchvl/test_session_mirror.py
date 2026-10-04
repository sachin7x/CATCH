from rllm.catchvl.session import SessionMirror
from rllm.catchvl.trajectory import Trajectory


def test_session_mirror_round_trip():
    mirror = SessionMirror(project_state={"branch": "feat/catch-vl-research-agent"})
    mirror.add_trajectory(Trajectory("t1", "task1", "model"))
    restored = SessionMirror.restore(mirror.export())
    assert restored.project_state == mirror.project_state
    assert restored.trajectories == mirror.trajectories
    assert restored.fingerprint() == mirror.fingerprint()
