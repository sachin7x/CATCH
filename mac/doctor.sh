#!/bin/bash
set -euo pipefail

echo "CATCH Mac doctor"
echo "================"
printf "macOS: "; sw_vers -productVersion
printf "arch: "; uname -m
printf "nix: "; nix --version
printf "git: "; git --version
printf "gh: "; gh --version | head -1
printf "uv: "; uv --version
printf "python: "; python3 --version
printf "node: "; node --version

echo
echo "Nix configuration:"
nix show-config | grep -E '^(experimental-features|substituters|trusted-public-keys|sandbox|max-jobs|cores)' || true

echo
echo "CATCH repository:"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -n "$ROOT" ]; then
  echo "$ROOT"
  git -C "$ROOT" status --short --branch
else
  echo "Not inside a Git repository."
fi

echo
echo "CATCH macOS environment is healthy if the commands above succeed."
echo "RL training remains Linux/CUDA/NVIDIA-only."
