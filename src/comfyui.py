import copy
import json
import os
import random
import time
import requests

COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "http://localhost:8188")
WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), "..", "workflows", "txt2img.json")

with open(WORKFLOW_PATH, encoding="utf-8") as f:
    _BASE_WORKFLOW = json.load(f)


def generate_image(prompt: str) -> bytes:
    workflow = copy.deepcopy(_BASE_WORKFLOW)
    workflow["2"]["inputs"]["text"] = prompt
    workflow["5"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

    resp = requests.post(f"{COMFYUI_BASE_URL}/prompt", json={"prompt": workflow}, timeout=30)
    resp.raise_for_status()
    prompt_id = resp.json()["prompt_id"]

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
