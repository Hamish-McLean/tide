import os
import sys

from tide import api, inky, plot
from tide.plot import plot_tides


def main():
    # Get tide data from Admiralty Discovery API
    API_KEY = os.getenv("ADMIRALTY_DISCOVERY_API_KEY")
    STATION = "0023C"  # Totnes

    if not API_KEY:
        print(
            "[ERROR] ADMIRALTY_DISCOVERY_API_KEY environment variable is not set!",
            file=sys.stderr,
        )
        exit(1)
    try:
        tide_data = api.fetch_admiralty_tides(API_KEY, STATION)
    except Exception as e:
        print(f"[ERROR] API fetch failed: {e}")
        exit(1)

    # Plot tide data
    try:
        tide_plot = plot_tides(tide_data)
    except Exception as e:
        print(f"[ERROR] Plotting failed {e}")
        exit(1)

    # Draw plot to inky phat display
    inky_display = inky.initialise_inky_display(invert=True)
    inky.display_image(inky_display, tide_plot)


if __name__ == "__main__":
    main()
