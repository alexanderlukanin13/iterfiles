import abc
import sys
import warnings
import datetime
from datetime import timedelta, tzinfo as tzinfo_t, date, datetime as datetime_t
from typing import Self, NoReturn, overload, SupportsIndex

import pendulum
from pendulum import Date, DateTime, Interval, FixedTimezone, UTC, Timezone
import typing_extensions
from pendulum.helpers import add_duration

from .protocol_pendulum import IndexOrNone
from .utils import _MATCH



__all__ = [
    'DateWithZoneWarning', 'DateWithZoneISOFormatWarning', 'DateWithZoneProlepticWarning',
    'DateWithZone', 'DateWithUnit', 'DateDay', 'DateWeek', 'DateMonth', 'DateYear',
]


class DateWithZoneWarning(UserWarning):
    pass


class DateWithZoneISOFormatWarning(DateWithZoneWarning):
    pass


class DateWithZoneProlepticWarning(DateWithZoneWarning):
    pass


_TimezoneT = tzinfo_t | str | int


# Timezone classes - quick reminder
# =================================
#
# datetime.tzinfo
#     abstract base class used by datetime(tzinfo=...)
#     abstract: tzname, utcoffset, dst
#     implements: fromutc
# zoneinfo.ZoneInfo(datetime.tzinfo)
#     IANA time zones - all the messy stuff
# PendulumTimezone(ABC)
#     abstract: name, convert, datetime
# Timezone(zoneinfo.ZoneInfo, PendulumTimezone)
#     represents a named timezone, implements PendulumTimezone
# FixedTimezone(datetime.tzinfo, PendulumTimezone)
#     represent unnamed timezone with fixed offset, implements PendulumTimezone
#
# In practice, we should accept tzinfo (any subclass fits), str and int

def timezone(name: str | int) -> Timezone | FixedTimezone:
    """
    Drop-in replacement for ``pendulum.timezone`` - does the same but also accepts 'local'.
    """
    if isinstance(name, int):
        return pendulum.fixed_timezone(name)
    match name.lower():
        case 'utc':
            return UTC
        case 'local':
            return pendulum.local_timezone()
        case _:
            return Timezone(name)


class DateWithZone(Date):
    """
    Date with timezone *loosely* attached.
    Fully compatible with naive date and can substitute ``datetime.date`` in all contexts,
    with one exception:

    >>> TODO

    Issues warnings when non-timezone-aware operations are performed.
    """

    def __new__(cls, year: SupportsIndex, month: SupportsIndex, day: SupportsIndex, tzinfo: tzinfo_t):
        instance = super().__new__(cls, year, month, day)
        if not isinstance(tzinfo, tzinfo_t):
            raise TypeError(f'Expected tzinfo, got {tzinfo!r}')
        instance.tzinfo = tzinfo
        return instance

    # ===========================================
    # SECTION 1: overriding datetime.date methods
    # ===========================================

    @classmethod
    def today(cls) -> Self:
        """Return the current local date with local timezone."""
        dt = date.today()
        return cls(dt.year, dt.month, dt.day, pendulum.local_timezone())

    # Implementation notes:
    # allowing default None (as synonym for 'local') kinda contradicts pendulum default=UTC convention,
    # but it is dictated by date.fromtimestamp spec: dt.fromtimestamp(t) -> local timezone.
    # (We would still use tz = 'local' as default, eschewing None, but we can't break pendulum.Date compatibility).
    @classmethod
    def fromtimestamp(cls, t: float, tz: _TimezoneT | None = None) -> Self:
        """
        Return the date corresponding to the POSIX timestamp, such as is
        returned by ``time.time()``.

        Default timezone is local, so DateWithZone.fromtimestamp(t) without
        timezone is compatible with datetime.date.fromtimestamp(t).

        :param t: POSIX timestamp
        :param tz: Optional timezone argument. Accepts all tz argument types
        including plain ``int`` offset.

        returns an object of corresponding pendulum_extras class.
        """
        # We have to use manual tzinfo conversion here:
        # weirdly, DateTime.fromtimestamp only supports tzinfo | None as of pendulum 3.2.0
        if tz is None:
            tz = pendulum.local_timezone()
        elif not isinstance(tz, tzinfo_t):
            tz = pendulum.timezone(tz)
        dt = DateTime.fromtimestamp(t, tz=tz)
        return cls(dt.year, dt.month, dt.day, tzinfo=dt.tzinfo)

    @classmethod
    def fromordinal(cls, n: int) -> Self:
        """
        Return the date corresponding to the proleptic Gregorian ordinal,
        where January 1 of year 1 has ordinal 1. Timezone is UTC.
        """
        warnings.warn(
            f'{cls.__qualname__}.fromordinal returns date in UTC. '
            'Timezone-aware date classes in pendulum_extras do not support proleptic Gregorian calendar '
            'in any meaningful way, please stick to naive dates for that purpose.', DateWithZoneProlepticWarning)
        d = Date.fromordinal(n)
        return cls(d.year, d.month, d.day, pendulum.UTC)

    def toordinal(self) -> int:
        warnings.warn(
            f'{self.__class__.__qualname__}.toordinal strips the timezone information and returns plain int, '
            'same regardless of timezone. '
            'Timezone-aware date classes in pendulum_extras do not support proleptic Gregorian calendar '
            'in any meaningful way, please stick to naive dates for that purpose.', DateWithZoneProlepticWarning)
        return Date.toordinal(self)

    def isoformat(self) -> str:
        """Return a string representing the date in ISO 8601 format, YYYY-MM-DD"""
        warnings.warn(
            f'{self.__class__.__qualname__}.isoformat strips the timezone information and returns '
            'naive YYYY-MM-DD representation. '

            , DateWithZoneISOFormatWarning)
        return date.isoformat(self)

    @classmethod
    def fromisoformat(cls, date_string: str) -> Self:
        warnings.warn(
            f'{cls.__qualname__}.fromisoformat returns date in UTC. '
            'Timezone-aware date classes in pendulum_extras do not support ISO 8601 format, '
            'because date+timezone is forbidden in ISO 8601. '
            'Please stick to naive dates for that purpose, or use pendulum_extras parsing functions.',
            DateWithZoneISOFormatWarning)
        d = Date.fromisoformat(date_string)
        return cls(d.year, d.month, d.day, pendulum.UTC)

    def isocalendar(self) -> 'datetime.IsoCalendarDate':
        warnings.warn(
            f'{self.__class__.__qualname__}.isocalendar strips the timezone information and returns naive IsoCalendarDate. '
            'Timezone-aware date classes in pendulum_extras do not support isocalendar in any meaningful way, '
            'please stick to naive dates for that purpose.', DateWithZoneWarning)
        return date.isocalendar(self)

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self:
        warnings.warn(
            f'{cls.__qualname__}.fromisocalendar returns date in UTC. '
            'Timezone-aware date classes in pendulum_extras do not support fromisocalendar in any meaningful way, '
            'please stick to naive dates for that purpose.', DateWithZoneWarning)
        d = date.fromisocalendar(year, week, day)
        return cls(d.year, d.month, d.day, pendulum.UTC)

    def replace(self, year: IndexOrNone = None, month: IndexOrNone = None, day: IndexOrNone = None,
                tzinfo: tzinfo_t | None = None) -> Self:
        return self.__class__(year or self.year, month or self.month, day or self.day, tzinfo or self.tzinfo)

    if sys.version_info >= (3, 14):
        @classmethod
        def strptime(cls, date_string: str, fmt: str) -> Self:
            warnings.warn(
                f'{cls.__qualname__}.strptime returns date in UTC. '
                'Timezone-aware date classes in pendulum_extras do not support strptime in any meaningful way, '
                'please stick to naive dates for that purpose.', DateWithZoneWarning)
            d = date.strptime(date_string, fmt)  # noqa
            return cls(d.year, d.month, d.day, pendulum.UTC)

    # ==========================================================
    # SECTION 2: overriding pendulum.Date methods and properties
    # ==========================================================

    def __str__(self) -> str:
        """
        Returns a string representing the date in custom format.

        >>> str(date_with_zone(2026, 3, 24, 'Europe/Paris'))
        '2025-03-24 @ Europe/Paris'
        """
        return self.petformat()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.year!r}, {self.month!r}, {self.day!r}, tzinfo={self.tzinfo!r})'

    def set(self, year: int | None = None, month: int | None = None, day: int | None = None,
            tzinfo: tzinfo_t | None = None) -> Self:
        return self.replace(year, month, day, tzinfo)

    def to_date_string(self) -> str:
        warnings.warn(
            f'{self.__class__.__qualname__}.to_date_string strips the timezone information and returns naive '
            f'YYYY-MM-DD representation.', DateWithZoneISOFormatWarning)
        return Date.to_date_string(self)

    def to_formatted_date_string(self) -> str:
        warnings.warn(
            f'{self.__class__.__qualname__}.to_formatted_date_string strips the timezone information and returns naive '
            f'YYYY-MM-DD representation.', DateWithZoneISOFormatWarning)
        return Date.to_formatted_date_string(self)

    def closest(self, dt1: date, dt2: date) -> Self:
        """Get the closest date from the instance."""
        dt1 = self.__class__(dt1.year, dt1.month, dt1.day)
        dt2 = self.__class__(dt2.year, dt2.month, dt2.day)

        if self.diff(dt1).in_seconds() < self.diff(dt2).in_seconds():
            return dt1

        return dt2

    def farthest(self, dt1: date, dt2: date) -> Self:
        """
        Get the farthest date from the instance.
        """
        dt1 = self.__class__(dt1.year, dt1.month, dt1.day)
        dt2 = self.__class__(dt2.year, dt2.month, dt2.day)

        if self.diff(dt1).in_seconds() > self.diff(dt2).in_seconds():
            return dt1

        return dt2

    def add(self, years: int = 0, months: int = 0, weeks: int = 0, days: int = 0) -> Self:
        """Add duration to the instance."""
        dt = add_duration(date(self.year, self.month, self.day),
                               years=years, months=months, weeks=weeks, days=days)
        return self.__class__(dt.year, dt.month, dt.day, self.tzinfo)

    # Note: subtract is defined in pendulum.Date via negative add

    @overload
    def __sub__(self, __delta: timedelta) -> Self: ...

    @overload
    def __sub__(self, __dt: datetime_t) -> NoReturn: ...

    @overload
    def __sub__(self, __dt: Date) -> Interval[Date]: ...

    def __sub__(self, other: timedelta | datetime_t | Self) -> Self | Interval[Date]:
        if isinstance(other, timedelta):
            return self._subtract_timedelta(other)
        if not isinstance(other, date) or isinstance(other, datetime_t):  # fixes bug in pendulum 3.2.0
            return NotImplemented
        dt = self.__class__(other.year, other.month, other.day)
        return dt.diff(self, False)

    def diff(self, d: date | None = None, abs: bool = True) -> Interval[Date]:
        """
        Returns the difference between two Date objects as an Interval[Date].

        :param d: The date to compare to (defaults to today)
        :param abs: Whether to return an absolute interval or not
        """
        if d is None:
            d = self.today()
        return Interval(self, Date(d.year, d.month, d.day), absolute=abs)

    # ===================================
    # SECTION 3: DateWithZone new methods
    # ===================================

    def naive(self) -> Date:
        return Date(self.year, self.month, self.day)

    @classmethod
    def from_datetime(cls, dt: datetime_t) -> Self:
        if dt.tzinfo is None:
            raise ValueError("Can't create DateWithZone from naive datetime")
        return cls(dt.year, dt.month, dt.day, dt.tzinfo)

    def petformat(self):
        """
        Returns a string representing the date in custom format.

        >>> date_with_zone(2026, 3, 24, 'Europe/Paris').petformat()
        '2025-03-24 @ Europe/Paris'
        >>> date_with_zone(2026, 3, 24, 3600).petformat()
        '2025-03-24 @ +01:00'
        """
        try:
            tzname = self.tzinfo.name
        except AttributeError:
            tzname = str(self.tzinfo)
        if tzname[0] == '+' and _MATCH.tz_offset_with_colon(tzname):
            tzname = f'UTC{tzname}'
        return f'{self.year:04}-{self.month:02}-{self.day:02} @ {tzname}'

    @classmethod
    def from_petformat(cls, s: str) -> Self:
        try:
            d, tz = s.split('@', 1)
        except ValueError:
            raise ValueError(f"Failed to parse {cls.__qualname__}, string doesn't contain @: {s!r}")
        d = date.fromisoformat(d.strip())
        return cls(d.year, d.month, d.day, tzinfo=pendulum.timezone())  # TODO: it won't parse @ UTC+05:00

    @staticmethod
    def disable_all_warnings():
        """
        Disables all warning arising by upcasting DateWithZone and using it
        as pendulum.Date or datetime.date.
        """
        warnings.filterwarnings("ignore", category=DateWithZoneWarning)


class DateWithUnit(DateWithZone, abc.ABC):

    @property
    def start_day(self) -> 'DateDay':
        d = self.start_of(self.unit)
        return DateDay(d.year, d.month, d.day, d.tzinfo)

    @property
    def end_day(self) -> 'DateDay':
        d = self.end_of(self.unit)
        return DateDay(d.year, d.month, d.day, d.tzinfo)

    @staticmethod
    @abc.abstractmethod
    def from_datetime(dt: datetime_t) -> 'DateWithUnit':
        raise NotImplementedError  # pragma: no cover

    def to_date_interval(self) -> pendulum.Interval['DateDay']:
        return Interval(self.start_day, self.end_day)

    def to_datetime_interval(self) -> pendulum.Interval[pendulum.DateTime]:
        # In normal conventional usage, self = self.start_of()
        # However, nothing prevents user from instantiating DateWithUnit in the middle of unit (week, month, etc.)
        # In any case, to_datetime_interval() should still return correct Interval(start, end)
        start = self.start_of(self.unit)
        start = DateTime(start.year, start.month, start.day, tzinfo=self.tzinfo)
        return Interval(start, start.end_of(self.unit))


class DateYear(DateWithUnit):
    unit = 'year'

    @staticmethod
    def from_datetime(dt: datetime_t) -> DateWithUnit:
        if dt.tzinfo is None:
            raise ValueError("Can't create DateYear from naive datetime")
        return DateYear(dt.year, 1, 1, dt.tzinfo)

class DateMonth(DateWithUnit):
    unit = 'month'

    @staticmethod
    def from_datetime(dt: datetime_t) -> DateWithUnit:
        if dt.tzinfo is None:
            raise ValueError("Can't create DateMonth from naive datetime")
        return DateMonth(dt.year, dt.month, 1, dt.tzinfo)

class DateWeek(DateWithUnit):
    unit = 'week'

    @staticmethod
    def from_datetime(dt: datetime_t) -> DateWithUnit:
        if dt.tzinfo is None:
            raise ValueError("Can't create DateWeek from naive datetime")
        dt = dt - timedelta(days=dt.weekday())
        return DateWeek(dt.year, dt.month, dt.day, dt.tzinfo)

class DateDay(DateWithUnit):
    unit = 'day'

    @staticmethod
    def from_datetime(dt: datetime_t) -> DateWithUnit:
        if dt.tzinfo is None:
            raise ValueError("Can't create DateDay from naive datetime")
        return DateDay(dt.year, dt.month, dt.day, dt.tzinfo)