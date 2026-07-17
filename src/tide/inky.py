from inky.auto import auto
from PIL import Image

from tide.utils import get_project_root


def initialise_inky_display(invert=False):
    inky_display = auto()
    inky_display.set_border(inky_display.WHITE)

    # Invert screen
    inky_display.h_flip = invert
    inky_display.v_flip = invert

    return inky_display


def display_image(inky_display, image: Image.Image):
    inky_display.set_image(image)


if __name__ == "__main__":
    project_root = get_project_root()
    cache_dir = project_root / ".cache"

    inky_display = initialise_inky_display(invert=True)

    image = Image.open(cache_dir / "tide_plot.png")

    display_image(inky_display, image)
