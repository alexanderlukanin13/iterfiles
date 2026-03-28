# This module contains extra functionality built on top of `pendulum` package
import functools
import re
import time
from datetime import tzinfo as tzinfo_t, date, datetime

import pendulum
from pendulum import Date, Time, DateTime, Duration, Interval, FixedTimezone, UTC

from .dates import *

_TYPES = {
    'day': DateDay,
    'week': DateWeek,
    'month': DateMonth,
    'year': DateYear,
}

def date_with_unit(dt: date | datetime, unit: str, *, tz: tzinfo_t | str | None = None) -> DateWithUnit:
    try:
        cls: type[DateWithUnit] = _TYPES[unit]
    except KeyError:
        raise ValueError(f'Invalid unit: {unit!r}')
    if isinstance(tz, str):
        tz = pendulum.timezone(tz)
    if isinstance(dt, date):
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            else:
                dt = dt.astimezone(tz)
            return cls.from_datetime(dt)
        elif isinstance(dt, DateWithUnit):
            return cls(dt.year, dt.month, dt.day, dt.tzinfo)
        return cls(dt.year, dt.month, dt.day, tz)
    raise TypeError(f'Expected date/datetime, got {dt!r}')


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


_normalize_space = functools.partial(re.compile(r'^ +| +(?= )| +$').sub, '')

class _MATCH:
    units_ago = re.compile(r'(day|week|month|year) (\d+) (day|week|month|year)s? ago', re.I).fullmatch


def parse_humanized(value: str) -> DateWithUnit | DateTime | Interval[DateDay] | Interval[DateTime]:
    s = _normalize_space(value)
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
    elif s == 'last week':
        return DateWeek.from_datetime(pendulum.now(tzinfo).subtract(weeks=1))
    elif s == 'last month':
        return DateMonth.from_datetime(pendulum.now(tzinfo).subtract(months=1))
    elif s == 'last year':
        return DateYear.from_datetime(pendulum.now(tzinfo).subtract(years=1))
    elif m := _MATCH.units_ago(s):
        desired_unit, number, unit = m.groups()
        return date_from_datetime(pendulum.now(tzinfo).subtract(**{f'{unit}s': int(number)}), desired_unit)
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
