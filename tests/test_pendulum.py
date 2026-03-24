import pendulum
import pytest
from pendulum import Interval, Date, DateTime, UTC

from iterfiles.pendulum import parse, DateDay, DateWeek, DateMonth, DateYear


def test_date_classes():
    tzinfo = pendulum.now(tz='local').timezone
    assert DateDay(2026, 3, 24, tzinfo=tzinfo).as_interval() == Interval(
        DateTime(2026, 3, 24, tzinfo=tzinfo),
        DateTime(2026, 3, 24, 23, 59, 59, 999999, tzinfo=tzinfo))

    assert DateWeek(2026, 3, 23, tzinfo=tzinfo).as_interval() == Interval(
        DateTime(2026, 3, 23, tzinfo=tzinfo),
        DateTime(2026, 3, 29, 23, 59, 59, 999999, tzinfo=tzinfo))

    assert DateMonth(2026, 3, 1, tzinfo=tzinfo).as_interval() == Interval(
        DateTime(2026, 3, 1, tzinfo=tzinfo),
        DateTime(2026, 3, 31, 23, 59, 59, 999999, tzinfo=tzinfo))

    assert DateYear(2026, 1, 1, tzinfo=tzinfo).as_interval() == Interval(
        DateTime(2026, 1, 1, tzinfo=tzinfo),
        DateTime(2026, 12, 31, 23, 59, 59, 999999, tzinfo=tzinfo))


def test_parse():
    tzinfo = pendulum.now(tz='local').timezone

    # DateTime (just a few)
    assert parse('20161001T14') == DateTime(2016, 10, 1, 14, tzinfo=tzinfo)

    # Day
    assert parse('2012-05-03').as_interval() == Interval(
        DateTime(2012, 5, 3, tzinfo=tzinfo),
        DateTime(2012, 5, 3, 23, 59, 59, 999999, tzinfo=tzinfo)
    )
    assert parse('2012-007').as_interval() == Interval(
        DateTime(2012, 1, 7, tzinfo=tzinfo),
        DateTime(2012, 1, 7, 23, 59, 59, 999999, tzinfo=tzinfo)
    )
    assert parse('2012007').as_interval() == Interval(
        DateTime(2012, 1, 7, tzinfo=tzinfo),
        DateTime(2012, 1, 7, 23, 59, 59, 999999, tzinfo=tzinfo)
    )

    # Day (with Week number)
    assert parse('2012W055').as_interval() == Interval(
        DateTime(2012, 2, 3, tzinfo=tzinfo),
        DateTime(2012, 2, 3, 23, 59, 59, 999999, tzinfo=tzinfo)
    )

    # Week
    assert parse('2012-W05').as_interval() == Interval(
        DateTime(2012, 1, 30, tzinfo=tzinfo),
        DateTime(2012, 2, 5, 23, 59, 59, 999999, tzinfo=tzinfo)
    )
    assert parse('2012W05').as_interval() == Interval(
        DateTime(2012, 1, 30, tzinfo=tzinfo),
        DateTime(2012, 2, 5, 23, 59, 59, 999999, tzinfo=tzinfo)
    )

    # Month
    assert parse('2012-05').as_interval() == Interval(
        DateTime(2012, 5, 1, tzinfo=tzinfo),
        DateTime(2012, 5, 31, 23, 59, 59, 999999, tzinfo=tzinfo)
    )

    # Year
    assert parse('2012').as_interval() == Interval(
        DateTime(2012, 1, 1, tzinfo=tzinfo),
        DateTime(2012, 12, 31, 23, 59, 59, 999999, tzinfo=tzinfo)
    )

    # Time
    with pytest.raises(ValueError):
        parse('12:30')
    with pytest.raises(ValueError):
        parse('12:04:23')
    with pytest.raises(ValueError):
        parse('120423')
    with pytest.raises(ValueError):
        parse('12:04:23.45')

    # Date Interval
    assert parse('2007-03-01/2008-05-11', tz='local') == Interval(
        DateDay(2007, 3, 1, tzinfo=tzinfo),
        DateDay(2008, 5, 11,tzinfo=tzinfo)
    )

    # DateTime Interval
    assert parse('2007-03-01T13:00:00Z/2008-05-11T15:30:00Z') == Interval(
        DateTime(2007, 3, 1, 13, 0, 0, tzinfo=UTC),
        DateTime(2008, 5, 11, 15, 30, 0, tzinfo=UTC)
    )
    assert parse('2007-03-01 13:00/2008-05-11 15:30') == Interval(
        DateTime(2007, 3, 1, 13, 0, 0, tzinfo=tzinfo),
        DateTime(2008, 5, 11, 15, 30, 0, tzinfo=tzinfo)
    )
