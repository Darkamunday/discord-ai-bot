import os
import requests
from src import config

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

IMAGE_SYSTEM_PROMPT = (
    "You are an expert image prompt engineer. "
    "Take the user's prompt and rewrite it as a single, detailed, vivid image generation prompt. "
    "Return only the improved prompt — no explanation, no preamble, no quotes."
)


def _ollama_chat(system: str, user: str, guild_id: int) -> str:
    cfg = config.load(guild_id)
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": cfg["ollama_model"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def improve_prompt(prompt: str, guild_id: int) -> str:
    return _ollama_chat(IMAGE_SYSTEM_PROMPT, prompt, guild_id)


def chat(message: str, guild_id: int) -> str:
    cfg = config.load(guild_id)
    return _ollama_chat(cfg["chat_system_prompt"], message, guild_id)
