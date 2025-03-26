import io
import os
import sqlite3

import supernotelib as sn
from PIL import Image

from sn2md.types import ImageExtractor

TILE_PIXELS = 128
# Magic number for the upper left tile in an SPD file
START_INDEX = 7976857


def tid_to_row_col(tid, row_stride=4096):
    row = (tid - START_INDEX) % row_stride
    col = (tid - START_INDEX - row) // row_stride
    return row, col


def max_x_y(tile_dict: list[dict]) -> tuple[int, int]:
    max_x = 0
    max_y = 0

    for tile_data in tile_dict:
        for tid in tile_data.keys():
            row, col = tid_to_row_col(tid)
            x = col * TILE_PIXELS
            y = row * TILE_PIXELS

            # Update max_x and max_y
            max_x = max(max_x, x + TILE_PIXELS)
            max_y = max(max_y, y + TILE_PIXELS)

    return max_x, max_y


def read_tiles_data(spd_file_path: str) -> list[dict]:
    conn = sqlite3.connect(spd_file_path)
    cursor = conn.cursor()

    # Check the format version - only version 2 is supported at present
    cursor.execute("select value from config where name='fmt_ver';")
    version = cursor.fetchone()[0].decode("utf-8")
    if version != "2":
        raise ValueError(f"Unsupported SPD format version: {version}")

    cursor.execute("select value from config where name='ls';")
    layers = [v for v in cursor.fetchone()[0].decode("utf-8").split("\n") if len(v) > 0]

    def is_not_visible(x):
        return x.endswith("\x00")

    tiles_data = []
    # Iterate over the layers from the top layer to the bottom layer
    for i in range(len(layers), 0, -1):
        if is_not_visible(layers[len(layers) - i]):
            continue
        # Fetch tiles, ordering them by tid.  Replace with the hardcoded `tids` list
        cursor.execute(f"SELECT tid, tile FROM surface_{i} ORDER BY tid ASC;")
        tile_dict = {tid: tile_data for tid, tile_data in cursor.fetchall()}
        tiles_data.append(tile_dict)

    conn.close()

    return tiles_data


def spd_to_png(spd_file_path: str, output_path: str) -> str:
    tiles_data = read_tiles_data(spd_file_path)
    full_image = Image.new("RGBA", max_x_y(tiles_data))

    # Ensure that even if the layers are all empty, we create a blank image
    image_size = full_image.size
    if full_image.size == (0, 0):
        image_size = (TILE_PIXELS * 12, TILE_PIXELS * 16)

    for tile_dict in reversed(tiles_data):
        for tid in tile_dict.keys():
            tile_data = tile_dict[tid]
            tile = Image.open(io.BytesIO(tile_data)).convert("RGBA")

            row, col = tid_to_row_col(tid)
            x = col * TILE_PIXELS
            y = row * TILE_PIXELS

            # Blend the tile image with the full image
            tile_image = Image.new("RGBA", image_size)
            tile_image.paste(tile, (x, y))
            full_image = Image.alpha_composite(full_image, tile_image)

    full_image_with_white_bg = Image.new("RGB", image_size, (255, 255, 255))
    full_image_with_white_bg.paste(full_image, (0, 0), full_image)

    image_path = (
        output_path
        + "/"
        + os.path.splitext(os.path.basename(spd_file_path))[0]
        + ".png"
    )
    full_image_with_white_bg.save(image_path)

    return image_path


class AtelierExtractor(ImageExtractor):
    def extract_images(self, filename: str, output_path: str) -> list[str]:
        return [spd_to_png(filename, output_path)]

    def get_notebook(self, filename: str) -> sn.Notebook | None:
        return None
