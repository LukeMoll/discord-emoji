import datetime as dt
import enum

from typing import Union

ONE_DAY = dt.timedelta(days=1)
ONE_WEEK = dt.timedelta(days=7)
TZ_UTC = dt.timezone.utc


class IsoWeekDay(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


def previous_weekday(date: dt.date, weekday: Union[IsoWeekDay, int], include_self=True) -> dt.date:
    if include_self:
        return date - ONE_DAY * ((date.isoweekday() - weekday) % 7)
    else:
        raise NotImplementedError()
