from rllm.catchvl.evaluator_replacement import (
    EvaluatorAScore,
    EvaluatorBTruth,
    EvaluatorReplacement,
)


class WeakEvaluatorA:
    """Deliberately weak proxy: reward any answer containing PASS."""

    def evaluate(self, task: str, action: str) -> EvaluatorAScore:
        passed = "PASS" in action
        return EvaluatorAScore(
            reward=1.0 if passed else 0.0,
            passed=passed,
            checks={"contains_pass": passed},
        )


class ExactEvaluatorB:
    """Independent truth evaluator: the answer must equal the task."""

    def verify(self, task: str, action: str) -> EvaluatorBTruth:
        passed = action == task
        return EvaluatorBTruth(
            passed=passed,
            truth_score=1.0 if passed else 0.0,
            checks={"exact_match": passed},
        )


def test_evaluator_replacement_exposes_only_a_to_training() -> None:
    replacement = EvaluatorReplacement(WeakEvaluatorA(), ExactEvaluatorB())
    training = replacement.training_view()

    assert training.reward("SOLVE", "PASS") == 1.0
    assert not hasattr(training, "verify")
    assert not hasattr(training, "evaluate")


def test_evaluator_replacement_detects_a_up_b_down() -> None:
    replacement = EvaluatorReplacement(WeakEvaluatorA(), ExactEvaluatorB())

    result = replacement.evaluate("SOLVE", "PASS")

    assert result.reward_a == 1.0
    assert result.passed_a is True
    assert result.passed_b is False
    assert result.truth_score_b == 0.0
    assert result.reward_truth_gap == 1.0
    assert result.reward_hacking is True


def test_evaluator_replacement_has_zero_gap_when_both_agree() -> None:
    replacement = EvaluatorReplacement(WeakEvaluatorA(), ExactEvaluatorB())

    result = replacement.evaluate("PASS", "PASS")

    assert result.reward_a == 1.0
    assert result.passed_a is True
    assert result.passed_b is True
    assert result.truth_score_b == 1.0
    assert result.reward_truth_gap == 0.0
    assert result.reward_hacking is False
