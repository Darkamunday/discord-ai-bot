import os
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")

SYSTEM_PROMPT_IMAGE = (
    "You are an expert image prompt engineer. "
    "Take the user's prompt and rewrite it as a single, detailed, vivid image generation prompt. "
    "Return only the improved prompt — no explanation, no preamble, no quotes."
)

SYSTEM_PROMPT_CHAT = (
    "You are Lucy, a friendly and helpful AI assistant in a Discord server. "
    "Keep responses concise and conversational."
)


def _ollama_chat(system: str, user: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
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


def improve_prompt(prompt: str) -> str:
    return _ollama_chat(SYSTEM_PROMPT_IMAGE, prompt)


def chat(message: str) -> str:
    return _ollama_chat(SYSTEM_PROMPT_CHAT, message)
