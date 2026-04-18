import asyncio
import discord
from src.llm import improve_prompt, get_inpaint_params, chat
from src.comfyui import generate_image, generate_image_qwen_inpaint, generate_image_upscale
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

    image_attachments = [
        a for a in message.attachments
        if (a.content_type and a.content_type.startswith("image/"))
        or a.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    ]

    if "upscale" in lower and image_attachments:
        attachment = image_attachments[0]
        msg = await message.reply("Upscaling...")
        try:
            attachment_bytes = await attachment.read()
            async with message.channel.typing():
                image_bytes = await asyncio.get_event_loop().run_in_executor(
                    None, generate_image_upscale, attachment_bytes, attachment.filename, guild_id
                )
            await message.channel.send(
                file=discord.File(fp=__import__("io").BytesIO(image_bytes), filename="upscaled.png")
            )
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"Error: {e}")

    elif "image of" in lower or image_attachments:
        if image_attachments:
            prompt_text = content[len(prefix):].strip()
            if not prompt_text:
                await message.reply("Describe what to do with the image.")
                return
        else:
            idx = lower.index("image of") + len("image of")
            prompt_text = content[idx:].strip()
            if not prompt_text:
                await message.reply("What should the image be of?")
                return

        msg = await message.reply("Improving your prompt...")
        try:
            if image_attachments:
                attachment = image_attachments[0]
                attachment_bytes = await attachment.read()
                await msg.edit(content="Analysing your image...")
                params = await asyncio.get_event_loop().run_in_executor(
                    None, get_inpaint_params, prompt_text, guild_id
                )
                mask_subject = params.get("mask_subject", "subject")
                improved = params.get("prompt", prompt_text)
                await msg.edit(content=f"Inpainting *{mask_subject}*: *{improved}*")
                async with message.channel.typing():
                    image_bytes = await asyncio.get_event_loop().run_in_executor(
                        None, generate_image_qwen_inpaint, improved, mask_subject, attachment_bytes, attachment.filename, guild_id
                    )
            else:
                nsfw = "nsfw" in lower
                improved = await asyncio.get_event_loop().run_in_executor(
                    None, improve_prompt, prompt_text, guild_id, nsfw
                )
                await msg.edit(content=f"Generating image for: *{improved}*")
                async with message.channel.typing():
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
