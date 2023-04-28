import discord

from .config import DISCORD_BOT_TOKEN

import datetime as dt
from time import perf_counter
from typing import Generator, Optional, Any

from .Cache import Cache
from .DayResults import DayResults
from .utils import *

__client__ : Optional["MyClient"] = None

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

def get_client() -> MyClient:
    if __client__ is None:
        intents = discord.Intents.default()
        intents.message_content = True
        __client__ = MyClient(intents=intents)
        __client__.run(DISCORD_BOT_TOKEN)

    return __client__


