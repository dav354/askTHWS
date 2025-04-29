{
  description = "devShell for the RAG tool";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = {
    self,
    nixpkgs,
    ...
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      config.allowUnfree = true;
    };

    pythonEnv = pkgs.python311.withPackages (ps:
      with ps; [
        # Scraper
        scrapy
        pymupdf
        torch-bin
        # compare_scraping_result
        deepdiff
        # Preprocess
        langdetect
        langchain
        pandas
        # Embedding
        sentence-transformers
        tqdm
        qdrant-client
        # Api server
        fastapi
        uvicorn
      ]);
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = [
        pythonEnv
        pkgs.ollama-cuda
        pkgs.commitizen
        pkgs.black
        pkgs.git-lfs
        pkgs.jq
        pkgs.isort
        pkgs.nvidia-docker
        pkgs.pre-commit
      ];

      shellHook = ''
        export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
      '';
    };
  };
}
