# Embedding to Qdrant

### Building the container

To build the container, run:

```shell
docker build -t embedding .
docker tag embedding ghcr.io/dav354/embedding:latest
docker push ghcr.io/dav354/embedding:latest
```

# Run the embedding Container

To run the container once, run:

```shell
docker run --rm \
  --name embedder \
  --device nvidia.com/gpu=all \
  -v $(pwd)/thws_scraper/result:/app/data \
  -v qdrant-model-cache:/root/.cache/huggingface \
  embed-to-qdrant \
  python3 embed_to_qdrant.py data/data_no_en_chunks.jsonl
```
