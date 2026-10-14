#!/usr/bin/env bash
set -euo pipefail

# This launcher targets a compatible Linux GPU host. Use the Mac for data
# validation/preparation, not for the repository's verl/FSDP training path.
: "${BASE_MODEL:?Set BASE_MODEL to the existing coding model ID or local checkpoint}"
: "${TRAIN_PARQUET:?Set TRAIN_PARQUET to the prepared train.parquet}"
: "${VAL_PARQUET:?Set VAL_PARQUET to the prepared validation.parquet}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/instruction-following-sft}"
NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
TRAIN_BATCH_SIZE="${TRAIN_BATCH_SIZE:-2}"
MICRO_BATCH_SIZE_PER_GPU="${MICRO_BATCH_SIZE_PER_GPU:-1}"
MAX_LENGTH="${MAX_LENGTH:-8192}"
LEARNING_RATE="${LEARNING_RATE:-5e-6}"
TOTAL_EPOCHS="${TOTAL_EPOCHS:-2}"

test -f "$TRAIN_PARQUET" || { echo "Missing TRAIN_PARQUET: $TRAIN_PARQUET" >&2; exit 2; }
test -f "$VAL_PARQUET" || { echo "Missing VAL_PARQUET: $VAL_PARQUET" >&2; exit 2; }
command -v python >/dev/null || { echo "python is required" >&2; exit 2; }

python -m torch.distributed.run \
  --standalone \
  --nnodes=1 \
  --nproc_per_node="$NPROC_PER_NODE" \
  "$SCRIPT_DIR/train_instruction_sft.py" \
  "model.partial_pretrain=$BASE_MODEL" \
  model.enable_gradient_checkpointing=true \
  model.lora_rank=16 \
  model.lora_alpha=32 \
  "trainer.total_epochs=$TOTAL_EPOCHS" \
  "data.train_batch_size=$TRAIN_BATCH_SIZE" \
  "data.micro_batch_size_per_gpu=$MICRO_BATCH_SIZE_PER_GPU" \
  "data.max_length=$MAX_LENGTH" \
  data.truncation=error \
  data.multiturn.enable=true \
  data.multiturn.messages_key=messages \
  "data.train_files=$TRAIN_PARQUET" \
  "data.val_files=$VAL_PARQUET" \
  "trainer.default_local_dir=$OUTPUT_DIR" \
  "trainer.logger=['console']" \
  "optim.lr=$LEARNING_RATE" \
  data.rllm.tokenize_and_mask_method=cumulative
