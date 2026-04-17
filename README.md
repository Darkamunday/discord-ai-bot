# discord-ai-bot

A Discord bot (Lucy) that generates and edits images using a local Ollama LLM for prompt refinement and a remote ComfyUI instance for image generation. Supports text-to-image and automatic image editing with no manual masking required.

## Features

- `lucy image of <prompt>` — generate an image via ComfyUI (JuggernautXL) with LLM-enhanced prompt
- `lucy <edit request>` + attach image — automatically segments the target region (GroundingDINO + SAM) and inpaints using Qwen Image Edit
- `lucy <anything>` — general chat via Ollama (Lucy persona)
- Per-guild configuration (prefix, model, allowed channels, image settings) via a localhost admin web UI
- Typing indicator shown while generating so users know it's working

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) running locally with your chosen model pulled
- ComfyUI on a remote machine with:
  - JuggernautXL checkpoint
  - Qwen Image Edit model + Lightning LoRA + Qwen 2.5 VL CLIP + Qwen VAE
  - [comfyui_segment_anything](https://github.com/storyicon/comfyui_segment_anything) custom node
  - GroundingDINO SwinT model + SAM ViT-H model

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

## Admin UI

A Flask admin panel runs at `http://localhost:5000` — configure per-guild settings including prefix, Ollama model, system prompt, image dimensions, steps, CFG, and allowed channels.

## Planned

- `lucy give me music of <prompt>` — music generation via ACE-Step
- ComfyUI auth (currently open IP, fine for dev)
- Discord OAuth for admin UI
