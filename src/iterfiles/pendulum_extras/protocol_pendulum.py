import sys
from collections.abc import Iterator
import datetime
from datetime import date as date_t, timedelta, time as time_t, tzinfo as tzinfo_t, datetime as datetime_t
from time import struct_time as struct_time_t
from typing import Protocol, Self, ClassVar, SupportsIndex, NamedTuple, Literal, TypeVar, Any, overload, NoReturn
import typing_extensions

import pendulum
from pendulum import WeekDay, Timezone, FixedTimezone, UTC

IndexOrNone = typing_extensions.SupportsIndex | None


class _TimezoneArgumentIgnored(tzinfo_t):
    """
    This is to facilitate dt.replace(..., tzinfo=None).
    DO NOT USE THIS CLASS ANYWHERE ELSE.
    """

    def tzname(self, dt):
        raise NotImplementedError

    def utcoffset(self, dt):
        raise NotImplementedError

    def dst(self, dt):
        raise NotImplementedError

TimezoneArgumentIgnored = _TimezoneArgumentIgnored()


class DateLike(Protocol):
    """Protocol for datetime.date"""

    @property
    def year(self) -> int:
        ...

    @property
    def month(self) -> int:
        ...

    @property
    def day(self) -> int:
        ...

    @classmethod
    def today(cls) -> Self:
        ...

    @classmethod
    def fromtimestamp(cls, t: float) -> Self:
        ...

    @classmethod
    def fromordinal(cls, n: int) -> Self:
        ...

    def toordinal(self) -> int:
        ...

    def isoformat(self) -> str:
        ...

    @classmethod
    def fromisoformat(cls, date_string: str) -> Self:
        ...

    def isocalendar(self) -> 'datetime.IsoCalendarDate':
        ...

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self:
        ...

    def replace(self, year: SupportsIndex, month: SupportsIndex, day: SupportsIndex) -> Self:
        ...

    if sys.version_info >= (3, 14):
        @classmethod
        def strptime(cls, date_string: str, fmt: str) -> Self:
            ...

    # TODO: Changed in version 3.13: Comparison between datetime object and an instance of the date subclass
    # that is not a datetime subclass no longer converts the latter to date, ignoring the time part and the time zone.
    # The default behavior can be changed by overriding the special comparison methods in subclasses.


class Date(DateLike, Protocol):
    """Protocol for pendulum.Date"""

    @property
    def day_of_week(self) -> WeekDay:
        ...

    @property
    def day_of_year(self) -> int:
        ...

    @property
    def week_of_year(self) -> int:
        ...

    @property
    def days_in_month(self) -> int:
        ...

    def set(self, year: int | None = None, month: int | None = None, day: int | None = None) -> Self:
        ...

    @property
    def week_of_month(self) -> int:
        ...

    @property
    def age(self) -> int:
        ...

    @property
    def quarter(self) -> int:
        ...

    def to_date_string(self) -> str:
        ...

    def to_formatted_date_string(self) -> str:
        ...

    def closest(self, dt1: date_t, dt2: date_t) -> Self:
        ...

    def farthest(self, dt1: date_t, dt2: date_t) -> Self:
        ...

    def is_future(self) -> bool:
        ...

    def is_past(self) -> bool:
        ...

    def is_leap_year(self) -> bool:
        ...

    def is_long_year(self) -> bool:
        ...

    def is_same_day(self, dt: date_t) -> bool:
        ...

    # NOTE: is_anniversary and is_birthday are synonyms
    def is_anniversary(self, dt: date_t | None = None) -> bool:
        ...

    def is_birthday(self, dt: date_t | None = None) -> bool:
        ...

    def add(self, years: int = 0, months: int = 0, weeks: int = 0, days: int = 0) -> Self:
        ...

    def subtract(self, years: int = 0, months: int = 0, weeks: int = 0, days: int = 0) -> Self:
        ...

    def __add__(self, other: timedelta) -> Self:
        ...

    @overload
    def __sub__(self, other: timedelta) -> pendulum.Date:
        ...

    # Date == datetime is explicitly disallowed in pendulum
    @overload
    def __sub__(self, __dt: datetime) -> NoReturn:
        ...

    @overload
    def __sub__(self, __dt: pendulum.Date) -> pendulum.Interval[pendulum.Date]:
        ...

    def diff(self, dt: date_t | None = None, abs: bool = True) -> pendulum.Interval[pendulum.Date]:
        ...

    def diff_for_humans(self, other: date_t | None = None, absolute: bool = False, locale: str | None = None) -> str:
        ...

    def start_of(self, unit: str) -> Self:
        ...

    def end_of(self, unit: str) -> Self:
        ...

    def next(self, day_of_week: WeekDay | None = None) -> Self:
        ...

    def previous(self, day_of_week: WeekDay | None = None) -> Self:
        ...

    def first_of(self, unit: str, day_of_week: WeekDay | None = None) -> Self:
        ...

    def last_of(self, unit: str, day_of_week: WeekDay | None = None) -> Self:
        ...

    def nth_of(self, unit: str, nth: int, day_of_week: WeekDay) -> Self:
        ...

    def average(self, dt: date_t | None = None) -> Self:
        ...


class TimeLike(Protocol):
    """Protocol for datetime.time"""
    min: ClassVar[time_t]
    max: ClassVar[time_t]
    resolution: ClassVar[timedelta]

    @property
    def hour(self) -> int:
        ...

    @property
    def minute(self) -> int:
        ...

    @property
    def second(self) -> int:
        ...

    @property
    def microsecond(self) -> int:
        ...

    @property
    def tzinfo(self) -> tzinfo_t | None:
        ...

    @property
    def fold(self) -> int:  # 0 or 1
        ...

    @classmethod
    def fromisoformat(cls, time_string: str) -> Self:
        ...

    if sys.version_info >= (3, 14):
        @classmethod
        def strptime(self, date_string: str, format: str) -> Self:
            ...

    def replace(self,
                hour: SupportsIndex = None,
                minute: SupportsIndex = None,
                second: SupportsIndex = None,
                microsecond: SupportsIndex = None,
                tzinfo: tzinfo_t | None = None,
                *, fold: int=0):
        ...

    def isoformat(self, timespec: str='auto'):
        ...

    def strftime(self, format: str) -> str:
        ...

    # Same as strftime
    def __format__(self, format: str) -> str:
        ...

    def utcoffset(self) -> timedelta | None:
        ...

    def dst(self) -> timedelta | None:
        ...

    def tzname(self) -> str | None:
        ...


class DateTimeLike(Protocol):
    """Protocol for datetime.datetime"""

    min: ClassVar[Self]
    max: ClassVar[Self]

    @property
    def year(self) -> int:
        ...

    @property
    def month(self) -> int:
        ...

    @property
    def day(self) -> int:
        ...

    @property
    def hour(self) -> int:
        ...

    @property
    def minute(self) -> int:
        ...

    @property
    def second(self) -> int:
        ...

    @property
    def microsecond(self) -> int:
        ...

    @property
    def tzinfo(self) -> tzinfo_t | None:
        ...

    @property
    def fold(self) -> int:  # 0 or 1
        ...

    # Note: it will be removed in "future version" of Python
    @classmethod
    def utcnow(cls) -> Self:
        ...

    # EXCLUDED_FROM_PROTOCOL
    #@classmethod
    #def now(cls, tz: tzinfo_t | None = None) -> Self:
    #    ...

    # Note: as per documentation, this is equivalent of now() but returning naive object
    @classmethod
    def today(cls) -> Self:
        ...

    @classmethod
    def fromtimestamp(cls, timestamp: int | float, tz:tzinfo_t | None = None) -> Self:
        ...

    @classmethod
    def utcfromtimestamp(cls, timestamp: int | float) -> Self:
        ...

    @classmethod
    def fromordinal(cls, ordinal: int) -> Self:
        ...

    @classmethod
    def combine(cls, date: date_t, time: time_t, tzinfo: tzinfo_t | None = None) -> Self:
        ...

    @classmethod
    def fromisoformat(cls, date_string: str) -> Self:
        ...

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self:
        ...

    @classmethod
    def strptime(cls, date_string: str, format: str) -> Self:
        ...

    def __eq__(self, other: datetime_t) -> bool:
        ...

    def __ne__(self, other: datetime_t) -> bool:
        ...

    def __lt__(self, other: datetime_t) -> bool:
        ...

    def __le__(self, other: datetime_t) -> bool:
        ...

    def __gt__(self, other: datetime_t) -> bool:
        ...

    def __ge__(self, other: datetime_t) -> bool:
        ...

    def __add__(self, other: timedelta) -> Self:
        ...

    # EXCLUDED_FROM_PROTOCOL: DateTimeLike.__sub__
    # pendulum returns custom subclasses which is fine (as long as they follow Liskov substitution principle),
    # but typing should be as follows:
    #
    # @overload
    # def __sub__(self, x: datetime_t, /) -> timedelta:
    #     ...
    #
    # @overload
    # def __sub__(self, x: timedelta, /) -> datetime_t:
    #     ...

    def date(self) -> DateLike:
        ...

    def time(self) -> time_t:
        ...

    def timetz(self) -> time_t:
        ...

    def replace(self,
                year: SupportsIndex = None,
                month: SupportsIndex = None,
                day: SupportsIndex = None,
                hour: SupportsIndex = None,
                minute: SupportsIndex = None,
                second: SupportsIndex = None,
                microsecond: SupportsIndex = None,
                tzinfo: tzinfo_t | None = None,
                *, fold: int = 0):
        ...

    def astimezone(self, tz: tzinfo_t | None = None) -> Self:
        ...

    def utcoffset(self) -> timedelta | None:
        ...

    def dst(self) -> timedelta | None:
        ...

    def tzname(self) -> str | None:
        ...

    def timetuple(self) -> struct_time_t:
        ...

    def utctimetuple(self) -> struct_time_t:
        ...

    def toordinal(self) -> int:
       ...

    def timestamp(self) -> float:
       ...

    def weekday(self) -> int:
        ...

    def isoweekday(self) -> int:
        ...

    def isocalendar(self) -> 'datetime.IsoCalendarDate':
        ...

    def isoformat(self, sep: str = 'T', timespec: str = 'auto') -> str:
        ...

    def ctime(self) -> str:
        ...

    def strftime(self, format: str) -> str:
        ...

    def __format__(self, format: str):
        ...


class DateTime(DateTimeLike, Protocol):
    """Protocol pendulum.DateTime"""

    @classmethod
    def create(
            cls,
            year: SupportsIndex,
            month: SupportsIndex,
            day: SupportsIndex,
            hour: SupportsIndex = 0,
            minute: SupportsIndex = 0,
            second: SupportsIndex = 0,
            microsecond: SupportsIndex = 0,
            tz: str | float | Timezone | FixedTimezone | tzinfo_t = UTC, # TODO: why float and not int???
            fold: int = 1, # TODO: why???
            raise_on_unknown_times: bool = False,
    ) -> Self:
        ...

    @classmethod
    def instance(cls, dt: datetime_t,
            tz: str | Timezone | FixedTimezone | tzinfo_t | None = UTC,
    ) -> Self:
        ...

    @overload
    def now(cls, tz: tzinfo_t | None = None) -> pendulum.DateTime:
        ...

    @overload
    def now(cls, tz: str | Timezone | FixedTimezone | None = ...) -> pendulum.DateTime:
        ...

    def set(self,
            year: int | None = None,
            month: int | None = None,
            day: int | None = None,
            hour: int | None = None,
            minute: int | None = None,
            second: int | None = None,
            microsecond: int | None = None,
            tz: str | int | float | Timezone | FixedTimezone | tzinfo_t | None = None,
    ) -> Self:
        ...

    @property
    def float_timestamp(self) -> float:
        ...

    @property
    def int_timestamp(self) -> int:
        ...

    @property
    def offset(self) -> int | None:
        ...

    @property
    def offset_hours(self) -> float | None:
        ...

    @property
    def timezone(self) -> Timezone | FixedTimezone | None:
        ...

    @property
    def tz(self) -> Timezone | FixedTimezone | None:
        ...

    @property
    def timezone_name(self) -> str | None:
        ...

    @property
    def age(self) -> int:
        ...

    def is_local(self) -> bool:
        ...

    def is_utc(self) -> bool:
        ...

    def is_dst(self) -> bool:
        ...

    def get_offset(self) -> int | None:
        ...

    def date(self) -> DateLike:
        ...

    def time(self) -> time_t:
        ...

    def naive(self) -> Self:
        ...

    def on(self, year: int, month: int, day: int) -> Self:
        ...

    def at(self, hour: int, minute: int = 0, second: int = 0, microsecond: int = 0) -> Self:
        ...

    def in_timezone(self, tz: str | Timezone | FixedTimezone) -> Self:
        ...

    def in_tz(self, tz: str | Timezone | FixedTimezone) -> Self:
        ...

    def to_time_string(self) -> str:
        ...

    def to_datetime_string(self) -> str:
        ...

    def to_day_datetime_string(self) -> str:
        ...

    def to_atom_string(self) -> str:
        ...

    def to_cookie_string(self) -> str:
        ...

    def to_iso8601_string(self) -> str:
        ...

    def to_rfc822_string(self) -> str:
        ...

    def to_rfc850_string(self) -> str:
        ...

    def to_rfc1036_string(self) -> str:
        ...

    def to_rfc1123_string(self) -> str:
        ...

    def to_rfc2822_string(self) -> str:
        ...

    def to_rfc3339_string(self) -> str:
        ...

    def to_rss_string(self) -> str:
        ...

    def to_w3c_string(self) -> str:
        ...

    def closest(self, *dts: datetime_t) -> Self:  # type: ignore[override]
        ...

    def farthest(self, *dts: datetime_t) -> Self:  # type: ignore[override]
        ...

    def is_future(self) -> bool:
        ...

    def is_past(self) -> bool:
        ...

    def is_long_year(self) -> bool:
        ...

    def is_same_day(self, dt: datetime_t) -> bool:  # type: ignore[override]
        ...

    def is_anniversary(self, dt: datetime_t | None = None) -> bool:
        ...

    def add(self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: float = 0,
        microseconds: int = 0,
    ) -> Self:
        ...

    def subtract(self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: float = 0,
        microseconds: int = 0,
    ) -> Self:
        ...

    def diff(self, dt: datetime_t | None = None, abs: bool = True) -> pendulum.Interval[datetime_t]:
        ...

    def diff_for_humans(self,
        other: pendulum.DateTime | None = None,
        absolute: bool = False,
        locale: str | None = None,
    ) -> str:
        ...

    def start_of(self, unit: str) -> Self:
        ...

    def end_of(self, unit: str) -> Self:
        ...

    def next(self, day_of_week: WeekDay | None = None, keep_time: bool = False) -> Self:
        ...

    def previous(self, day_of_week: WeekDay | None = None, keep_time: bool = False) -> Self:
        ...

    def first_of(self, unit: str, day_of_week: WeekDay | None = None) -> Self:
        ...

    def last_of(self, unit: str, day_of_week: WeekDay | None = None) -> Self:
        ...

    def nth_of(self, unit: str, nth: int, day_of_week: WeekDay) -> Self:
        ...

    def average(self, dt: pendulum.DateTime | None = None) -> Self:
        ...

    @overload
    def __sub__(self, other: timedelta) -> pendulum.DateTime:
        ...

    @overload
    def __sub__(self, other: pendulum.DateTime) -> pendulum.Interval[datetime_t]:
        ...

    def __rsub__(self, other: pendulum.DateTime) -> pendulum.Interval[datetime_t]:
        ...

    def __add__(self, other: timedelta) -> pendulum.DateTime:
        ...

    def __radd__(self, other: timedelta) -> pendulum.DateTime:
        ...

    @classmethod
    def fromtimestamp(cls, t: float, tz: tzinfo_t | None = None) -> Self:
        ...

    @classmethod
    def utcfromtimestamp(cls, t: float) -> Self:
        ...

    @classmethod
    def fromordinal(cls, n: int) -> Self:
        ...

    @classmethod
    def combine(cls, date: date_t, time: time_t, tzinfo: tzinfo_t | None = None) -> Self:
        ...

    def astimezone(self, tz: tzinfo_t | None = None) -> Self:
        ...

    def replace(self,
            year: IndexOrNone = None,
            month: IndexOrNone = None,
            day: IndexOrNone = None,
            hour: IndexOrNone = None,
            minute: IndexOrNone = None,
            second: IndexOrNone = None,
            microsecond: IndexOrNone = None,
            tzinfo: tzinfo_t | None | bool | Literal[True] = True,  # TODO: remove bool
            fold: int | None = None,
    ) -> Self:
        ...


class TimeDeltaLike(Protocol):
    """Protocol for datetime.timedelta"""
    min: ClassVar['TimeDeltaLike']
    max: ClassVar['TimeDeltaLike']
    resolution: ClassVar['TimeDeltaLike']

    days: int          # Between -999,999,999 and 999,999,999 inclusive.
    seconds: int       # Between 0 and 86,399 inclusive.
    microseconds: int  # Between 0 and 999,999 inclusive.

    def __eq__(self, other: 'TimeDeltaLike') -> bool:
        ...

    def __ne__(self, other: 'TimeDeltaLike') -> bool:
        ...

    # NOTE: following are timedelta arithmetics, as per docs

    # t1 = t2 + t3
    # Sum of t2 and t3. Afterwards t1 - t2 == t3 and t1 - t3 == t2 are true. (1)
    # 1. This is exact but may overflow.
    def __add__(self, other: Self) -> Self:
        ...

    # t1 = t2 - t3
    # Difference of t2 and t3. Afterwards t1 == t2 - t3 and t2 == t1 + t3 are true. (1)(6)
    #
    # 1. This is exact but may overflow.
    # 6. The expression t2 - t3 will always be equal to the expression t2 + (-t3) except when t3 is equal to
    # timedelta.max; in that case the former will produce a result while the latter will overflow.
    def __sub__(self, other: Self) -> Self:
        ...

    # t1 = t2 * i
    # Delta multiplied by an integer. Afterwards t1 // i == t2 is true, provided i != 0.
    # In general, t1  * i == t1 * (i-1) + t1 is true. (1)
    #
    # t1 = t2 * f
    # Delta multiplied by a float.
    # The result is rounded to the nearest multiple of timedelta.resolution using round-half-to-even.
    #
    # 1. This is exact but may overflow.
    def __mul__(self, other: int | float) -> Self:
        ...

    # t1 = i * t2
    # Delta multiplied by an integer. Afterwards t1 // i == t2 is true, provided i != 0.
    # In general, t1  * i == t1 * (i-1) + t1 is true. (1)
    #
    # t1 = f * t2
    # Delta multiplied by a float.
    # The result is rounded to the nearest multiple of timedelta.resolution using round-half-to-even.
    #
    # 1. This is exact but may overflow.
    def __rmul__(self, other: int | float) -> Self:
        ...

    # f = t2 / t3
    # Division (3) of overall duration t2 by interval unit t3. Returns a float object.
    #
    # t1 = t2 / f or t1 = t2 / i
    # Delta divided by a float or an int.
    # The result is rounded to the nearest multiple of timedelta.resolution using round-half-to-even.
    #
    # 3. Division by zero raises ZeroDivisionError.
    def __truediv__(self, other: Self | float | int) -> float:
        ...

    # t1 = t2 // i or t1 = t2 // t3
    # The floor is computed and the remainder (if any) is thrown away. In the second case, an integer is returned. (3)
    #
    # 3. Division by zero raises ZeroDivisionError.
    def __floordiv__(self, other: Self | int) -> int | Self:
        ...

    # t1 = t2 % t3
    # The remainder is computed as a timedelta object. (3)
    #
    # 3. Division by zero raises ZeroDivisionError.
    def __mod__(self, other: Self) -> Self:
        ...

    # q, r = divmod(t1, t2)
    # Computes the quotient and the remainder:
    # q = t1 // t2 (3) and r = t1 % t2. q is an integer and r is a timedelta object.
    def __divmod__(self, other: Self) -> tuple[int, Self]:
        ...

    # +t1
    # Returns a timedelta object with the same value. (2)


    # -t1
    # Equivalent to timedelta(-t1.days, -t1.seconds, -t1.microseconds), and to t1 * -1. (1)(4)
    #
    # 1. This is exact but may overflow.
    # 4. -timedelta.max is not representable as a timedelta object.
    def __neg__(self) -> Self:
        ...

    # abs(t)
    # Equivalent to +t when t.days >= 0, and to -t when t.days < 0. (2)
    #
    # 2. This is exact and cannot overflow.
    def __abs__(self) -> Self:
        ...

    # Returns a string in the form [D day[s], ][H]H:MM:SS[.UUUUUU], where D is negative for negative t. (5)
    #
    # 5. String representations of timedelta objects are normalized similarly to their internal representation.
    # This leads to somewhat unusual results for negative timedeltas. For example:
    #
    # >>> timedelta(hours=-5)
    # datetime.timedelta(days=-1, seconds=68400)
    # >>> print(_)
    # -1 day, 19:00:00
    def __str__(self) -> str:
        ...

    # Returns a string representation of the timedelta object as a constructor call with canonical attribute values.
    def __repr__(self) -> str:
        ...

    def total_seconds(self) -> float:
        ...


class Duration(TimeDeltaLike, Protocol):


    def total_minutes(self) -> float:
        ...

    def total_hours(self) -> float:
        ...

    def total_days(self) -> float:
        ...

    def total_weeks(self) -> float:
        ...

  #  if PYPY:  # TODO: do we need this? Test on pypy
#
 #       def total_seconds(self) -> float:
  #          ...

    @property
    def years(self) -> int:
        ...

    @property
    def months(self) -> int:
        ...

    @property
    def weeks(self) -> int:
        ...

    #if PYPY:  # TODO: do we need this? Test on pypy
#
 #       @property
  #      def days(self) -> int:
   #         ...

    @property
    def remaining_days(self) -> int:
        ...

    @property
    def hours(self) -> int:
        ...

    @property
    def minutes(self) -> int:
        ...

    @property
    def remaining_seconds(self) -> int:
        ...

    # Note: microseconds is a field in TimeDeltaLike - omitted here

    @property
    def invert(self) -> bool:
        ...

    def in_weeks(self) -> int:
        ...

    def in_days(self) -> int:
        ...

    def in_hours(self) -> int:
        ...

    def in_minutes(self) -> int:
        ...

    def in_seconds(self) -> int:
        ...

    def in_words(self, locale: str | None = None, separator: str = " ") -> str:
        ...

    def as_timedelta(self) -> timedelta:
        ...


_T = TypeVar("_T", bound=DateLike | DateTimeLike)

class Interval(Protocol[_T]):
    years: int
    months: int
    weeks: int
    days: int
    remaining_days: int
    hours: int
    minutes: int
    start: _T
    end: _T

    def in_years(self) -> int:
        ...

    def in_months(self) -> int:
        ...

    def in_weeks(self) -> int:
        ...

    def in_days(self) -> int:
        ...

    def in_words(self, locale: str | None = None, separator: str = " ") -> str:
        ...

    def range(self, unit: str, amount: int = 1) -> Iterator[_T]:
        ...

    def as_duration(self) -> Duration:
        ...

    def __iter__(self) -> Iterator[_T]:
        ...

    def __contains__(self, item: _T) -> bool:
        ...

    def __add__(self, other: TimeDeltaLike) -> Duration:
        ...

    def __radd__(self, other: TimeDeltaLike) -> Duration:
        ...

    def __sub__(self, other: TimeDeltaLike) -> Duration:
        ...

    def __neg__(self) -> Self:
        ...

    def __mul__(self, other: int | float) -> Duration:
        ...

    def __rmul__(self, other: int | float) -> Duration:
        ...

    def __floordiv__(self, other: int | TimeDeltaLike) -> int | Duration:
        ...

    def __truediv__(self, other: float | TimeDeltaLike) -> Duration | float:
        ...

    def __mod__(self, other: TimeDeltaLike) -> Duration:
        ...

    def __divmod__(self, other: TimeDeltaLike) -> tuple[int, Duration]:
        ...

    def __abs__(self) -> Self:
        ...

    def __eq__(self, other: Any) -> bool:
        ...

    def __ne__(self, other: Any) -> bool:
        ...

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        ...
