import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sn2md.importers.atelier import read_tiles_data, spd_to_png, tid_to_row_col, START_INDEX



@pytest.mark.parametrize("tid, row, col", [
    (START_INDEX, 0, 0),
    (8009635, 8, 10),
])
def test_tid_to_row_col(tid, row, col):
    assert tid_to_row_col(tid) == (row, col)


@pytest.mark.parametrize(
    "spd_file, tiles_data_length",
    [
        (str(Path(__file__).parent / "fixtures/20250325_165251-blank.spd"), 1),
        (str(Path(__file__).parent / "fixtures/20250325_165308-Layers.spd"), 4),
    ],
)
def test_read_tiles_data(spd_file, tiles_data_length):
    tiles_data = read_tiles_data(spd_file)
    assert len(tiles_data) == tiles_data_length


@pytest.mark.parametrize(
    "spd_file",
    [
        (str(Path(__file__).parent / "fixtures/20250325_165251-blank.spd")),
        # (str(Path(__file__).parent / "fixtures/20250325_165308-Layers.spd")),
    ],
)
def test_spd_to_png(spd_file):
    with TemporaryDirectory() as tmpdir:
        img_path = spd_to_png(spd_file, tmpdir)
        assert os.path.exists(img_path)
