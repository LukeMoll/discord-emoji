import datetime as dt

import enum

ONE_DAY = dt.timedelta(days=1)
ONE_WEEK = dt.timedelta(days=7)
TZ_UTC = dt.timezone.utc


class IsoWeekDay(enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


def previous_weekday(date: dt.date, weekday: IsoWeekDay) -> dt.date:
    return date - ONE_DAY * ((date.isoweekday() - weekday) % 7)
