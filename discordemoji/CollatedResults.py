import datetime as dt

from typing import Iterable, Generator
from .DayResults import DayResults
from .utils import ONE_DAY, ONE_WEEK, IsoWeekDay, previous_weekday

from operator import attrgetter


class CollatedResults:
    start_inc: dt.date
    end_inc: dt.date
    span_days: int
    guild_id: int
    message_count: int
    emoji_sent: dict[str, int]
    emoji_reacted: dict[str, int]

    def __init__(self, span: int, start_date: dt.date, dayresults: Iterable[DayResults]) -> None:
        self.start_inc = start_date
        self.span_days = span
        self.end_inc = start_date + ((self.span_days - 1) * ONE_DAY)

        lstDayresults = list(dayresults)
        assert len(lstDayresults) <= span

        dates = [dr.day for dr in lstDayresults]
        assert start_date <= min(dates)
        assert max(dates) <= start_date + (span * ONE_DAY)

        if len(lstDayresults) > 0:
            self.guild_id = lstDayresults[0].guild_id
            assert all([dr.guild_id == self.guild_id for dr in lstDayresults])
        else:
            self.guild_id = -1

        self.message_count = 0
        self.emoji_sent = dict()
        self.emoji_reacted = dict()

        for dr in lstDayresults:
            self.message_count += dr.message_count

            for k, v in dr.emoji_sent.items():
                if k in self.emoji_sent:
                    self.emoji_sent[k] += v
                else:
                    self.emoji_sent[k] = v

            for k, v in dr.emoji_reacted.items():
                if k in self.emoji_reacted:
                    self.emoji_reacted[k] += v
                else:
                    self.emoji_reacted[k] = v

    @staticmethod
    def by_week(
        dayresults: Iterable[DayResults], starts_on: IsoWeekDay) -> Generator["CollatedResults", None, None]:
        # TODO: unit test:
        # first and last CollatedResults should not be empty

        this_week: list[DayResults] = []

        # start a new Week
        # Calculate end date of this week from first element -> set weekday to starts_on -> + 7
        # Add to this_week until the next element is greater than the next end_date
        # HOLD next_element and construct the CollatedResults, then move on
        dayresults_it = iter(dayresults)
        this_week.append(next(dayresults_it))
        end_date_incl = previous_weekday(this_week[0].day, starts_on) + ONE_WEEK

        for dr in dayresults_it:
            if dr.day > end_date_incl:
                yield CollatedResults(7, end_date_incl - ONE_WEEK, this_week)
                this_week.clear()

                assert previous_weekday(dr.day, starts_on) == end_date_incl
                end_date_incl += ONE_WEEK

            this_week.append(dr)

        if len(this_week) > 0:
            yield CollatedResults(7, end_date_incl - ONE_WEEK, this_week)

    def __str__(self) -> str:
        return (
            f"<{self.start_inc.isoformat()}..{self.end_inc.isoformat()}: {self.message_count} msgs, "
            f"{sum(self.emoji_sent.values())} sent ({len(self.emoji_sent.keys())} uniq), "
            f"{sum(self.emoji_reacted.values())} reacted ({len(self.emoji_reacted.keys())} uniq)>"
        )
