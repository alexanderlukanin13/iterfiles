import dataclasses
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from unittest.mock import patch
import pytest

from iterfiles import iterfiles
from iterfiles.stat import *


from . import DATA_DIR


UTC = timezone.utc
DEC31_11PM = datetime(2025, 12, 31, hour=23, tzinfo=UTC)
JAN1 = datetime(2026, 1, 1, tzinfo=UTC)
JAN1_7AM = datetime(2026, 1, 1, 7, tzinfo=UTC)
JAN1_11AM = datetime(2026, 1, 1, 11, tzinfo=UTC)
JAN2 = datetime(2026, 1, 2, tzinfo=UTC)
JAN2_6AM = datetime(2026, 1, 2, 6, tzinfo=UTC)


@dataclass
class StatResultMock:
    st_mode: int = 33279
    st_ino: int = 844424931054097  # doesn't matter
    st_dev: int = 82               # doesn't matter
    st_nlink: int = 1              # doesn't matter
    st_uid: int = 1000
    st_gid: int = 1000
    st_size: int = 0
    st_atime: int = JAN1.timestamp()
    st_mtime: int = JAN1.timestamp()
    st_ctime: int = JAN1.timestamp()


def patch_stat(results: dict[Path, StatResultMock]):
    def stat_mock(self):
        try:
            if results[self].st_size > 0:
                return results[self]
            else:
                print(f'{self} -> {results[self]}')
                return dataclasses.replace(results[self], st_size=os.stat(self).st_size)
        except KeyError:
            raise Exception(f'FIX TEST: {self} is not in patch_stat')
    return patch('pathlib.Path.stat', autospec=True, side_effect=stat_mock)


def test_st_size():
    path = DATA_DIR / 'example1'

    # st_size < 15
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size__lt=15).list() == [
        path / 'aa' / 'numbers.txt',
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size < 15).list() == [
        path / 'aa' / 'numbers.txt',
    ]

    # st_size <= 15
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size__le=15).list() == [
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size <= 15).list() == [
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
    ]

    # st_size == 15
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size=15).list() == [
        path / 'aa' / 'pets.txt',
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size == 15).list() == [
        path / 'aa' / 'pets.txt',
    ]

    # st_size != 15
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').exclude_stat(st_size=15).list() == [
        path / 'shapes.txt',
        path / 'aa' / 'numbers.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt'
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size != 15).list() == [
        path / 'shapes.txt',
        path / 'aa' / 'numbers.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt'
    ]

    # st_size > 15
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size__gt=15).list() == [
        path / 'shapes.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt'
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size > 15).list() == [
        path / 'shapes.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt'
    ]

    # st_size >= 15
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size__ge=15).list() == [
        path / 'shapes.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt'
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size >= 15).list() == [
        path / 'shapes.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt'
    ]

    # st_size in range (15,18)
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_size__range=(15,18)).list() == [
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    ]
    assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat((st_size >= 15) & (st_size <= 18)).list() == [
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    ]


#@pytest.mark.parametrize('attr', ['st_atime', 'st_ctime', 'st_mtime'])
@pytest.mark.parametrize('attr', ['st_atime'])
def test_time(attr):
    path = DATA_DIR / 'example1'
    st_attr = globals()[attr]  # st_atime, etc.

    with patch_stat({
        path / 'shapes.txt': StatResultMock(**{attr: DEC31_11PM}),
        path / 'aa' / 'numbers.txt': StatResultMock(),
        path / 'aa' / 'pets.txt': StatResultMock(**{attr:DEC31_11PM}),
        path / 'bb' / 'names.txt': StatResultMock(**{attr:JAN1_7AM}),
        path / 'bb' / 'cc' / 'cars.txt': StatResultMock(**{attr:JAN1_11AM})
    }):
        # time < 2026-01-01 00:00:00 UTC
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(**{f'{attr}__lt': JAN1.timestamp()}).set() == {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt'
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_attr < JAN1.timestamp()).set() == {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt'
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(**{f'{attr}__lt': JAN1}).set() == {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt'
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_attr < JAN1).set() == {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt'
        }

        # time <= 2026-01-01 00:00:00 UTC
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(**{f'{attr}__le': JAN1}).set() == {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt',
            path / 'aa' / 'numbers.txt',
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_attr <= JAN1).set() == {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
        }

        # time == 2026-01-01 07:00:00 UTC
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(**{f'{attr}': JAN1}).set() == {
            path / 'aa' / 'numbers.txt'
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_attr == JAN1).set() == {
            path / 'aa' / 'numbers.txt'
        }

        # time > 2026-01-01 00:00:00 UTC
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(**{f'{attr}__gt': JAN1}).set() == {
            path / 'bb' / 'names.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_attr > JAN1).set() == {
            path / 'bb' / 'names.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }

        # time >= 2026-01-01 00:00:00 UTC
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(**{f'{attr}__ge': JAN1}).set() == {
            path / 'bb' / 'names.txt',
            path / 'aa' / 'numbers.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(DATA_DIR / 'example1', '**/*.txt').filter_stat(st_attr >= JAN1).set() == {
            path / 'bb' / 'names.txt',
            path / 'aa' / 'numbers.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
