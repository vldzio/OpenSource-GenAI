# OpenSource-GenAI — illustrated story generation

A two-step Python pipeline that turns an LLM-written story into **character portraits and scene images**. Gemini writes a structured story; Hugging Face Inference serves the open-weight **FLUX.1-schnell** model to render it. A sample story and its generated images are included.

```text
Gemini (LangChain ChatGoogleGenerativeAI)
       ↓ structured story_data.json
       ├── characters[*].characterPrompt → FLUX.1-schnell → char*.jpg
       └── scenes[*].settingPrompt      → FLUX.1-schnell → scene*.jpg
                                            + image_generation_results.json
```

## How it works

- `generate_story.py` asks Gemini for a JSON story with characters, scene descriptions, narration, visual prompts, and motion/duration fields. Pass `--theme` to choose the theme, or let Gemini pick one.
- `generate_images.py` cleans and parses the story JSON, generates one image per character and one per scene through `huggingface_hub.InferenceClient`, and writes a manifest of the saved files.
- `story_data.json` and `generated_images/` contain an example run.

The JSON schema is the contract between the two stages: the story model writes reusable prompt data, and the image stage consumes character and setting prompts separately.

## Quick start

Requires Python 3.10+, a Gemini API key, and a Hugging Face token.

```bash
python -m venv .venv
source .venv/bin/activate                   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```dotenv
GOOGLE_API_KEY=your-gemini-api-key
HF_TOKEN=your-hugging-face-token
```

Run both steps from the repository root:

```bash
python generate_story.py --theme "a lighthouse keeper who befriends a storm"
python generate_images.py
```

Images are saved to `generated_images/`, with an index in `generated_images/image_generation_results.json`.

## Project structure

| Path | Purpose |
| --- | --- |
| `generate_story.py` | Story generation with Gemini |
| `generate_images.py` | Character and scene image generation with FLUX.1-schnell |
| `story_data.json` | Example structured story |
| `generated_images/` | Example character and scene images plus manifest |
| `requirements.txt` | Python dependencies |

## Roadmap

- Schema validation of the story JSON
- Compositing characters into scene backgrounds for visual consistency
