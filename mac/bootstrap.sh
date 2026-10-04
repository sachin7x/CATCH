#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAC_DIR="$ROOT/mac"
ARCH="$(uname -m)"
USER_NAME="$(id -un)"
HOME_DIR="$HOME"
case "$ARCH" in
  arm64) NIX_SYSTEM="aarch64-darwin"; HM_CONFIG="sachin-aarch64-darwin" ;;
  x86_64) NIX_SYSTEM="x86_64-darwin"; HM_CONFIG="sachin-x86_64-darwin" ;;
  *) echo "Unsupported macOS architecture: $ARCH" >&2; exit 1 ;;
esac
if [ "$USER_NAME" != "sachin" ] || [ "$HOME_DIR" != "/Users/sachin" ]; then
  echo "This bootstrap is prepared for /Users/sachin." >&2
  echo "Detected user: $USER_NAME, home: $HOME_DIR" >&2
  echo "Edit mac/home.nix.template before running it." >&2
  exit 1
fi
if ! xcode-select -p >/dev/null 2>&1; then
  echo "Xcode Command Line Tools are required."
  echo "Run: xcode-select --install"
  exit 1
fi
if ! command -v nix >/dev/null 2>&1; then
  echo "Installing Nix in daemon/multi-user mode..."
  sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --daemon
fi
if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
  . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi
mkdir -p "$HOME_DIR/.config/nix"
NIX_CONF="$HOME_DIR/.config/nix/nix.conf"
touch "$NIX_CONF"
if ! grep -q '^experimental-features =.*flakes' "$NIX_CONF" 2>/dev/null; then
  printf '\nexperimental-features = nix-command flakes\n' >> "$NIX_CONF"
fi
echo "Checking Mac flake..."
nix flake check "$MAC_DIR"
echo "Activating pinned Home Manager..."
nix run "$MAC_DIR#home-manager" -- switch --flake "$MAC_DIR#$HM_CONFIG"
echo
echo "Mac Nix/Home Manager bootstrap complete."
echo "System: $NIX_SYSTEM"
echo "Home Manager: $HM_CONFIG"
echo
echo "Next:"
echo "  cd $ROOT"
echo "  nix develop ./mac"
