FROM python:3.11-slim

LABEL org.opencontainers.image.title="askTHWS"
LABEL org.opencontainers.image.source="https://github.com/dav354/askthws"
LABEL org.opencontainers.image.description="Master orchestrator that controls the full pipeline and provides a WebUI."

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
