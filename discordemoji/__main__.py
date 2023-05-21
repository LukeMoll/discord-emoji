from .DiscordClient import get_client
from .api import get_app
from .config import DISCORD_BOT_TOKEN
from .utils import skip_middle

import threading

if __name__ == "__main__":
    print(f"Using discord token {skip_middle(DISCORD_BOT_TOKEN, 3)} ({len(DISCORD_BOT_TOKEN)})")

    client = get_client()
    app = get_app()

    t1 = threading.Thread(target=client.run, args=(DISCORD_BOT_TOKEN,))
    t2 = threading.Thread(target=app.run, kwargs={"host":"0.0.0.0","port":80})

    t1.start()
    t2.start()

    # So as not to immediately exit the main thread
    t1.join()
    t2.join()
