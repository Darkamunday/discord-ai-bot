from flask import Flask, render_template_string, request, redirect, url_for
from src import config, state

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lucy Admin</title>
  <style>
    body { font-family: sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; background: #1a1a2e; color: #eee; }
    h1 { color: #a78bfa; }
    h2 { color: #c4b5fd; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 2rem; }
    label { display: block; margin: 12px 0 4px; font-size: 0.9rem; color: #aaa; }
    input[type=text], input[type=number], textarea, select {
      width: 100%; box-sizing: border-box; padding: 8px; border-radius: 6px;
      border: 1px solid #444; background: #2d2d44; color: #eee; font-size: 0.95rem;
    }
    textarea { height: 80px; resize: vertical; }
    .row { display: flex; gap: 16px; }
    .row > div { flex: 1; }
    .ch-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
    .ch-row input[type=checkbox] { width: 16px; height: 16px; margin: 0; flex-shrink: 0; }
    .ch-row label { display: inline; color: #eee; margin: 0; font-size: 0.95rem; }
    button { margin-top: 24px; padding: 10px 28px; background: #7c3aed; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; }
    button:hover { background: #6d28d9; }
    .flash { background: #166534; color: #bbf7d0; padding: 10px 16px; border-radius: 6px; margin-bottom: 16px; }
    .muted { color: #888; font-size: 0.9rem; }
    .guild-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
    .guild-bar select { width: auto; flex: 1; }
    .guild-bar button { margin-top: 0; padding: 8px 18px; }
  </style>
</head>
<body>
  <h1>Lucy Admin</h1>

  <form method="get" class="guild-bar">
    <label style="margin:0;white-space:nowrap">Server:</label>
    {% if guilds %}
      <select name="guild" onchange="this.form.submit()">
        {% for g in guilds %}
          <option value="{{ g.id }}" {% if g.id == selected_guild_id %}selected{% endif %}>{{ g.name }}</option>
        {% endfor %}
      </select>
    {% else %}
      <span class="muted">Bot not connected yet — guilds will appear once it's online.</span>
    {% endif %}
  </form>

  {% if selected_guild_id %}
    {% if saved %}<div class="flash">Settings saved for {{ selected_guild_name }}.</div>{% endif %}
    <form method="post">
      <input type="hidden" name="guild_id" value="{{ selected_guild_id }}">

      <h2>Bot</h2>
      <label>Trigger prefix</label>
      <input type="text" name="prefix" value="{{ cfg.prefix }}">

      <h2>Language Model</h2>
      <label>Ollama model</label>
      <input type="text" name="ollama_model" value="{{ cfg.ollama_model }}">
      <label>Chat system prompt</label>
      <textarea name="chat_system_prompt">{{ cfg.chat_system_prompt }}</textarea>

      <h2>Image Generation</h2>
      <div class="row">
        <div><label>Width</label><input type="number" name="image_width" value="{{ cfg.image_width }}"></div>
        <div><label>Height</label><input type="number" name="image_height" value="{{ cfg.image_height }}"></div>
      </div>
      <div class="row">
        <div><label>Steps</label><input type="number" name="image_steps" value="{{ cfg.image_steps }}"></div>
        <div><label>CFG</label><input type="number" step="0.1" name="image_cfg" value="{{ cfg.image_cfg }}"></div>
      </div>

      <h2>Image Editing (Inpaint)</h2>
      <div class="row">
        <div>
          <label>Detection threshold</label>
          <input type="number" step="0.01" min="0.01" max="1" name="inpaint_threshold" value="{{ cfg.inpaint_threshold }}">
          <span class="muted">Lower = catch more strands (0.05 recommended)</span>
        </div>
        <div>
          <label>Mask expand (px)</label>
          <input type="number" name="inpaint_expand" value="{{ cfg.inpaint_expand }}">
          <span class="muted">Grows mask outward to catch edges</span>
        </div>
        <div>
          <label>Mask blur radius</label>
          <input type="number" name="inpaint_blur_radius" value="{{ cfg.inpaint_blur_radius }}">
          <span class="muted">Feathers mask edges</span>
        </div>
      </div>

      <h2>Allowed Channels</h2>
      <p class="muted" style="margin:4px 0 10px">None selected = respond in all channels.</p>
      {% if guild_channels %}
        {% for ch in guild_channels %}
          <div class="ch-row">
            <input type="checkbox" name="allowed_channels" value="{{ ch.id }}" id="ch_{{ ch.id }}"
              {% if ch.id in cfg.allowed_channels %}checked{% endif %}>
            <label for="ch_{{ ch.id }}">#{{ ch.name }}</label>
          </div>
        {% endfor %}
      {% else %}
        <p class="muted">No channels found for this server.</p>
      {% endif %}

      <button type="submit">Save</button>
    </form>
  {% elif guilds %}
    <p class="muted">Select a server above to configure it.</p>
  {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    guilds = state.guilds
    saved = False
    selected_guild_id = None
    selected_guild_name = ""
    cfg = {}
    guild_channels = []

    if request.method == "POST":
        guild_id = int(request.form["guild_id"])
        cfg = config.load(guild_id)
        cfg["prefix"] = request.form["prefix"].strip()
        cfg["ollama_model"] = request.form["ollama_model"].strip()
        cfg["chat_system_prompt"] = request.form["chat_system_prompt"].strip()
        cfg["image_width"] = int(request.form["image_width"])
        cfg["image_height"] = int(request.form["image_height"])
        cfg["image_steps"] = int(request.form["image_steps"])
        cfg["image_cfg"] = float(request.form["image_cfg"])
        cfg["inpaint_threshold"] = float(request.form["inpaint_threshold"])
        cfg["inpaint_expand"] = int(request.form["inpaint_expand"])
        cfg["inpaint_blur_radius"] = int(request.form["inpaint_blur_radius"])
        cfg["allowed_channels"] = [int(v) for v in request.form.getlist("allowed_channels")]
        config.save(guild_id, cfg)
        saved = True
        selected_guild_id = guild_id
    elif request.args.get("guild"):
        selected_guild_id = int(request.args["guild"])
    elif guilds:
        selected_guild_id = guilds[0]["id"]

    if selected_guild_id:
        cfg = config.load(selected_guild_id)
        guild_channels = [ch for ch in state.channels if ch["guild_id"] == selected_guild_id]
        match = next((g for g in guilds if g["id"] == selected_guild_id), None)
        selected_guild_name = match["name"] if match else ""

    return render_template_string(
        TEMPLATE,
        guilds=guilds,
        selected_guild_id=selected_guild_id,
        selected_guild_name=selected_guild_name,
        cfg=cfg,
        guild_channels=guild_channels,
        saved=saved,
    )


def run():
    app.run(host="127.0.0.1", port=5000, use_reloader=False)
