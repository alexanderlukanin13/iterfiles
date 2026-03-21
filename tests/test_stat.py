from iterfiles.stat import Path

import pytest

from iterfiles import iterfiles, InvalidPathError

from . import DATA_DIR


def test_st_size():
    path = DATA_DIR / 'example1'

    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size__lt=15).list() == [
        path / 'aa' / 'numbers.txt',
    ]
