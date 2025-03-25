import io
import os
import sqlite3
from typing import Any

import supernotelib as sn
from PIL import Image

from sn2md.types import ImageExtractor

ROWS = 16
COLUMNS = 12
TILE_PIXELS = 128

# Generate the starting numbers using range
START_INDEX = 7976857

def tid_to_row_col(tid):
    row = (tid - START_INDEX) % TILE_PIXELS
    col = (tid - START_INDEX - row) // TILE_PIXELS
    return row, col


def max_x_y(tile_dict) -> tuple[int, int]:
    max_x = 0
    max_y = 0

    for tid in tile_dict.keys():
        row, col = tid_to_row_col(tid)
        x = col * TILE_PIXELS
        y = row * TILE_PIXELS

        # Update max_x and max_y
        max_x = max(max_x, x + TILE_PIXELS)
        max_y = max(max_y, y + TILE_PIXELS)

    return max_x, max_y


def read_tiles_data(spd_file_path: str) -> list[Any]:
    conn = sqlite3.connect(spd_file_path)
    cursor = conn.cursor()

    # Check the format version - only version 2 is supported at present
    cursor.execute("select value from config where name='fmt_ver';")
    version = cursor.fetchone()[0].decode("utf-8")
    if version != "2":
        raise ValueError(f"Unsupported SPD format version: {version}")

    # cursor.execute("select value from config where name='ls';")
    # layers = cursor.fetchall()
    # TODO we need to discover all "Layer X" tables to discover all the layer tables.

    # Fetch tiles, ordering them by tid.  Replace with the hardcoded `tids` list
    cursor.execute("SELECT tid, tile FROM surface_1 ORDER BY tid ASC;")
    tiles_data = cursor.fetchall()

    conn.close()

    return tiles_data


def spd_to_png(spd_file_path: str, output_path: str) -> str:
    tiles_data = read_tiles_data(spd_file_path)
    # Convert to a dictionary of {tid: tile_data} for easy lookup
    tile_dict = {tid: tile_data for tid, tile_data in tiles_data}

    full_image = Image.new("LA", max_x_y(tile_dict))

    for tid in tile_dict.keys():
        tile_data = tile_dict[tid]
        tile = Image.open(io.BytesIO(tile_data))

        # Calculate tile position based on index and dimensions
        row, col = tid_to_row_col(tid)
        print("|tid = {0}".format(tid))
        print("|tid_to_row_col(tid) = {0}".format(tid_to_row_col(tid)))
        print("|row,col = {0},{1}".format(row, col))
        x = col * TILE_PIXELS
        y = row * TILE_PIXELS
        print("|x,y = {0},{1}".format(x, y))

        full_image.paste(tile, (x, y))

    full_image = full_image.convert("RGBA")
    full_image_with_white_bg = Image.new("RGB", full_image.size, (255, 255, 255))
    full_image_with_white_bg.paste(full_image, (0, 0), full_image)

    image_path = output_path + "/" + os.path.splitext(os.path.basename(spd_file_path))[0] + ".png"
    full_image_with_white_bg.save(image_path)

    return image_path


class AtelierExtractor(ImageExtractor):
    def extract_images(self, filename: str, output_path: str) -> list[str]:
        return [spd_to_png(filename, output_path)]

    def get_notebook(self, filename: str) -> sn.Notebook | None:
        return None
