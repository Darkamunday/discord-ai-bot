import base64
import json
import os
import re

from flask import Blueprint, Response, render_template_string, request, stream_with_context

from src import config
from src.llm import improve_prompt, get_inpaint_params, chat, describe_image
from src.comfyui import (
    generate_image, generate_image_lora,
    generate_image_qwen_inpaint, generate_image_manual_inpaint,
    generate_image_upscale, generate_image_flux2_i2i,
)
from src.music import generate_music

bp = Blueprint("webapp", __name__)


def _guild_id() -> int:
    return int(os.getenv("WEBAPP_GUILD_ID", "0"))


def _event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lucy</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: sans-serif; background: #0f0f1a; color: #eee; height: 100dvh; display: flex; flex-direction: column; }

    #topbar { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: #15152a; border-bottom: 1px solid #2a2a40; }
    #topbar span { color: #a78bfa; font-weight: 600; font-size: 0.95rem; }
    #clear-btn { background: none; border: 1px solid #444; color: #888; padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
    #clear-btn:hover { color: #eee; border-color: #666; }

    #messages {
      flex: 1; overflow-y: auto; padding: 20px;
      display: flex; flex-direction: column; gap: 14px;
    }

    .msg { display: flex; flex-direction: column; max-width: 75%; }
    .msg.user { align-self: flex-end; align-items: flex-end; }
    .msg.lucy  { align-self: flex-start; align-items: flex-start; }

    .bubble {
      padding: 11px 15px; border-radius: 14px; line-height: 1.5;
      word-break: break-word; white-space: pre-wrap;
    }
    .user .bubble { background: #7c3aed; color: #fff; border-bottom-right-radius: 3px; }
    .lucy .bubble { background: #1e1e3a; border: 1px solid #2d2d50; border-bottom-left-radius: 3px; }
    .bubble img { max-width: 100%; max-height: 420px; object-fit: contain; border-radius: 8px; display: block; margin-top: 8px; cursor: pointer; }
    .bubble audio { display: block; margin-top: 8px; width: 100%; max-width: 480px; }
    .prompt-caption { font-size: 0.75rem; color: #666; margin-top: 5px; font-style: italic; }
    .status { color: #a78bfa; }
    .error   { color: #f87171; }

    #bar { padding: 12px 16px; background: #15152a; border-top: 1px solid #2a2a40; }
    #preview {
      display: none; align-items: center; gap: 8px;
      margin-bottom: 8px; padding: 6px 10px;
      background: #1e1e3a; border-radius: 8px;
    }
    #preview img { height: 40px; border-radius: 4px; object-fit: cover; }
    #preview span { font-size: 0.85rem; color: #aaa; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    #preview button { background: none; border: none; color: #888; cursor: pointer; font-size: 1.1rem; padding: 0 4px; }
    #preview button:hover { color: #eee; }
    #row { display: flex; gap: 8px; align-items: flex-end; }
    #attach-btn {
      flex-shrink: 0; width: 42px; height: 42px; background: #1e1e3a;
      border: 1px solid #2d2d50; border-radius: 8px;
      color: #aaa; font-size: 1.2rem; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }
    #attach-btn:hover { background: #2d2d50; }
    #text {
      flex: 1; padding: 10px 14px; background: #1e1e3a;
      border: 1px solid #2d2d50; border-radius: 8px;
      color: #eee; font-size: 0.95rem; resize: none;
      min-height: 42px; max-height: 140px; overflow-y: auto;
      line-height: 1.4;
    }
    #text:focus { outline: none; border-color: #7c3aed; }
    #send-btn {
      flex-shrink: 0; padding: 0 20px; height: 42px;
      background: #7c3aed; color: #fff;
      border: none; border-radius: 8px;
      font-size: 0.95rem; font-weight: 600; cursor: pointer;
    }
    #send-btn:hover:not(:disabled) { background: #6d28d9; }
    #send-btn:disabled { background: #3a3a5c; cursor: not-allowed; }
    #file-input { display: none; }

    #modes { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
    .mode-btn {
      padding: 4px 13px; border-radius: 6px; border: 1px solid #444;
      background: #1e1e3a; color: #aaa; cursor: pointer; font-size: 0.82rem;
      white-space: nowrap; transition: background 0.15s, color 0.15s;
    }
    .mode-btn:hover { background: #2d2d50; color: #eee; }
    .mode-btn.active { background: #7c3aed; border-color: #7c3aed; color: #fff; }

    .name { font-size: 0.75rem; color: #666; margin-bottom: 3px; padding: 0 4px; }

    /* Mask editor */
    #mask-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.85); z-index: 100;
      flex-direction: column; align-items: center; justify-content: center; gap: 12px;
    }
    #mask-overlay.open { display: flex; }
    #mask-box {
      background: #1a1a2e; border: 1px solid #333; border-radius: 12px;
      display: flex; flex-direction: column; max-width: 95vw; max-height: 95vh;
      overflow: hidden;
    }
    #mask-topbar {
      display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
      padding: 10px 14px; border-bottom: 1px solid #2a2a40; background: #15152a;
    }
    #mask-topbar span { color: #a78bfa; font-weight: 600; margin-right: auto; }
    #mask-topbar label { font-size: 0.85rem; color: #aaa; display: flex; align-items: center; gap: 6px; }
    #mask-topbar input[type=range] { width: 80px; }
    .mask-btn {
      padding: 5px 14px; border-radius: 6px; border: 1px solid #444;
      background: #2d2d44; color: #eee; cursor: pointer; font-size: 0.85rem;
    }
    .mask-btn:hover { background: #3a3a5c; }
    .mask-btn.active { background: #7c3aed; border-color: #7c3aed; }
    #mask-canvas-wrap {
      overflow: auto; flex: 1;
      display: flex; align-items: center; justify-content: center;
      background: #0f0f1a; min-height: 200px; padding: 12px;
    }
    #mask-img-container { position: relative; display: inline-block; line-height: 0; }
    #mask-bg { display: block; max-width: 85vw; max-height: 70vh; user-select: none; pointer-events: none; }
    #mask-canvas {
      position: absolute; inset: 0;
      cursor: crosshair; touch-action: none;
    }
    #mask-bottombar {
      display: flex; justify-content: flex-end; gap: 10px;
      padding: 10px 14px; border-top: 1px solid #2a2a40; background: #15152a;
    }
    #mask-gen-btn { padding: 8px 24px; background: #7c3aed; color: #fff; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; }
    #mask-gen-btn:hover { background: #6d28d9; }
    #mask-gen-btn:disabled { background: #444; cursor: not-allowed; }
  </style>
</head>
<body>
  <!-- Mask editor overlay -->
  <div id="mask-overlay">
    <div id="mask-box">
      <div id="mask-topbar">
        <span>Paint the area to edit</span>
        <label>Brush <input type="range" id="brush-size" min="4" max="120" value="24" oninput="updateBrush()"></label>
        <button class="mask-btn active" id="paint-btn" onclick="setMaskMode('paint')">Paint</button>
        <button class="mask-btn" id="erase-btn" onclick="setMaskMode('erase')">Erase</button>
        <button class="mask-btn" onclick="clearMask()">Clear</button>
      </div>
      <div id="mask-canvas-wrap">
        <div id="mask-img-container">
          <img id="mask-bg" alt="source image">
          <canvas id="mask-canvas"></canvas>
        </div>
      </div>
      <div id="mask-bottombar">
        <button class="mask-btn" onclick="closeMaskEditor()">Cancel</button>
        <button id="mask-gen-btn" onclick="submitMask()">Generate</button>
      </div>
    </div>
  </div>

  <div id="topbar">
    <span>Lucy</span>
    <button id="clear-btn" onclick="clearHistory()">New chat</button>
  </div>

  <div id="messages"></div>

  <div id="bar">
    <div id="preview">
      <img id="prev-img" src="" alt="">
      <span id="prev-name"></span>
      <button onclick="clearFile()" title="Remove">✕</button>
    </div>
    <div id="modes">
      <button class="mode-btn active" data-mode="chat"  onclick="selectMode('chat')">Chat</button>
      <button class="mode-btn"        data-mode="image" onclick="selectMode('image')">Image</button>
      <button class="mode-btn"        data-mode="music" onclick="selectMode('music')">Music</button>
    </div>
    <div id="row">
      <button id="attach-btn" onclick="document.getElementById('file-input').click()" title="Attach image">📎</button>
      <input type="file" id="file-input" accept="image/*" onchange="pickFile(this)">
      <textarea id="text" rows="1"
        oninput="autosize(this)" onkeydown="onKey(event)"></textarea>
      <button id="send-btn" onclick="send()">Send</button>
    </div>
  </div>

<script>
  // ── history ──────────────────────────────────────────────────────
  const LS_KEY = 'lucy_chat_history';
  const MAX_HIST_PAIRS = 20;
  let chatHistory = [];
  let selectedMode = 'chat';

  const TEXT_MODES = [
    {id:'chat', label:'Chat'}, {id:'image', label:'Image'}, {id:'music', label:'Music'}
  ];
  const IMAGE_MODES = [
    {id:'describe', label:'Describe'}, {id:'inpaint', label:'Inpaint'},
    {id:'paint-mask', label:'Paint Mask'}, {id:'upscale', label:'Upscale'},
    {id:'restyle', label:'Restyle'}
  ];
  const PLACEHOLDERS = {
    'chat':       'Ask Lucy anything…',
    'image':      'Describe the image to generate…',
    'music':      'Describe the music (style, mood, genre)…',
    'describe':   'Ask about the image (optional)…',
    'inpaint':    'Describe the edit to make…',
    'paint-mask': 'Describe what to do with the painted area…',
    'upscale':    '(No prompt needed, just send)',
    'restyle':    'Describe the new style…',
  };

  function renderModes(modes, defaultId) {
    const el = document.getElementById('modes');
    el.innerHTML = '';
    for (const m of modes) {
      const btn = document.createElement('button');
      btn.className = 'mode-btn' + (m.id === defaultId ? ' active' : '');
      btn.dataset.mode = m.id;
      btn.textContent = m.label;
      btn.onclick = () => selectMode(m.id);
      el.appendChild(btn);
    }
  }

  function selectMode(id) {
    selectedMode = id;
    document.querySelectorAll('#modes .mode-btn').forEach(b =>
      b.classList.toggle('active', b.dataset.mode === id)
    );
    document.getElementById('text').placeholder = PLACEHOLDERS[id] || '';
  }

  function loadHistory() {
    try {
      const saved = localStorage.getItem(LS_KEY);
      if (!saved) return;
      chatHistory = JSON.parse(saved);
      for (const msg of chatHistory) {
        const isImg = msg.content.startsWith('[Generated image:');
        const html = isImg
          ? `<em style="color:#a78bfa">${escape(msg.content)}</em>`
          : escape(msg.content).replace(/\\n/g, '<br>');
        addBubble(msg.role === 'user' ? 'user' : 'lucy', html);
      }
    } catch(e) { chatHistory = []; }
  }

  function saveHistory() {
    if (chatHistory.length > MAX_HIST_PAIRS * 2)
      chatHistory = chatHistory.slice(-MAX_HIST_PAIRS * 2);
    try { localStorage.setItem(LS_KEY, JSON.stringify(chatHistory)); } catch(e) {}
  }

  function clearHistory() {
    chatHistory = [];
    localStorage.removeItem(LS_KEY);
    document.getElementById('messages').innerHTML = '';
  }

  // ── file attachment ──────────────────────────────────────────────
  let file = null;

  function autosize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 140) + 'px';
  }
  function pickFile(input) {
    file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      document.getElementById('prev-img').src = e.target.result;
      document.getElementById('prev-name').textContent = file.name;
      document.getElementById('preview').style.display = 'flex';
    };
    reader.readAsDataURL(file);
    renderModes(IMAGE_MODES, 'describe');
    selectMode('describe');
  }
  function clearFile() {
    file = null;
    document.getElementById('file-input').value = '';
    document.getElementById('preview').style.display = 'none';
    renderModes(TEXT_MODES, 'chat');
    selectMode('chat');
  }
  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }

  // ── chat UI helpers ──────────────────────────────────────────────
  function escape(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function scrollBottom() { const m = document.getElementById('messages'); m.scrollTop = m.scrollHeight; }
  function openFull(src) {
    const w = window.open('', '_blank');
    w.document.write(`<!doctype html><html><body style="margin:0;background:#000;display:flex;align-items:center;justify-content:center;min-height:100vh"><img src="${src}" style="max-width:100%;max-height:100vh;object-fit:contain"></body></html>`);
    w.document.close();
  }
  function addBubble(role, html) {
    const msgs = document.getElementById('messages');
    const wrap = document.createElement('div'); wrap.className = 'msg ' + role;
    const name = document.createElement('div'); name.className = 'name';
    name.textContent = role === 'user' ? 'You' : 'Lucy';
    const bubble = document.createElement('div'); bubble.className = 'bubble';
    bubble.innerHTML = html;
    wrap.appendChild(name); wrap.appendChild(bubble);
    msgs.appendChild(wrap); scrollBottom();
    return bubble;
  }
  async function streamInto(bubble, fetchPromise) {
    let result = { text: null, image: null, prompt: null };
    try {
      const resp = await fetchPromise;
      const reader = resp.body.getReader();
      const dec = new TextDecoder();
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split('\\n'); buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const ev = JSON.parse(line.slice(6));
          if (ev.done) break;
          if (ev.status) {
            bubble.innerHTML = `<span class="status">${escape(ev.status)}</span>`;
          } else if (ev.image) {
            result.image = ev.image; result.prompt = ev.prompt || null;
            let html = `<img src="data:image/png;base64,${ev.image}" alt="Generated"
              onclick="openFull(this.src)" title="Click to open full size">`;
            if (ev.prompt) html += `<div class="prompt-caption">${escape(ev.prompt)}</div>`;
            bubble.innerHTML = html;
          } else if (ev.text) {
            result.text = ev.text;
            bubble.innerHTML = escape(ev.text).replace(/\\n/g,'<br>');
          } else if (ev.audio) {
            let html = `<audio controls src="data:audio/wav;base64,${ev.audio}"></audio>`;
            if (ev.prompt) html += `<div class="prompt-caption">${escape(ev.prompt)}</div>`;
            bubble.innerHTML = html;
          } else if (ev.error) {
            bubble.innerHTML = `<span class="error">Error: ${escape(ev.error)}</span>`;
          }
          scrollBottom();
        }
      }
    } catch (e) {
      bubble.innerHTML = `<span class="error">Connection error: ${escape(e.message)}</span>`;
    }
    return result;
  }

  // ── send ─────────────────────────────────────────────────────────
  async function send() {
    const textEl = document.getElementById('text');
    const text = textEl.value.trim();
    if (!text && !file && selectedMode !== 'upscale') return;

    if (selectedMode === 'paint-mask') {
      if (!file) return;
      showMaskEditor(file, text);
      textEl.value = ''; autosize(textEl); clearFile();
      return;
    }

    document.getElementById('send-btn').disabled = true;
    let userHtml = text ? escape(text).replace(/\\n/g,'<br>') : '';
    if (file) userHtml += (userHtml ? '<br>' : '') +
      `<span style="font-size:0.8rem;color:#c4b5fd">📎 ${escape(file.name)}</span>`;
    addBubble('user', userHtml);
    textEl.value = ''; autosize(textEl);
    const lucyBubble = addBubble('lucy', '<span class="status">...</span>');
    const fd = new FormData();
    fd.append('text', text);
    fd.append('mode', selectedMode);
    fd.append('history', JSON.stringify(chatHistory));
    if (file) fd.append('image', file);
    clearFile();
    if (text) chatHistory.push({role: 'user', content: text});
    const result = await streamInto(lucyBubble, fetch('/app/send', {method:'POST', body:fd}));
    if (result.text) {
      chatHistory.push({role: 'assistant', content: result.text});
      saveHistory();
    } else if (result.image) {
      chatHistory.push({role: 'assistant', content: `[Generated image: ${result.prompt || ''}]`});
      saveHistory();
    }
    document.getElementById('send-btn').disabled = false;
    textEl.focus();
  }

  // ── mask editor ──────────────────────────────────────────────────
  let maskFile = null, maskText = '';
  let maskMode = 'paint', maskDrawing = false;
  let maskOrigW = 0, maskOrigH = 0;
  let maskLastX = 0, maskLastY = 0;

  function showMaskEditor(imgFile, text) {
    maskFile = imgFile; maskText = text;
    // show overlay FIRST so the image renders and offsetWidth/Height are valid
    document.getElementById('mask-overlay').classList.add('open');
    setMaskMode('paint');
    const img = document.getElementById('mask-bg');
    const canvas = document.getElementById('mask-canvas');
    const reader = new FileReader();
    reader.onload = e => {
      img.onload = () => {
        maskOrigW = img.naturalWidth;
        maskOrigH = img.naturalHeight;
        // wait one frame so layout is complete before reading rendered size
        requestAnimationFrame(() => {
          canvas.width  = img.offsetWidth;
          canvas.height = img.offsetHeight;
          clearMask();
        });
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(imgFile);
  }

  function closeMaskEditor() {
    document.getElementById('mask-overlay').classList.remove('open');
    maskFile = null; maskText = '';
  }

  function setMaskMode(m) {
    maskMode = m;
    document.getElementById('paint-btn').classList.toggle('active', m === 'paint');
    document.getElementById('erase-btn').classList.toggle('active', m === 'erase');
  }

  function updateBrush() {} // slider oninput hook (brush size read live)

  function clearMask() {
    const c = document.getElementById('mask-canvas');
    c.getContext('2d').clearRect(0, 0, c.width, c.height);
  }

  function getMaskPos(e) {
    const c = document.getElementById('mask-canvas');
    const rect = c.getBoundingClientRect();
    const src = e.touches ? e.touches[0] : e;
    return {
      x: (src.clientX - rect.left) * (c.width  / rect.width),
      y: (src.clientY - rect.top)  * (c.height / rect.height),
    };
  }

  function maskPaint(x, y, fromX, fromY) {
    const c = document.getElementById('mask-canvas');
    const ctx = c.getContext('2d');
    const r = parseInt(document.getElementById('brush-size').value) / 2;
    ctx.globalCompositeOperation = maskMode === 'erase' ? 'destination-out' : 'source-over';
    ctx.strokeStyle = 'rgba(220,60,60,0.55)';
    ctx.lineWidth = r * 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(fromX ?? x, fromY ?? y);
    ctx.lineTo(x, y);
    ctx.stroke();
    // fill dot at start
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(220,60,60,0.55)';
    ctx.fill();
  }

  (function bindMaskCanvas() {
    const c = document.getElementById('mask-canvas');
    c.addEventListener('mousedown', e => {
      maskDrawing = true;
      const p = getMaskPos(e); maskLastX = p.x; maskLastY = p.y;
      maskPaint(p.x, p.y);
    });
    c.addEventListener('mousemove', e => {
      if (!maskDrawing) return;
      const p = getMaskPos(e);
      maskPaint(p.x, p.y, maskLastX, maskLastY);
      maskLastX = p.x; maskLastY = p.y;
    });
    c.addEventListener('mouseup',    () => maskDrawing = false);
    c.addEventListener('mouseleave', () => maskDrawing = false);
    c.addEventListener('touchstart', e => {
      e.preventDefault(); maskDrawing = true;
      const p = getMaskPos(e); maskLastX = p.x; maskLastY = p.y;
      maskPaint(p.x, p.y);
    }, { passive: false });
    c.addEventListener('touchmove', e => {
      e.preventDefault(); if (!maskDrawing) return;
      const p = getMaskPos(e);
      maskPaint(p.x, p.y, maskLastX, maskLastY);
      maskLastX = p.x; maskLastY = p.y;
    }, { passive: false });
    c.addEventListener('touchend', () => maskDrawing = false);
  })();

  loadHistory();
  selectMode('chat');

  async function submitMask() {
    console.log('[mask] submitMask fired, maskOrigW=', maskOrigW, 'maskOrigH=', maskOrigH,
                'maskFile=', maskFile && maskFile.name, 'maskText=', maskText);
    const genBtn = document.getElementById('mask-gen-btn');
    if (maskOrigW === 0 || maskOrigH === 0) {
      console.warn('[mask] dims are 0, aborting');
      alert('Image not ready yet — please wait a moment and try again.');
      return;
    }
    genBtn.disabled = true;
    try {
      console.log('[mask] building offscreen canvas');
      const paintCanvas = document.getElementById('mask-canvas');
      console.log('[mask] paintCanvas size:', paintCanvas.width, 'x', paintCanvas.height);
      const offscreen = document.createElement('canvas');
      offscreen.width = maskOrigW; offscreen.height = maskOrigH;
      const offCtx = offscreen.getContext('2d');
      offCtx.drawImage(paintCanvas, 0, 0, maskOrigW, maskOrigH);
      const imgData = offCtx.getImageData(0, 0, maskOrigW, maskOrigH);
      const bw = new Uint8ClampedArray(imgData.data.length);
      for (let i = 0; i < imgData.data.length; i += 4) {
        const v = imgData.data[i + 3] > 10 ? 255 : 0;
        bw[i] = v; bw[i+1] = v; bw[i+2] = v; bw[i+3] = 255;
      }
      offCtx.putImageData(new ImageData(bw, maskOrigW, maskOrigH), 0, 0);

      console.log('[mask] calling toBlob');
      const blob = await new Promise(res => offscreen.toBlob(res, 'image/png'));
      console.log('[mask] blob result:', blob);
      if (!blob) throw new Error('Canvas produced no image data');

      console.log('[mask] closing editor');
      const savedFile = maskFile, savedText = maskText;
      closeMaskEditor();

      let userHtml = savedText ? escape(savedText).replace(/\\n/g,'<br>') : '';
      userHtml += (userHtml ? '<br>' : '') +
        `<span style="font-size:0.8rem;color:#c4b5fd">📎 ${escape(savedFile.name)} + mask</span>`;
      addBubble('user', userHtml);
      const lucyBubble = addBubble('lucy', '<span class="status">Sending to ComfyUI…</span>');

      console.log('[mask] posting to /app/inpaint');
      const fd = new FormData();
      fd.append('text', savedText);
      fd.append('image', savedFile);
      fd.append('mask', blob, 'mask.png');
      await streamInto(lucyBubble, fetch('/app/inpaint', { method: 'POST', body: fd }));
      console.log('[mask] done');
    } catch(err) {
      console.error('[mask] caught error:', err);
      alert('Mask editor error: ' + err.message);
    }
    genBtn.disabled = false;
  }
</script>
</body>
</html>"""


@bp.route("/app")
def index():
    return render_template_string(TEMPLATE)


@bp.route("/app/send", methods=["POST"])
def send():
    text = request.form.get("text", "").strip()
    img_file = request.files.get("image")
    guild_id = _guild_id()
    lower = text.lower()
    mode = request.form.get("mode", "").strip().lower()

    try:
        history = json.loads(request.form.get("history", "[]"))
    except Exception:
        history = []

    image_bytes = img_file.read() if img_file else None
    filename = img_file.filename if img_file else "upload.png"

    @stream_with_context
    def generate():
        try:
            nsfw = "nsfw" in lower
            cfg = config.load(guild_id)

            if mode == "upscale" and image_bytes:
                yield _event({"status": "Upscaling…"})
                result = generate_image_upscale(image_bytes, filename, guild_id)
                yield _event({"image": base64.b64encode(result).decode()})

            elif mode == "restyle" and image_bytes:
                yield _event({"status": "Improving prompt…"})
                improved = improve_prompt(text, guild_id, nsfw)
                yield _event({"status": f"Restyling: {improved[:80]}…"})
                result = generate_image_flux2_i2i(improved, image_bytes, filename, guild_id)
                yield _event({"image": base64.b64encode(result).decode(), "prompt": improved})

            elif mode == "inpaint" and image_bytes:
                yield _event({"status": "Analysing image…"})
                params = get_inpaint_params(text, guild_id, nsfw)
                subject = params.get("mask_subject", "subject")
                improved = params.get("prompt", text)
                yield _event({"status": f"Inpainting {subject}…"})
                result = generate_image_qwen_inpaint(improved, subject, image_bytes, filename, guild_id)
                yield _event({"image": base64.b64encode(result).decode(), "prompt": improved})

            elif mode == "describe" and image_bytes:
                yield _event({"status": "Analysing image…"})
                description = describe_image(image_bytes, text, guild_id)
                yield _event({"text": description})

            elif mode == "image":
                matched_lora = next(
                    (l for l in cfg.get("loras", []) if l.get("trigger", "").lower() in lower),
                    None
                )
                yield _event({"status": "Improving prompt…"})
                if matched_lora:
                    trigger = matched_lora.get("trigger", "")
                    clean = re.sub(rf'\b{re.escape(trigger)}\b', '', text, flags=re.IGNORECASE).strip()
                    improved = improve_prompt(clean, guild_id, nsfw)
                    prepend = matched_lora.get("prepend", "").strip()
                    if prepend:
                        improved = f"{prepend}, {improved}"
                else:
                    improved = improve_prompt(text, guild_id, nsfw)
                yield _event({"status": f"Generating: {improved[:80]}…"})
                if matched_lora:
                    result = generate_image_lora(
                        improved, matched_lora.get("lora", ""), matched_lora.get("strength", 1.0), guild_id
                    )
                else:
                    result = generate_image(improved, guild_id)
                yield _event({"image": base64.b64encode(result).decode(), "prompt": improved})

            elif mode == "music":
                yield _event({"status": f"Composing: {text[:80]}…"})
                audio_bytes = generate_music(text, guild_id)
                yield _event({"audio": base64.b64encode(audio_bytes).decode(), "prompt": text})

            else:
                yield _event({"status": "Thinking…"})
                reply = chat(text, guild_id, history)
                yield _event({"text": reply})

        except Exception as e:
            yield _event({"error": str(e)[:500]})

        yield _event({"done": True})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp.route("/app/inpaint", methods=["POST"])
def inpaint():
    text = request.form.get("text", "").strip()
    img_file = request.files.get("image")
    mask_file = request.files.get("mask")
    guild_id = _guild_id()

    if not img_file or not mask_file:
        return Response(_event({"error": "Missing image or mask"}), mimetype="text/event-stream")

    image_bytes = img_file.read()
    mask_bytes = mask_file.read()
    filename = img_file.filename or "upload.png"

    @stream_with_context
    def generate():
        try:
            yield _event({"status": "Uploading to ComfyUI…"})
            result = generate_image_manual_inpaint(text, image_bytes, mask_bytes, filename, guild_id)
            yield _event({"image": base64.b64encode(result).decode(), "prompt": text})
        except Exception as e:
            yield _event({"error": str(e)[:500]})
        yield _event({"done": True})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
