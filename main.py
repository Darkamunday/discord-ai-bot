import os
from dotenv import load_dotenv

load_dotenv()

from src.bot import bot

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN not set in .env")

bot.run(token)
