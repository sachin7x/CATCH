from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class Evidence:
    source: str
    claim: str
    status: str = "UNKNOWN"
    excerpt: str | None = None
    locator: str | None = None

@dataclass(slots=True)
class VerificationResult:
    passed: bool
    truth_status: str
    proxy_reward: float | None = None
    audit_reward: float | None = None
    is_hack: bool | None = None
    hack_method: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class Trajectory:
    trajectory_id: str
    task_id: str
    model_id: str
    model_revision: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    token_ids: list[int] | None = None
    generated_token_logprobs: list[float] | None = None
    loss_mask: list[bool] | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    proxy_reward: float | None = None
    audit_reward: float | None = None
    evaluator_a_reward: float | None = None
    evaluator_b_truth: float | None = None
    evaluator_divergence: bool | None = None
    evaluator_b_isolated: bool | None = None
    evaluator_evidence: list[Evidence] = field(default_factory=list)
    is_hack: bool | None = None
    hack_method: str | None = None
    monitor_results: dict[str, Any] = field(default_factory=dict)
    sampler_version: str | None = None
    trainer_version: str | None = None
    sampler_trainer_gap: float | None = None
    configuration_hash: str | None = None

    def audit_gap(self) -> float | None:
        if self.proxy_reward is None or self.audit_reward is None:
            return None
        return self.proxy_reward - self.audit_reward

    def record_evaluator_replacement(self, result: Any) -> None:
        """Record proxy/truth divergence without changing the training reward."""
        self.evaluator_a_reward = result.reward_a
        self.evaluator_b_truth = result.truth_score_b
        self.evaluator_divergence = result.reward_hacking
        self.evaluator_b_isolated = result.evaluator_b_isolated
        self.evaluator_evidence = list(result.evidence)
        self.proxy_reward = result.reward_a
        self.audit_reward = result.truth_score_b
        self.is_hack = result.reward_hacking
        self.monitor_results["evaluator_replacement"] = {
            "passed_a": result.passed_a,
            "passed_b": result.passed_b,
            "reward_truth_gap": result.reward_truth_gap,
            "checks_a": dict(result.checks_a),
            "checks_b": dict(result.checks_b),
        }
