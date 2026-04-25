# pendulum_extras.dates_strict has (mostly) the same structural interface as dates,
# but is strictly incompatible with naive dates
from typing import NoReturn

from . import dates, protocol


class DateWithZoneError(Exception):
    pass


class DateWithZone(dates.DateWithZone):
    """
    Similar to :py:class:`pendulum_extras.dates.DateWithZone`, but
    raises exceptions when non-timezone-aware or ambiguous operations are
    performed.

    Use this class when you intend to never mix timezone-aware dates with
    naive dates. When typing, consider :py:class:`pendulum_extras.protocol.DateWithZone`
    """

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

    def __eq__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            self._raise_compare(other)
        if self.tzinfo != other.tzinfo:
            self._raise_compare_tz(other)
        return (self.year, self.month, self.day) == (other.year, other.month, other.day)

    def __ne__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            self._raise_compare(other)
        if self.tzinfo != other.tzinfo:
            self._raise_compare_tz(other)
        return (self.year, self.month, self.day) != (other.year, other.month, other.day)

    def __lt__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            self._raise_compare(other)
        if self.tzinfo != other.tzinfo:
            self._raise_compare_tz(other)
        return (self.year, self.month, self.day) < (other.year, other.month, other.day)

    def __le__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            self._raise_compare(other)
        if self.tzinfo != other.tzinfo:
            self._raise_compare_tz(other)
        return (self.year, self.month, self.day) <= (other.year, other.month, other.day)

    def __gt__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            self._raise_compare(other)
        if self.tzinfo != other.tzinfo:
            self._raise_compare_tz(other)
        return (self.year, self.month, self.day) > (other.year, other.month, other.day)

    def __ge__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            self._raise_compare(other)
        if self.tzinfo != other.tzinfo:
            self._raise_compare_tz(other)
        return (self.year, self.month, self.day) >= (other.year, other.month, other.day)
