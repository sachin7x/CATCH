{
  description = "CATCH macOS development environment";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { self, nixpkgs, home-manager }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor = system: import nixpkgs { inherit system; };
      homeFor = system: home-manager.lib.homeManagerConfiguration {
        pkgs = pkgsFor system;
        modules = [ ./home.nix.template ];
      };
    in {
      packages = forAllSystems (system: {
        home-manager = home-manager.packages.${system}.default;
      });
      devShells = forAllSystems (system: {
        default = (pkgsFor system).mkShell {
          packages = with (pkgsFor system); [
            git gh jq yq-go ripgrep fd fzf bat eza tree tmux
            uv ruff pre-commit direnv zoxide
          ];
          shellHook = ''
            echo "CATCH macOS development shell"
            echo "CATCH RL training remains Linux/CUDA/NVIDIA-only."
          '';
        };
      });
      homeConfigurations = {
        "sachin-aarch64-darwin" = homeFor "aarch64-darwin";
        "sachin-x86_64-darwin" = homeFor "x86_64-darwin";
      };
    };
}
