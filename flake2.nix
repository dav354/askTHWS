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

    python = pkgs.python311.override {
      packageOverrides = pyFinal: pyPrev: {
        torch = pyPrev.torch.override { cudaSupport = true; };
      };
    };

    pythonEnv = python.withPackages (ps:
      with ps; [
        # Scraper
        scrapy
        pymupdf
        rich
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
      ];
    };
  };
}
