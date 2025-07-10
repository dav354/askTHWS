
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, ProgressColumn
from rich.text import Text


class EstimatedTimeRemainingColumn(ProgressColumn):
    """Renders the estimated time remaining based on time per item."""

    def render(self, task: "Task") -> Text:
        """Calculate and render the estimated time remaining."""
        if (
            task.total is None
            or task.completed is None
            or task.elapsed is None
            or task.completed == 0
        ):
            return Text("ETA -", style="cyan")

        remaining_items = task.total - task.completed
        if remaining_items <= 0:
            return Text("ETA 0s", style="cyan")

        time_per_item = task.elapsed / task.completed
        estimated_remaining_time = time_per_item * remaining_items

        if estimated_remaining_time < 60:
            return Text(f"ETA {round(estimated_remaining_time)}s", style="cyan")
        elif estimated_remaining_time < 3600:
            minutes = estimated_remaining_time / 60
            return Text(f"ETA {round(minutes)}m", style="cyan")
        else:
            hours = estimated_remaining_time / 3600
            return Text(f"ETA {round(hours)}h", style="cyan")
