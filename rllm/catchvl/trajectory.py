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
