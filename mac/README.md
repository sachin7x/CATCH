# CATCH macOS development environment

This directory defines a **thin, reproducible macOS development shell** for CATCH.

## Why this is intentionally thin

The audited Mac already has an established Nix/nix-darwin/Home Manager installation, Homebrew toolchain, Claude/Codex tooling, local gateways, and other developer services. This project must not replace or overwrite that machine-level configuration.

Therefore:

- **Nix/nix-darwin/Home Manager:** machine-level configuration owned by the Mac.
- **Homebrew:** native macOS/system applications and tools already managed on the Mac.
- **uv:** Python project environments.
- **This flake:** only the reproducible CATCH developer shell.
- **CATCH RL training:** remains Linux/CUDA/NVIDIA infrastructure.

This separation prevents a project checkout from rewriting a working workstation.

## Bootstrap

From the CATCH repository root:

```bash
bash mac/bootstrap.sh
```

The bootstrap is deliberately non-destructive. It:

1. Verifies macOS and the CPU architecture.
2. Verifies Xcode Command Line Tools.
3. Requires an existing Nix installation.
4. Runs `nix flake check ./mac`.
5. Enters the flake shell temporarily and verifies the core tools.

It does **not** install Nix, modify `/etc/nix/nix.conf`, install Home Manager, or replace your shell configuration.

## Development shell

```bash
nix develop ./mac
```

The shell provides lightweight repository tooling such as Git/GitHub CLI, ripgrep/fd/fzf, uv, Ruff, pre-commit, shellcheck/shfmt, Node.js, make, and related utilities.

## Architecture boundary

macOS is the **control/development plane**.

```text
Mac
 ├── Git / GitHub
 ├── Claude / Codex / agents
 ├── repository development
 ├── local verification
 └── orchestration
       │
       ▼
Linux + NVIDIA CUDA
 ├── vLLM
 ├── verl
 ├── FlashAttention
 └── CATCH RL experiments
```

Do not attempt to make the macOS shell claim native CUDA support.

## GitHub Actions

The repository has a hosted macOS validation workflow. A self-hosted Mac runner should be a separate, explicitly trusted setup. Never expose a personal Mac runner to untrusted public pull requests.

## Files

```text
mac/
├── flake.nix
├── bootstrap.sh
└── README.md
```
