import os
import json
import time
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Configure Hugging Face Inference
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in environment. Add it to your .env file.")

MODEL_ID = "black-forest-labs/FLUX.1-schnell"
client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)


def clean_and_load_story(path="story_data.json"):
    """
    Read story_data.json, remove non-UTF-8 characters, strip Markdown fences, 
    save cleaned JSON back in place, and return the parsed story object.
    """
    try:
        # Read file as bytes
        with open(path, "rb") as f:
            raw_bytes = f.read()
        
        # First decode with 'replace' to see bad characters
        temp = raw_bytes.decode("utf-8", errors="replace")
        bad_chars_count = temp.count("�")
        
        # Then decode with 'ignore' to remove them
        raw = raw_bytes.decode("utf-8", errors="ignore")
        
        print(f"✓ Found {path}")
        if bad_chars_count > 0:
            print(f"✓ Removed {bad_chars_count} non-UTF-8 character(s)")
        
    except FileNotFoundError:
        print(f"✗ Error: {path} not found. Please run main.py first.")
        return None

    cleaned = raw.strip()

    # Remove starting fence: ``````
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
        print("✓ Removed ```json fence")
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
        print("✓ Removed ``` fence")

    # Remove trailing fence ```
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
        print("✓ Removed closing ```")

    cleaned = cleaned.strip()

    try:
        story = json.loads(cleaned)
        print(f"✓ Parsed JSON successfully")
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON in story_data.json: {e}")
        return None

    # Write cleaned JSON back to file (pretty, pure UTF-8)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved cleaned JSON back to {path}")

    return story


def generate_hf_image(prompt: str, filename: str, out_dir="generated_images"):
    """
    Generate an image from a text prompt using Hugging Face InferenceClient,
    then save it to disk with the specified filename.
    """
    try:
        print(f"  → Generating {filename}...")
        print(f"  → Prompt: {prompt[:80]}...")
        
        image = client.text_to_image(prompt=prompt, model=MODEL_ID)
        
        print(f"  → Image generated successfully")
        
        os.makedirs(out_dir, exist_ok=True)
        filepath = os.path.join(out_dir, filename)
        
        image.save(filepath)
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"  ✓ Saved: {filepath} ({file_size} bytes)")
        else:
            print(f"  ✗ File not found after save: {filepath}")
        
        return filepath
    except Exception as e:
        print(f"  ✗ Error generating {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_all_images():
    print("="*60)
    print("STARTING IMAGE GENERATION")
    print("="*60)
    
    story_data = clean_and_load_story()
    if story_data is None:
        print("✗ Failed to load story. Exiting.")
        return

    # Validate structure
    if "characters" not in story_data or "scenes" not in story_data:
        print("✗ Error: JSON must have 'characters' and 'scenes' keys")
        return
    
    characters = story_data.get("characters", [])
    scenes = story_data.get("scenes", [])
    
    print(f"\n✓ Found {len(characters)} character(s) and {len(scenes)} scene(s)\n")

    results = {
        "characters": [],
        "scenes": []
    }

    # ==========================================
    # GENERATE CHARACTER IMAGES
    # ==========================================
    print(f"\n{'='*60}")
    print(f"GENERATING CHARACTER IMAGES")
    print(f"{'='*60}\n")
    
    for char in characters:
        char_id = char.get("characterId")
        char_name = char.get("name", "Unknown")
        char_prompt = char.get("characterPrompt", "").strip()
        
        if not char_id:
            print("⚠ Skipping character without 'characterId'")
            continue
        
        if not char_prompt:
            print(f"⚠ Skipping {char_id} - no character prompt")
            continue
        
        print(f"[{char_id} - {char_name}]")
        
        filename = f"{char_id}.jpg"
        filepath = generate_hf_image(char_prompt, filename)
        
        results["characters"].append({
            "characterId": char_id,
            "name": char_name,
            "file": filepath
        })
        
        time.sleep(2)  # Rate limiting
        print()

    # ==========================================
    # GENERATE SCENE IMAGES
    # ==========================================
    print(f"\n{'='*60}")
    print(f"GENERATING SCENE IMAGES")
    print(f"{'='*60}\n")
    
    for scene in scenes:
        scene_num = scene.get("sceneNumber")
        setting_prompt = scene.get("settingPrompt", "").strip()
        
        if scene_num is None:
            print("⚠ Skipping scene without 'sceneNumber'")
            continue
        
        if not setting_prompt:
            print(f"⚠ Skipping scene {scene_num} - no setting prompt")
            continue
        
        print(f"[Scene {scene_num}]")
        
        filename = f"scene{scene_num}.jpg"
        filepath = generate_hf_image(setting_prompt, filename)
        
        results["scenes"].append({
            "sceneNumber": scene_num,
            "file": filepath
        })
        
        time.sleep(2)  # Rate limiting
        print()

    # Save generation results
    index_path = os.path.join("generated_images", "image_generation_results.json")
    os.makedirs("generated_images", exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("🎉 All done!")
    print(f"📁 Images in: {os.path.abspath('generated_images')}/")
    print(f"👥 Generated {len(results['characters'])} character image(s)")
    print(f"🎬 Generated {len(results['scenes'])} scene image(s)")
    print(f"📄 Index saved to: {index_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    generate_all_images()
