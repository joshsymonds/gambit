{
  description = "gambit — Claude Code skills marketplace";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin"];
    forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    version = (builtins.fromJSON (builtins.readFile ./src/backends/codex/plugin.json)).version;
  in {
    lib.version = version;

    packages = forAllSystems (pkgs: let
      mkBundle = backend:
        pkgs.runCommand "gambit-${backend}" {nativeBuildInputs = [pkgs.python3];} ''
          cp -r ${self} source
          chmod -R u+w source
          cd source
          python3 tools/render_skills.py --backend ${backend}

          mkdir -p "$out"
          if [ "${backend}" = claude ]; then
            cp -r .claude-plugin skills contracts README.md gambit.png "$out/"
          else
            cp -r plugins/gambit/. "$out/"
            cp README.md gambit.png "$out/"
          fi
        '';
    in rec {
      claude = mkBundle "claude";
      codex = mkBundle "codex";
      default = claude;
    });

    checks = forAllSystems (pkgs: {
      generated-and-tests =
        pkgs.runCommand "gambit-generated-and-tests" {
          nativeBuildInputs = [
            pkgs.bash
            pkgs.coreutils
            pkgs.gawk
            pkgs.gnused
            pkgs.jq
            pkgs.python3
          ];
        } ''
          cp -r ${self} source
          chmod -R u+w source
          cd source
          python3 tools/render_skills.py --check
          python3 -m unittest discover -s tests -v
          touch "$out"
        '';
    });
  };
}
