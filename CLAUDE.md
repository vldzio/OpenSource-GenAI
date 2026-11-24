# OpenSource-GenAI (Illustrated Story Generator) - project context

## What this is
Two scripts: `generate_story.py` (Gemini writes structured story JSON) and `generate_images.py` (FLUX.1-schnell via Hugging Face renders character/scene images). The `demo-ready` branch adds a web demo:

```text
Browser (Vercel, static `demo/`) -> Hugging Face Space `demo_api/` (limits, BYO key, LangSmith)
        /story -> private FreeLLMAPI gateway (127.0.0.1:3001, same container) -> free-tier LLMs
        /image -> Hugging Face Inference (FLUX.1-schnell), server HF_TOKEN or the visitor's own X-HF-Token
```

## Layout
- `demo_api/app.py` - `POST /story` (repo prompt, optional visitor theme, schema-validated; costs 2 credits), `POST /image` (3 credits; 0 when the visitor supplies their own HF token). `demo_api/story_prompt.py` is the prompt copied from `generate_story.py` (keep in sync by hand). Shared plumbing: `llm.py`, `base.py`, `guard.py`, `gateway.py`.
- `demo/index.html` (+ `byo.js`, `base.css`, `config.js`, `write-config.mjs`) - UI with a "Sample" tab; `demo/sample/` is the real story + images from the repo's earlier run (labelled as such). `deploy/space/` - HF Space recipe.

## Run and test
- `python -m venv .venv && .venv\Scripts\pip install -r demo_api/requirements.txt pytest && .venv\Scripts\pytest tests` (7 tests; LLM and HF image calls stubbed).
- Local UI: set `API_URL` in `demo/config.js` to a local `uvicorn demo_api.app:app --port 8160`, serve `demo/` with `python -m http.server`. Restore `API_URL` to `""` before committing.

## Rules
- Never hard-code LLM output; the sample gallery is the only canned content and must stay labelled. LLM seam: `demo_api/llm.py`.
- Client IP for limits = LAST `X-Forwarded-For` entry. Never log API keys or tokens. Image generation burns free Hugging Face credits: keep `RL_GLOBAL_DAILY` modest.

## Deploy facts
- Space `genai-demo-api`, LangSmith project `genai-demo`, Vercel dir `demo/`, env var `DEMO_API_URL`.
- Space secrets: `ENCRYPTION_KEY` (64 hex), `FREEAPI_CONFIG_JSON`, `LANGSMITH_API_KEY`, `UPSTASH_REDIS_REST_URL/TOKEN`, `HF_TOKEN` (for images); optional `CORS_ORIGINS`, `RL_PER_IP_DAILY`, `RL_GLOBAL_DAILY`. The Space clones branch `demo-ready`.
- Steps: `hf auth login`, `vercel login`, create the Space from `deploy/space/`, set secrets, then `vercel deploy --prod --yes --build-env DEMO_API_URL=<space url>` from the repo root.

## Status
Verified: 7 tests pass; UI checked in a browser (sample gallery renders 7 images; live path reports gateway status). NOT verified: Space Docker build, real story generation, real FLUX image generation, live deploy.
