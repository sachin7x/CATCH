#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAC_DIR="$ROOT/mac"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[ "$(uname -s)" = "Darwin" ] || fail "This bootstrap is for macOS only."

ARCH="$(uname -m)"
case "$ARCH" in
  arm64) NIX_SYSTEM="aarch64-darwin" ;;
  x86_64) NIX_SYSTEM="x86_64-darwin" ;;
  *) fail "Unsupported architecture: $ARCH" ;;
esac

command -v xcode-select >/dev/null 2>&1 || fail "xcode-select is missing."
xcode-select -p >/dev/null 2>&1 || fail "Install Xcode Command Line Tools with: xcode-select --install"

command -v nix >/dev/null 2>&1 || fail "Nix is not installed. Install Nix separately; this project will not mutate the system Nix installation."

NIX_VERSION="$(nix --version)"
echo "Nix: $NIX_VERSION"
echo "System: $NIX_SYSTEM"

echo
echo "Checking repository flake..."
nix flake check "$MAC_DIR"

echo
echo "Checking development shell..."
nix develop "$MAC_DIR" --command bash -lc '
  set -e
  printf "git: "; git --version
  printf "gh: "; gh --version | head -1
  printf "uv: "; uv --version
  printf "ruff: "; ruff --version
  printf "node: "; node --version
'

echo
echo "CATCH macOS bootstrap verification complete."
echo
echo "Enter the development shell with:"
echo "  nix develop ./mac"
echo
echo "Important:"
echo "  Home Manager/nix-darwin remain machine-level concerns."
echo "  This repository does not overwrite your existing user configuration."
echo "  CATCH RL training remains Linux/CUDA/NVIDIA-only."
