import os
import time
import requests


def _base_url() -> str:
    return os.getenv("ACESTEP_BASE_URL", "http://localhost:8001")


def generate_music(prompt: str, guild_id: int) -> bytes:
    from src import config
    cfg = config.load(guild_id)

    payload = {
        "prompt": prompt,
        "lyrics": "",
        "audio_duration": cfg.get("music_duration", 30),
        "inference_steps": cfg.get("music_steps", 20),
        "guidance_scale": cfg.get("music_guidance", 4.0),
        "seed": -1,
    }

    resp = requests.post(f"{_base_url()}/release_task", json=payload, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"ACE-Step {resp.status_code}: {resp.text}")

    task_id = resp.json()["data"]["task_id"]

    for _ in range(300):
        time.sleep(2)
        poll = requests.post(
            f"{_base_url()}/query_result",
            json={"task_ids": [task_id]},
            timeout=10,
        )
        poll.raise_for_status()
        tasks = poll.json()["data"]["tasks"]
        if not tasks:
            continue
        task = tasks[0]
        if task["status"] == 2:
            raise RuntimeError("ACE-Step generation failed")
        if task["status"] == 1:
            file_path = task["result"]["file"]
            audio = requests.get(
                f"{_base_url()}/v1/audio",
                params={"file": file_path},
                timeout=60,
            )
            audio.raise_for_status()
            return audio.content

    raise TimeoutError("ACE-Step did not return audio within 10 minutes")
