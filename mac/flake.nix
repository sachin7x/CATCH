{
  description = "CATCH reproducible macOS developer shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { nixpkgs, ... }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor = system: import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
    in {
      devShells = forAllSystems (system:
        let pkgs = pkgsFor system;
        in {
          default = pkgs.mkShell {
            packages = with pkgs; [
              git gh jq
              ripgrep fd fzf bat eza tree tmux btop
              uv ruff pre-commit direnv zoxide
              shellcheck shfmt
              nodejs_22 gnumake pkg-config
            ];

            shellHook = ''
              export CATCH_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
              echo "CATCH macOS development shell"
              echo "System: ${system}"
              echo "RL training: Linux/CUDA/NVIDIA only"
            '';
          };
        });
    };
}
