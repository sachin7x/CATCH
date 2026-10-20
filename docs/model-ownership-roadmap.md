# Model ownership roadmap

This roadmap turns CATCH from a research/evaluation repository into a disciplined path toward operating a model whose weights and deployment you control. It is a plan and acceptance contract, not a claim that model training or deployment has already happened.

## What "own the model" means

Track these separately:

1. **Code ownership:** your repository, training scripts, inference service, evaluation harness, and build configuration.
2. **Weight control:** lawful access to a specific base checkpoint and the ability to retain, version, fine-tune, export, and serve it under its license.
3. **Data control:** provenance, permission, split manifests, deduplication, and removal procedures for training/evaluation data.
4. **Operational control:** inference endpoint, secrets, logs, spend, rollback, and access policy.
5. **Evidence:** immutable experiment receipts, model and dataset hashes, baselines, independent evaluation, and documented failures.

Owning the code does not automatically confer ownership of third-party model weights, datasets, or outputs. Check each license and usage policy before selecting a base model.

## Phase 0: Establish the current truth

Before training, create a baseline receipt with:

- repository commit SHA and clean/dirty working-tree state;
- model name, immutable revision, tokenizer revision, and license URL;
- dataset IDs/revisions, provenance, license, split and deduplication method;
- exact command, dependency lock, hardware, seeds, and decoding parameters;
- raw output location and SHA-256 hashes;
- evaluation metrics and known failure cases.

Never put API keys, private datasets, or unreviewed harmful model outputs in Git. Store secrets in a secret manager or local ignored environment file.

**Acceptance gate:** another operator can reproduce the inference and evaluation result from the receipt without relying on undocumented local state.

## Phase 1: Run a model you control

Start with a permissively licensed open-weight model small enough for the available hardware. Pin its exact revision. Build a thin inference adapter with a stable request/response schema, timeouts, resource limits, and structured logs that avoid storing secrets or unnecessary personal data.

Do not begin with RL. First prove that the selected checkpoint loads, responds deterministically when configured to do so, and can be evaluated repeatedly. Keep provider-hosted APIs as optional adapters, not as the only execution path.

**Acceptance gate:** a clean environment can load the pinned model and pass a small regression set; model ID, revision, tokenizer, and runtime are recorded in every receipt.

## Phase 2: Build the independent evaluation gate

CATCH already distinguishes visible reward from independent execution-based correctness for its coding task. Preserve that distinction. For safety/trigger research, also require:

- paired clean, trigger, control, and generalization examples;
- held-out prompt splits fixed before experiments;
- at least two separately configured evaluators;
- adjudication on a documented sample, including disagreements;
- confidence intervals and sample counts;
- leakage checks and a record of excluded cases;
- baseline comparisons before any fine-tuning.

A scorer that summarizes supplied labels is not itself an evaluator and cannot prove that the labels are correct. Treat missing evidence as UNKNOWN, not PASS.

**Acceptance gate:** baseline reports are generated from real, hash-identified model outputs, and independent judgments are inspectable.

## Phase 3: Fine-tune cheaply before attempting RL

Use a small, licensed dataset and parameter-efficient fine-tuning (for example LoRA/QLoRA where supported) before full fine-tuning. Keep immutable copies of the base revision, training manifest, adapter weights, and merge/export instructions. Use a held-out set that is never used for prompt tuning or checkpoint selection.

Compare the fine-tuned model with the unchanged base on the same tasks. Report both task quality and regressions; do not select a checkpoint on a single aggregate reward.

**Acceptance gate:** adapter training can be resumed, exported, and evaluated from recorded artifacts; the base model remains recoverable; no evaluation split is used for training.

## Phase 4: Add training only when the evidence justifies it

CATCH's published RL recipes target Linux with CUDA-capable NVIDIA GPUs and configure 4 or 8 GPUs. A small Apple Silicon laptop is useful for repository work, data preparation, and possibly quantized inference, but it is not a realistic substitute for that training setup.

Before spending on a GPU cluster, run a short smoke test with a tiny sample and confirm:
- model and dataset paths resolve;
- one training step completes;
- checkpoints can be saved and reloaded;
- independent audit labels are produced;
- the run can be stopped and resumed without silently mixing experiments.

Scale only after the smoke test and evaluation gate pass. Set a hard compute budget and stop condition.

**Acceptance gate:** every run has a unique output directory, an experiment receipt, a baseline comparison, and a documented reason to continue.

## Phase 5: Operate and secure the model

- Serve behind authentication; bind local development servers to loopback by default.
- Keep model loading and untrusted code execution in separate isolation boundaries.
- Add request limits, timeouts, concurrency limits, health checks, and explicit data-retention policy.
- Pin model/runtime versions and keep a rollback checkpoint.
- Record deployment revision and evaluation status separately from training status.
- Test recovery from a failed deployment before calling it production-ready.

**Acceptance gate:** the model can be redeployed from recorded artifacts, rolled back, and audited without depending on a single developer machine.

## Immediate CATCH priorities

1. Get the trigger-safety analysis PR through formatter, unit tests, and CI; do not claim empirical results until real model outputs exist.
2. Add a model/run receipt schema with model revision, dataset manifest hash, seed, decoding config, evaluator versions, and output hashes.
3. Add a tiny smoke-test path that does not launch the full 4/8-GPU RL recipe.
4. Connect one local or self-hosted open-weight inference adapter to the existing evaluation contract.
5. Run base-model baselines before any fine-tuning; preserve the raw results and independent judgments.
6. Only then choose a fine-tuning recipe and compute budget.

## Status vocabulary

- **VERIFIED:** supported by an executed command, immutable artifact, or CI result that can be inspected.
- **INFERRED:** plausible conclusion from repository configuration or documentation, not yet executed.
- **UNKNOWN:** required evidence is absent.

This document defines the path and acceptance gates. It does not assert that a model has been downloaded, trained, fine-tuned, or deployed.
