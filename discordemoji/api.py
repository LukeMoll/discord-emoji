import datetime as dt
import os

from flask import Flask

from .Cache import Cache
from .DayResults import DayResults
from .DiscordClient import MyClient, get_client
from .CollatedResults import CollatedResults
from .utils import ONE_DAY, IsoWeekDay

from typing import cast

__app__ = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    static_url_path="/",
)


def get_app() -> Flask:
    return __app__


@__app__.route("/api/")
def index() -> str:
    client = get_client()
    return f"{len(client.cache.contiguous_period())} days cached!"


@__app__.route("/api/cache")
def cache() -> dict:
    client = get_client()
    total_days = len(list(client.cache.cached_days()))
    contig_days = len(list(client.cache.contiguous_period()))
    all_days = (dt.date.today() - ONE_DAY - client.guild.created_at.date()).days

    return {
        "cached_days_count": total_days,
        "contiguous_days_count": contig_days,
        "days_since_created": all_days,
    }


@__app__.route("/api/messages")
def users() -> dict:
    cache = get_client().cache
    data = list(cache.get_all(cache.contiguous_period()))

    result = {
        "start": data[0].day.isoformat(),
        "end": data[-1].day.isoformat(),
        "dates": list(map(lambda x: x.day.isoformat(), data)),
        "messages": list(map(lambda x: x.message_count, data)),
    }

    return result


@__app__.route("/api/emoji")
def emoji() -> dict:
    cache = get_client().cache
    data = cast(list[DayResults], list(cache.get_all(cache.contiguous_period())))

    dates = list(map(lambda x: x.day.isoformat(), data))
    all_emoji: set[str] = set()
    for d in data:
        all_emoji.update(d.emoji_sent.keys())
        all_emoji.update(d.emoji_reacted.keys())

    sent_emoji: dict[str, list[int]] = {k: [] for k in all_emoji}
    reacted_emoji: dict[str, list[int]] = {k: [] for k in all_emoji}

    for d in data:
        for e in all_emoji:
            sent_emoji[e].append(d.emoji_sent.get(e, 0))
            reacted_emoji[e].append(d.emoji_reacted.get(e, 0))

    return {
        "start": data[0].day.isoformat(),
        "end": data[-1].day.isoformat(),
        "dates": dates,
        "sent_emoji": sent_emoji,
        "reacted_emoji": reacted_emoji,
    }


@__app__.route("/api/byweek")
def emojibyweek() -> dict:
    cache = get_client().cache
    data = cast(list[DayResults], list(cache.get_all(cache.contiguous_period())))

    data_byweek = CollatedResults.by_week(data, starts_on=IsoWeekDay.MONDAY)

    dates = list(map(lambda x: x.start_inc.isoformat(), data_byweek))
    all_emoji: set[str] = set()
    for d in data_byweek:
        all_emoji.update(d.emoji_sent.keys())
        all_emoji.update(d.emoji_reacted.keys())

    message_count: list[int] = []
    sent_emoji: dict[str, list[int]] = {k: [] for k in all_emoji}
    reacted_emoji: dict[str, list[int]] = {k: [] for k in all_emoji}

    for d in data_byweek:
        message_count.append(d.message_count)
        for e in all_emoji:
            sent_emoji[e].append(d.emoji_sent.get(e, 0))
            reacted_emoji[e].append(d.emoji_reacted.get(e, 0))

    assert len(message_count) == len(dates)
    for v in sent_emoji.values():
        assert len(v) == len(dates)
    for v in reacted_emoji.values():
        assert len(v) == len(dates)

    return {
        "start": dates[0],
        "end": dates[-1],
        "dates": dates,
        "message_count": message_count,
        "sent_emoji": sent_emoji,
        "reacted_emoji": reacted_emoji,
    }
