import discord
import aiostream
import re

from .config import DISCORD_BOT_TOKEN

import os
import pickle
from datetime import date, datetime, time, timedelta
from typing import Generator, Optional
from pprint import pprint as pp


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as", self.user)
        print(f"Member of {len(self.guilds)} guilds:")
        if len(self.guilds) == 0:
            exit(0)

        for g in self.guilds:
            print(f" - {g.name} ({g.id})")
            print(f"   {len(g.text_channels)} text channels")

        guild = self.guilds[0]

        channel = None
        channel_search_name = "beep-boop"
        for c in guild.text_channels:
            if c.name.lower() == channel_search_name:
                channel = c
                break
        if channel is None:
            print(f"Could not find #{channel_search_name}")
            exit(0)
        else:
            print(f"Using channel {channel} ({channel.id})")

        # self.get_emoji(guild)

        # await self.send_emoji_test(channel)
        await self.get_emoji_results(90, guild)

        # print(f"Printing messages from {guild.name}:")
        # await self.read_history(channel)

        # print(f"Counting reactions from {guild.name}:")
        # await self.get_reactions(channel)

        print(" === DONE === ")

    def get_emoji(self, guild: discord.Guild):
        print(f"{len(guild.emojis)}/{guild.emoji_limit} custom emoji")
        for e in guild.emojis:
            print("Y" if e.is_usable else " ", e.id, e.name)

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
        msg = " ".join(str(e) for e in channel.guild.emojis if e.is_usable)
        print("Done.")

    async def get_reactions(self, channel: discord.TextChannel):
        reaction_count: dict[str, int] = dict()
        limit = 5000
        count = 0
        async for m in channel.history(limit=limit):
            if count % (limit // 100) == 0:
                print(".", end="", flush=True)
            count += 1
            for r in m.reactions:
                if type(r.emoji) is str or not r.is_custom_emoji():
                    continue
                key = r.emoji.name
                if key in reaction_count:
                    reaction_count[key] += r.count
                else:
                    reaction_count[key] = r.count

        pp(reaction_count)

    async def get_emoji_results(self, days: int, guild: discord.Guild):
        today = date.today()
        total_msgs = 0
        total_sent = 0
        total_reacted = 0
        for i in range(days):
            day = today - timedelta(days=i)
            results = DayResults.try_cache(day, guild)
            if results is None:
                results = await DayResults.count_emoji(day, guild)
            total_msgs += results.message_count
            total_reacted += sum(results.emoji_reacted.values())
            total_sent += sum(results.emoji_sent.values())
            print(str(results))

        print(
            f"{days} days, {total_msgs} messages, {total_sent} emoji sent, {total_reacted} emoji reacted."
        )

    async def read_history(self, channel: discord.TextChannel):
        text_limit = 50
        m: discord.Message
        async for m in channel.history():
            output = m.clean_content
            l_output = len(output)
            if l_output > text_limit - 3:
                print(m.id, f": ({l_output})", output[: text_limit - 3] + "...")
            else:
                print(m.id, f": ({l_output})", output)


class DayResults:
    day: date
    guild_id: int
    emoji_sent: dict[str, int]
    emoji_reacted: dict[str, int]
    message_count: int

    @staticmethod
    def try_cache(on_date: date, guild: discord.Guild) -> Optional["DayResults"]:
        filename = f"cache/{guild.id}_{on_date.isoformat()}_DayResults.dat"
        if os.path.exists(filename):
            with open(filename, mode="rb") as fd:
                obj = pickle.load(fd)
                if (
                    type(obj) is DayResults
                    and obj.day == on_date
                    and obj.guild_id == guild.id
                ):
                    print("Cache hit", filename)
                    return obj
        return None

    @staticmethod
    async def count_emoji(on_date: date, guild: discord.Guild) -> "DayResults":
        all_channels = aiostream.stream.merge(
            *[
                chan.history(
                    limit=5000,
                    after=datetime.combine(on_date, time(0, 0, 0)),
                    before=datetime.combine(on_date + timedelta(days=1), time(0, 0, 0)),
                )
                for chan in guild.text_channels
                if guild.me in chan.members
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

                for pe in find_custom_emoji(m):
                    if pe.name in results.emoji_sent:
                        results.emoji_sent[pe.name] += 1
                    else:
                        results.emoji_sent[pe.name] = 1
            # ... async for m in streamer

        if on_date < date.today():  # Today hasn't finished, so don't cache it.
            try:
                filename = f"cache/{guild.id}_{on_date.isoformat()}_DayResults.dat"
                with open(filename, mode="wb") as fd:
                    pickle.dump(results, fd)
                print("Cached", filename)
            except Exception as e:
                print("Failed to cache object:", str(e))

        return results

    def __str__(self) -> str:
        return (
            f"<{self.day.isoformat()}: {self.message_count} msgs, "
            f"{sum(self.emoji_sent.values())} sent ({len(self.emoji_sent.keys())} uniq), "
            f"{sum(self.emoji_reacted.values())} reacted ({len(self.emoji_reacted.keys())} uniq)>"
        )


def find_custom_emoji(
    m: discord.Message,
) -> Generator[discord.PartialEmoji, None, None]:
    emoji_re = re.compile(r"<:\w+:[0-9]+>")

    for match in emoji_re.finditer(m.content):
        yield discord.PartialEmoji.from_str(match.group(0))


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(DISCORD_BOT_TOKEN)
