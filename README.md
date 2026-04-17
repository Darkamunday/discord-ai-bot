# discord-ai-bot

A Discord bot that accepts `!image <prompt>`, refines the prompt via a local Gemma LLM (Ollama), sends it to a remote ComfyUI instance to generate an image, and returns the result to Discord.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) running locally with a Gemma model pulled
- ComfyUI running on a remote machine (RTX 5090), reachable via public IP

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env        # then fill in your values
python main.py
```

## Environment variables

See `.env.example` for all required variables.

## Planned features

- `!image` — generate an image via ComfyUI with LLM-enhanced prompt
- `!music` — generate music via ACE-Step (coming later)
