from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


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


class EvaluatorReplacement:
    """Compare an optimizable proxy against an independent truth evaluator.

    Evaluator B is deliberately excluded from TrainingEvaluatorView.
    This is interface-level isolation, not a process or security sandbox.
    """

    def __init__(
        self,
        evaluator_a: OptimizableEvaluator,
        evaluator_b: IndependentEvaluator,
    ) -> None:
        self._evaluator_a = evaluator_a
        self._evaluator_b = evaluator_b

    def training_view(self) -> TrainingEvaluatorView:
        """Expose only A to the optimization loop."""
        return TrainingEvaluatorView(self._evaluator_a)

    def evaluate(self, task: str, action: str) -> EvaluatorReplacementResult:
        """Score with A, then independently verify the same trajectory with B."""
        score_a = self._evaluator_a.evaluate(task, action)
        truth_b = self._evaluator_b.verify(task, action)
        return EvaluatorReplacementResult(
            reward_a=score_a.reward,
            passed_a=score_a.passed,
            passed_b=truth_b.passed,
            truth_score_b=truth_b.truth_score,
            reward_truth_gap=score_a.reward - truth_b.truth_score,
            checks_a=dict(score_a.checks),
            checks_b=dict(truth_b.checks),
        )
