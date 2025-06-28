{
  lib,
  python3,
  pyproject-nix,
  ffmpeg,
  pkg-config,
  makeWrapper,
  ninja,
}: let
  # Load project metadata from pyproject.toml
  project = pyproject-nix.lib.project.loadPyproject {
    projectRoot = ./.;
  };
in
  python3.pkgs.buildPythonPackage {
    pname = project.pyproject.project.name;
    version = project.pyproject.project.version;
    pyproject = true;

    src = lib.cleanSource ./.;

    # Build dependencies
    build-system = with python3.pkgs; [
      setuptools
      wheel
    ];

    dependencies = with python3.pkgs; [
      opencv-python
      numpy
      rich
    ];

    nativeBuildInputs = [
      pkg-config
      ninja
      makeWrapper
    ];

    buildInputs = [
      ffmpeg
    ];

    # Ensure FFmpeg is available at runtime
    postInstall = ''
      wrapProgram $out/bin/tesseract \
        --prefix PATH : ${lib.makeBinPath [ffmpeg]}
    '';

    # Import checks
    pythonImportsCheck = [
      "tesseract"
      "tesseract.cli"
      "tesseract.models"
      "tesseract.utils"
      "tesseract.detector"
      "tesseract.analyzer"
    ];

    # Skip tests for now
    doCheck = false;

    # Pass through optional dependencies for dev shell
    passthru.optional-dependencies = {
      dev = with python3.pkgs; [
        pytest
        pytest-cov
        black
        isort
        flake8
        mypy
      ];
    };

    meta = with lib; {
      description = project.pyproject.project.description;
      homepage = project.pyproject.project.urls.Homepage or "https://github.com/CPlusPatch/tesseract";
      license = licenses.mit;
      maintainers = [];
      platforms = platforms.unix;
      mainProgram = "tesseract";
    };
  }
