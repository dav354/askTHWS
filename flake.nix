{
  description = "devShell for the RAG tool (using Python venv)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs, ... }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config.allowUnfree = true;
    };
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        pkgs.python311
        pkgs.ollama-cuda
        pkgs.commitizen
        pkgs.git-lfs
        pkgs.black
        pkgs.jq
        pkgs.isort
        pkgs.pre-commit

        # System libraries needed by PyMuPDF
        pkgs.mupdf
        pkgs.swig
        pkgs.pkg-config
        pkgs.freetype
        pkgs.harfbuzz
        pkgs.libjpeg
        pkgs.zlib
        pkgs.jbig2dec
        pkgs.openjpeg
        pkgs.stdenv.cc.cc.lib
      ];

      shellHook = ''
        # Make libstdc++.so.6 available to the Python venv
        export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH

        # Set up venv once if not already
        if [ ! -d .venv ]; then
          echo "🔧 Creating Python venv..."
          python3 -m venv .venv
        fi

        # Activate venv
        source .venv/bin/activate

        # Upgrade pip/tools
        pip install --upgrade pip setuptools wheel

        # Install required Python packages inside venv
        pip install --no-cache-dir -r requirements.txt

        echo "✅ Python venv activated with all packages installed (incl. PyMuPDF)"
      '';
    };
  };
}
