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

## Next — Step 3
Wire up `src/llm.py`: send the `!image` prompt to Ollama (`/api/generate`) to get an improved prompt back. `bot.py` calls `llm.py` and prints the improved prompt (still no ComfyUI yet). Goal: confirm Ollama round-trip works end to end.
