"""
Ollama orqali mahalliy (offline, bepul) AI.

O'rnatish:  https://ollama.com
Matn modeli: ollama pull qwen2.5:7b
Vision:      ollama pull llava:7b
"""
import base64
import os

import aiohttp

OLLAMA_URL   = os.environ.get("OLLAMA_URL",   "http://localhost:11434")
LOCAL_MODEL  = os.environ.get("LOCAL_MODEL",  "qwen2.5:7b")
VISION_MODEL = os.environ.get("VISION_MODEL", "llava:7b")


async def chat(messages: list[dict], system: str = "") -> str:
    all_msgs = ([{"role": "system", "content": system}] if system else []) + messages
    payload = {"model": LOCAL_MODEL, "messages": all_msgs, "stream": False}
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{OLLAMA_URL}/api/chat", json=payload,
            timeout=aiohttp.ClientTimeout(total=180),
        ) as r:
            if r.status != 200:
                raise RuntimeError(f"Ollama {r.status}: {(await r.text())[:200]}")
            return (await r.json())["message"]["content"]


async def vision(image_bytes: bytes, prompt: str) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": VISION_MODEL,
        "messages": [{"role": "user", "content": prompt, "images": [b64]}],
        "stream": False,
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{OLLAMA_URL}/api/chat", json=payload,
            timeout=aiohttp.ClientTimeout(total=240),
        ) as r:
            if r.status != 200:
                raise RuntimeError(f"Ollama vision {r.status}: {(await r.text())[:200]}")
            return (await r.json())["message"]["content"]


async def is_available() -> bool:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{OLLAMA_URL}/api/tags",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as r:
                return r.status == 200
    except Exception:
        return False


async def list_models() -> list[str]:
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{OLLAMA_URL}/api/tags") as r:
            data = await r.json()
            return [m["name"] for m in data.get("models", [])]
