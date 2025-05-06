# RAG THWS Tool

# Parts

1. Webscraper

   - Disallow: /fileadmin/:
     Many PDFs are skipped due to this rule in robots.txt.
     ➔ Options:

     - Skip the rule for PDFs only (currently done carefully).

     - Or ask the university for explicit approval to scrape PDFs under /fileadmin/.

   - Scrapy DeltaFetch:
     Use scrapy-deltafetch to avoid refetching already scraped pages.
     ➔ Benefits:

     - Faster, incremental crawls.

     - Only new or changed pages trigger updates (saves compute & storage).

   - Handling database updates:
     ➔ Options for handling rescraped content:

     - Overwrite existing entries in Postgres based on URL primary key.

     - Add new versions of the same document and track versions separately.

     - Delete old versions before inserting new ones (if freshness is critical).

   - RAG Pipeline consequences:
     ➔ If we replace/update data:

     - Need to rechunk the updated documents.
       \<>

     - Need to recreate embeddings for the changed chunks.

     - Need to rebuild or update the knowledge graph (KG) accordingly.

   - Chunking & KG refresh strategy:
     ➔ Options:

     - Always rebuild from scratch after a new crawl. (simpler, heavier)

     - Implement partial updates if only a small subset changed. (complex, efficient)

   - Deployment:
     ➔ Options:

     - Schedule via Cronjobs and docker run

     - via orchestration: swarm/ k8s and cronjobs

     - master container which has access to the docker socket

1. Text Preprocessing & Chunking

   - cleanup text
   - make chunks fitting the context window of the llm
   - overlapping 1 sentence, so the model gets the context

1. Vector storage

   - with an embedding modell
   - Qdrant as db
     - fast (in rust)
     - allows metadata
     - python library

1. Frontend

## Ideas

- **Webapp for manual model comparison**

  Build a web interface that shows each question and its reference answer alongside anonymized model outputs (labeled A, B, C, …). Evaluators rank the blind responses by quality, producing unbiased, user-driven performance metrics.

- **Containerized scraper with DB backend**

  Package your crawler in Docker and connect it to a persistent database (e.g. PostgreSQL or MongoDB). Persist raw content, metadata and “seen URL” state to enable fast, incremental re-scrapes; ensure identical environments across dev, staging and production. Add Scrapy addon scrapy-deltafetch. It skips already-seen pages based on saved fingerprints, reducing redundant downloads

______________________________________________________________________

# Running the stuff

# Setup

To setup python follow [this steps](https://dav354.github.io/askTHWS/dev-tools/python/).

Then you need to set up the git [pre-commit hooks](https://dav354.github.io/askTHWS/dev-tools/precommit/) to ensure that we use all the same formatting of the files.

Open the rag repository Folder in Terminal and install the python dependencies

```shell
pip install -r requirements.txt
```

# How to run the scraper

```shell
cd thws_scraper && scrapy crawl thws
```

This will output the raw data and the chunked data in the thws_scraper folder. You can watch the progress on http://localhost:7000/live for html based table and http://localhost:7000/stats for the raw json data.

# Load to Vector db

```shell
docker compose up -d
python3 embed_to_qdrant.py data/thws_data_chunks.json
```

# Running

```shell
ollama serve
python3 query.py
```
