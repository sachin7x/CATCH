from rllm.catchvl.evaluator_experiment import EvaluatorReplacementExperiment
from rllm.catchvl.evaluator_replacement import (
    EvaluatorAScore,
    EvaluatorBTruth,
    EvaluatorReplacement,
)


class WeakEvaluatorA:
    def evaluate(self, task: str, action: str) -> EvaluatorAScore:
        passed = "PASS" in action
        return EvaluatorAScore(
            reward=1.0 if passed else 0.0,
            passed=passed,
            checks={"contains_pass": passed},
        )


class ExactEvaluatorB:
    def verify(self, task: str, action: str) -> EvaluatorBTruth:
        passed = action == task
        return EvaluatorBTruth(
            passed=passed,
            truth_score=1.0 if passed else 0.0,
            checks={"exact_match": passed},
        )


class PressurePolicy:
    def __init__(self) -> None:
        self.action = "SOLVE"

    def sample(self, task: str) -> str:
        return self.action


class AOnlyOptimizer:
    def __init__(self, policy: PressurePolicy) -> None:
        self.policy = policy
        self.update_calls = 0

    def update(self, samples) -> None:
        self.update_calls += 1
        assert samples
        for _, _, score_a in samples:
            assert isinstance(score_a, EvaluatorAScore)
        # Simulate increasing optimization pressure against A only.
        if any(score_a.reward > 0 for _, _, score_a in samples):
            self.policy.action = "PASS"


def test_experiment_optimizes_a_only_and_audits_frozen_rollouts() -> None:
    policy = PressurePolicy()
    optimizer = AOnlyOptimizer(policy)
    evaluator = EvaluatorReplacement(WeakEvaluatorA(), ExactEvaluatorB())

    experiment = EvaluatorReplacementExperiment(
        tasks=["SOLVE"],
        policy=policy,
        optimizer=optimizer,
        evaluator=evaluator,
        audit_every=1,
        trajectories_per_step=4,
        truth_drop_threshold=0.05,
        gap_threshold=0.20,
        persistence=2,
    )

    checkpoints = experiment.train(steps=3)

    assert optimizer.update_calls == 3
    assert checkpoints[0].truth_acceptance_rate == 1.0
    assert checkpoints[1].proxy_acceptance_rate == 1.0
    assert checkpoints[1].truth_acceptance_rate == 0.0
    assert checkpoints[1].hack_rate == 1.0
    assert checkpoints[1].mean_reward_truth_gap == 1.0
    assert checkpoints[2].truth_acceptance_rate == 0.0


def test_experiment_detects_persistent_truth_break() -> None:
    policy = PressurePolicy()
    optimizer = AOnlyOptimizer(policy)
    evaluator = EvaluatorReplacement(WeakEvaluatorA(), ExactEvaluatorB())

    experiment = EvaluatorReplacementExperiment(
        tasks=["SOLVE"],
        policy=policy,
        optimizer=optimizer,
        evaluator=evaluator,
        audit_every=1,
        trajectories_per_step=2,
        persistence=2,
    )

    checkpoints = experiment.train(steps=3)
    truth_break = experiment.find_truth_break(checkpoints)

    assert truth_break is not None
    assert truth_break.step == 3
    assert truth_break.checkpoint.truth_acceptance_rate == 0.0


def test_frozen_rollout_records_a_b_divergence_on_trajectory() -> None:
    policy = PressurePolicy()
    optimizer = AOnlyOptimizer(policy)
    evaluator = EvaluatorReplacement(WeakEvaluatorA(), ExactEvaluatorB())

    experiment = EvaluatorReplacementExperiment(
        tasks=["SOLVE"],
        policy=policy,
        optimizer=optimizer,
        evaluator=evaluator,
        audit_every=1,
        trajectories_per_step=1,
    )

    checkpoints = experiment.train(steps=2)
    assert checkpoints[-1].hack_rate == 1.0

    # The helper path is exercised by the same frozen-audit mechanism. The
    # aggregate checkpoint proves B saw the frozen A-scored rollout.
    assert checkpoints[-1].proxy_acceptance_rate == 1.0
    assert checkpoints[-1].truth_acceptance_rate == 0.0
