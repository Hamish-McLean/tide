import argparse
import logging
import os
import sys

from tide import api, inky, plot
from tide.plot import plot_tides

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true", help="Only log errors")
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Get tide data from Admiralty Discovery API
    API_KEY = os.getenv("ADMIRALTY_DISCOVERY_API_KEY")
    STATION = "0023C"  # Totnes

    if not API_KEY:
        logging.error("ADMIRALTY_DISCOVERY_API_KEY environment variable is not set!")
        sys.exit(1)

    logging.info("Querying Admiralty Discovery API")
    try:
        tide_data = api.fetch_admiralty_tides(API_KEY, STATION)
        logging.info("API call successful.")
    except Exception as e:
        logging.error(f"API fetch failed: {e}")
        sys.exit(1)

    # Plot tide data
    logging.info("Plotting tides...")
    try:
        tide_plot = plot_tides(tide_data)
        logging.info("Plotting successful.")
    except Exception as e:
        logging.error(f"Plotting failed {e}")
        sys.exit(1)

    # Draw plot to inky phat display
    logging.info("Drawing plot to Inky pHAT display")
    try:
        inky_display = inky.initialise_inky_display(invert=False)
        inky.display_image(inky_display, tide_plot)
        logging.info("Tides completed successfully.")
    except Exception as e:
        logging.error(f"Hardware display failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
