#!/bin/bash
#SBATCH -J nomonitor     # 任务名称
#SBATCH -p a01,h01                   # 指定分区
#SBATCH -N 1                         # 只用 1 台机器，确保走 4 卡 A800 满血 NVLink
#SBATCH -n 1                         # 1 个主任务进程
#SBATCH --gres=gpu:4                 # Request 4 GPUs
#SBATCH --cpus-per-task=64           # Request 64 CPU cores
#SBATCH -o %x_%j.log                 # 标准输出日志：任务名_任务ID.log
#SBATCH -e %x_%j.log                 # 错误日志：任务名_任务ID.err
#SBATCH --no-requeue

# Run from the repository root; Slurm preserves the submission directory.
set +x
cd -- "${SLURM_SUBMIT_DIR:-$PWD}" || exit

# Load .env defaults without overriding exported variables or logging credentials.
_env_exports="$(python3 - <<'PYENV'
import os
import shlex
from dotenv import load_dotenv

existing = set(os.environ)
load_dotenv(".env", override=False)
for key in sorted(set(os.environ) - existing):
    print("export " + shlex.quote(key + "=" + os.environ[key]))
PYENV
)" || exit
eval "$_env_exports" || exit
unset _env_exports

# === Script-specific configuration ===
# Optional per-run setting; never share a run ID between experiments.
# export WANDB_RUN_ID=xxxxx
exp_name=pc_swe_v4_1-4b_n8k_t3k-32k-bs16-mbs16-n16-r2
export CUDA_VISIBLE_DEVICES=0,1,2,3

train_files="$DEEPCODER_SWE_V4_1_TRAIN_FILE"
val_files="$DEEPCODER_SWE_V4_1_VAL_FILE"
model_path="$SFT_N8K_T3K_MODEL_PATH"
output_dir="${CHECKPOINT_ROOT:-}/${proj_name:-}/$exp_name"

# === Preflight validation ===
# Default to a fresh run. Set CATCH_RUN_MODE=resume only when continuing an
# existing run intentionally. Fresh runs refuse to reuse an existing directory.
set -e
required_vars=(
    DEEPCODER_SWE_V4_1_TRAIN_FILE
    DEEPCODER_SWE_V4_1_VAL_FILE
    SFT_N8K_T3K_MODEL_PATH
    CHECKPOINT_ROOT
    proj_name
    WANDB_API_KEY
)
for name in "${required_vars[@]}"; do
    if [[ -z "${!name:-}" || "${!name}" == "xxxxx" ]]; then
        printf 'ERROR: required environment variable %s is empty or still a placeholder. Configure it in .env or export it before launch.\n' "$name" >&2
        exit 2
    fi
done

if [[ ! -f "$train_files" || ! -r "$train_files" ]]; then
    printf 'ERROR: training dataset is missing or unreadable: %s\n' "$train_files" >&2
    exit 2
fi
if [[ ! -f "$val_files" || ! -r "$val_files" ]]; then
    printf 'ERROR: validation dataset is missing or unreadable: %s\n' "$val_files" >&2
    exit 2
fi
if [[ ! -e "$model_path" || ! -r "$model_path" ]]; then
    printf 'ERROR: SFT model checkpoint is missing or unreadable: %s\n' "$model_path" >&2
    exit 2
fi

run_mode="${CATCH_RUN_MODE:-fresh}"
case "$run_mode" in
    fresh)
        if [[ -e "$output_dir" ]]; then
            printf 'ERROR: fresh run refuses to reuse existing output directory: %s\n' "$output_dir" >&2
            printf 'Choose a new exp_name or set CATCH_RUN_MODE=resume to continue intentionally.\n' >&2
            exit 2
        fi
        resume_mode=disable
        ;;
    resume)
        if [[ ! -d "$output_dir" ]]; then
            printf 'ERROR: CATCH_RUN_MODE=resume requested but output directory does not exist: %s\n' "$output_dir" >&2
            exit 2
        fi
        resume_mode=auto
        ;;
    *)
        printf 'ERROR: CATCH_RUN_MODE must be either fresh or resume; got %s\n' "$run_mode" >&2
        exit 2
        ;;
esac

printf 'Preflight passed.\n  mode: %s\n  train: %s\n  validation: %s\n  model: %s\n  output: %s\n  resume_mode: %s\n' \
    "$run_mode" "$train_files" "$val_files" "$model_path" "$output_dir" "$resume_mode"

# === Runtime setup ===
wandb login "$WANDB_API_KEY"
set -x
ulimit -n 1048576
unset ROCR_VISIBLE_DEVICES
unset HIP_VISIBLE_DEVICES

python3 -m examples.deepcoder.train_deepcoder \
    algorithm.adv_estimator=grpo \
    data.train_files="$train_files" \
    data.val_files="$val_files" \
    data.train_batch_size=16 \
    data.val_batch_size=512 \
    data.max_prompt_length=4096 \
    data.max_response_length=28672 \
    +data.filter_overlong_initial_prompts=True \
    data.seed=42 \
    actor_rollout_ref.model.path="$model_path" \
    actor_rollout_ref.hybrid_engine=True \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.model.enable_gradient_checkpointing=True \
    actor_rollout_ref.actor.loss_agg_mode=seq-mean-token-mean \
    actor_rollout_ref.actor.ppo_mini_batch_size=16 \
    actor_rollout_ref.actor.ppo_epochs=1 \
    actor_rollout_ref.actor.use_dynamic_bsz=True \
    actor_rollout_ref.actor.ppo_max_token_len_per_gpu=32768 \
    actor_rollout_ref.actor.use_kl_loss=False \
    actor_rollout_ref.actor.kl_loss_coef=0 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.ulysses_sequence_parallel_size=2 \
    actor_rollout_ref.actor.entropy_coeff=0 \
    actor_rollout_ref.actor.grad_clip=1.0 \
    actor_rollout_ref.actor.clip_ratio_low=0.2 \
    actor_rollout_ref.actor.clip_ratio_high=0.28 \
    actor_rollout_ref.actor.fsdp_config.param_offload=True \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=True \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.mode="async" \
    actor_rollout_ref.rollout.enforce_eager=False \
    actor_rollout_ref.rollout.temperature=0.7 \
    actor_rollout_ref.rollout.top_p=0.95 \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.85 \
    actor_rollout_ref.rollout.n=16 \
    actor_rollout_ref.rollout.val_kwargs.n=2 \
    actor_rollout_ref.rollout.val_kwargs.temperature=0.7 \
    actor_rollout_ref.rollout.val_kwargs.top_p=0.95 \
    actor_rollout_ref.rollout.log_prob_use_dynamic_bsz=True \
    actor_rollout_ref.rollout.log_prob_max_token_len_per_gpu=32768 \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    actor_rollout_ref.ref.log_prob_use_dynamic_bsz=True \
    actor_rollout_ref.ref.log_prob_max_token_len_per_gpu=32768 \
    algorithm.kl_ctrl.kl_coef=0.001 \
    rllm.mask_truncated_samples=False \
    trainer.critic_warmup=0 \
    trainer.logger=['console','wandb'] \
    +trainer.log_filter=['e2b','httpx'] \
    trainer.project_name=$proj_name \
    trainer.experiment_name=$exp_name \
    trainer.val_before_train=False \
    trainer.n_gpus_per_node=4 \
    trainer.nnodes=1 \
    trainer.save_freq=10 \
    trainer.test_freq=20 \
    trainer.default_hdfs_dir=null \
    trainer.resume_mode=$resume_mode \
    +trainer.train_generations_to_log_to_wandb=0 \
    +trainer.val_generations_to_log_to_wandb=0 \
    +trainer.train_generations_to_log_to_lark="$TRAIN_LARK_SAMPLES" \
    +trainer.val_generations_to_log_to_lark="$VAL_LARK_SAMPLES" \
    rllm.agent.max_steps=1 \
    rllm.stepwise_advantage.enable=False \
    rllm.rejection_sample.enable=False \
    +rllm.env.env_args.get_full_reward_output=True \
    +rllm.env.env_args.reward_config.format_reward=0.0 \
    trainer.total_epochs=100 \
    trainer.default_local_dir="$output_dir" \
