import requests
import zipfile
import io
from openai import OpenAI
from dotenv import load_dotenv
import os


load_dotenv()

KLUCZ = os.getenv("KLUCZ")

client = OpenAI()

print("downloading zip file")
response = requests.get("***************************************")
zip_file = zipfile.ZipFile(io.BytesIO(response.content))
print("extracting zip file")
zip_file.extractall()

converted_files = []

def get_openai_response() -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
    {"role": "system", "content": """You are a skilled detective analyzing audio transcripts. 
Your task requires a strict two-step process:

STEP 1: IDENTIFY EXACT WORKPLACE
- Find where Andrzej Maj works at Jagiellonian University
- You must identify the exact faculty name
- Pay attention to mentions of departments, faculties, or institutes
- Do not proceed until you have confirmed his exact workplace

STEP 2: FIND ACTUAL STREET
- Once you have confirmed his workplace at Jagiellonian University
- Use your knowledge to determine the exact street where that faculty is located
- The Faculty of Mathematics and Computer Science has a specific address
- Return ONLY the street name (no building number)"""},
    {"role": "user", "content": f"""
Follow this exact process:
1. First find where exactly Andrzej Maj works at University
2. Once confirmed, determine the street where that specific faculty is located
3. Return only the street name
4. Be carefull as there could be some misleading street names mentioned in transcripts

Transcripts: {converted_files}"""}
],
temperature=0
    )
    
    return str(response.choices[0].message.content).strip()

def convert_audio_to_text(file_path):
    print(f"Converting {file_path} to text")
    model = client.audio.transcriptions.create(model="whisper-1", file=open(file_path, "rb"))
    result = model.text
    print(f"Converted {file_path} to text")
    return result

for file in zip_file.namelist():
    print(f"starting converting {file} to text")
    text = convert_audio_to_text(file)
    print(text)
    print(f"converted {file} to text, appending to list")
    converted_files.append(text)
    print(f"appended {file} to list")

print("starting to get openai response")
print(get_openai_response())


execute_fatality = requests.post("******************************************", json={"task": "mp3", "apikey": KLUCZ, "answer": get_openai_response()})
print(execute_fatality.json())
