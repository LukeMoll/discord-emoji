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


def previous_weekday(
    date: dt.date,
    argWeekday: Union[IsoWeekDay, int],
    include_self=True,
) -> dt.date:
    weekday: int
    if type(argWeekday) is IsoWeekDay:
        weekday = argWeekday.value
    elif type(argWeekday) is int:
        weekday = argWeekday
    else:
        raise TypeError(f"Invalid type: {type(argWeekday)=}")

    if include_self:
        return date - ONE_DAY * ((date.isoweekday() - weekday) % 7)
    else:
        raise NotImplementedError()

def skip_middle(s : str, shown : int) -> str:
    if len(s) <= shown * 2:
        return s
    else:
        return s[:shown] + "..." + s[-shown:]