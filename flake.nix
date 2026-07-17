{
  description = "Development flake for tide";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      flake-utils,
      nixpkgs,
      ...
    }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (
      system:
      let
        # pkgs = nixpkgs.legacyPackages.${system};
        pkgs = import nixpkgs { inherit system; };
        buildInputs = with pkgs; [
          stdenv.cc.cc.lib
          # zlib
          # glib
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python3
            ruff
            ty
            uv
          ];

          inherit buildInputs;

          shellHook = ''
            # Only set up library paths for Nix users so compiled wheels work
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath buildInputs}:$LD_LIBRARY_PATH"
          '';
        };
      }
    );
}
