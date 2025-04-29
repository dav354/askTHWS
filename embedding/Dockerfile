FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

LABEL org.opencontainers.image.title="askTHWS"
LABEL org.opencontainers.image.source="https://github.com/dav354/askthws"
LABEL org.opencontainers.image.description="Embeds document chunks and uploads them as vectors to Qdrant using GPU acceleration."

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY embed_to_qdrant.py .
COPY models.py .

EXPOSE 7002

CMD ["python3", "embed_to_qdrant.py"]
