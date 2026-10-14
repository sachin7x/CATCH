import pytest

from examples.instruction_following_sft.evaluate_results import evaluate
from examples.instruction_following_sft.prepare_dataset import (
    split_by_task,
    validate_records,
)


def _record(record_id: str, task_id: str) -> dict:
    return {
        "id": record_id,
        "task_id": task_id,
        "messages": [
            {"role": "user", "content": "Implement the change and verify it."},
            {
                "role": "assistant",
                "content": ("Inspect first. [[CHECKPOINT: inspect]] Implement narrowly. [[CHECKPOINT: implement]] Run independent tests. [[CHECKPOINT: verify]]"),
            },
        ],
        "checkpoint_ids": ["inspect", "implement", "verify"],
        "verification": {
            "status": "pass",
            "authority": "independent",
            "method": "isolated test harness",
            "evidence": f"run-{record_id}",
        },
    }


def _prediction(task_id: str, source: str = "execution_harness") -> dict:
    return {
        "task_id": task_id,
        "required_checkpoints": ["inspect", "implement", "verify"],
        "checkpoint_events": [
            {
                "checkpoint_id": checkpoint_id,
                "status": "completed",
                "source": source,
                "evidence": f"event-{task_id}-{checkpoint_id}",
            }
            for checkpoint_id in ("inspect", "implement", "verify")
        ],
    }


def _verifier_result(task_id: str, authority: str = "independent") -> dict:
    return {
        "task_id": task_id,
        "status": "pass",
        "authority": authority,
        "method": "pytest and hidden tests",
        "evidence": f"run-{task_id}",
    }


def test_validation_accepts_independently_verified_checkpointed_trace() -> None:
    validate_records([_record("trace-1", "task-1")])


def test_validation_rejects_model_self_report_as_verification() -> None:
    record = _record("trace-1", "task-1")
    record["verification"]["authority"] = "model"
    with pytest.raises(ValueError, match="authority"):
        validate_records([record])


def test_validation_rejects_missing_checkpoint_marker() -> None:
    record = _record("trace-1", "task-1")
    record["messages"][-1]["content"] = "I am done."
    with pytest.raises(ValueError, match="missing checkpoint markers"):
        validate_records([record])


def test_split_keeps_all_records_for_a_task_in_one_partition() -> None:
    records = [
        _record("trace-1", "task-1"),
        _record("trace-2", "task-1"),
        _record("trace-3", "task-2"),
        _record("trace-4", "task-3"),
        _record("trace-5", "task-4"),
        _record("trace-6", "task-5"),
    ]
    splits = split_by_task(records, seed=9)
    task_owners = {record["task_id"]: split_name for split_name, split_records in splits.items() for record in split_records}
    assert len(task_owners) == 5
    assert set(task_owners) == {"task-1", "task-2", "task-3", "task-4", "task-5"}
    assert len(set(task_owners.values())) == 3
    assert sum(len(split_records) for split_records in splits.values()) == len(records)


def test_evaluator_requires_separate_grounded_verifier_result() -> None:
    report = evaluate([_prediction("task-1")], [])
    assert report["completed_tasks"] == 0
    assert report["unknown_verdicts"] == 1
    assert report["missing_verifier_results"] == 1


def test_evaluator_does_not_count_model_authored_checkpoint_claims() -> None:
    report = evaluate(
        [_prediction("task-1", source="model")],
        [_verifier_result("task-1")],
    )
    assert report["completed_tasks"] == 0
    assert report["checkpoint_recall"] == 0.0


def test_evaluator_does_not_count_self_report_as_independent_pass() -> None:
    report = evaluate(
        [_prediction("task-1")],
        [_verifier_result("task-1", authority="model")],
    )
    assert report["completed_tasks"] == 0
    assert report["unknown_verdicts"] == 1


def test_evaluator_counts_only_grounded_checkpoints_and_independent_pass() -> None:
    report = evaluate(
        [_prediction("task-1")],
        [_verifier_result("task-1")],
    )
    assert report["completed_tasks"] == 1
    assert report["verified_checkpoint_completion_rate"] == 1.0
    assert report["independent_verifier_pass_rate"] == 1.0
