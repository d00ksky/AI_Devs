import io
import requests
import zipfile
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import re
import base64
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionContentPartImageParam
)
from typing import List, Dict, Union, Any

load_dotenv()

client = OpenAI()
KLUCZ = os.getenv("KLUCZ")

raw_data_zip = requests.get(f"**********************************************")

print("Downloading data...")

with open("pliki_z_fabryki.zip", "wb") as f:
    f.write(raw_data_zip.content)


    
print("Starting...")

def get_openai_response(file_content, file_type):
    try:
        system_prompt = """You are a security analyst in a factory. Your task is to analyze content and return ONLY ONE WORD:
- 'people' if there is evidence of:
  * unauthorized persons or intruders
  * suspicious footsteps or movements
  * doors being opened at unusual times
  * unexpected human presence
  * sounds of people when there shouldn't be any
  * any signs of unauthorized access
  * physical evidence of human presence
  * security alerts about intruders
  * reports mentioning unauthorized individuals
  * any suspicious activity that suggests human presence
  * any unusual patterns of movement or access
  * any anomalies that could indicate human intrusion

- 'hardware' if it ONLY mentions:
  * physical equipment repairs
  * mechanical failures
  * broken machines
  * physical device malfunctions
  * EXCLUDE any software/IT issues

- 'not_applicable' for:
  * routine maintenance
  * normal authorized personnel
  * system logs
  * general observations
  * catalog facts
  * software issues

If there's ANY reasonable indication of unauthorized human activity or suspicious presence, classify as 'people'."""

        if file_type == "txt":
            content = file_content.read().decode('utf-8')
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this text CAREFULLY for ANY signs of unauthorized human presence: {content}"}
                ]
            )
            return response.choices[0].message.content

        elif file_type == "mp3":
            audio_content = file_content.read()
            with open("temp.mp3", "wb") as f:
                f.write(audio_content)
            
            audio_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=open("temp.mp3", "rb")
            )
            os.remove("temp.mp3")
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this transcribed audio CAREFULLY for ANY signs of unauthorized human presence or suspicious activity: {audio_response.text}"}
                ]
            )
            result = response.choices[0].message.content
            return result.strip().lower() if result else "not_applicable"

        elif file_type == "png":
            image_content = file_content.read()
            base64_image = base64.b64encode(image_content).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and tell me if it shows hardware repairs/issues or people/human presence."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return "not_applicable"

categorized_files = {
    "people": [],
    "hardware": []
}

with zipfile.ZipFile("pliki_z_fabryki.zip", "r") as zip_file:
    for file in zip_file.namelist():
        if file.endswith((".txt", ".png", ".mp3")) and not file.startswith("facts/"):
            with zip_file.open(file) as f:
                file_type = file.split(".")[-1].lower()
                response = str(get_openai_response(f, file_type)).lower().strip()
                print(f"File: {file}, Raw Response: {response}")
                
                if "people" in response:
                    response = "people"
                elif "hardware" in response:
                    response = "hardware"
                
                if response in ["people", "hardware"]:
                    categorized_files[response].append(file)
                    print(f"Categorized {file} as {response}")

print("\nFinal categorization:")
print(json.dumps(categorized_files, indent=2))
final_answer = {
    "people": categorized_files["people"],
    "hardware": categorized_files["hardware"]
}
print(final_answer)
finnish = requests.post("**********************************************", json={"task": "kategorie", "apikey": KLUCZ, "answer": final_answer})

print(finnish.text)
