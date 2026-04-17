import json
import os
import requests
from src import config

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

IMAGE_SYSTEM_PROMPT = (
    "You are an expert image prompt engineer. "
    "Take the user's prompt and rewrite it as a single, detailed, vivid image generation prompt. "
    "Return only the improved prompt — no explanation, no preamble, no quotes."
)

IMG2IMG_SYSTEM_PROMPT = (
    "You are an expert image prompt engineer specialising in image-to-image editing. "
    "The user wants to make a specific edit to an existing image. "
    "Rewrite their request as a concise prompt describing the image after the edit. "
    "ONLY mention what the user explicitly asked to change. "
    "NEVER add skin tone, freckles, eye colour, facial features, or any detail not in the user's request. "
    "Keep the same style, character, and composition — only change what was asked. "
    "Return only the prompt — no explanation, no preamble, no quotes."
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


def improve_img2img_prompt(prompt: str, guild_id: int) -> str:
    return _ollama_chat(IMG2IMG_SYSTEM_PROMPT, prompt, guild_id)


INPAINT_SYSTEM_PROMPT = (
    "You are an image editing assistant. The user wants to edit a specific part of an image. "
    "Respond with a JSON object with exactly two keys:\n"
    "- \"mask_subject\": a short noun (1-3 words) describing the region to edit, e.g. \"hair\", \"shirt\", \"background\". "
    "If editing hair, always use \"hair\".\n"
    "- \"prompt\": a clear, direct edit instruction in plain English, e.g. \"Change the hair to red\", \"Make the jacket blue\". "
    "Keep it concise — one sentence.\n"
    "Return only valid JSON — no explanation, no markdown, no code fences."
)


def get_inpaint_params(user_request: str, guild_id: int) -> dict:
    raw = _ollama_chat(INPAINT_SYSTEM_PROMPT, user_request, guild_id)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])


def chat(message: str, guild_id: int) -> str:
    cfg = config.load(guild_id)
    return _ollama_chat(cfg["chat_system_prompt"], message, guild_id)
