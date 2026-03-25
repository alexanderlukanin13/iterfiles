import dataclasses
import os
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path

from unittest.mock import patch

import time_machine
import pendulum
import pytest

from iterfiles import iterfiles
from iterfiles.stat import *


from . import DATA_DIR


local_tz = pendulum.local_timezone()
DEC31_11PM = datetime(2025, 12, 31, hour=23, tzinfo=local_tz)
JAN1 = datetime(2026, 1, 1, tzinfo=local_tz)
JAN1_7AM = datetime(2026, 1, 1, 7, tzinfo=local_tz)
JAN1_11AM = datetime(2026, 1, 1, 11, tzinfo=local_tz)
JAN2 = datetime(2026, 1, 2, tzinfo=local_tz)
JAN2_6AM = datetime(2026, 1, 2, 6, tzinfo=local_tz)
FEB14_7AM = datetime(2026, 2, 14, 7, tzinfo=local_tz)
MARCH13_9AM = datetime(2026, 3, 13, 9, tzinfo=local_tz)



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

def stat_mock(**kw):
    for attr in ('st_atime', 'st_mtime', 'st_ctime'):
        if isinstance(kw.get(attr), datetime):
            kw[attr] = int(round(kw[attr].timestamp()))
    return StatResultMock(**kw)


def patch_stat(results: dict[Path, StatResultMock]):
    def stat_mock(self):
        try:
            if results[self].st_size > 0:
                return results[self]
            else:
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
    path = DATA_DIR / 'example2'
    st_attr = globals()[attr]  # st_atime, etc.

    with patch_stat({
        path / 'shapes.txt': stat_mock(**{attr: DEC31_11PM}),
        path / 'aa' / 'numbers.txt': stat_mock(**{attr: JAN1}),
        path / 'aa' / 'pets.txt': stat_mock(**{attr:DEC31_11PM}),
        path / 'bb' / 'names.txt': stat_mock(**{attr:JAN1_7AM}),
        path / 'bb' / 'birds.txt': stat_mock(**{attr: FEB14_7AM}),
        path / 'bb' / 'cc' / 'aircraft.txt': stat_mock(**{attr:JAN2_6AM}),
        path / 'bb' / 'cc' / 'cars.txt': stat_mock(**{attr:JAN1_11AM})
    }):
        # time < 2026-01-01 00:00:00 UTC
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__lt': JAN1.timestamp()}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr < JAN1.timestamp()).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__lt': JAN1}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr < JAN1).set() == expected

        # time <= 2026-01-01 00:00:00 UTC
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt',
            path / 'aa' / 'numbers.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__le': JAN1}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr <= JAN1).set() == expected

        # time == 2026-01-01 07:00:00 UTC
        expected = {
            path / 'aa' / 'numbers.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}': JAN1}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == JAN1).set() == expected

        # time > 2026-01-01 00:00:00 UTC
        expected = {
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'names.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__gt': JAN1}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr > JAN1).set() == expected

        # time >= 2026-01-01 00:00:00 UTC
        expected = {
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'names.txt',
            path / 'aa' / 'numbers.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ge': JAN1}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr >= JAN1).set() == expected

        # on Jan 1
        expected = {
            path / 'aa' / 'numbers.txt',
            path / 'bb' / 'names.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{attr: date(2026, 1, 1)}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == date(2026, 1, 1)).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(**{attr: '2026-01-01'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == '2026-01-01').set() == expected

        # not on Jan 1
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ne': date(2026, 1, 1)}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr != date(2026, 1, 1)).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ne': '2026-01-01'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr != '2026-01-01').set() == expected

        # in January 2026
        expected = {
            path / 'aa' / 'numbers.txt',
            path / 'bb' / 'names.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{attr: '2026-01'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == '2026-01').set() == expected

        # not in January 2026
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt',
            path / 'bb' / 'birds.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ne': '2026-01'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr != '2026-01').set() == expected

        # in 2026
        expected = {
            path / 'aa' / 'numbers.txt',
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{attr: '2026'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == '2026').set() == expected

        # not in 2026
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'pets.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ne': '2026'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr != '2026').set() == expected


@pytest.mark.time_machine(datetime(2026, 3, 26, 12, 30, 57, tzinfo=pendulum.timezone('US/Alaska')))
@pytest.mark.parametrize('attr', ['st_atime']) # ['st_atime', 'st_ctime', 'st_mtime'])
def test_time_humanized(attr):
    path = DATA_DIR / 'example2'
    st_attr = globals()[attr]  # st_atime, etc.
    now = pendulum.datetime(2026, 3, 26, 12, 30, 57, tz='US/Alaska')

    with patch_stat({
        path / 'shapes.txt':                 stat_mock(**{attr:now.subtract(years=1, days=1)}),
        path / 'aa' / 'numbers.txt':         stat_mock(**{attr:now.subtract(days=32)}),
        path / 'aa' / 'pets.txt':            stat_mock(**{attr:now.subtract(days=8)}),
        path / 'bb' / 'names.txt':           stat_mock(**{attr:now.subtract(days=1)}),
        path / 'bb' / 'birds.txt':           stat_mock(**{attr:now.subtract(hours=1)}),
        path / 'bb' / 'cc' / 'aircraft.txt': stat_mock(**{attr:now.subtract(minutes=1)}),
        path / 'bb' / 'cc' / 'cars.txt':     stat_mock(**{attr:now})
    }):
        # time = today
        expected = {
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}': 'today'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == 'today').set() == expected
        # time >= today (weird but technically allowed) - same results here
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ge': 'today'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr >= 'today').set() == expected
        # time > yesterday - same results here
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__gt': 'yesterday'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr > 'yesterday').set() == expected

        # time < today (weird but technically allowed)
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
            path / 'bb' / 'names.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__lt': 'today'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr < 'today').set() == expected
        # time != today - same results here
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ne': 'today'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr != 'today').set() == expected
        # time <= yesterday - same results here
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__le': 'yesterday'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr <= 'yesterday').set() == expected

        # time <= today (weird but technically allowed)
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__le': 'today'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr <= 'today').set() == expected

        # time > today (weird but technically allowed)
        expected = set()
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__gt': 'today'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr > 'today').set() == expected

        # time = yesterday
        expected = {
            path / 'bb' / 'names.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}': 'yesterday'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == 'yesterday').set() == expected

        # time < yesterday
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__lt': 'yesterday'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr < 'yesterday').set() == expected

        # time >= yesterday
        expected = {
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ge': 'yesterday'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr >= 'yesterday').set() == expected


@pytest.mark.time_machine(datetime(2026, 3, 26, 12, 30, 57, tzinfo=pendulum.timezone('US/Alaska')))
@pytest.mark.parametrize('attr', ['st_atime'])  # ['st_atime', 'st_ctime', 'st_mtime'])
def test_time_humanized_week(attr):
    path = DATA_DIR / 'example2'
    st_attr = globals()[attr]  # st_atime, etc.
    now = pendulum.datetime(2026, 3, 26, 12, 30, 57, tz='US/Alaska')
    with patch_stat({
        path / 'shapes.txt': stat_mock(**{attr: now.subtract(years=1, days=1)}),
        path / 'aa' / 'numbers.txt': stat_mock(**{attr: now.subtract(days=5)}),
        path / 'aa' / 'pets.txt': stat_mock(**{attr: now.subtract(days=4)}),
        path / 'bb' / 'names.txt': stat_mock(**{attr: now.subtract(days=3)}),
        path / 'bb' / 'birds.txt': stat_mock(**{attr: now.subtract(days=2)}),
        path / 'bb' / 'cc' / 'aircraft.txt': stat_mock(**{attr: now.add(days=1)}),
        path / 'bb' / 'cc' / 'cars.txt': stat_mock(**{attr: now.add(days=7)})
        }):
        # time = this week
        expected = {
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}': 'this week @ US/Alaska'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == 'this week @ US/Alaska').set() == expected

        # time != this week
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
            path / 'bb' / 'cc' / 'cars.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ne': 'this week @ US/Alaska'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr != 'this week @ US/Alaska').set() == expected

        # time < this week
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__lt': 'this week @ US/Alaska'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr < 'this week @ US/Alaska').set() == expected

        # time <= this week
        expected = {
            path / 'shapes.txt',
            path / 'aa' / 'numbers.txt',
            path / 'aa' / 'pets.txt',
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__le': 'this week @ US/Alaska'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr <= 'this week @ US/Alaska').set() == expected

        # time > this week
        expected = {
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__gt': 'this week @ US/Alaska'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr > 'this week @ US/Alaska').set() == expected

        # time >= this week
        expected = {
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
            path / 'bb' / 'cc' / 'cars.txt'
        }
        assert iterfiles(path, '**/*.txt').filter_stat(**{f'{attr}__ge': 'this week @ US/Alaska'}).set() == expected
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr >= 'this week @ US/Alaska').set() == expected

        # timezone difference
        expected = {
            path / 'aa' / 'pets.txt',  # due to 13 hours difference, this also fits into week
            path / 'bb' / 'names.txt',
            path / 'bb' / 'birds.txt',
            path / 'bb' / 'cc' / 'aircraft.txt',
        }
        assert iterfiles(path, '**/*.txt').filter_stat(st_attr == 'this week @ Asia/Bishkek').set() == expected
