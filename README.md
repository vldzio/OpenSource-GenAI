# OpenSource-GenAI

An AI-powered pipeline that generates illustrated stories from text prompts using open-source models. Built with Google Gemini for story generation and FLUX.1 Schnell for image synthesis.

## What It Does

Takes a simple theme (e.g., "magical forest adventure") and automatically:
- Generates a structured story with characters and scenes using **Gemini API**
- Creates matching images for characters and scenes using **FLUX.1 Schnell** (Hugging Face)
- Saves story data as JSON and images in organized folders

## Tech Stack

- **Python** - Core language
- **Google Gemini API** - Story and narrative generation
- **FLUX.1 Schnell** - Fast, open-source text-to-image model (12B parameters)
- **Hugging Face** - Model hosting and inference

## Project Structure

OpenSource-GenAI/
├── generate_story.py # Gemini-powered story generation
├── generate_images.py # FLUX.1 image synthesis
├── story_data.json # Generated story structure
└── generated_images/ # Output images

## Quick Start

Install dependencies
pip install google-generativeai huggingface_hub pillow requests python-dotenv

Set up API keys in .env
GEMINI_API_KEY=your_key
HF_TOKEN=your_token

Generate story and images
python generate_story.py
python generate_images.py

## Output Example

**story_data.json** contains:
- Characters with names and image prompts
- Scenes with descriptions and visual details
- Structured data ready for further processing

**generated_images/** contains:
- Character images (char1.png, char2.png, etc.)
- Scene backgrounds (scene1.png, scene2.png, etc.)

## Why These Models?

- **Gemini**: Advanced language understanding for coherent storytelling
- **FLUX.1 Schnell**: Apache 2.0 licensed, generates images in 2-4 seconds with quality rivaling proprietary models

## Use Cases

- Content creation for social media
- Educational storytelling materials
- Rapid prototyping for creative projects
- Visual content generation at scale
