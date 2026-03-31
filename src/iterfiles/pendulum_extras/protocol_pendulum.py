from collections.abc import Iterator
from datetime import date, timedelta, tzinfo as tzinfo_t, datetime, time as time_t
from time import struct_time as struct_time_t
from typing import Protocol, Self, ClassVar, SupportsIndex, NamedTuple, Literal, TypeVar, Generic, Any
import typing_extensions

from pendulum import WeekDay, Timezone, FixedTimezone, UTC
from pendulum.utils._compat import PYPY

IndexOrNone = typing_extensions.SupportsIndex | None


class IsoCalendarDate(NamedTuple):
    year: int
    week: int
    weekday: int


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
    year: int
    month: int
    day: int

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

    def isocalendar(self):
        ...

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self:
        ...

    def replace(self, year: IndexOrNone = None, month: IndexOrNone = None, day: IndexOrNone = None) -> Self:
        ...

    @classmethod
    def strptime(cls, date_string: str, fmt: str) -> Self:
        ...


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

    def closest(self, dt1: date, dt2: date) -> Self:
        ...

    def farthest(self, dt1: date, dt2: date) -> Self:
        ...

    def is_future(self) -> bool:
        ...

    def is_past(self) -> bool:
        ...

    def is_leap_year(self) -> bool:
        ...

    def is_long_year(self) -> bool:
        ...

    def is_same_day(self, dt: date) -> bool:
        ...

    # NOTE: is_anniversary and is_birthday are synonyms
    def is_anniversary(self, dt: date | None = None) -> bool:
        ...

    def is_birthday(self, dt: date | None = None) -> bool:
        ...

    def add(self, years: int = 0, months: int = 0, weeks: int = 0, days: int = 0) -> Self:
        ...

    def subtract(self, years: int = 0, months: int = 0, weeks: int = 0, days: int = 0) -> Self:
        ...

    def __add__(self, other: timedelta) -> Self:
        ...

    def __sub__(self, other: timedelta) -> Self:
        ...

    # NOTE: pendulum (as of version 3.2.0) also supports Date - Date -> Interval
    # We believe this is bad design to mix types like this.
    #@overload
    #def __sub__(self, __dt: Self) -> Interval[Self]:
    #    ...

    # Date == datetime is explicitly disallowed in pendulum
    #@overload
    #def __sub__(self, __dt: datetime) -> NoReturn: ...
    #    ...

    def diff(self, dt: date | None = None, abs: bool = True) -> Interval[Self]:
        ...

    def diff_for_humans(self, other: date | None = None, absolute: bool = False, locale: str | None = None) -> str:
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

    def average(self, dt: date | None = None) -> Self:
        ...


class TimeLike(Protocol):
    """Protocol for datetime.time"""
    min: ClassVar['TimeLike']
    max: ClassVar['TimeLike']
    resolution: ClassVar[timedelta]

    hour: int
    minute: int
    second: int
    microsecond: int
    tzinfo: tzinfo_t | None
    fold: int  # 0 or 1

    @classmethod
    def fromisoformat(cls, time_string: str) -> Self:
        ...

    @classmethod
    def strptime(self, date_string: str, format: str) -> Self:
        ...

    def replace(self,
                hour: int | None = None,
                minute: int | None = None,
                second: int | None = None,
                microsecond: int | None = None,
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

    def utcoffset(self) -> int | None:
        ...

    def dst(self) -> timedelta | None:
        ...

    def tzname(self) -> str | None:
        ...


class DateTimeLike(Protocol):
    """Protocol for datetime.datetime"""

    min: ClassVar['DateTimeLike']
    max: ClassVar['DateTimeLike']

    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    microsecond: int
    tzinfo: tzinfo_t | None
    fold: int  # 0 or 1

    # Note: it will be removed in "future version" of Python
    @classmethod
    def utcnow(cls) -> Self:
        ...

    @classmethod
    def now(cls, tz: tzinfo_t | None = None) -> Self:
        ...

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
    def combine(cls, date: DateLike, time: TimeLike, tzinfo: tzinfo_t | None = None) -> Self:
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

    def __eq__(self, other: 'DateTimeLike') -> bool:
        ...

    def __ne__(self, other: 'DateTimeLike') -> bool:
        ...

    def __lt__(self, other: 'DateTimeLike') -> bool:
        ...

    def __le__(self, other: 'DateTimeLike') -> bool:
        ...

    def __gt__(self, other: 'DateTimeLike') -> bool:
        ...

    def __ge__(self, other: 'DateTimeLike') -> bool:
        ...

    def __add__(self, other: timedelta) -> Self:
        ...

    def __sub__(self, other: timedelta | 'DateTimeLike') -> Self:
        ...

    @classmethod
    def date(cls) -> DateLike:
        ...

    @classmethod
    def time(cls) -> time_t:
        ...

    @classmethod
    def timetz(cls) -> time_t:
        ...

    def replace(self,
                year: int | None = None,
                month: int | None = None,
                day: int | None = None,
                hour: int | None = None,
                minute: int | None = None,
                second: int | None = None,
                microsecond: int | None = None,
                tzinfo: tzinfo_t | None = None,
                *, fold: int = 0):
        ...

    def astimezone(self, tz: tzinfo_t | None = None) -> Self:
        ...

    def utcoffset(self) -> int | None:
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

    def isocalendar(self) -> IsoCalendarDate:
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
    def instance(cls, dt: datetime,
            tz: str | Timezone | FixedTimezone | tzinfo_t | None = UTC,
    ) -> Self:
        ...

    @classmethod
    def now(cls, tz: str | Timezone | FixedTimezone | tzinfo_t | None = None) -> Self:
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

    def closest(self, *dts: datetime.datetime) -> Self:  # type: ignore[override]
        ...

    def farthest(self, *dts: datetime.datetime) -> Self:  # type: ignore[override]
        ...

    def is_future(self) -> bool:
        ...

    def is_past(self) -> bool:
        ...

    def is_long_year(self) -> bool:
        ...

    def is_same_day(self, dt: DateTimeLike) -> bool:  # type: ignore[override]
        ...

    def is_anniversary(self, dt: DateTimeLike | None = None) -> bool:
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

    def diff(self, dt: DateTimeLike | None = None, abs: bool = True) -> Interval[DateLike]:
        ...

    def diff_for_humans(self,
        other: DateTimeLike | None = None,
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

    def average(self, dt: DateTimeLike | None = None) -> Self:
        ...

    def __sub__(self, other: timedelta | DateLike) -> Self | Interval[Self]:
        ...

    def __rsub__(self, other: DateLike) -> Interval[Self]:
        ...

    def __add__(self, other: timedelta) -> Self:
        ...

    def __radd__(self, other: timedelta) -> Self:
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
    def combine(cls, date: DateLike, time: TimeLike, tzinfo: tzinfo_t | None = None) -> Self:
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
    min: ClassVar['TimeDeltaLike']
    max: ClassVar['TimeDeltaLike']
    resolution: ClassVar['TimeDeltaLike']

    days: int
    seconds: int
    microseconds: int

    def __eq__(self, other: 'TimeDeltaLike') -> bool:
        ...

    def __ne__(self, other: 'TimeDeltaLike') -> bool:
        ...

    # TODO: add arithmetics as per docs

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
    def seconds(self) -> int:
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
