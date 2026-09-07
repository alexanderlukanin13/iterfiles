# pendulum_extras.dates_strict has (mostly) the same structural interface as dates,
# but is strictly incompatible with naive dates
import abc
import operator
import sys
import datetime
from abc import abstractmethod
from datetime import date as date_t, datetime as datetime_t, tzinfo as tzinfo_t, timedelta
from time import struct_time
from typing import NoReturn, SupportsIndex, ClassVar, Self, overload, Generic, TypeVar

import pendulum
from pendulum import Interval

from . import dates, protocol
from . import _pendulum_date
from .utils import classproperty


class DateWithZoneError(Exception):
    pass


class _NoArg:

    def __index__(self) -> int:
        return 0

_No = _NoArg()


class _StrictDateImpl:

    min: ClassVar['StrictDate']  # strict_date(date_t.min), assigned after class definition
    max: ClassVar['StrictDate']  # strict_date(date_t.max), assigned after class definition
    resolution: ClassVar['timedelta'] = date_t.resolution

    # Dumb implementation: just use date as a private field
    # TODO: rewrite the whole thing in Rust
    _d: date_t

    @property
    def year(self) -> int:
        return self._d.year

    @property
    def month(self) -> int:
        return self._d.year

    @property
    def day(self) -> int:
        return self._d.year

    def __new__(cls, year: SupportsIndex, month: SupportsIndex, day: SupportsIndex) -> Self:
        instance = super().__new__(cls)
        instance._d = date_t(year, month, day)
        return instance

    @classmethod
    def fromtimestamp(cls, __timestamp: float) -> Self:
        d = date_t.fromtimestamp(__timestamp)
        return cls(d.year, d.month, d.day)

    @classmethod
    def today(cls) -> Self:
        d = date_t.today()
        return cls(d.year, d.month, d.day)

    @classmethod
    def fromordinal(cls, __n: int) -> Self:
        d = date_t.fromordinal(__n)
        return cls(d.year, d.month, d.day)

    @classmethod
    def fromisoformat(cls, __date_string: str) -> Self:
        d = date_t.fromisoformat(__date_string)
        return cls(d.year, d.month, d.day)

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self:
        d = date_t.fromisocalendar(year, week, day)
        return cls(d.year, d.month, d.day)

    if sys.version_info >= (3, 14):
        @classmethod
        def strptime(cls, date_string: str, fmt: str) -> Self:
            d = date_t.strptime(date_string, fmt)
            return cls(d.year, d.month, d.day)

    def ctime(self) -> str:
        return self._d.ctime()

    # On <3.12, the name of the parameter in the pure-Python implementation
    # didn't match the name in the C implementation,
    # meaning it is only *safe* to pass it as a keyword argument on 3.12+
    if sys.version_info >= (3, 12):
        def strftime(self, format: str) -> str:
            return self._d.strftime(format)
    else:
        def strftime(self, __format: str) -> str:
            return self._d.strftime(__format)

    def __format__(self, __fmt: str) -> str:
        return self._d.__format__(__fmt)

    def isoformat(self) -> str:
        return self._d.isoformat()

    def timetuple(self) -> struct_time:
        return self._d.timetuple()

    def toordinal(self) -> int:
        return self._d.toordinal()

    def replace(self, year: SupportsIndex = _No, month: SupportsIndex = _No, day: SupportsIndex = _No) -> Self:
        kw = {}
        if year is not _No:
            kw['year'] = year
        if month is not _No:
            kw['month'] = month
        if day is not _No:
            kw['day'] = day
        d = self._d.replace(**kw)
        return self.__class__(d.year, d.month, d.day)



    def __add__(self, __value: timedelta) -> Self:
        d = self._d + __value
        return self.__class__(d.year, d.month, d.day)

    def __radd__(self, __value: timedelta) -> Self:
        d = self._d + __value
        return self.__class__(d.year, d.month, d.day)

    @overload
    def __sub__(self, __value: timedelta) -> Self: ...

    @overload
    def __sub__(self, __value: datetime_t) -> NoReturn: ...

    @overload
    def __sub__(self, __value: 'StrictDate') -> timedelta: ...

    def __sub__(self, __value: timedelta | datetime_t | 'StrictDate') -> Self | timedelta:
        if isinstance(__value, timedelta):
            d = self._d - __value
            return self.__class__(d.year, d.month, d.day)
        if isinstance(__value, StrictDate):
            d = self._d - __value._d
            return self.__class__(d.year, d.month, d.day)
        return NotImplemented

    def weekday(self) -> int:
        return self._d.weekday()

    def isoweekday(self) -> int:
        return self._d.isoweekday()

    def isocalendar(self) -> 'datetime.IsoCalendarDate':
        return self._d.isocalendar()

    # ===========================================
    # Custom methods
    # ===========================================

    def to_naive_date(self) -> date_t:
        return self._d


class _CompareMixIn(abc.ABC):

    @abstractmethod
    def _compare(self, other, op) -> bool | NotImplemented: ...

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        return self._compare(other, operator.lt)

    def __le__(self, other) -> bool:
        return self._compare(other, operator.le)

    def __gt__(self, other) -> bool:
        return self._compare(other, operator.gt)

    def __ge__(self, other) -> bool:
        return self._compare(other, operator.ge)

T = TypeVar("T")

class DateUnitBase(Generic[T], abc.ABC):
    """Abstract base class for DateUnit classes (both easy and strict)."""

    @abstractmethod
    def start(self) -> T: ...

    @abstractmethod
    def end(self) -> T: ...

import pendulum
pendulum.parse()


class StrictDate(_CompareMixIn, _StrictDateImpl):
    """
    Date class that is *not* based on datetime.date,
    and *not* a superclass of datetime.datetime.

    1. Compares to datetime.date objects and has the same fields and methods.
    2. Compares to any date-like objects without tzinfo or with tzinfo=None.
       (this, by definition, excludes DateWithZone of any kind).
    3. Never equal, and doesn't compare to datetime.datetime objects.
    4. Never equal, and doesn't compare to any datetime-like objects
       (with `hour` etc.).
    5. Typing: only assignable to itself.
    """

    def __eq__(self, other) -> bool:
        if isinstance(other, StrictDate):
            return self._d == other._d
        elif isinstance(other, date_t):
            return self._d == other
        elif hasattr(other, 'year') and not hasattr(other, 'hour') and not getattr(other, 'tzinfo', None):
            try:
                return (self.year, self.month, self.day) == (other.year, other.month, other.day)
            except AttributeError:
                return False
        return False

    def _compare(self, other, op) -> bool | NotImplemented:
        if isinstance(other, StrictDate):
            return op(self._d, other._d)
        elif isinstance(other, date_t):
            return op(self._d, other)
        elif isinstance(other, DateWithUnit)
        elif hasattr(other, 'year') and not hasattr(other, 'hour') and not getattr(other, 'tzinfo', None):
            try:
                return (self.year, self.month, self.day) < (other.year, other.month, other.day)
            except AttributeError:
                return NotImplemented
        return NotImplemented


def strict_date(d: date_t) -> StrictDate:
    return StrictDate(d.year, d.month, d.day)


_StrictDateImpl.min = strict_date(date_t.min)
_StrictDateImpl.max = strict_date(date_t.max)


class _DateWithZoneImpl(_CompareMixIn, dates._DateWithZoneImpl, _StrictDateImpl):

    @classmethod
    def _raise(cls, method: str) -> NoReturn:
        raise DateWithZoneError(f"{cls.__qualname__}.{method} is forbidden (strict mode). "
                                "Either don't use it, or switch to non-strict classes from pendulum_extras.dates")

    @classmethod
    def _raise_compare(cls, other):
        raise DateWithZoneError(f"Can't compare {cls.__qualname__} to {other.__class__.__qualname__}  (strict mode). "
                                "Either don't do it, or switch to non-strict classes from pendulum_extras.dates")

    def _raise_compare_tz(self, other):
        raise DateWithZoneError(f"Can't compare {self!r} to {other!r}  (strict mode). "
                                "Either don't do it, or switch to non-strict classes from pendulum_extras.dates")

    @classmethod
    def fromordinal(cls, n: int) -> NoReturn:
        cls._raise('fromordinal')

    def toordinal(self) -> NoReturn:
        self._raise('toordinal')

    def isoformat(self) -> NoReturn:
        self._raise('isoformat')

    @classmethod
    def fromisoformat(cls, date_string: str) -> NoReturn:
        cls._raise('fromisoformat')

    def isocalendar(self) -> NoReturn:
        self._raise('isocalendar')

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> NoReturn:
        cls._raise('fromisocalendar')

    @classmethod
    def strptime(cls, date_string: str, fmt: str) -> NoReturn:
        cls._raise('strptime')


class DateWithZone(_DateWithZoneImpl):
    """
    Similar to :py:class:`pendulum_extras.dates.DateWithZone`, but
    raises exceptions when non-timezone-aware or ambiguous operations are
    performed.

    Use this class when you intend to never mix timezone-aware dates with
    naive dates.

    When typing, consider :py:class:`pendulum_extras.protocol.DateWithZone`
    if you want extra flexibility.
    """

    def __eq__(self, other) -> bool:
        # tz-aware date-like, but not datetime
        if hasattr(other, 'year') and hasattr(other, 'tzinfo') and not hasattr(other, 'hour'):
            try:
                if self.tzinfo != other.tzinfo:
                    return False
                return (self.year, self.month, self.day) == (other.year, other.month, other.day)
            except AttributeError:
                return False
        return False

    def _compare(self, other, op) -> bool | NotImplemented:
        # tz-aware date-like, but not datetime
        if hasattr(other, 'year') and hasattr(other, 'tzinfo') and not hasattr(other, 'hour'):
            try:
                if self.tzinfo != other.tzinfo:
                    return NotImplemented
                return op((self.year, self.month, self.day), (other.year, other.month, other.day))
            except AttributeError:
                return NotImplemented
        return NotImplemented


class DateWithUnit(dates._DateWithUnitImpl, _DateWithZoneImpl, abc.ABC):

    @property
    def start_day(self) -> 'DateDay':
        d = self.start_of(self.unit)
        return DateDay(d.year, d.month, d.day, d.tzinfo)

    @property
    def end_day(self) -> 'DateDay':
        d = self.end_of(self.unit)
        return DateDay(d.year, d.month, d.day, d.tzinfo)

    def to_date_interval(self) -> pendulum.Interval['DateDay']:
        return Interval(self.start_day, self.end_day)

    def __eq__(self, other) -> bool:
        # tz-aware date-like, but not datetime
        if hasattr(other, 'year') and hasattr(other, 'tzinfo') and not hasattr(other, 'hour'):
            try:
                if
                if self.tzinfo != other.tzinfo:
                    return False
                return (self.year, self.month, self.day) == (other.year, other.month, other.day)
            except AttributeError:
                return False
        return False

    def _compare(self, other, op) -> bool | NotImplemented:
        if isinstance(other, DateWithZone):
            if self.unit != other.unit
        # tz-aware date-like, but not datetime
        if hasattr(other, 'year') and hasattr(other, 'tzinfo') and not hasattr(other, 'hour'):
            try:
                if self.tzinfo != other.tzinfo:
                    return NotImplemented
                return op((self.year, self.month, self.day), (other.year, other.month, other.day))
            except AttributeError:
                return NotImplemented
        return NotImplemented


class DateYear(dates._DateYearImpl, DateWithUnit):
    pass


class DateMonth(dates._DateMonthImpl, DateWithUnit):
    pass


class DateWeek(dates._DateWeekImpl, DateWithUnit):
    pass


class DateDay(dates._DateDayImpl, DateWithUnit):
    pass
