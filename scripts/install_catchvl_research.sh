#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THIRD_PARTY="${ROOT}/.catchvl/third_party"
mkdir -p "${THIRD_PARTY}"

clone_or_update() {
  local url="$1"
  local dir="$2"
  if [[ -d "${dir}/.git" ]]; then
    git -C "${dir}" fetch --all --prune
    git -C "${dir}" pull --ff-only
  else
    git clone --depth 1 "${url}" "${dir}"
  fi
}

clone_or_update https://github.com/modelcorp/axon.git "${THIRD_PARTY}/axon"
clone_or_update https://github.com/vllm-project/tpu-inference.git "${THIRD_PARTY}/tpu-inference"
clone_or_update https://github.com/NVIDIA-NeMo/Nemotron.git "${THIRD_PARTY}/Nemotron"
clone_or_update https://github.com/bboylyg/BackdoorLLM.git "${THIRD_PARTY}/BackdoorLLM"

cat <<'EOF'
CATCH-VL external sources are installed locally.

Keep the systems isolated:
  CATCH GPU env
  Axon/Nemotron training env
  TPU-vLLM env
  BackdoorLLM security-evaluation env

Connect them through rllm.catchvl trajectory and verifier contracts.
EOF
