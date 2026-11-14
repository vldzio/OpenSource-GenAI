# OpenSource-GenAI — illustrated story generation

A two-step Python experiment that turns an LLM-generated story outline into **character portraits and scene images**. Gemini writes a structured story; Hugging Face Inference serves **FLUX.1-schnell** to render the visual prompts. Sample story data and generated images are included so the output format is visible without running the APIs.

```text
Gemini (LangChain ChatGoogleGenerativeAI)
       ↓ structured story_data.json
       ├── characters[*].characterPrompt → FLUX.1-schnell → char*.jpg
       └── scenes[*].settingPrompt      → FLUX.1-schnell → scene*.jpg
                                            + image_generation_results.json
```

## What is implemented

- `generate_story.py` asks Gemini for JSON containing character identities, scene descriptions, narration text, visual prompts, and motion/duration fields. The current prompt asks the model to **choose its own theme**; there is no CLI theme argument.
- `generate_images.py` strips optional Markdown fences, parses the story JSON, generates one image per valid character and one per scene through `huggingface_hub.InferenceClient`, and writes an index of saved file paths.
- `story_data.json` and `generated_images/` include an example result. Those examples are artifacts, not guarantees that the same outputs will be reproduced on another run.

**Scope:** The pipeline generates still images. It does not render a video, synthesize audio, automatically compose characters into scene backgrounds, or enforce visual identity across independently generated images. `FLUX.1-schnell` is an externally hosted open-weight image model here; this repository does not train or fine-tune it.

## Quick start

Python 3.10+ and working API credentials for Gemini and Hugging Face Inference are needed for a fresh run.

```bash
python -m venv .venv
source .venv/bin/activate                   # Windows: .venv\Scripts\activate
pip install langchain-google-genai huggingface_hub python-dotenv pillow
```

Create an untracked `.env` at the repo root:

```dotenv
GOOGLE_API_KEY=your-gemini-api-key
HF_TOKEN=your-hugging-face-token
```

Run the scripts **from the repository root**, in order:

```bash
python generate_story.py
python generate_images.py
```

`generate_story.py` writes the model response directly to `story_data.json`; `generate_images.py` attempts to clean/parse that response and then overwrites the file with formatted JSON. If Gemini returns invalid JSON, image generation stops. The image step needs `HF_TOKEN` even if you only intend to parse the sample file, because the token is checked at import time.

The image step writes JPGs into `generated_images/` and a `generated_images/image_generation_results.json` manifest. Failed image requests are logged; a manifest entry can contain a `null` file path, so check it before using generated artifacts downstream. Hugging Face availability, model access, and inference charges/quotas depend on your account/provider.

## Design choices and next steps

The JSON schema serves as a small **interface contract** between text and image generation: one model produces reusable prompt data while the next stage consumes character and setting prompts separately. Useful extensions would be schema validation before writing, a user-supplied theme option, reproducible generation metadata, and consistent character compositing. These are next steps, not features already implemented.

**Note:** The `GOOGLE_API_KEY` variable and `langchain-google-genai` dependency above reflect the actual code; an older repository README listed a different Gemini package and key name. Never commit `.env` or API tokens.

## Live web demo

[`demo/`](demo) is a static UI (Vercel) and [`demo_api/`](demo_api) its FastAPI backend (Hugging Face Space with a private [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) gateway):

* **Write story** - the LLM runs this repo's own story prompt (optionally with a visitor theme) and the result is schema-validated JSON, same structure as `story_data.json`.
* **Generate image** - FLUX.1-schnell through Hugging Face Inference, per character/scene prompt. Uses the Space's `HF_TOKEN` (small daily allowance per visitor) or the visitor's own token.
* The **Sample** tab shows the real story and images committed from an earlier run, clearly labelled.
* All LLM calls are traced to LangSmith (`genai-demo`). Deploy: [`deploy/space/`](deploy/space) and [`vercel.json`](vercel.json) (set `DEMO_API_URL`). Tests: `pip install -r demo_api/requirements.txt pytest && pytest tests`.
