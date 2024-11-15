import requests
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI()

KLUCZ = os.getenv("KLUCZ")

robot_description_raw = requests.get(f"******************************")


print(robot_description_raw.json())

robot_description_polished = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a robot description expert. From prompt create description for DALLE to create image of robot. Instruct DALLE to create just image without any text"},
        {"role": "user", "content": str(robot_description_raw.json())}
    ]
)
robot_description_polished_str = robot_description_polished.choices[0].message.content
print(robot_description_polished_str)


response = client.images.generate(
    model="dall-e-3", 
    prompt=str(robot_description_polished_str),
    n=1,  
    size="1024x1024",
    quality="standard",
    response_format="url"
)

image_url = response.data[0].url

print(image_url)

finnish = requests.post(f"******************************", json={"task": "robotid", "apikey": KLUCZ, "answer": image_url})

print(finnish.json())
