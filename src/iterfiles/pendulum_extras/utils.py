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


class _MATCH:
    offset_with_colon = re.compile(r'\+\d{2}:\d{2}').fullmatch
