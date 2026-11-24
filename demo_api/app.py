"""Illustrated Story Generator demo API.

* POST /story  - LLM writes the structured story (the repo's own prompt; optional visitor theme)
* POST /image  - FLUX.1-schnell via Hugging Face Inference (server HF_TOKEN, or the visitor's own token)

Both calls are traced to LangSmith. Image calls are more expensive than text, so they cost more credits.
"""
from __future__ import annotations

import base64
import io
import os

os.environ.setdefault("DEMO_PROJECT", "genai")
os.environ.setdefault("LANGSMITH_PROJECT", "genai-demo")

from fastapi import Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from . import llm  # noqa: E402
from .base import create_app, guarded  # noqa: E402
from .story_prompt import STORY_PROMPT  # noqa: E402

MODEL_ID = "black-forest-labs/FLUX.1-schnell"
IMAGE_COST = 3
STORY_COST = 2

app = create_app("Illustrated Story Generator demo API")

STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "characters": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {"characterId": {"type": "string"}, "name": {"type": "string"}, "characterPrompt": {"type": "string"}},
                "required": ["characterId", "name", "characterPrompt"],
            },
        },
        "scenes": {
            "type": "array",
            "minItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "sceneNumber": {"type": "integer"},
                    "sceneDescription": {"type": "string"},
                    "audioText": {"type": "string"},
                    "characterIds": {"type": "array", "items": {"type": "string"}},
                    "settingPrompt": {"type": "string"},
                    "motionPrompt": {"type": "string"},
                    "durationSeconds": {"type": "number"},
                },
                "required": ["sceneNumber", "sceneDescription", "settingPrompt"],
            },
        },
    },
    "required": ["characters", "scenes"],
}


async def _body(req: Request) -> dict:
    try:
        data = await req.json()
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def build_story_user_prompt(theme: str | None) -> str:
    base = STORY_PROMPT
    if theme:
        base = base.replace("based on a theme of your choice", f"based on this theme: {theme}")
    return base


@app.post("/story")
async def story(req: Request):
    body = await _body(req)
    theme = str(body.get("theme") or "").strip()[:200] or None

    def run():
        system = "You are a creative screenwriter producing structured JSON for an image/video pipeline."
        out = llm.chat_json(system, build_story_user_prompt(theme), schema=STORY_SCHEMA, temperature=0.8, max_tokens=3500, metadata={"route": "story", "theme": bool(theme)})
        return {"story": out, "theme": theme}

    return await guarded(req, STORY_COST, run, name="genai.story")


def _generate_image(prompt: str, token: str) -> bytes:
    from huggingface_hub import InferenceClient

    client = InferenceClient(provider="hf-inference", api_key=token)
    image = client.text_to_image(prompt=prompt, model=MODEL_ID)
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=88)
    return buf.getvalue()


@app.post("/image")
async def image(req: Request):
    body = await _body(req)
    prompt = str(body.get("prompt") or "").strip()[:1200]
    if len(prompt) < 10:
        return JSONResponse({"error": "Provide an image prompt (at least 10 characters)."}, status_code=400)
    visitor_token = (req.headers.get("x-hf-token") or "").strip()
    token = visitor_token or os.environ.get("HF_TOKEN", "")
    if not token:
        return JSONResponse({"error": "Image generation is not configured on this deployment. Paste your own Hugging Face token to try it."}, status_code=503)

    def run():
        try:
            data = _generate_image(prompt, token)
        except Exception as exc:  # noqa: BLE001 - provider errors vary widely
            msg = str(exc)
            if "402" in msg or "credit" in msg.lower() or "quota" in msg.lower() or "429" in msg:
                raise llm.LLMUnavailable("The image provider's free quota is used up for now. Paste your own Hugging Face token or try later.") from exc
            raise llm.LLMUnavailable("The image model could not generate this image right now. Please try again.") from exc
        return {"image": "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii"), "model": MODEL_ID}

    # a visitor's own HF token spends their quota, not ours
    return await guarded(req, 0 if visitor_token else IMAGE_COST, run, name="genai.image")
