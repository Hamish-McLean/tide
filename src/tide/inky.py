from inky.auto import auto
from PIL import Image

from tide.utils import get_project_root


def initialise_inky_display(border=inky_display.WHITE, invert=False):
    inky_display = auto()
    inky_display.set_border(border)

    # Invert screen
    inky_display.h_flip = invert
    inky_display.v_flip = invert


def display_image(image: Image.Image):
    inky.set_image(image)


if __name__ == "__main__":
    project_root = get_project_root()
    cache_dir = project_root / ".cache"

    initialise_inky_display(invert=True)

    image = Image.open(cache_dir / "tide_plot.png")

    display_image(image)
