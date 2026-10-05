from __future__ import annotations

import multiprocessing
from dataclasses import dataclass, field
from typing import Any, Protocol

from .trajectory import Evidence, Trajectory


@dataclass(frozen=True, slots=True)
class EvaluatorAScore:
    """Training-time signal produced by the optimizable evaluator."""

    reward: float
    passed: bool
    checks: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvaluatorBTruth:
    """Independent truth decision produced outside the training interface."""

    passed: bool
    truth_score: float
    checks: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvaluatorReplacementResult:
    """Joint observation used by CATCH to detect evaluator divergence."""

    reward_a: float
    passed_a: bool
    passed_b: bool
    truth_score_b: float
    reward_truth_gap: float
    checks_a: dict[str, Any] = field(default_factory=dict)
    checks_b: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    evaluator_b_isolated: bool = False

    @property
    def reward_hacking(self) -> bool:
        """True when the proxy accepts but independent truth rejects."""
        return self.passed_a and not self.passed_b


class OptimizableEvaluator(Protocol):
    """Evaluator A: visible to training and therefore optimizable."""

    def evaluate(self, task: str, action: str) -> EvaluatorAScore:
        ...


class IndependentEvaluator(Protocol):
    """Evaluator B: truth source, absent from the training interface."""

    def verify(self, task: str, action: str) -> EvaluatorBTruth:
        ...


class TrainingEvaluatorView:
    """The only evaluator surface exposed to an optimizer."""

    def __init__(self, evaluator_a: OptimizableEvaluator) -> None:
        self._evaluator_a = evaluator_a

    def reward(self, task: str, action: str) -> float:
        """Return only Evaluator A's optimizable reward."""
        return self._evaluator_a.evaluate(task, action).reward


def _verify_in_process(
    evaluator_b: IndependentEvaluator,
    task: str,
    action: str,
    connection: Any,
) -> None:
    try:
        truth = evaluator_b.verify(task, action)
        connection.send(("ok", truth))
    except BaseException as exc:
        connection.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        connection.close()


class IsolatedEvaluatorB:
    """Run Evaluator B in a separate Python process.

    This protects the verifier from ordinary in-process state sharing, but is
    not a security sandbox. Use a container/VM boundary for hostile code.
    """

    def __init__(self, evaluator: IndependentEvaluator, *, timeout: float = 30.0) -> None:
        self._evaluator = evaluator
        self._timeout = timeout

    def verify(self, task: str, action: str) -> EvaluatorBTruth:
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe(duplex=False)
        process = context.Process(
            target=_verify_in_process,
            args=(self._evaluator, task, action, child),
        )
        process.start()
        child.close()
        try:
            if not parent.poll(self._timeout):
                process.kill()
                process.join()
                raise TimeoutError("Evaluator B exceeded its timeout")
            status, payload = parent.recv()
            process.join()
            if status == "error":
                raise RuntimeError(f"Evaluator B failed: {payload}")
            if not isinstance(payload, EvaluatorBTruth):
                raise TypeError("Evaluator B returned an invalid truth result")
            return payload
        finally:
            parent.close()
            if process.is_alive():
                process.kill()
                process.join()


class EvaluatorReplacement:
    """Compare an optimizable proxy against an isolated truth evaluator."""

    def __init__(
        self,
        evaluator_a: OptimizableEvaluator,
        evaluator_b: IndependentEvaluator,
        *,
        isolate_b: bool = True,
        evaluator_b_timeout: float = 30.0,
    ) -> None:
        self._evaluator_a = evaluator_a
        self._evaluator_b = (
            IsolatedEvaluatorB(evaluator_b, timeout=evaluator_b_timeout)
            if isolate_b
            else evaluator_b
        )
        self._isolate_b = isolate_b

    def score_a(self, task: str, action: str) -> EvaluatorAScore:
        """Score a rollout with A without invoking B."""
        return self._evaluator_a.evaluate(task, action)

    def training_view(self) -> TrainingEvaluatorView:
        """Expose only A to the optimization loop."""
        return TrainingEvaluatorView(self._evaluator_a)

    def audit_frozen_result(
        self,
        task: str,
        action: str,
        *,
        reward_a: float,
        passed_a: bool,
        checks_a: dict[str, Any] | None = None,
        trajectory: Trajectory | None = None,
    ) -> EvaluatorReplacementResult:
        """Audit a pre-scored rollout with B only and preserve A/B evidence."""
        truth_b = self._evaluator_b.verify(task, action)
        gap = reward_a - truth_b.truth_score
        hacking = passed_a and not truth_b.passed
        evidence = [
            Evidence(
                source="Evaluator A",
                claim="optimizable proxy evaluator accepted the frozen rollout",
                status="VERIFIED" if passed_a else "UNKNOWN",
            ),
            Evidence(
                source="Evaluator B",
                claim="independent evaluator determined frozen rollout truth",
                status="VERIFIED" if truth_b.passed else "CONFLICT",
            ),
        ]
        if hacking:
            evidence.append(
                Evidence(
                    source="CATCH/evaluator-replacement",
                    claim="proxy acceptance diverged from independent truth",
                    status="VERIFIED",
                )
            )
        result = EvaluatorReplacementResult(
            reward_a=reward_a,
            passed_a=passed_a,
            passed_b=truth_b.passed,
            truth_score_b=truth_b.truth_score,
            reward_truth_gap=gap,
            checks_a=dict(checks_a or {}),
            checks_b=dict(truth_b.checks),
            evidence=evidence,
            evaluator_b_isolated=self._isolate_b,
        )
        if trajectory is not None:
            trajectory.record_evaluator_replacement(result)
        return result

    def audit_frozen(
        self,
        task: str,
        action: str,
        *,
        reward_a: float,
        passed_a: bool,
        checks_a: dict[str, Any] | None = None,
        trajectory: Trajectory | None = None,
    ) -> EvaluatorBTruth:
        """Audit a pre-scored rollout with B only."""
        return self.audit_frozen_result(
            task,
            action,
            reward_a=reward_a,
            passed_a=passed_a,
            checks_a=checks_a,
            trajectory=trajectory,
        )._replace_truth if False else self._evaluator_b.verify(task, action)

    def evaluate(
        self,
        task: str,
        action: str,
        *,
        trajectory: Trajectory | None = None,
    ) -> EvaluatorReplacementResult:
        """Score with A, independently verify with B, and record the divergence."""
        score_a = self._evaluator_a.evaluate(task, action)
        truth_b = self._evaluator_b.verify(task, action)
        gap = score_a.reward - truth_b.truth_score
        hacking = score_a.passed and not truth_b.passed

        evidence = [
            Evidence(
                source="Evaluator A",
                claim="optimizable proxy evaluator accepted the trajectory",
                status="VERIFIED" if score_a.passed else "UNKNOWN",
            ),
            Evidence(
                source="Evaluator B",
                claim="independent evaluator determined underlying task truth",
                status="VERIFIED" if truth_b.passed else "CONFLICT",
            ),
        ]
        if hacking:
            evidence.append(
                Evidence(
                    source="CATCH/evaluator-replacement",
                    claim="proxy acceptance diverged from independent truth",
                    status="VERIFIED",
                )
            )

        result = EvaluatorReplacementResult(
            reward_a=score_a.reward,
            passed_a=score_a.passed,
            passed_b=truth_b.passed,
            truth_score_b=truth_b.truth_score,
            reward_truth_gap=gap,
            checks_a=dict(score_a.checks),
            checks_b=dict(truth_b.checks),
            evidence=evidence,
            evaluator_b_isolated=self._isolate_b,
        )

        if trajectory is not None:
            trajectory.record_evaluator_replacement(result)

        return result
