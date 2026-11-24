"""Story/image demo tests. LLM and HF image calls are stubbed at their seams; routing, limits and validation are real."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from demo_api import app as app_module, guard, llm  # noqa: E402

STORY = {
    "characters": [{"characterId": "char1", "name": "Mira", "characterPrompt": "A young cartographer with ink-stained hands"}],
    "scenes": [
        {"sceneNumber": 1, "sceneDescription": "She finds a map.", "settingPrompt": "A dusty attic with light shafts"},
        {"sceneNumber": 2, "sceneDescription": "She follows it.", "settingPrompt": "A misty mountain trail at dawn"},
    ],
}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(guard, "UPSTASH_URL", "")
    guard._mem.clear()
    return TestClient(app_module.app)


def test_story_uses_theme_in_prompt_and_returns_story(client, monkeypatch):
    seen = {}

    def fake(system, user, **kw):
        seen["user"], seen["schema"] = user, kw.get("schema")
        return STORY

    monkeypatch.setattr(llm, "chat_json", fake)
    r = client.post("/story", json={"theme": "a lighthouse keeper"})
    assert r.status_code == 200 and r.json()["story"]["characters"][0]["name"] == "Mira"
    assert "a lighthouse keeper" in seen["user"] and "characters" in seen["user"]
    assert seen["schema"]["required"] == ["characters", "scenes"]


def test_story_without_theme_keeps_original_prompt(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(llm, "chat_json", lambda s, u, **k: seen.setdefault("u", u) and STORY)
    client.post("/story", json={})
    assert "theme of your choice" in seen["u"]


def test_story_schema_rejects_bad_output():
    import jsonschema

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"characters": [], "scenes": []}, app_module.STORY_SCHEMA)
    jsonschema.validate(STORY, app_module.STORY_SCHEMA)


def test_image_requires_prompt_and_token(client, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert client.post("/image", json={"prompt": "x"}).status_code == 400
    r = client.post("/image", json={"prompt": "a castle on a hill at sunset"})
    assert r.status_code == 503 and "Hugging Face token" in r.json()["error"]


def test_image_success_returns_data_url(client, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.setattr(app_module, "_generate_image", lambda prompt, token: b"\xff\xd8jpegbytes")
    r = client.post("/image", json={"prompt": "a castle on a hill at sunset"})
    assert r.status_code == 200 and r.json()["image"].startswith("data:image/jpeg;base64,")


def test_image_cost_limits_server_token_but_not_visitor_token(client, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.setattr(guard, "PER_IP_DAILY", 3)
    monkeypatch.setattr(app_module, "_generate_image", lambda p, t: b"x")
    body = {"prompt": "a castle on a hill at sunset"}
    assert client.post("/image", json=body).status_code == 200  # 3 credits
    assert client.post("/image", json=body).status_code == 429
    assert client.post("/image", json=body, headers={"X-HF-Token": "hf_mine"}).status_code == 200


def test_provider_quota_error_is_friendly(client, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test")

    def boom(p, t):
        raise RuntimeError("402 Payment Required: out of credits")

    monkeypatch.setattr(app_module, "_generate_image", boom)
    r = client.post("/image", json={"prompt": "a castle on a hill at sunset"})
    assert r.status_code == 503 and "quota" in r.json()["error"]
