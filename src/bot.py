import asyncio
import discord
from discord.ext import commands
from src.llm import improve_prompt

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.command(name="image")
async def image(ctx, *, prompt: str):
    msg = await ctx.reply("Improving your prompt...")
    try:
        improved = await asyncio.get_event_loop().run_in_executor(
            None, improve_prompt, prompt
        )
        await msg.edit(content=f"**Improved prompt:**\n{improved}")
    except Exception as e:
        await msg.edit(content=f"Error improving prompt: {e}")
