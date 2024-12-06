import base64
import os
import requests
from pdf2image import convert_from_path
from openai import OpenAI
from dotenv import load_dotenv
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

load_dotenv()

client = OpenAI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
REPORT_URL = os.getenv("REPORT_URL")
NOTES_URL = os.getenv("NOTES_URL")
BASE_URL = os.getenv("BASE_URL")
KLUCZ = os.getenv("KLUCZ")

QUESTION_URL = f"{BASE_URL}data/{KLUCZ}/notes.json"

logging.info(f"Downloading notes from {NOTES_URL}")
pdf_path = "notes.pdf"

if not os.path.exists(pdf_path):
    response = requests.get(f"{NOTES_URL}", stream=True)
    total_size = int(response.headers.get('content-length', 0))

    # Create progress bar
    with open(pdf_path, 'wb') as f, tqdm(
        desc='Downloading',
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)
else:
    logging.info(f"File {pdf_path} already exists, skipping download")

output_dir = "notes_images"
os.makedirs(output_dir, exist_ok=True)


# Check if images already exist
existing_images = os.listdir(output_dir) if os.path.exists(output_dir) else []


if not existing_images:
    logging.info("Converting and saving images...")
    notes_images = convert_from_path(pdf_path)

    for i, image in enumerate(tqdm(notes_images, desc="Saving images")):
        logging.info(f"Saving image {i+1} of {len(notes_images)}")
        image_path = os.path.join(output_dir, f"page_{i+1}.jpg")
        image.save(image_path, "JPEG")
        logging.info(f"Saved image {image_path}")
else:
    logging.info(f"Images already exist in {output_dir}, skipping conversion")

logging.info(f"Downloading questions from {QUESTION_URL}")
questions = requests.get(QUESTION_URL).json()

logging.info(f"Questions: {questions}")


def encode_image(image_path: str):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def vision_transcription(image):
    base64_image = encode_image(image)
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",  # or your specific model
        messages=[
            {"role": "system", "content": "You are a helpful assistant that transcribes images of notes into text. If text is in some color also describe the color and that it is distinct from other text."},
            {"role": "user", "content": [
                {"type": "text", "text": "Transcribe text from the image"},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
            ]}
        ]
    )
    return response.choices[0].message.content


