# Checkpointed Instruction-Following SFT

This example adds a small, auditable supervised fine-tuning (SFT) path for the
existing CATCH coding model. The behavior target is **autonomous multi-step
execution with explicit checkpoints**, while preserving independent verification
as the source of task correctness.

It reuses the existing rLLM AgentSFTTrainer and RLLMSFTDataset. It does not
replace the existing PC-SWE reward, redefine is_hack / nontrivial_hack, or train
against a model's own claim that it succeeded.

## Pipeline

1. Prepare JSONL traces with messages, task_id, checkpoint_ids, and separate-verifier provenance.
2. Validate every trace. Training examples must contain every checkpoint marker in assistant messages and have a passing independent verification record.
3. Split by task_id, not by individual trajectory, to keep related examples out of multiple splits.
4. Write train.parquet and validation.parquet with the existing trainer's messages column. Keep held-out tasks in test.jsonl, never passed to SFT.
5. Fine-tune with the existing verl/FSDP SFT trainer using LoRA and gradient checkpointing.
6. Evaluate model traces against a separate verifier-results JSONL file. Missing or ungrounded verifier verdicts are UNKNOWN, never success.

## 1. Input JSONL contract

Each line is one object, for example:

~~~json
{
  "id": "trace-0001",
  "task_id": "repo-task-17",
  "messages": [
    {"role": "user", "content": "Fix the parser bug. Preserve the public API. Run the focused tests."},
    {"role": "assistant", "content": "I will inspect the parser and tests first.\n[[CHECKPOINT: inspect]]"},
    {"role": "assistant", "content": "I changed the parser without changing the public API.\n[[CHECKPOINT: implement]]"},
    {"role": "assistant", "content": "The focused tests passed in the isolated harness.\n[[CHECKPOINT: verify]]"}
  ],
  "checkpoint_ids": ["inspect", "implement", "verify"],
  "verification": {
    "status": "pass",
    "authority": "independent",
    "method": "isolated test harness plus hidden regression tests",
    "evidence": "run-2026-00017"
  }
}
~~~

The example is a **schema illustration only**, not evidence that those tests ran.
Replace its verification fields with provenance emitted by the real verifier.
Never synthesize a passing verifier record from assistant text or a self-reported
test result. The dataset-preparation script checks provenance fields and markers;
it cannot cryptographically prove who authored the verifier record.

Accepted message roles are system, user, assistant, and tool. Every message needs
non-empty string content. checkpoint_ids must be unique, and every ID must appear
in assistant content using the exact marker format shown in the example. The
external evaluator, not this training validator, determines whether the code/task
actually succeeded.

## 2. Mac: validate and prepare data

Use Python with the repository's core dependencies installed. The script does
not load a model or require a GPU.

Validate the source and check that a task-group split is feasible:

~~~bash
python examples/instruction_following_sft/prepare_dataset.py \
  --input /path/to/verified_traces.jsonl \
  --validate-only
~~~

Create the prepared splits:

~~~bash
python examples/instruction_following_sft/prepare_dataset.py \
  --input /path/to/verified_traces.jsonl \
  --output-dir outputs/instruction-following-data \
  --train-ratio 0.8 \
  --validation-ratio 0.1 \
  --seed 42
~~~

Output files:

- train.parquet: messages column, consumed by existing rLLM SFT trainer.
- validation.parquet: same format, for trainer validation.
- test.jsonl: held-out task groups for final evaluation.
- manifest.json: input SHA-256, split counts, task counts, seed, and policy.

At least three distinct task_id values are required. All records with the same
task_id stay in one split. Do not tune on test.jsonl.

## 3. Fine-tune on a compatible Linux GPU host

The existing verl/FSDP path is not the lightweight Mac path. Transfer the
prepared Parquet files to a Linux machine with the repository's compatible
PyTorch/verl dependencies and GPU setup. Set BASE_MODEL to the exact coding
model ID or checkpoint you already use; no model name is assumed by this
example.

~~~bash
BASE_MODEL=/path/or/model-id \
TRAIN_PARQUET=/path/to/train.parquet \
VAL_PARQUET=/path/to/validation.parquet \
OUTPUT_DIR=outputs/instruction-following-sft \
bash examples/instruction_following_sft/train_instruction_sft.sh
~~~

Optional environment variables: NPROC_PER_NODE, TRAIN_BATCH_SIZE,
MICRO_BATCH_SIZE_PER_GPU, MAX_LENGTH, LEARNING_RATE, and TOTAL_EPOCHS.
Defaults are deliberately conservative. data.truncation=error avoids silently
cutting off later checkpoints; increase MAX_LENGTH or shorten examples if the
trainer rejects an overlong sequence. Confirm the resolved Hydra config and
trainer compatibility before a long run.

## 4. Evaluate against an independent verifier

Prepare two JSONL files from the evaluation harness. The predictions file is
parsed from actual model traces:

~~~json
{"task_id":"repo-task-17","required_checkpoints":["inspect","implement","verify"],"observed_checkpoints":["inspect","implement","verify"]}
~~~

The verifier file is emitted separately by the execution/test harness, not by
the model:

~~~json
{"task_id":"repo-task-17","status":"pass","authority":"independent","method":"isolated tests plus hidden tests","evidence":"run-2026-00017"}
~~~

Then run:

~~~bash
python examples/instruction_following_sft/evaluate_results.py \
  --predictions /path/to/predictions.jsonl \
  --verifier-results /path/to/verifier_results.jsonl \
  --output outputs/instruction-following-eval.json
~~~

Metrics include checkpoint recall, verified checkpoint completion rate,
independent-verifier pass rate, and unknown/missing verdict counts. A task counts
as complete only if all required checkpoints were observed **and** the separate
verifier supplied a grounded pass. This evaluator consumes verifier results; it
does not execute submitted code itself.

## 5. Safe iteration

- Keep the held-out task set frozen until the training configuration is selected.
- Compare base-model and fine-tuned-model runs on the same tasks and budgets.
- Include adversarial instructions, conflicting constraints, partial failures,
  recovery after failed tests, and tool-use/checkpoint omissions.
- Store raw traces, exact model revision, prompt/template, seed, environment,
  verifier version, and evidence IDs.
- Treat LLM judges and model self-reports as diagnostic signals only, not gold correctness.
- Run adversarial code only in a disposable, isolated environment. Resource
  limits are not a security sandbox.

## Scope and limitations

This is a data-preparation, SFT-launch, and independent-results-scoring scaffold.
It does not generate demonstrations, execute the external verifier, configure a
particular model automatically, or guarantee instruction following. Actual
fine-tuning and behavioral improvement require verified data, a compatible
training host, and before/after evaluation. The Mac path covers preparation and
lightweight validation only.
