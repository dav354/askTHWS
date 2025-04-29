# Master Container

The master container orchestrates all the other ones. First it runs the scraper, then the chunking and then the embedding.

### Building the container

To build the container, run:

```shell
docker build -t master .
docker tag master ghcr.io/dav354/master:latest
docker push ghcr.io/dav354/master:latest
```
