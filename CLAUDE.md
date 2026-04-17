# CLAUDE.md

## Project goal
Discord bot that accepts `!image <prompt>`, sends it to a local Gemma LLM via Ollama to improve the prompt, then calls a remote ComfyUI API to generate an image and returns it to Discord. Later: `!music` command via ACE-Step.

## Infrastructure
- Bot + Gemma (Ollama): local Windows machine
- ComfyUI: offsite machine with RTX 5090, reachable via public IP — auth not yet implemented, required before going live

## Folder structure
```
discord-ai-bot/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
└── src/
    ├── __init__.py
    ├── bot.py
    ├── llm.py
    └── comfyui.py
```

## Working style
- Small, controlled steps only
- Explain what you're about to do before doing it
- Ask for confirmation before major changes
- No Docker, no database, no unnecessary frameworks
- Python only
- No comments unless the WHY is non-obvious
- Update CLAUDE.md at the end of each step to reflect current progress

## Progress
### Completed — Step 1
- Folder skeleton created
- Python venv at `.venv/`, dependencies installed (`discord.py`, `requests`, `python-dotenv`)
- `.gitignore`, `.env.example`, `README.md`, `requirements.txt` written
- Git initialised, first commit `49f5702` (`chore: initial project skeleton`)

### Completed — Step 2
- `src/bot.py`: Discord client with `!image` command (static reply), `on_ready` log
- `main.py`: loads `.env`, validates `DISCORD_TOKEN`, starts bot
- Bot tested successfully — comes online and responds to `!image` in Discord

### Completed — Step 3
- `src/llm.py`: `improve_prompt()` calls Ollama `/api/chat` (cloud model requires chat endpoint, not `/api/generate`)
- `bot.py`: calls `improve_prompt()` in executor, shows "Improving..." then edits to improved prompt
- `main.py`: `load_dotenv()` moved before imports so env vars are available at module load time
- Tested successfully end to end with `gpt-oss:120b-cloud`

## Next — Step 4
Wire up `src/comfyui.py`: take the improved prompt from Step 3 and send it to the remote ComfyUI API to generate an image. Return the image file to Discord. Goal: confirm the full pipeline works — Discord → LLM → ComfyUI → image back in Discord.
