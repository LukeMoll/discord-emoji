import datetime as dt
import discord
import os
import pickle

from typing import Union, Generator, Optional, Iterable

from .DayResults import DayResults
from .utils import *

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
        results : list[dt.date] = []

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
    
    def get_all(self, days: Iterable[dt.date]) -> Iterable[Optional["DayResults"]]:
        return map(self.get, days)