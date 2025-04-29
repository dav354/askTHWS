FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY embed_to_qdrant.py .

CMD ["python3", "embed_to_qdrant.py"]
