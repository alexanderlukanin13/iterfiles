import functools
import re


def run_once(func):
    """Decorator that ensures the decorated function only runs once."""
    has_run = False

    @functools.wraps(func)  # Preserves metadata of the original function
    def wrapper(*args, **kwargs):
        nonlocal has_run
        if has_run:
            return
        has_run = True
        return func(*args, **kwargs)

    return wrapper


class classproperty[T]:  # noqa
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner) -> T:
        return self.fget(owner)


# Regular expressions belong here
class _MATCH:
    tz_offset_with_colon = re.compile(r'[+-]\d{2}:\d{2}').fullmatch
    tz_utc_offset_with_colon = re.compile(r'UTC[+-]\d{2}:\d{2}', re.I).fullmatch
