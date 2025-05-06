FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y  --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p result

CMD ["scrapy", "crawl", "thws"]
