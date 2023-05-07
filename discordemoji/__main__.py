from .DiscordClient import get_client
from .api import get_app
from .config import DISCORD_BOT_TOKEN

import threading

if __name__ == "__main__":
    client = get_client()
    app = get_app()

    t1 = threading.Thread(target=client.run, args=(DISCORD_BOT_TOKEN,))
    t2 = threading.Thread(target=app.run)

    t1.start()
    t2.start()

    # So as not to immediately exit the main thread
    t1.join()
    t2.join()
