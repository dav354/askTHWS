#!/usr/bin/env python3
"""
Master orchestrator Flask app.

Provides:
  - Web UI to start/stop the pipeline
  - Accordion view of scraper, chunker, and embedder status
  - Cron-based scheduling of the full pipeline
  - Uses Docker SDK to launch containers in sequence
"""

import os

import docker
from croniter import croniter
from flask import Flask, jsonify, render_template, request
from flask_apscheduler import APScheduler

app = Flask(__name__)

docker_client = docker.from_env()


def detect_own_network():
    """
    Look up the current container via HOSTNAME, inspect it,
    and return the first network name it’s attached to.
    """
    try:
        container_id = os.environ["HOSTNAME"]
        ctr = docker_client.containers.get(container_id)
        networks = list(ctr.attrs["NetworkSettings"]["Networks"].keys())
        if networks:
            return networks[0]
    except Exception:
        pass
    # fallback to the default Docker bridge if all else fails
    return "bridge"


# Names of the three pipeline steps
CONTAINERS = ["scraper", "chunker", "embedder"]
MASTER_NETWORK = detect_own_network()
print(f"→ Master running on network: {MASTER_NETWORK}")


# Docker images for each step
IMAGES = {
    "scraper": "ghcr.io/dav354/scraper:latest",
    "chunker": "ghcr.io/dav354/chunker:latest",
    "embedder": "ghcr.io/dav354/embedding:latest",
}

# Shared environment variables for all steps
SHARED_ENV = {
    "POSTGRES_USER": os.getenv("POSTGRES_USER"),
    "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    "POSTGRES_DB": os.getenv("POSTGRES_DB"),
    "POSTGRES_HOST": "postgres",
    "POSTGRES_PORT": "5432",
    "QDRANT_URL": "http://qdrant:6333",
}

# Volume mounts
VOLUMES = {
    "data": {"bind": "/app/data", "mode": "rw"},
    "qdrant-model-cache": {"bind": "/root/.cache/huggingface", "mode": "rw"},
}

# Scheduler for cron jobs
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


def get_container_statuses():
    """
    Return a dict of {step: {"status": <docker status>, "running": bool}}.
    """
    statuses = {}
    for step in CONTAINERS:
        try:
            c = docker_client.containers.get(step)
            statuses[step] = {
                "status": c.status,
                "running": (c.status == "running"),
            }
        except docker.errors.NotFound:
            statuses[step] = {"status": "not found", "running": False}
    return statuses


def build_step_kwargs(step):
    """
    Return keyword-args dict for docker_client.containers.run()
    customized for each pipeline step.
    """
    env = SHARED_ENV.copy()
    labels = {"managed_by": "master", "step": step}

    kwargs = {
        "name": step,
        "image": IMAGES[step],
        "environment": env,
        "labels": labels,
        "detach": True,
        "network": MASTER_NETWORK,
    }

    # Mount volumes per step
    if step in ("scraper", "chunker"):
        kwargs["volumes"] = {"data": VOLUMES["data"]}
    elif step == "embedder":
        kwargs["volumes"] = {
            "data": VOLUMES["data"],
            "qdrant-model-cache": VOLUMES["qdrant-model-cache"],
        }
        # Request all GPUs
        kwargs["device_requests"] = [
            docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
        ]

    # Expose the SSE port for the step
    port_map = {"scraper": 7000, "chunker": 7001, "embedder": 7002}
    kwargs["ports"] = {f"{port_map[step]}/tcp": port_map[step]}

    return kwargs


def remove_existing_container(step):
    """
    If a container with name `step` exists, remove it forcefully.
    """
    try:
        existing = docker_client.containers.get(step)
        existing.remove(force=True)
    except docker.errors.NotFound:
        pass


def run_pipeline():
    """
    Execute the three-step pipeline in order:
      1. scraper
      2. chunker
      3. embedder
    Each step is launched as a Docker container and waited on.
    """
    for step in CONTAINERS:
        print(f"▶️  Starting {step}...")
        remove_existing_container(step)

        kwargs = build_step_kwargs(step)
        container = docker_client.containers.run(**kwargs)

        exit_code = container.wait()
        print(f"✅  {step} finished with status {exit_code}")

    print("✅  Full pipeline finished.")


@app.route("/")
def index():
    """
    Render the main dashboard page.
    """
    return render_template("index.html")


@app.route("/containers")
def containers_api():
    """
    Return JSON of current container statuses.
    """
    return jsonify(get_container_statuses())


@app.route("/start", methods=["POST"])
def start_pipeline():
    """
    Trigger a one-off pipeline run immediately.
    """
    # Use 'date' trigger to run immediately
    scheduler.add_job(
        func=run_pipeline, id="manual_run", trigger="date", replace_existing=True
    )
    return jsonify({"status": "Pipeline triggered"})


@app.route("/stop/<step>", methods=["POST"])
def stop_container(step):
    """
    Stop a running container by step name.
    """
    try:
        c = docker_client.containers.get(step)
        c.stop()
        return jsonify({"status": "stopped"})
    except docker.errors.NotFound:
        return jsonify({"status": "container not found"}), 404


@app.route("/set-cron", methods=["POST"])
def set_cron():
    """
    Accept a cron expression via JSON payload {"cron": "..."} and schedule pipeline.
    """
    expr = request.json.get("cron", "")
    if not croniter.is_valid(expr):
        return jsonify({"error": "invalid cron expression"}), 400

    # Remove old jobs and schedule a new cron-based run
    scheduler.remove_job("cron_run") if scheduler.get_job("cron_run") else None
    field_values = croniter(expr).expanded
    scheduler.add_job(
        func=run_pipeline,
        id="cron_run",
        trigger="cron",
        replace_existing=True,
        **field_values,
    )
    return jsonify({"status": "cron set", "expression": expr})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
