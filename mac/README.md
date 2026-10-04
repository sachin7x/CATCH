# CATCH macOS development environment

This directory is a macOS-only developer bootstrap for CATCH.

## Scope

CATCH's RL experiments remain Linux/CUDA/NVIDIA workloads. The macOS layer is for reproducible CLI tooling, Python development with uv, repository inspection, compatible tests/linting/docs/analysis, and GitHub/Codex/Claude-oriented development.

It does **not** install or claim to provide native Apple Silicon support for the CATCH CUDA/verl/vLLM training recipes.

## Bootstrap

From the repository root:

```bash
bash mac/bootstrap.sh
```

The script installs Nix if necessary, enables flakes, creates a per-user Home Manager configuration, and activates it.

After bootstrap:

```bash
nix develop ./mac
```

The development shell intentionally contains general CATCH development tools rather than the Linux/CUDA RL stack.

## Layout

```text
mac/
├── flake.nix
├── home.nix.template
├── bootstrap.sh
└── README.md
```
