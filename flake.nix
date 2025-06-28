{
  description = "Tesseract - A video analysis tool for detecting cuts by analyzing black bar changes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    nixpkgs,
    flake-utils,
    pyproject-nix,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
        };

        python = pkgs.python313;

        tesseract = python.pkgs.callPackage ./package.nix {
          inherit (pkgs) lib ffmpeg pkg-config ninja makeWrapper;
          inherit pyproject-nix;
          python3 = python;
        };

        # Development dependencies
        devDependencies = tesseract.optional-dependencies.dev;
      in {
        packages = {
          default = tesseract;
          tesseract = tesseract;
        };

        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs;
            [
              # Python and development tools
              python
              python.pkgs.pip
              python.pkgs.setuptools
              python.pkgs.wheel

              # System dependencies
              ffmpeg
              pkg-config
              cmake
              ninja

              # Development tools
              git
              alejandra
            ]
            # Python development dependencies
            ++ devDependencies;

          shellHook = ''
            # Create virtual environment if it doesn't exist
            if [ ! -d "venv" ]; then
              echo "Creating Python virtual environment..."
              python -m venv venv
            fi

            # Activate virtual environment
            if [ -d "venv" ]; then
              echo "Activating virtual environment..."
              source venv/bin/activate

              # Install package in development mode
              pip install -e .
            fi
          '';

          # Environment variables
          PYTHONPATH = "${tesseract}/${python.sitePackages}";

          # Ensure FFmpeg is in PATH
          PATH = "${pkgs.ffmpeg}/bin:$PATH";
        };

        apps = {
          default = {
            type = "app";
            program = "${tesseract}/bin/tesseract";
          };
          tesseract = {
            type = "app";
            program = "${tesseract}/bin/tesseract";
          };
        };

        checks = {
          # Build test
          build = tesseract;

          # Import test
          python-import =
            pkgs.runCommand "python-import-test" {
              buildInputs = [tesseract python];
            } ''
              ${python}/bin/python -c "
              import tesseract
              import tesseract.cli
              import tesseract.models
              import tesseract.utils
              import tesseract.detector
              import tesseract.analyzer
              print('✅ All imports successful')
              "
              touch $out
            '';
        };
      }
    );
}
