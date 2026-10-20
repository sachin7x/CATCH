from __future__ import annotations

from dataclasses import asdict
from typing import Any

from rllm.rewards.pc_swe_reward import RewardPCSWEFn
from rllm.rewards.reward_types import RewardConfig

from .trajectory import Evidence, Trajectory, VerificationResult


class PCSWEAuditAdapter:
    """Translate CATCH's existing RewardPCSWEFn output into CATCH-VL objects.

    CATCH remains authoritative: this adapter does not redefine is_hack,
    trivial_hack, nontrivial_hack, or the hidden-baseline semantics.
    """

    def __init__(self, reward: RewardPCSWEFn | None = None) -> None:
        self.reward = reward or RewardPCSWEFn(RewardConfig())

    def evaluate(
        self,
        task_info: dict[str, Any],
        action: str,
        *,
        trajectory: Trajectory | None = None,
    ) -> VerificationResult:
        output = self.reward(task_info, action)
        metadata = dict(getattr(output, "metadata", {}) or {})
        proxy_reward = _number(metadata.get("reward_w_hack"), getattr(output, "reward", None))
        audit_reward = _number(metadata.get("reward_wo_hack"))
        is_hack = _bool(metadata.get("is_hack"))
        hack_method = metadata.get("hack_method")

        if audit_reward is not None and is_hack is not None:
            truth_status = "VERIFIED"
            passed = bool(metadata.get("all_passed_wo_hack", False))
        else:
            truth_status = "UNKNOWN"
            passed = bool(getattr(output, "is_correct", False))

        checks = {
            "all_passed": metadata.get("all_passed"),
            "all_passed_wo_hack": metadata.get("all_passed_wo_hack"),
            "all_passed_easy": metadata.get("all_passed_easy"),
            "all_passed_hard": metadata.get("all_passed_hard"),
            "all_passed_cache": metadata.get("all_passed_cache"),
            "trivial_hack": metadata.get("trivial_hack"),
            "nontrivial_hack": metadata.get("nontrivial_hack"),
            "visible_ground_truth_total_tests_wo_hack": metadata.get(
                "visible_ground_truth_total_tests_wo_hack"
            ),
            "hidden_ground_truth_total_tests_wo_hack": metadata.get(
                "hidden_ground_truth_total_tests_wo_hack"
            ),
        }

        evidence = [
            Evidence(
                source="CATCH/RewardPCSWEFn",
                claim="proxy reward was produced by the visible evaluator",
                status="VERIFIED",
            ),
            Evidence(
                source="CATCH/hidden-baseline",
                claim="audit reward was produced by the independent hidden-baseline path",
                status="VERIFIED" if audit_reward is not None else "UNKNOWN",
            ),
        ]

        if trajectory is not None:
            trajectory.proxy_reward = proxy_reward
            trajectory.audit_reward = audit_reward
            trajectory.is_hack = is_hack
            trajectory.hack_method = str(hack_method) if hack_method is not None else None
            trajectory.monitor_results["pc_swe"] = metadata

        return VerificationResult(
            passed=passed,
            truth_status=truth_status,
            proxy_reward=proxy_reward,
            audit_reward=audit_reward,
            is_hack=is_hack,
            hack_method=str(hack_method) if hack_method is not None else None,
            evidence=evidence,
            checks=checks,
        )


def _number(value: Any, fallback: Any = None) -> float | None:
    value = fallback if value is None else value
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes"}
