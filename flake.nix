{
  description = "A Python script to download and format YouTube subtitles.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = pkgs.python3.withPackages (ps: [
        ps.yt-dlp
        ps.requests
        ps.pytest
        ps.ruff
      ]);
      # Define the default app wrapper here to simplify the program attribute
      ytSubsDlWrapper = pkgs.writeShellApplication {
        name = "yt-subs-dl-wrapper";
        runtimeInputs = [ pythonEnv ];
        text = ''exec ${pkgs.lib.getBin pythonEnv}/bin/python3 ${self}/yt_subs_dl.py "$@"'';
      };
      pytestWrapper = pkgs.writeShellApplication {
        name = "pytest-wrapper";
        runtimeInputs = [ pythonEnv ];
        text = ''
          export PYTHONPATH=${self}
          exec ${pkgs.lib.getBin pythonEnv}/bin/pytest "$@"
        '';
      };
      ruffLintWrapper = pkgs.writeShellApplication {
        name = "ruff-lint-wrapper";
        runtimeInputs = [ pythonEnv ];
        text = ''exec ${pkgs.lib.getBin pythonEnv}/bin/ruff check .'';
      };
      ruffFormatWrapper = pkgs.writeShellApplication {
        name = "ruff-format-wrapper";
        runtimeInputs = [ pythonEnv ];
        text = ''exec ${pkgs.lib.getBin pythonEnv}/bin/ruff format .'';
      };
      mdFormatWrapper = pkgs.writeShellApplication {
        name = "mdformat-wrapper";
        runtimeInputs = [ pkgs.markdownlint-cli2 ];
        text = ''exec ${pkgs.lib.getBin pkgs.markdownlint-cli2}/bin/markdownlint-cli2 "**/*.md" --fix'';
      };
      formatAllWrapper = pkgs.writeShellApplication {
        name = "format-all-wrapper";
        runtimeInputs = [ ruffFormatWrapper mdFormatWrapper ];
        text = ''
          ${ruffFormatWrapper}/bin/ruff-format-wrapper
          ${mdFormatWrapper}/bin/mdformat-wrapper
        '';
      };
      runFromRequirementsInstallWrapper = pkgs.writeShellApplication {
        name = "run-from-requirements-install-wrapper";
        runtimeInputs = [ pkgs.python3 ];
        text = ''
          #!/bin/bash
          set -euo pipefail

          # Create a temporary directory for the virtual environment
          TMP_DIR=$(mktemp -d)
          # Ensure cleanup of the temporary directory on exit
          trap 'rm -rf "$TMP_DIR"' EXIT

          # Create a virtual environment using the python3 from nixpkgs
          ${pkgs.python3}/bin/python3 -m venv "$TMP_DIR/venv"

          # Activate the virtual environment and install requirements
          "$TMP_DIR"/venv/bin/pip install -r ${self}/requirements.txt

          # Run the application with any arguments passed to nix run
          "$TMP_DIR"/venv/bin/python ${self}/yt_subs_dl.py "$@"
        '';
      };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [ pythonEnv pkgs.markdownlint-cli2 ];
      };

      formatter.${system} = pkgs.nixpkgs-fmt;

      packages.${system}.default = pkgs.writeShellApplication {
        name = "yt_subs_dl";
        runtimeInputs = [ ytSubsDlWrapper ];
        text = ''exec ${ytSubsDlWrapper}/bin/yt-subs-dl-wrapper "$@"'';
      };

      apps.${system} = {
        default = {
          type = "app";
          program = "${ytSubsDlWrapper}/bin/yt-subs-dl-wrapper";
        };
        test = {
          type = "app";
          program = "${pytestWrapper}/bin/pytest-wrapper";
        };
        lint = {
          type = "app";
          program = "${ruffLintWrapper}/bin/ruff-lint-wrapper";
        };
        format-py = {
          type = "app";
          program = "${ruffFormatWrapper}/bin/ruff-format-wrapper";
        };
        format-md = {
          type = "app";
          program = "${mdFormatWrapper}/bin/mdformat-wrapper";
        };
        format = {
          type = "app";
          program = "${formatAllWrapper}/bin/format-all-wrapper";
        };

        # use for test requirements.txt
        run-from-requirements-install = {
          type = "app";
          program = "${runFromRequirementsInstallWrapper}/bin/run-from-requirements-install-wrapper";
        };
      };
    };
}
