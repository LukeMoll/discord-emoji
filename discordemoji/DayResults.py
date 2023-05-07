import datetime as dt
import discord
import aiostream.stream  # type: ignore
import re

from typing import Generator, Iterable

from .utils import *


class DayResults:
    day: dt.date
    guild_id: int
    message_count: int
    emoji_sent: dict[str, int]
    emoji_reacted: dict[str, int]

    @staticmethod
    async def count_emoji(on_date: dt.date, guild: discord.Guild) -> "DayResults":
        today_start = dt.datetime.combine(
            on_date,
            dt.time(0, 0, 0),
            tzinfo=TZ_UTC,
        )
        today_end = dt.datetime.combine(
            on_date + ONE_DAY,
            dt.time(0, 0, 0),
            tzinfo=TZ_UTC,
        )

        all_channels = aiostream.stream.merge(
            *[
                chan.history(
                    limit=5000000,
                    after=today_start,
                    before=today_end,
                )
                for chan in guild.text_channels
                if guild.me in chan.members and chan.created_at < today_end
            ]
        )

        results = DayResults()
        results.day = on_date
        results.guild_id = guild.id
        results.emoji_sent = dict()
        results.emoji_reacted = dict()
        results.message_count = 0

        async with all_channels.stream() as streamer:
            m: discord.Message
            async for m in streamer:
                results.message_count += 1
                for r in m.reactions:
                    if type(r.emoji) is str or not r.is_custom_emoji():
                        continue

                    if r.emoji.name in results.emoji_reacted:
                        results.emoji_reacted[r.emoji.name] += r.count
                    else:
                        results.emoji_reacted[r.emoji.name] = r.count

                for pe in DayResults.find_custom_emoji(m):
                    if pe.name in results.emoji_sent:
                        results.emoji_sent[pe.name] += 1
                    else:
                        results.emoji_sent[pe.name] = 1
            # ... async for m in streamer

        return results

    @staticmethod
    def find_custom_emoji(
        m: discord.Message,
    ) -> Generator[discord.PartialEmoji, None, None]:
        emoji_re = re.compile(r"<:\w+:[0-9]+>")

        for match in emoji_re.finditer(m.content):
            yield discord.PartialEmoji.from_str(match.group(0))

    def __str__(self) -> str:
        return (
            f"<{self.day.isoformat()}: {self.message_count} msgs, "
            f"{sum(self.emoji_sent.values())} sent ({len(self.emoji_sent.keys())} uniq), "
            f"{sum(self.emoji_reacted.values())} reacted ({len(self.emoji_reacted.keys())} uniq)>"
        )
