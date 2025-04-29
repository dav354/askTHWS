FROM python:3.11-slim AS builder

LABEL org.opencontainers.image.title="askTHWS"
LABEL org.opencontainers.image.source="https://github.com/dav354/askthws"
LABEL org.opencontainers.image.description="Scraper that fetches raw pages and stores them into Postgres."

WORKDIR /app

RUN apt-get update && apt-get install -y  --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip &&\
    pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p result

CMD ["scrapy", "crawl", "thws"]
