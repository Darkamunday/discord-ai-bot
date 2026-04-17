import copy
import json
import os
import random
import time
import requests
from src import config

COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "http://localhost:8188")

_WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "..", "workflows")

def _load_workflow(name: str) -> dict:
    with open(os.path.join(_WORKFLOWS_DIR, name), encoding="utf-8") as f:
        return json.load(f)

def _get_workflow(name: str) -> dict:
    return _load_workflow(name)


def _poll_for_image(prompt_id: str) -> bytes:
    for _ in range(120):
        time.sleep(2)
        history = requests.get(f"{COMFYUI_BASE_URL}/history/{prompt_id}", timeout=10)
        history.raise_for_status()
        data = history.json()
        if prompt_id not in data:
            continue
        outputs = data[prompt_id]["outputs"]
        for node_output in outputs.values():
            if "images" in node_output:
                image_info = node_output["images"][0]
                img = requests.get(
                    f"{COMFYUI_BASE_URL}/view",
                    params={"filename": image_info["filename"], "subfolder": image_info["subfolder"], "type": image_info["type"]},
                    timeout=30,
                )
                img.raise_for_status()
                return img.content
    raise TimeoutError("ComfyUI did not return an image within 4 minutes")


def generate_image(prompt: str, guild_id: int) -> bytes:
    cfg = config.load(guild_id)
    workflow = _get_workflow("txt2img.json")
    workflow["2"]["inputs"]["text"] = prompt
    workflow["4"]["inputs"]["width"] = cfg["image_width"]
    workflow["4"]["inputs"]["height"] = cfg["image_height"]
    workflow["5"]["inputs"]["steps"] = cfg["image_steps"]
    workflow["5"]["inputs"]["cfg"] = cfg["image_cfg"]
    workflow["5"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

    resp = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    return _poll_for_image(resp.json()["prompt_id"])


def generate_image_from_image(prompt: str, image_bytes: bytes, filename: str, guild_id: int) -> bytes:
    upload = requests.post(
        f"{COMFYUI_BASE_URL}/upload/image",
        files={"image": (filename, image_bytes)},
        timeout=30,
    )
    upload.raise_for_status()
    uploaded_name = upload.json()["name"]

    cfg = config.load(guild_id)
    workflow = _get_workflow("img2img.json")
    workflow["2"]["inputs"]["text"] = prompt
    workflow["4"]["inputs"]["image"] = uploaded_name
    workflow["5"]["inputs"]["steps"] = cfg["image_steps"]
    workflow["5"]["inputs"]["cfg"] = cfg["image_cfg"]
    workflow["5"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

    resp = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    return _poll_for_image(resp.json()["prompt_id"])


def generate_image_qwen_inpaint(prompt: str, mask_subject: str, image_bytes: bytes, filename: str, guild_id: int) -> bytes:
    upload = requests.post(
        f"{COMFYUI_BASE_URL}/upload/image",
        files={"image": (filename, image_bytes)},
        timeout=30,
    )
    upload.raise_for_status()
    uploaded_name = upload.json()["name"]

    workflow = _get_workflow("qwen_inpaint.json")
    workflow["101"]["inputs"]["image"] = uploaded_name
    workflow["202"]["inputs"]["prompt"] = mask_subject
    workflow["53"]["inputs"]["prompt"] = prompt
    workflow["43"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

    resp = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    return _poll_for_image(resp.json()["prompt_id"])


def generate_image_inpaint(prompt: str, mask_subject: str, image_bytes: bytes, filename: str, guild_id: int) -> bytes:
    upload = requests.post(
        f"{COMFYUI_BASE_URL}/upload/image",
        files={"image": (filename, image_bytes)},
        timeout=30,
    )
    upload.raise_for_status()
    uploaded_name = upload.json()["name"]

    cfg = config.load(guild_id)
    workflow = _get_workflow("inpaint.json")
    workflow["2"]["inputs"]["text"] = prompt
    workflow["4"]["inputs"]["image"] = uploaded_name
    workflow["9"]["inputs"]["steps"] = cfg["image_steps"]
    workflow["9"]["inputs"]["cfg"] = cfg["image_cfg"]
    workflow["9"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

    resp = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    return _poll_for_image(resp.json()["prompt_id"])
