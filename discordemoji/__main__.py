import discord
import aiostream
import re

from .config import DISCORD_BOT_TOKEN

import os
import pickle
import datetime as dt
from time import perf_counter
from typing import Generator, Optional, Union, Iterable, Any
from pprint import pprint as pp

ONE_DAY = dt.timedelta(days=1)
TZ_UTC = dt.timezone.utc

class MyClient(discord.Client):
    cache: "Cache"
    guild: discord.Guild

    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        print("Logged on as", self.user)
        print(f"Member of {len(self.guilds)} guilds:")
        if len(self.guilds) == 0:
            exit(0)

        for g in self.guilds:
            print(f" - {g.name} ({g.id})")
            print(f"   {len(g.text_channels)} text channels")

        self.guild = self.guilds[0]
        self.cache = Cache("cache/", self.guild)

        channel = None
        channel_search_name = "beep-boop"
        for c in self.guild.text_channels:
            if c.name.lower() == channel_search_name:
                channel = c
                break
        if channel is None:
            print(f"Could not find #{channel_search_name}")
            exit(0)
        else:
            print(f"Using channel {channel} ({channel.id})")

        # await self.send_emoji_test(channel)
        # await self.get_emoji_results(90, self.guild)

        # print(f"Printing messages from {guild.name}:")
        # await self.read_history(channel)

        # print(f"Counting reactions from {guild.name}:")
        # await self.get_reactions(channel)

        await self.crawl()

        print(" === DONE === ")

    def get_usable_emoji(self, guild: discord.Guild):
        print(f"{len(guild.emojis)}/{guild.emoji_limit} custom emoji")
        for e in guild.emojis:
            print("Y" if e.is_usable() else " ", e.id, e.name, e.url)

    async def send_emoji_test(self, channel: discord.TextChannel):
        msg = ""
        emojis = iter(channel.guild.emojis)
        e = str(next(emojis))
        try:
            while True:
                while len(msg) + len(e) < 1999:
                    msg += e + " "
                    e = str(next(emojis))
                await channel.send(content=msg, silent=True)
                msg = ""

        except StopIteration:
            await channel.send(content=msg, silent=True)
        msg = " ".join(str(e) for e in channel.guild.emojis if e.is_usable())

    async def get_emoji_results(self, days: int, guild: discord.Guild):
        today = dt.date.today()
        total_msgs = 0
        total_sent = 0
        total_reacted = 0
        for i in range(days):
            day = today - dt.timedelta(days=i)
            results = self.cache.get(day)
            if results is None:
                results = await DayResults.count_emoji(day, guild)
                self.cache.insert(results)
            total_msgs += results.message_count
            total_reacted += sum(results.emoji_reacted.values())
            total_sent += sum(results.emoji_sent.values())
            print(str(results))

        print(
            f"{days} days, {total_msgs} messages, {total_sent} emoji sent, {total_reacted} emoji reacted."
        )

    async def crawl(self):
        for day in self.days_to_crawl():
            before_s = perf_counter()
            results = await DayResults.count_emoji(day, self.guild)
            duration_s = perf_counter() - before_s
            self.cache.insert(results)
            print(f"Cached {self.cache.filename_for(day)} ({results.message_count:5d} msgs, {duration_s:4.1f}s)")

    def days_to_crawl(self) -> Generator[dt.date, None, None]:
        # Should be cached up to (inclusive)
        yesterday = dt.date.today() - dt.timedelta(days=1)

        # Should be cached back to (inclusive)
        server_created = self.guild.created_at.date()

        cached_days = set(self.cache.cached_days())

        if len(cached_days) > 0:
            last_cached = max(cached_days)
            progress = len(cached_days) / (yesterday - server_created).days
            print(f"{len(cached_days)} days already cached ({progress:.0%}) - most recent was {last_cached}")

            # First priority is last_cached..yesterday
            d = last_cached + ONE_DAY
            while d <= yesterday:
                yield d
                d += ONE_DAY

            d = last_cached - ONE_DAY
        else:
            d = yesterday

        print(f"Building historical cache backwards from {d}")

        # Next is:
        #   end of the most-recent continugously cached period
        # ..the next cached day (excl) OR server creation (incl)
        while d in cached_days:
            d -= ONE_DAY

        # d is now the first un-cached day before the contiguous cached period
        while server_created <= d and d not in cached_days:
            yield d
            d -= ONE_DAY


class Cache:
    path: str
    guild_id: int
    last_updated: dt.datetime

    def __init__(self: "Cache", path: str, guild_or_id: Union[discord.Guild, int]) -> None:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        self.path = path

        if isinstance(guild_or_id, discord.Guild):
            self.guild_id = guild_or_id.id
        elif type(guild_or_id) is int:
            self.guild_id = guild_or_id
        else:
            raise TypeError()
        
        self.last_updated = dt.datetime.now(TZ_UTC)

    def insert(self, obj: "DayResults") -> bool:
        assert obj.guild_id == self.guild_id
        if obj.day < dt.date.today():  # Today hasn't finished, so don't cache it.
            try:
                filename = self.filename_for(obj.day)

                with open(filename, mode="wb") as fd:
                    pickle.dump(obj, fd)

                self.last_updated = dt.datetime.now(TZ_UTC)
                return True
            except Exception as e:
                print("Failed to cache object:", str(e))

        return False

    def filename_for(self, day: dt.date) -> str:
        return os.path.join(self.path, f"{self.guild_id}_{day.isoformat()}_DayResults.dat")

    def has(self, day: dt.date) -> bool:
        return os.path.exists(self.filename_for(day))

    def cached_days(self) -> Generator[dt.date, None, None]:
        prefix = f"{self.guild_id}_"
        suffix = "_DayResults.dat"

        gen = (
            fn[len(prefix) : -len(suffix)]
            for fn in os.listdir(self.path)
            if (os.path.isfile(os.path.join(self.path,fn)) and fn.startswith(prefix) and fn.endswith(suffix))
        )

        for day_str in gen:
            try:
                day = dt.date.fromisoformat(day_str)
                yield day
            except:
                print(f"Unexpected date format {day_str}")
                continue

    def contiguous_period(self) -> list[dt.date]:
        results = []

        cached_days = sorted(self.cached_days(), reverse=True)

        for d in cached_days:
            if len(results) == 0:
                results.append(d)
                continue
            elif d - results[-1] > ONE_DAY:
                break
            else:
                results.append(d)
        
        return results

    def get(self, day: dt.date) -> Optional["DayResults"]:
        if self.has(day):
            filename = self.filename_for(day)
            with open(filename, mode="rb") as fd:
                obj = pickle.load(fd)
                if type(obj) is DayResults and obj.day == day and obj.guild_id == self.guild_id:
                    return obj
                else:
                    print(f"Malformed or incompatible unpickled object from {filename}")
        return None
    
    def get_all(self, days: Iterable[dt.date]) -> Generator["DayResults", None, None]:
        return map(self.get, days)


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
            tzinfo=TZ_UTC
        )
        today_end = dt.datetime.combine(
            on_date + ONE_DAY,
            dt.time(0, 0, 0),
            tzinfo=TZ_UTC
        )

        all_channels = aiostream.stream.merge(
            *[
                chan.history(
                    limit=5000,
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


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run(DISCORD_BOT_TOKEN)
