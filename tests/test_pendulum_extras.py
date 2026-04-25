import re
from datetime import date

import pendulum
from pendulum.parsing.exceptions import ParserError
import pytest
from pendulum import Interval, Date, DateTime, UTC

from iterfiles.pendulum_extras.__init__ import parse_exact, parse_humanized, DateWithZone, DateDay, DateWeek, DateMonth, \
    DateYear, DateWithZoneWarning, DateWithZoneISOFormatWarning


def test_date_with_zone():
    tzinfo_local = pendulum.local_timezone()
    tzinfo_paris = pendulum.now(tz='Europe/Paris').timezone

    with pytest.raises(TypeError, match=re.escape("DateWithZone.__new__() missing 1 required positional argument: 'tzinfo'")):
        DateWithZone(2026, 1, 1)

    with pytest.raises(TypeError, match="Expected tzinfo, got None"):
        DateWithZone(2026, 1,1, None)

    with pytest.raises(TypeError, match="Expected tzinfo, got 'local'"):
        DateWithZone(2026, 1,1, 'local')

    # =====================================
    # SECTION 1: Test datetime.date methods
    # =====================================

    d = DateWithZone.today()
    assert type(d) is DateWithZone
    assert d.naive() == date(d.year, d.month, d.day)
    assert d.tzinfo is tzinfo_local

    d = DateWithZone.fromtimestamp(DateTime(2026, 3, 24).timestamp())
    assert type(d) is DateWithZone
    assert d == date(2026, 3, 24)
    assert d.tzinfo is tzinfo_local

    with pytest.warns(DateWithZoneWarning, match='.+fromisoformat returns date in UTC'):
        d = DateWithZone.fromisoformat('2026-03-24')
        assert type(d) is DateWithZone
        assert d == date(2026, 3, 24)

    # toordinal, fromordinal
    with pytest.warns(DateWithZoneWarning, match='.+toordinal strips the timezone information and returns plain int'):
        assert DateWithZone(1, 1, 1, tzinfo_paris).toordinal() == 1
    with pytest.warns(DateWithZoneWarning, match='.+fromordinal returns date in UTC'):
        d = DateWithZone.fromordinal(1)
        assert type(d) is DateWithZone
        assert d == date(1, 1, 1)

    # isoformat, fromisoformat
    #with pytest.warns(DateWithZoneISOFormatWarning, match=''):
    #    assert DateWithZone(2026, 3, 24, tzinfo_paris).isoformat() == '2026-03-24'




def test_date_to_interval():
    tzinfo = pendulum.now(tz='US/Alaska').timezone

    # Day
    assert DateDay(2026, 3, 24, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 3, 24, tzinfo=tzinfo),
        DateTime(2026, 3, 24, 23, 59, 59, 999999, tzinfo=tzinfo))

    # Week
    assert DateWeek(2026, 3, 23, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 3, 23, tzinfo=tzinfo),
        DateTime(2026, 3, 29, 23, 59, 59, 999999, tzinfo=tzinfo))
    assert DateWeek(2026, 3, 25, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 3, 23, tzinfo=tzinfo),
        DateTime(2026, 3, 29, 23, 59, 59, 999999, tzinfo=tzinfo))

    # Month
    assert DateMonth(2026, 3, 1, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 3, 1, tzinfo=tzinfo),
        DateTime(2026, 3, 31, 23, 59, 59, 999999, tzinfo=tzinfo))
    assert DateMonth(2026, 3, 15, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 3, 1, tzinfo=tzinfo),
        DateTime(2026, 3, 31, 23, 59, 59, 999999, tzinfo=tzinfo))

    # Year
    assert DateYear(2026, 1, 1, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 1, 1, tzinfo=tzinfo),
        DateTime(2026, 12, 31, 23, 59, 59, 999999, tzinfo=tzinfo))
    assert DateYear(2026, 6, 15, tzinfo=tzinfo).to_datetime_interval() == Interval(
        DateTime(2026, 1, 1, tzinfo=tzinfo),
        DateTime(2026, 12, 31, 23, 59, 59, 999999, tzinfo=tzinfo))


def test_parse_exact():
    local = pendulum.local_timezone()
    paris = pendulum.timezone('Europe/Paris')

    parse = parse_exact

    # DateTime (just a few)
    assert parse('20161001T14') == DateTime(2016, 10, 1, 14, tzinfo=local)

    # Day
    assert parse('2012-05-03').to_datetime_interval() == Interval(
        DateTime(2012, 5, 3, tzinfo=local),
        DateTime(2012, 5, 3, 23, 59, 59, 999999, tzinfo=local)
    )
    assert parse('2012-007').to_datetime_interval() == Interval(
        DateTime(2012, 1, 7, tzinfo=local),
        DateTime(2012, 1, 7, 23, 59, 59, 999999, tzinfo=local)
    )
    assert parse('2012007').to_datetime_interval() == Interval(
        DateTime(2012, 1, 7, tzinfo=local),
        DateTime(2012, 1, 7, 23, 59, 59, 999999, tzinfo=local)
    )

    # Day (with Week number)
    assert parse('2012W055').to_datetime_interval() == Interval(
        DateTime(2012, 2, 3, tzinfo=local),
        DateTime(2012, 2, 3, 23, 59, 59, 999999, tzinfo=local)
    )

    # Week
    assert parse('2012-W05').to_datetime_interval() == Interval(
        DateTime(2012, 1, 30, tzinfo=local),
        DateTime(2012, 2, 5, 23, 59, 59, 999999, tzinfo=local)
    )
    assert parse('2012W05').to_datetime_interval() == Interval(
        DateTime(2012, 1, 30, tzinfo=local),
        DateTime(2012, 2, 5, 23, 59, 59, 999999, tzinfo=local)
    )

    # Month
    assert parse('2012-05').to_datetime_interval() == Interval(
        DateTime(2012, 5, 1, tzinfo=local),
        DateTime(2012, 5, 31, 23, 59, 59, 999999, tzinfo=local)
    )

    # Year
    assert parse('2012').to_datetime_interval() == Interval(
        DateTime(2012, 1, 1, tzinfo=local),
        DateTime(2012, 12, 31, 23, 59, 59, 999999, tzinfo=local)
    )

    # start/end
    dt = parse('2012')
    assert dt.start_day == DateDay(2012, 1, 1, tzinfo=local)

    # Ambiguous (date? time?)
    with pytest.raises(ParserError):
        parse('120423')

    # Date Interval
    assert parse('2007-03-01/2008-05-11', tz='local') == Interval(
        DateDay(2007, 3, 1, tzinfo=local),
        DateDay(2008, 5, 11,tzinfo=local)
    )
    assert parse('2007-03-01/2008-05-11', tz='Europe/Paris') == Interval(
        DateDay(2007, 3, 1, tzinfo=paris),
        DateDay(2008, 5, 11, tzinfo=paris)
    )

    # DateTime Interval
    assert parse('2007-03-01T13:00:00Z/2008-05-11T15:30:00Z') == Interval(
        DateTime(2007, 3, 1, 13, 0, 0, tzinfo=UTC),
        DateTime(2008, 5, 11, 15, 30, 0, tzinfo=UTC)
    )
    assert parse('2007-03-01 13:00/2008-05-11 15:30') == Interval(
        DateTime(2007, 3, 1, 13, 0, 0, tzinfo=local),
        DateTime(2008, 5, 11, 15, 30, 0, tzinfo=local)
    )


def test_parse_humanized():
    paris = pendulum.timezone('Europe/Paris')

    parse = parse_humanized

    # Day
    assert parse('2012-05-03 @ Europe/Paris').to_datetime_interval() == Interval(
        DateTime(2012, 5, 3, tzinfo=paris),
        DateTime(2012, 5, 3, 23, 59, 59, 999999, tzinfo=paris)
    )

    # Week
    assert parse('2012W05 @ Europe/Paris').to_datetime_interval() == Interval(
        DateTime(2012, 1, 30, tzinfo=paris),
        DateTime(2012, 2, 5, 23, 59, 59, 999999, tzinfo=paris)
    )

    # Month
    assert parse('2012-05 @ Europe/Paris').to_datetime_interval() == Interval(
        DateTime(2012, 5, 1, tzinfo=paris),
        DateTime(2012, 5, 31, 23, 59, 59, 999999, tzinfo=paris)
    )

    # Year
    assert parse('2012 @ Europe/Paris').to_datetime_interval() == Interval(
        DateTime(2012, 1, 1, tzinfo=paris),
        DateTime(2012, 12, 31, 23, 59, 59, 999999, tzinfo=paris)
    )


def test_parse_humanized_time(local_timezone_bishkek):
    today = pendulum.today('local')
    tzinfo_05 = pendulum.parse('2026-03-26T12:30+05:00').tzinfo
    paris = pendulum.timezone('Europe/Paris')
    local = pendulum.local_timezone()

    parse = parse_humanized

    # Time only
    assert parse('12:30') == today.replace(hour=12, minute=30, second=0, microsecond=0, tzinfo=local)
    assert parse('12:30:23') == today.replace(hour=12, minute=30, second=23, microsecond=0, tzinfo=local)
    assert parse('12:30:23.456') == today.replace(hour=12, minute=30, second=23, microsecond=456000, tzinfo=local)  # sic!
    assert parse('12:30:23.456789') == today.replace(hour=12, minute=30, second=23, microsecond=456789, tzinfo=local)

    # Time + Timezone
    assert parse('12:30+05:00') == today.replace(hour=12, minute=30, second=0, microsecond=0, tzinfo=tzinfo_05)
    assert parse('12:30Z') == today.replace(hour=12, minute=30, second=0, microsecond=0, tzinfo=UTC)

    assert parse('12:30 @ Europe/Paris') == today.replace(hour=12, minute=30, second=0, microsecond=0, tzinfo=paris)

    with pytest.raises(ValueError, match=re.escape("Two conflicting ways to represent timezone: '12:30+05:00 @ Europe/Paris'")):
        parse('12:30+05:00 @ Europe/Paris')
    with pytest.raises(ValueError, match=re.escape("Two conflicting ways to represent timezone: '12:30Z @ Europe/Paris'")):
        parse('12:30Z @ Europe/Paris')
