import asyncio
import discord
from src.llm import improve_prompt, chat
from src.comfyui import generate_image
from src import config, state

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def _refresh_state():
    state.guilds = [{"id": g.id, "name": g.name} for g in client.guilds]
    state.channels = [
        {"id": ch.id, "name": ch.name, "guild_id": g.id, "guild": g.name}
        for g in client.guilds
        for ch in g.text_channels
    ]


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    _refresh_state()
    print(f"Connected to {len(state.guilds)} guild(s), {len(state.channels)} text channels")


@client.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name}")
    _refresh_state()


@client.event
async def on_guild_remove(guild):
    print(f"Removed from guild: {guild.name}")
    _refresh_state()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not message.guild:
        return

    guild_id = message.guild.id
    cfg = config.load(guild_id)
    content = message.content.strip()
    prefix = cfg["prefix"].lower()

    allowed = cfg.get("allowed_channels", [])
    if allowed and message.channel.id not in allowed:
        return

    if not content.lower().startswith(prefix):
        return

    lower = content.lower()

    if "image of" in lower:
        idx = lower.index("image of") + len("image of")
        prompt = content[idx:].strip()
        if not prompt:
            await message.reply("What should the image be of?")
            return
        msg = await message.reply("Improving your prompt...")
        try:
            improved = await asyncio.get_event_loop().run_in_executor(
                None, improve_prompt, prompt, guild_id
            )
            await msg.edit(content=f"Generating image for: *{improved}*")
            image_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_image, improved, guild_id
            )
            await message.channel.send(
                file=discord.File(fp=__import__("io").BytesIO(image_bytes), filename="image.png")
            )
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"Error: {e}")
    else:
        user_message = content[len(prefix):].strip()
        msg = await message.reply("Thinking...")
        try:
            reply = await asyncio.get_event_loop().run_in_executor(
                None, chat, user_message, guild_id
            )
            await msg.edit(content=reply)
        except Exception as e:
            await msg.edit(content=f"Error: {e}")
