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

### Completed — Natural language interface + chat
- Replaced `!image` command with `on_message` listener triggered by messages starting with `lucy`
- `"lucy ... image of ..."` → image generation pipeline
- `"lucy ..."` (anything else) → general chat via Ollama, Lucy persona
- `llm.py` refactored: shared `_ollama_chat()` helper, `improve_prompt()` and `chat()` as public functions

### Completed — Step 4
- `workflows/txt2img.json` copied into project (JuggernautXL, 1024×1536, 20 steps)
- `src/comfyui.py`: injects improved prompt into node 2, randomises seed, POSTs to `/prompt`, polls `/history/{id}`, fetches image from `/view`
- `src/bot.py`: full pipeline — improve prompt → generate image → send as Discord file attachment
- ComfyUI running at `194.93.48.43:8188` (set in `.env`, gitignored)
- Fixed Windows encoding issue on workflow JSON (utf-8 explicit open)
- Full pipeline tested and working end to end

## Next — Step 5
Add auth to the ComfyUI connection before going live. Options: API key header, HTTP basic auth, or VPN/tunnel. To be decided based on what ComfyUI supports on the remote machine.
