import io
import json
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from PIL import Image

from tide.utils import get_project_root


def cosine_interpolate(
    x: np.ndarray, x1: float, x2: float, y1: float, y2: float
) -> np.ndarray:
    """Applies a smooth cosine transition between (x1, y1) and (x2, y2)"""
    # Scale x array segment to 0.0 -> 1.0 range
    fraction = (x - x1) / (x2 - x1)
    # Cosine scaling factor for 0.0 -> 1.0
    scale = (1 - np.cos(fraction * np.pi)) / 2
    return y1 + (y2 - y1) * scale


def fit_tide_curve(raw_events: list[dict]) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Fit a cosine curve to discrete tide event times"""
    # Process events
    events = []
    for event in raw_events:
        dt = datetime.fromisoformat(event["DateTime"])
        events.append(
            {
                "date": dt.date(),
                "weekday": dt.date().strftime("%A"),
                "time": dt.time().isoformat(timespec="minutes"),
                "minute": dt.hour * 60 + dt.minute,
                "type": event["EventType"],
                "height": 1.0 if event["EventType"] == "HighWater" else -1.0,
            }
        )
    events.sort(key=lambda x: x["minute"])

    # Generate smooth points
    minutes_x: np.ndarray = np.arange(0, 1441, 1)
    heights_y: np.ndarray = np.zeros_like(minutes_x, dtype=float)

    # Extrapolate curve back to midnight (00:00)
    first_mask = minutes_x < events[0]["minute"]
    heights_y[first_mask] = cosine_interpolate(
        minutes_x[first_mask],
        events[0]["minute"],
        events[1]["minute"],
        events[0]["height"],
        events[1]["height"],
    )

    # Fit cosine curve
    for i in range(len(events) - 1):
        event1, event2 = events[i], events[i + 1]
        x1, x2 = event1["minute"], event2["minute"]

        # Select array slice for this segment
        mask = (minutes_x >= x1) & (minutes_x <= x2)
        heights_y[mask] = cosine_interpolate(
            minutes_x[mask], x1, x2, event1["height"], event2["height"]
        )

    # Extrapolate curve back to midnight (00:00)
    last_mask = minutes_x > events[-1]["minute"]
    heights_y[last_mask] = cosine_interpolate(
        minutes_x[last_mask],
        events[-2]["minute"],
        events[-1]["minute"],
        events[-2]["height"],
        events[-1]["height"],
    )

    return minutes_x, heights_y, events


def plot_tides(
    raw_events: list[dict], width: int = 250, height: int = 122
) -> Image.Image:
    """Plot tide curve from discrete tide event times"""
    minutes_x, heights_y, events = fit_tide_curve(raw_events)

    # Set matplotlib outputs
    dpi = 100
    fig, ax = plt.subplots(
        figsize=(width / dpi, height / dpi), dpi=dpi, layout="constrained"
    )
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Plot curve
    ax.plot(minutes_x, heights_y, color="black", linewidth=2)

    # Plot and annotate events
    for event in events:
        y_pos = 1.0 if event["type"] == "HighWater" else -1.0

        # Draw marker
        ax.plot(event["minute"], y_pos, marker="o", color="black", markersize=4)

        # Keep text label offset dynamically in-bounds
        offset = -18 if y_pos > 0 else 12
        ax.annotate(
            event["time"],
            xy=(event["minute"], y_pos),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            # fontweight="bold",
            color="black",
        )

    # Format axes
    ax.set_xlim(0, 1440)
    ax.set_xmargin(0)
    ax.set_xticks(np.arange(0, 1441, 240))
    ax.set_xticklabels(
        ["00", "04", "08", "12", "16", "20", "24"], fontsize=8, color="black"
    )
    # ax.tick_params(axis="x", bottom=False)
    ax.set_ylim(-1.1, 1.1)
    ax.get_yaxis().set_visible(False)

    # Format borders
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("black")
    ax.spines["bottom"].set_linewidth(1)

    # Set title
    date = events[0]["date"]
    weekday = events[0]["weekday"]  # date.strftime("%A")
    ax.set_title(f"{weekday} {date}", fontsize=10, fontweight="bold")

    # Save plot in buffer
    buf = io.BytesIO()
    plt.savefig(
        buf, format="png", dpi=dpi
    )  # , bbox_inches="tight")  # , pad_inches=-0.001)
    plt.close(fig)
    buf.seek(0)

    return Image.open(buf)


if __name__ == "__main__":
    print("Plotting tides")

    project_root = get_project_root()
    cache_dir = project_root / ".cache"

    # Get data
    station = "0023C"
    raw_json_file = cache_dir / f"admiralty_response_{station}.json"
    with open(raw_json_file, "r") as f:
        raw_events = json.load(f)

    try:
        tide_plot = plot_tides(raw_events)
        output_file = cache_dir / "tide_plot.png"
        tide_plot.save(output_file)
    except Exception as e:
        print(f"[ERROR] Plotting failed {e}")
        sys.exit(1)
