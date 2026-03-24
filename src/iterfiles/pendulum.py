# This module contains extra functionality built on top of `pendulum` package
import re
from datetime import tzinfo

import pendulum
from pendulum import Date, Time, DateTime, Duration, Interval, Timezone


class DateWithUnit(pendulum.Date):

    def __new__(cls, year: int, month: int, day: int, tzinfo: Timezone = pendulum.UTC):
        instance = super().__new__(cls, year, month, day)
        instance.tzinfo = tzinfo
        return instance

    _UNIT = ''

    def as_interval(self) -> pendulum.Interval[pendulum.DateTime]:
        d = DateTime(self.year, self.month, self.day, tzinfo=self.tzinfo)
        return Interval(d, d.end_of(self._UNIT))


class DateYear(DateWithUnit):
    _UNIT = 'year'


class DateMonth(DateWithUnit):
    _UNIT = 'month'


class DateWeek(DateWithUnit):
    _UNIT = 'week'


class DateDay(DateWithUnit):
    _UNIT = 'day'


_match_year = re.compile(r'\d{4}').fullmatch
_match_month = re.compile(r'\d{4}-\d{2}').fullmatch
_match_week = re.compile(r'\d{4}-?W\d{2}').fullmatch

def parse(s: str, tz: str = 'local') -> DateWithUnit | DateTime | Interval:
    result = pendulum.parse(s, exact=True, tz=tz)
    if isinstance(result, DateTime):
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
        raise ValueError('Time is not allowed, use date/datetime/interval')
