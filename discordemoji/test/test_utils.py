import unittest

from ..utils import IsoWeekDay, previous_weekday, ONE_DAY, ONE_WEEK
import datetime as dt


class TestUtils(unittest.TestCase):
    def test_previous_weekday(self):
        today = dt.date.today()
        test_dates = [today + ONE_DAY * i for i in range(14)]

        for d in test_dates:
            for i in range(7):
                day = d + (ONE_DAY * i)
                result = previous_weekday(day, d.isoweekday())
                self.assertEqual(result, d,
                                 f"Previous {IsoWeekDay(d.isoweekday()).name} ({d.isoweekday()}) from {day}:\n\texpected {d}\n\tgot {result}")

                self.assertEqual(
                    previous_weekday((d + ONE_WEEK) + (ONE_DAY * (i)), d.isoweekday()), d + ONE_WEEK
                )
