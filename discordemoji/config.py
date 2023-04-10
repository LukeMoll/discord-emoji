import os

if "DISCORD_BOT_TOKEN" not in os.environ or len(os.environ["DISCORD_BOT_TOKEN"]) == 0:
    raise RuntimeError("Environment variable DISCORD_BOT_TOKEN not set")
else:
    DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
