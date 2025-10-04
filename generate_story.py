import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# Initialize the Gemini model
gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    temperature=0.7,
    google_api_key=api_key
)

# Define the prompt
prompt = """
Create a creative, engaging short story based on a theme of your choice.
Design the story to fit within a 30 to 60 second video duration and break it down into 3 to 6 distinct scenes.

Return a JSON object with TWO main sections:

1. "characters": An array of all unique characters in the story. For each character, provide:
   - characterId: A unique identifier (e.g., "char1", "char2")
   - name: The character's name
   - characterPrompt: A highly detailed text prompt describing the character's appearance, clothing, age, distinctive features, hair, eyes, and overall visual style. This will be used to generate a consistent character image that will appear throughout all scenes.

2. "scenes": An array of scenes. For each scene, provide:
   - sceneNumber: The position of the scene in the story
   - sceneDescription: A vivid and concise description of the scene's visuals and actions
   - audioText: Creative text for background audio (dialogue, narration, ambient sounds)
   - characterIds: An array of character IDs that appear in this scene (e.g., ["char1", "char2"])
   - characterContext: Brief description of what the character(s) are doing in this specific scene (pose, expression, action)
   - settingPrompt: A detailed text prompt describing the environment, location, lighting, mood, and atmosphere for this scene
   - startingSettingPrompt: Description of the setting at the start of the scene, including character position and interaction
   - endingSettingPrompt: Description of the setting at the end of the scene, including how the character's position or interaction changes
   - motionPrompt: Description of animation, movement, or visual effects that occur
   - durationSeconds: Suggested duration in seconds

Return the complete story as a JSON object in this exact structure:
{
  "characters": [
    {
      "characterId": "char1",
      "name": "Character Name",
      "characterPrompt": "Detailed visual description for image generation..."
    }
  ],
  "scenes": [
    {
      "sceneNumber": 1,
      "sceneDescription": "...",
      "audioText": "...",
      "characterIds": ["char1"],
      "characterContext": "...",
      "settingPrompt": "...",
      "startingSettingPrompt": "...",
      "endingSettingPrompt": "...",
      "motionPrompt": "...",
      "durationSeconds": 10
    }
  ]
}

Ensure the story flows smoothly with a clear beginning, middle, and end. Use descriptive language that evokes emotions and paints clear imagery suitable for visual generation. Focus on imaginative and engaging themes with consistent character appearances across all scenes.
"""

# Call Gemini API
response = gemini.invoke(prompt)

# Store the response content
story_json = response.content

# Print and save the result
print(story_json)

# Save to file
with open('story_data.json', 'w') as f:
    f.write(story_json)

print("\nStory saved to story_data.json")