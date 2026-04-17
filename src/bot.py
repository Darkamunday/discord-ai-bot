import asyncio
import discord
from src.llm import improve_prompt, chat
from src.comfyui import generate_image

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()
    lower = content.lower()

    if not lower.startswith("lucy"):
        return

    if "image of" in lower:
        idx = lower.index("image of") + len("image of")
        prompt = content[idx:].strip()
        if not prompt:
            await message.reply("What should the image be of?")
            return
        msg = await message.reply("Improving your prompt...")
        try:
            improved = await asyncio.get_event_loop().run_in_executor(
                None, improve_prompt, prompt
            )
            await msg.edit(content=f"Generating image for: *{improved}*")
            image_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_image, improved
            )
            await message.channel.send(
                file=discord.File(fp=__import__("io").BytesIO(image_bytes), filename="image.png")
            )
            await msg.delete()
        except Exception as e:
            await msg.edit(content=f"Error: {e}")
    else:
        user_message = content[4:].strip()
        msg = await message.reply("Thinking...")
        try:
            reply = await asyncio.get_event_loop().run_in_executor(
                None, chat, user_message
            )
            await msg.edit(content=reply)
        except Exception as e:
            await msg.edit(content=f"Error: {e}")
