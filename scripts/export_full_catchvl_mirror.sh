#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-https://github.com/sachin7x/CATCH.git}"
BRANCH="${2:-feat/catch-vl-research-agent}"
OUT="${3:-catch-vl-full-mirror}"

rm -rf "${OUT}"
git clone --branch "${BRANCH}" --single-branch "${REPO}" "${OUT}"
rm -rf "${OUT}/.git"
zip -qr "${OUT}.zip" "${OUT}"
echo "Created ${OUT}.zip"
