{
  description = "CATCH reproducible macOS developer environment";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-26.05";
    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { self, nixpkgs, home-manager }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor = system: import nixpkgs { inherit system; config.allowUnfree = true; };
      homeFor = system: home-manager.lib.homeManagerConfiguration {
        pkgs = pkgsFor system;
        modules = [ ./home.nix ];
      };
    in {
      devShells = forAllSystems (system: {
        default = (pkgsFor system).mkShell {
          packages = with (pkgsFor system); [
            git gh jq yq-go ripgrep fd fzf bat eza tree
            tmux btop uv ruff pre-commit direnv zoxide
            shellcheck shfmt nodejs_22 gnumake pkg-config
          ];
          shellHook = ''
            export CATCH_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
            echo "CATCH macOS development shell"
            echo "System: ${system}"
            echo "RL training: Linux/CUDA/NVIDIA only"
          '';
        };
      });
      homeConfigurations = {
        "sachin-aarch64-darwin" = homeFor "aarch64-darwin";
        "sachin-x86_64-darwin" = homeFor "x86_64-darwin";
      };
    };
}
