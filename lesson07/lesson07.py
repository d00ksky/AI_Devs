import glob
from openai import OpenAI
import base64
from dotenv import load_dotenv
import os

load_dotenv()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_map_description(base64_image):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": """Analyze this map image carefully:
1. Focus specifically on street names, building names, and landmarks
2. Pay attention to the exact spelling of each name
3. Note the relative positions and connections between streets
4. Describe only the factual information you can read, ignore visual styles
5. If the image is unclear or text is blurry, please state that explicitly
6. List all visible text elements systematically"""},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=600
    )
    return response.choices[0].message.content

client = OpenAI()
map_descriptions = []
script_dir = os.path.dirname(os.path.abspath(__file__))

# Process all images in the script's directory
for image_path in glob.glob(os.path.join(script_dir, "Zrzut*")):
    try:
        base64_image = encode_image(image_path)
        description = get_map_description(base64_image)
        print(description)
        map_descriptions.append(description)
        print(f"Processed: {image_path}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")


chat_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
            {
                "role": "system", 
                "content": """You are a Polish geography expert. Your task is to:
1. Analyze multiple map descriptions carefully
2. Look for patterns in street names and landmarks
3. Cross-reference between descriptions to find consistencies
4. Filter out false descriptions
5. Based on the consistent information, determine the most likely Polish city
6. Explain your reasoning using specific street names and landmarks
7. Focus on where exact street crosses are located and in which city they are located
Note: This is not Warszawa, Kraków, Łódź, Poznań, Wrocław, Toruń, Szczecin, Bydgoszcz, Bielsko-Biała, Gdańsk - do not default to that assumption."""
            },
            {
                "role": "user",
                "content": str(map_descriptions)
            }
        ]
    )

print(chat_response.choices[0].message.content)
