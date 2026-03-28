import pendulum

from .dates import DateWithZone
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
    compatibility with DateWithZoneStrict.
    """
    def __eq__(self, other) -> bool:
        if isinstance(other, DateWithZoneStrict):
            return False
        return super().__eq__(self, other)

    def __ne__(self, other) -> bool:
        if isinstance(other, DateWithZone):
            return False
        return super().__ne__(self, other)

    def __lt__(self, other) -> bool:
        if isinstance(other, DateWithZone):
            return False
        return super().__lt__(self, other)

    def __lt__(self, other) -> bool:
        if isinstance(other, DateWithZone):
            return False
        return super().__lt__(self, other)