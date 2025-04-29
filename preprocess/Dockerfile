FROM python:3.11-slim AS builder

LABEL org.opencontainers.image.title="askTHWS"
LABEL org.opencontainers.image.source="https://github.com/dav354/askthws"
LABEL org.opencontainers.image.description="Preprocessor that chunks documents from Postgres and saves the chunks back into Postgres."

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY preprocess.py .
COPY models.py .

EXPOSE 7001

ENTRYPOINT ["python", "preprocess.py"]
