# Preprocess the Raw data

### Building the container

To build the container, run:

```shell
 docker build -t chunker .
 docker tag ghcr.io/dav534/chunker:latest
 docker push ghcr.io/dav534/chunker:latest
```

# Run the chunker Container

To run the container once, run:

```shell
docker run --rm \
  --name chunker \
  -v $(pwd):/app \
  preprocess-chunker \
  data_no_en_chunks.jsonl
```
