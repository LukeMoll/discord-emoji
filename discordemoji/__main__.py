from .DiscordClient import get_client
from .api import get_app
from .config import DISCORD_BOT_TOKEN

if __name__ == "__main__":
    client = get_client()
    client.run(DISCORD_BOT_TOKEN) # TODO: need to run this "in the background"

    app = get_app()
    app.run()