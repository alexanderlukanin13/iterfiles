from . import dates, protocol


class DateWithZoneError(Exception):
    pass


class DateWithZone(dates.DateWithZone):

    @classmethod
    def _raise(cls, method: str) -> NotImplemented:
        raise DateWithZoneError(f"{cls.__qualname__}.{method} is forbidden in strict mode. "
                                f"Either don't use it, or switch to non-strict classes from pendulum_extras.dates")

    @classmethod
    def fromordinal(cls, n: int) -> NotImplemented:
        cls._raise('fromordinal')

    def toordinal(self) -> NotImplemented:
        self._raise('toordinal')

    def isoformat(self) -> NotImplemented:
        self._raise('isoformat')

    @classmethod
    def fromisoformat(cls, date_string: str) -> NotImplemented:
        cls._raise('fromisoformat')

    def isocalendar(self) -> NotImplemented:
        self._raise('isocalendar')

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> NotImplemented:
        cls._raise('fromisocalendar')

    @classmethod
    def strptime(cls, date_string: str, fmt: str) -> NotImplemented:
        cls._raise('strptime')

    def __eq__(self, other) -> bool:
        if not isinstance(other, protocol.DateWithZone):
            raise DateWithZoneError(f"Can't compare {self.__class__.__qualname__} to {other.__class__.__qualname__}")
        return self.year == other.year and self.month == other.month and self.day == other.day and self.tzinfo == other.tzinfo

