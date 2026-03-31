from datetime import tzinfo as tzinfo_t

from typing import Self

from .protocol_pendulum import Date, DateTime, DateTimeLike


class DateWithZone(Date):

    tzinfo: tzinfo_t

    def naive(self) -> Self:
        ...

    @classmethod
    def from_datetime(cls, dt: DateTimeLike) -> Self:
        ...

