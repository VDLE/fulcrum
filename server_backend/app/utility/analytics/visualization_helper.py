import matplotlib.pyplot as plt
import numpy as np
import base64
import logging
from io import BytesIO
from matplotlib.figure import Figure
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def plot_to_base64(plot_function, dpi=100, format="png", quality=90):
    # Converts matplotlib plot to base64 string for embedding in web pages
    try:
        # Make the figure
        plt.figure(figsize=(10, 6), dpi=dpi)
        plot_function()

        # Save to memory buffer
        buf = BytesIO()

        # Handle different formats
        if format.lower() in ("jpg", "jpeg"):
            plt.savefig(
                buf, format=format, bbox_inches="tight", dpi=dpi, quality=quality
            )
        elif format.lower() == "webp":
            plt.savefig(
                buf, format=format, bbox_inches="tight", dpi=dpi, quality=quality
            )
        else:
            # Default to PNG
            plt.savefig(
                buf,
                format="png",
                bbox_inches="tight",
                dpi=dpi,
                transparent=False,
                optimize=True,
                compress_level=9,
            )

        plt.close()

        # Convert to base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")

        return img_str
    except Exception as e:
        logger.error(f"Error generating plot: {str(e)}")
        # Return tiny placeholder image on error
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFdwI2P/kcWQAAAABJRU5ErkJggg=="


def generate_task_completion_chart(task_data):
    """
    Create a color-coded bar chart of task success rates

    Args:
        task_data: List of task performance data

    Returns:
        Base64 encoded string of the chart image
    """

    def plot_chart():
        task_names = [task["taskName"] for task in task_data]
        completion_rates = [task["successRate"] for task in task_data]

        # Color bars by success level (red, orange, or green)
        colors = [
            "#f44336" if rate < 50 else "#ff9800" if rate < 70 else "#4caf50"
            for rate in completion_rates
        ]

        plt.bar(task_names, completion_rates, color=colors)
        plt.xlabel("Tasks")
        plt.ylabel("Completion Rate (%)")
        plt.title("Task Completion Rates")
        plt.ylim(0, 100)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Add percentage labels on top of each bar
        for i, rate in enumerate(completion_rates):
            plt.text(i, rate + 2, f"{rate:.1f}%", ha="center")

    return plot_to_base64(plot_chart)


def generate_error_rate_chart(task_data):
    # Create bar chart of error rates by task
    # task_data: List of task stats
    # Returns: Base64 encoded image
    def plot_chart():
        task_names = [task["taskName"] for task in task_data]
        error_rates = [task.get("errorRate", 0) for task in task_data]

        plt.bar(task_names, error_rates, color="#FFC107")
        plt.xlabel("Tasks")
        plt.ylabel("Error Rate (errors/min)")
        plt.title("Error Rates by Task")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Add labels on top of each bar
        for i, rate in enumerate(error_rates):
            plt.text(i, rate + 0.1, f"{rate:.2f}", ha="center")

    return plot_to_base64(plot_chart)


def plot_learning_curve(task_data):
    # Plot improvement in task completion time over multiple attempts
    # task_data: Dict with attempts and completion times
    colors = ["#4285F4", "#EA4335", "#FBBC05", "#34A853", "#FF6D01", "#46BDC6"]

    for i, (task_name, data) in enumerate(task_data.items()):
        color = colors[i % len(colors)]
        plt.plot(data["attempts"], data["times"], "o-", label=task_name, color=color)

    plt.xlabel("Attempt Number")
    plt.ylabel("Completion Time (seconds)")
    plt.title("Learning Curve: Improvement Over Attempts")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()


def plot_bar_chart(categories, values, title, xlabel, ylabel, color="#1976D2"):
    # Create a simple bar chart with labels
    # Takes categories, values and labels to create a formatted chart
    plt.bar(categories, values, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()


def calculate_interaction_metrics(tracking_data, duration_seconds=None):
    # Count mouse/keyboard actions and calculate rates
    # tracking_data: Raw interaction events
    # duration_seconds: Optional session length
    # Returns: Dict with interaction metrics
    # If we have tracking_data in the expected format (dict with lists)
    if isinstance(tracking_data, dict) and any(
        k in tracking_data for k in ["mouse_movements", "mouse_clicks", "keystrokes"]
    ):
        metrics = {
            "mouse_movements": len(tracking_data.get("mouse_movements", [])),
            "mouse_clicks": len(tracking_data.get("mouse_clicks", [])),
            "scrolls": len(tracking_data.get("scrolls", [])),
            "keystrokes": len(tracking_data.get("keystrokes", [])),
        }

        # Calculate mouse travel distance if data available
        movements = tracking_data.get("mouse_movements", [])
        if len(movements) > 1:
            total_distance = 0
            prev_x, prev_y = movements[0]["x"], movements[0]["y"]

            for movement in movements[1:]:
                curr_x, curr_y = movement["x"], movement["y"]
                # Euclidean distance
                distance = ((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2) ** 0.5
                total_distance += distance
                prev_x, prev_y = curr_x, curr_y

            metrics["mouse_travel_distance"] = total_distance

        return metrics

    # Alternative format (list of events)
    elif duration_seconds is not None:
        # Handle edge cases
        if not tracking_data or duration_seconds <= 0:
            return {"clicks": 0, "keyPresses": 0, "mouseMoves": 0, "scrolls": 0}

        # Count each interaction type
        clicks = sum(1 for e in tracking_data if e.get("type") == "mouse_click")
        key_presses = sum(1 for e in tracking_data if e.get("type") == "key_press")
        mouse_moves = sum(1 for e in tracking_data if e.get("type") == "mouse_move")
        scrolls = sum(1 for e in tracking_data if e.get("type") == "scroll")

        # Convert to per-minute rates
        duration_minutes = duration_seconds / 60

        return {
            "clicks": round(clicks / duration_minutes, 2),
            "keyPresses": round(key_presses / duration_minutes, 2),
            "mouseMoves": round(mouse_moves / duration_minutes, 2),
            "scrolls": round(scrolls / duration_minutes, 2),
        }

    # Default fallback
    return {"clicks": 0, "keyPresses": 0, "mouseMoves": 0, "scrolls": 0}
