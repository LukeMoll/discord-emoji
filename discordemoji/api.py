from flask import Flask

from .Cache import Cache
from .DayResults import DayResults
from .DiscordClient import MyClient, get_client

__app__ = Flask(__name__)

def get_app():
    return __app__

@__app__.route("/")
def index():
    client = get_client()
    return f"{len(client.cache.contiguous_period())} days cached!"