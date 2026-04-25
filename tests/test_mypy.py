# NOTE: this is tested via mypy, not pytest
import datetime
import pendulum
from iterfiles import pendulum_extras as extras
from iterfiles.pendulum_extras import dates, dates_strict
from iterfiles.pendulum_extras import protocol_pendulum as proto


def mypy_datetime_protocols() -> None:
    # DateLike - datetime.date protocol
    date_like: proto.DateLike = datetime.date(2026, 3, 21)
    date_pend: proto.DateLike = pendulum.Date(2026, 3, 21)
    date_unit: proto.DateLike = extras.DateWithZone(2026, 3, 21, pendulum.UTC)

    # DateTimeLike - datetime.datetime protocol
    # note: it doesn't cover 100%, there are few methods not included, see EXCLUDED_FROM_PROTOCOL comments
    datetime_like: proto.DateTimeLike = datetime.datetime(2026, 3, 21, 12, 30)
    datetime_pend: proto.DateTimeLike = pendulum.DateTime(2026, 3, 21, 12, 30)

    # TimeLike - datetime.time protocol
    time_like: proto.TimeLike = datetime.time(12, 30)
    time_pend: proto.TimeLike = pendulum.Time(12, 30)


def mypy_pendulum_protocols() -> None:
    # dates.DateWithZone and dates_strict.DateWithZone adhere to pendulum.Date protocol
    date_pend: proto.Date = pendulum.Date(2026, 3, 21)
    date_tz: proto.Date = dates.DateWithZone(2026, 3, 21, pendulum.UTC)
    date_tz_s: proto.Date = dates_strict.DateWithZone(2026, 3, 21, pendulum.UTC)

    datetime_pend: proto.DateTime = pendulum.DateTime(2026, 3, 21, 12, 30)
