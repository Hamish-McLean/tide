import io
import json
import sys
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
    raw_events: list[dict],
    width: int = 250,
    height: int = 122,
) -> Image.Image:
    """
    Renders a pixel-perfect tide plot entirely via PIL using relative proportions.
    Adapts cleanly to any display width or height.
    """
    BLACK = 0
    WHITE = 1
    YELLOW = 2
    RED = 3

    x_min, y_val, events = fit_tide_curve(raw_events)

    # Initialize a pure monochrome 1-bit canvas (1 = White background)
    img = Image.new("P", (width, height), color=WHITE)
    draw = ImageDraw.Draw(img)

    # --- 1. Dynamic Font Scaling ---
    # Base font sizes on a proportion of total display height
    font_path = get_project_root() / "src/tide/assets"
    title_font_file = "ElecSign.ttf"  # "JetBrainsMonoNerdFont-Medium.ttf"
    label_font_file = "ElecSign.ttf"
    title_size = max(12, int(height * 0.12))
    label_size = max(8, int(height * 0.082))

    try:
        title_font = ImageFont.load_default(
            title_size
        )  # ImageFont.truetype(font_path / title_font_file, title_size)
        label_font = ImageFont.truetype(font_path / label_font_file, label_size)
    except IOError:
        print("[WARNING] Failed to load fonts, using defaults.")
        title_font = ImageFont.load_default(title_size)
        label_font = ImageFont.load_default(label_size)

    # --- 2. Proportional Layout Matrix ---
    # Define bounding margins as explicit fractions of total size
    top_margin = int(height * 0.18)  # Room for header title
    bottom_margin = int(height * 0.12)  # Room for time labels at bottom
    side_margin = int(width * 0.04)  # Small edge safety padding

    plot_width = width - (2 * side_margin)
    plot_height = height - top_margin - bottom_margin

    # Central baseline horizontal anchor point
    baseline_y = top_margin + (plot_height // 2)

    # --- 3. Draw Header ---
    title_text = f"{events[0]["weekday"]} {events[0]["date"]}"
    draw.text(
        (width // 2, int(height * 0.02)),
        title_text,
        font=title_font,
        fill=BLACK,
        anchor="mt",
    )

    # --- 4. Coordinate Transformation Functions ---
    def to_pixel_x(minutes: float) -> float:
        # Map 0..1440 min into side_margin..width-side_margin
        return side_margin + (minutes / 1440.0) * plot_width

    def to_pixel_y(tide_height: float) -> float:
        # Invert scale: positive height moves UP towards plot_top
        # Map -1.0..1.0 height into plot bounding zone
        return baseline_y - (tide_height * (plot_height / 2.0))

    # --- 5. Render Chart Elements ---
    # Map the wave curve coordinates array
    pixel_xs = to_pixel_x(x_min)
    pixel_ys = to_pixel_y(y_val)
    points = list(zip(pixel_xs, pixel_ys))
    draw.line(points, fill=BLACK, width=2)

    # --- 6. Annotate High/Low Anchor Nodes ---
    node_radius = max(2, int(height * 0.016))
    text_offset = max(4, int(height * 0.15))

    for evt in events:
        ex = int(to_pixel_x(evt["minute"]))
        ey = int(to_pixel_y(evt["height"]))

        # Render a crisp node box centered over coordinates
        draw.rectangle(
            [ex - node_radius, ey - node_radius, ex + node_radius, ey + node_radius],
            fill=RED,
        )

        # Place labels based on relative direction shifts
        label_text = evt["time"]
        if evt["height"] > 0:
            # High Tide -> text floats safely below the peak line
            draw.text(
                (ex, ey + text_offset),
                label_text,
                font=label_font,
                fill=RED,
                anchor="mt",
            )
        else:
            # Low Tide -> text floats safely above the trough line
            draw.text(
                (ex, ey - text_offset - label_size),
                label_text,
                font=label_font,
                fill=RED,
                anchor="mt",
            )

    # --- 7. Dynamic Axis Timeline Marks ---
    timeline_y = height - bottom_margin

    # Draw zero-line axis
    draw.line(
        [(side_margin, timeline_y), (width - side_margin, timeline_y)], fill=0, width=1
    )

    # Draw standard interval timeline marks across bottom
    for hour in [0, 6, 12, 18, 24]:
        tx = int(to_pixel_x(hour * 60))
        # Tick marker line
        draw.line(
            [(tx, timeline_y), (tx, timeline_y + int(height * 0.025))], fill=0, width=1
        )
        # Clock text string label
        draw.text(
            (tx, timeline_y + int(height * 0.033)),
            f"{hour:02d}",
            font=label_font,
            fill=BLACK,
            anchor="ma",
        )

    return img


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
