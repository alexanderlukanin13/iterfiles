import pendulum

from .dates_strict import DateWithZone as DateWithZoneStrict
from .utils import run_once

@run_once
def patch_pendulum_date_naive() -> None:
    """
    Adds naive() method to pendulum.Date class (if not exists yet).
    """
    if not hasattr(pendulum.Date, 'naive'):
        def naive(self: pendulum.Date) -> pendulum.Date:
            return self
        pendulum.Date.naive = naive


@run_once
def patch_pendulum_date_comparison_strict() -> None:
    """
    Patches comparison methods (__eq__ and family) to achieve smooth two-way
    compatibility with :py:class:`pendulum_extras.dates_strict.DateWithZone`.
    """
    def __eq__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return other == self
        return super().__eq__(self, other)

    def __ne__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return other != self
        return super().__ne__(self, other)

    def __lt__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return other >= self
        return super().__lt__(self, other)

    def __le__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return other > self
        return super().__le__(self, other)

    def __gt__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return other <= self
        return super().__gt__(self, other)

    def __ge__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return other < self
        return super().__ge__(self, other)

    pendulum.Date.__eq__ = __eq__
    pendulum.Date.__ne__ = __ne__
    pendulum.Date.__lt__ = __lt__
    pendulum.Date.__le__ = __le__
    pendulum.Date.__gt__ = __gt__
    pendulum.Date.__ge__ = __ge__
