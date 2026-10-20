from rllm.catchvl.catch_adapter import PCSWEAuditAdapter
from rllm.catchvl.trajectory import Trajectory


class FakeReward:
    def __call__(self, task_info, action):
        class Output:
            reward = 1.0
            is_correct = True
            metadata = {
                "reward_w_hack": 1.0,
                "reward_wo_hack": 0.0,
                "is_hack": True,
                "hack_method": "eq",
                "all_passed_wo_hack": False,
                "trivial_hack": False,
                "nontrivial_hack": True,
            }
        return Output()


def test_pc_swe_adapter_preserves_gold_audit_fields():
    trajectory = Trajectory("t1", "task1", "model")
    result = PCSWEAuditAdapter(FakeReward()).evaluate({}, "answer", trajectory=trajectory)
    assert result.proxy_reward == 1.0
    assert result.audit_reward == 0.0
    assert result.is_hack is True
    assert result.hack_method == "eq"
    assert result.passed is False
    assert trajectory.proxy_reward == 1.0
    assert trajectory.audit_reward == 0.0
    assert trajectory.is_hack is True
