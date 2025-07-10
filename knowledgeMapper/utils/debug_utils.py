import logging
import os
import sys

import config
import torch
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

log = logging.getLogger(__name__)


def get_system_info():
    """Gathers information about the Python, PyTorch, and hardware environment."""
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    torch_version = torch.__version__

    # Check for CUDA GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        cuda_version = torch.version.cuda
        device_info = f"[green]✔ CUDA available[/green]\n  GPU: [bold cyan]{gpu_name}[/bold cyan]\n  CUDA Version: [bold cyan]{cuda_version}[/bold cyan]"
    else:
        device_info = "[yellow]⚠ No CUDA GPU found. Using CPU.[/yellow]"

    cpu_count = os.cpu_count()

    return {
        "Python Version": py_version,
        "PyTorch Version": torch_version,
        "Device Info": device_info,
        "CPU Cores": str(cpu_count),
    }


def log_config_summary():
    """
    Logs a detailed summary of the pipeline configuration and system environment
    by printing a Rich Panel directly to the console.
    """
    console = Console()

    system_info = get_system_info()

    pipeline_text = Text.from_markup(
        f"""[bold]Language:[/bold] [yellow]{config.LANGUAGE}[/yellow]"""
    )

    embedding_text = Text.from_markup(
        f"""[bold]Model:[/bold] [yellow]{config.EMBEDDING_MODEL_NAME}[/yellow]
[bold]Device:[/bold] [yellow]{config.EMBEDDING_DEVICE}[/yellow]
[bold]Batch Size:[/bold] [yellow]{config.EMBEDDING_BATCH_SIZE}[/yellow]"""
    )

    llm_text = Text.from_markup(
        f"""[bold]Model:[/bold] [yellow]{config.OLLAMA_MODEL_NAME}[/yellow]
[bold]Host:[/bold] [yellow]{config.OLLAMA_HOST}[/yellow]
[bold]Context Size:[/bold] [yellow]{config.OLLAMA_NUM_CTX:,}[/yellow]"""
    )

    system_text = Text.from_markup(
        f"""[bold]Python:[/bold] [yellow]{system_info['Python Version']}[/yellow]
[bold]PyTorch:[/bold] [yellow]{system_info['PyTorch Version']}[/yellow]
[bold]CPUs:[/bold] [yellow]{system_info['CPU Cores']}[/yellow]
[bold]Active Device:[/bold]\n{system_info['Device Info']}"""
    )

    config_group = Group(
        Text("Pipeline Settings", style="bold blue"),
        pipeline_text,
        Rule(style="dim"),
        Text("Embedding Model", style="bold blue"),
        embedding_text,
        Rule(style="dim"),
        Text("Generation LLM", style="bold blue"),
        llm_text,
        Rule(style="dim"),
        Text("System Environment", style="bold blue"),
        system_text,
    )

    console.print(
        Panel(
            config_group,
            title="[bold yellow]🚀 Pipeline Configuration[/bold yellow]",
            border_style="green",
            expand=False,
        )
    )
