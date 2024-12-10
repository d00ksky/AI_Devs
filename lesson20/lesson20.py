import base64
import json
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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
        model="chatgpt-4o-latest",
        messages=[
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"You are a helpful assistant that transcribes images of notes into text. If text is in some color also describe the color and that it is distinct from other text. If there is some image in the image, describe it.Transcribe text from the image and describe every picture and image. Here is the image: "},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content


trancribed_images = []
logging.info(f"Transcribing images from {output_dir}")
for image in tqdm(os.listdir(output_dir), desc="Transcribing images"):
    logging.info(f"Transcribing image {image}")
    trancribed_images.append(vision_transcription(os.path.join(output_dir, image)))
logging.info(f"Transcribed images: {trancribed_images}")


def answer_questions(questions, trancribed_images):
    logging.info(f"Answering questions: {questions}")
    response = client.chat.completions.create(
        model="o1-preview-2024-09-12",
        messages=[
            {"role": "user", "content": [{"type": "text", "text": f"You are a helpful assistant that answers questions based on the provided text. Answer in Polish. Answers should be concise and to the point. Provide answers in JSON format with keys as question numbers and values as answers with the following format: {{'01': 'answer1', '02': 'answer2', '03': 'answer3', '04': 'answer4', '05': 'answer5'}}. Don't add any other text to response, just the JSON. Uwzględnij wszystkie fakty podane w tekście, w szczególności odwołania do wydarzeń. Przeanalizuj dokładnie tekst, niektóre pytania są podchwytliwe. Answer the following questions  - {questions} . Answer based on the provided text: {trancribed_images}"}, ]}
        ]
    )
    logging.info(f"Response: {response.choices[0].message.content}")
    return response.choices[0].message.content

logging.info("Answering questions")
answer = answer_questions(questions, trancribed_images)
logging.info(f"Answer: {answer}")
answer = str(answer).replace("'", '"')
answer = json.loads(answer)
logging.info(f"Answer after processing: {answer}")

def final_call(answer):
    logging.info(f"Final call: {answer}")
    json_data = {
        "task": "notes",
        "apikey": KLUCZ,
        "answer": answer
        
    }
    response = requests.post(f"{REPORT_URL}", json=json_data)
    logging.info(f"Response: {response.json()}")
    return response.json()

solution = final_call(answer)

print(solution)

