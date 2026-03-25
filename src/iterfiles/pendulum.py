# This module contains extra functionality built on top of `pendulum` package
import abc
import re
import time
from datetime import timedelta, tzinfo as tzinfo_t

import pendulum
from pendulum import Date, Time, DateTime, Duration, Interval, Timezone, FixedTimezone, UTC


class DateWithUnit(pendulum.Date, abc.ABC):

    def __new__(cls, year: int, month: int, day: int, tzinfo: tzinfo_t = pendulum.UTC):
        instance = super().__new__(cls, year, month, day)
        instance.tzinfo = tzinfo
        return instance

    @property
    def start(self) -> 'DateDay':
        d = self.start_of(self.unit)
        return DateDay(d.year, d.month, d.day, d.tzinfo)

    @property
    def end(self) -> 'DateDay':
        d = self.end_of(self.unit)
        return DateDay(d.year, d.month, d.day, d.tzinfo)

    @staticmethod
    @abc.abstractmethod
    def from_datetime(dt: DateTime) -> 'DateWithUnit':
        raise NotImplementedError  # pragma: no cover

    def as_interval(self) -> pendulum.Interval[pendulum.DateTime]:
        # In normal conventional usage, self = self.start_of()
        # However, nothing prevents user from instantiating DateWithUnit in the middle of unit (week, month, etc.)
        # Anyway, as_interval() should still return correct Interval(start, end)
        start = self.start_of(self.unit)
        start = DateTime(start.year, start.month, start.day, tzinfo=self.tzinfo)
        return Interval(start, start.end_of(self.unit))


class DateYear(DateWithUnit):
    unit = 'year'

    @staticmethod
    def from_datetime(dt: DateTime) -> DateWithUnit:
        assert dt.tzinfo is not None
        return DateYear(dt.year, 1, 1, dt.tzinfo)

class DateMonth(DateWithUnit):
    unit = 'month'

    @staticmethod
    def from_datetime(dt: DateTime) -> DateWithUnit:
        assert dt.tzinfo is not None
        return DateMonth(dt.year, dt.month, 1, dt.tzinfo)

class DateWeek(DateWithUnit):
    unit = 'week'

    @staticmethod
    def from_datetime(dt: DateTime) -> DateWithUnit:
        assert dt.tzinfo is not None
        dt = dt - timedelta(days=dt.weekday())
        return DateWeek(dt.year, dt.month, dt.day, dt.tzinfo)

class DateDay(DateWithUnit):
    unit = 'day'

    @staticmethod
    def from_datetime(dt: DateTime) -> DateWithUnit:
        assert dt.tzinfo is not None
        return DateDay(dt.year, dt.month, dt.day, dt.tzinfo)


_match_year = re.compile(r'\d{4}').fullmatch
_match_month = re.compile(r'\d{4}-\d{2}').fullmatch
_match_week = re.compile(r'\d{4}-?W\d{2}').fullmatch


def parse_exact(s: str, tz: str = 'local') -> DateWithUnit | DateTime | Interval[DateDay] | Interval[DateTime] | Time:
    """Drop-in replacement for pendulum.parse(), returns DateWithUnit or Interval[DateDay] where appropriate."""
    result = pendulum.parse(s, exact=True, tz=tz)
    if isinstance(result, (DateTime, Time)):
        return result
    elif isinstance(result, Date):
        tzinfo = pendulum.now(tz=tz).timezone
        if result.day == 1:
            if result.month == 1 and _match_year(s):
                return DateYear(result.year, 1, 1, tzinfo=tzinfo)
            if _match_month(s):
                return DateMonth(result.year, result.month, 1, tzinfo=tzinfo)
        if _match_week(s):
            return DateWeek(result.year, result.month, result.day, tzinfo=tzinfo)
        return DateDay(result.year, result.month, result.day, tzinfo=tzinfo)
    elif isinstance(result, Interval):
        if isinstance(result.start, Date) and not isinstance(result.start, DateTime):
            tzinfo = pendulum.now(tz=tz).timezone
            start, end = result.start, result.end
            return Interval(
                DateDay(start.year, start.month, start.day, tzinfo=tzinfo),
                DateDay(end.year, end.month, end.day, tzinfo=tzinfo),
            )
        return result
    elif isinstance(result, Duration):
        raise ValueError('Duration is not allowed, use date/datetime/interval')
    else:
        raise TypeError(f'Unexpected type returned by pendulum.parse: {result!r}')


def parse_humanized(value: str) -> DateWithUnit | DateTime | Interval[DateDay] | Interval[DateTime]:
    s = value.strip()
    if '@' in s:
        s, tz = (x.strip() for x in s.split('@', 1))
        # Note that pendulum.parse(tz=...) serves as default if '+' or 'Z' is omitted - it's not an error.
        # But we make sure that '@' always returns desired timezone,
        # and that '@' and '+'/'Z' are never accepted together
        if '+' in s or 'Z' in s:
            raise ValueError(f'Two conflicting ways to represent timezone: {value!r}')
        tzinfo = pendulum.timezone(tz)
    else:
        tz = 'local'
        tzinfo = pendulum.local_timezone()
    if s == 'today':
        return DateDay.from_datetime(pendulum.today(tzinfo))
    elif s == 'yesterday':
        return DateDay.from_datetime(pendulum.yesterday(tzinfo))
    elif s == 'this week':
        return DateWeek.from_datetime(pendulum.now(tzinfo))
    elif s == 'this month':
        return DateMonth.from_datetime(pendulum.now(tzinfo))
    elif s == 'this year':
        return DateYear.from_datetime(pendulum.now(tzinfo))
    res = parse_exact(s, tz=tz)
    if isinstance(res, Time):
        # Workaround for '12:30+05:00' - pendulum (as of 3.2.0) silently drops the timezone info
        #
        # >>> pendulum.parse('12:30+05:00', exact=True)
        # Time(12, 30, 0)
        # >>> pendulum.parse('12:30+05:00')
        # DateTime(2026, 3, 25, 12, 30, 0, tzinfo=Timezone('UTC'))
        if '+' in s:
            tzinfo = FixedTimezone(time.strptime(s[s.index('+'):], '%z').tm_gmtoff)
            # Note that we check that '@' and '+'/'Z' are never present in input together
        elif 'Z' in s:
            tzinfo = UTC
        return pendulum.now(tzinfo).replace(hour=res.hour, minute=res.minute, second=res.second,
                                            microsecond=res.microsecond)
    return res
