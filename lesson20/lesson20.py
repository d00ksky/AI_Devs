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
        model="chatgpt-4o-latest",
        messages=[
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"""\
You are a helpful assistant that transcribes images of fictional notes into text. All characters and events are fictional. Transcribe **all text exactly as it appears** in the image, including any dates, numbers, and names. Do not omit any text. If text is in some color, also describe the color and that it is distinct from other text. If there is any image in the image, describe it in detail. Here is the image:"""},
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
    transcription = vision_transcription(os.path.join(output_dir, image))
    trancribed_images.append(f"PDF page {image}: {transcription}")
logging.info(f"Transcribed images: {trancribed_images}")


def answer_questions(questions, transcribed_text):
    logging.info(f"Answering questions: {questions}")
    response = client.chat.completions.create(
        model="o1-preview-2024-09-12",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
Jesteś pomocnym asystentem, który odpowiada na pytania na podstawie dostarczonego tekstu. Odpowiadaj po polsku. Odpowiedzi powinny być zwięzłe i na temat.

Podaj odpowiedzi w formacie JSON z kluczami jako numery pytań i wartościami jako odpowiedzi, w następującym formacie:

{{ "01": "odpowiedź1", "02": "odpowiedź2", "03": "odpowiedź3", "04": "odpowiedź4", "05": "odpowiedź5" }}

Nie dodawaj żadnego innego tekstu do odpowiedzi, tylko JSON.

Przed udzieleniem odpowiedzi:

- Przeanalizuj dokładnie dostarczony tekst, zwracając szczególną uwagę na wszystkie daty, wydarzenia i odwołania do nich.
- Utwórz wewnętrzną linię czasu na podstawie tych informacji (nie umieszczaj jej w odpowiedzi), aby upewnić się, że uwzględniasz wszystkie fakty i chronologię wydarzeń.
- Rozwiąż wszelkie sprzeczności, wybierając informacje najbardziej bezpośrednie i uzasadnione kontekstem.

Oto pytania:

{json.dumps(questions, ensure_ascii=False)}

A oto tekst:

{transcribed_text}
"""
                    }
                ]
            }
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

def correct_answers(questions, transcribed_text):
    max_attempts = 5  # Set a limit to avoid infinite loops
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        logging.info(f"Attempt {attempt}")
        
        # Generate answers
        answer = answer_questions(questions, transcribed_text)
        logging.info(f"Answer: {answer}")
        answer_dict = json.loads(str(answer).replace("'", '"'))
        logging.info(f"Answer after processing: {answer_dict}")
        
        # Submit answers and get feedback
        response = final_call(answer_dict)
        
        if response.get('code') == 0:
            logging.info("All answers are correct.")
            break  # Exit loop when all answers are correct
        else:
            # Extract feedback
            incorrect_question = response.get('message')
            hint = response.get('hint')
            debug_info = response.get('debug')
            logging.info(f"Received feedback: {response}")
            
            # Update prompt with feedback
            questions = update_questions_with_feedback(questions, incorrect_question, hint, debug_info)
    else:
        logging.warning("Maximum attempts reached without correcting all answers.")
    return answer_dict

def update_questions_with_feedback(questions, incorrect_question_msg, hint, debug_info):
    import re
    match = re.search(r'Answer for question (\d{2}) is incorrect', incorrect_question_msg)
    if match:
        question_number = match.group(1)
        # Append hint directly to the question to clarify the required focus
        questions[question_number] = f"{questions[question_number]} (Hint: {hint})"
    else:
        logging.error("Failed to parse incorrect question number from server message.")
    return questions


# Use the new function instead of directly calling answer_questions and final_call
logging.info("Answering questions with correction loop")
answer = correct_answers(questions, trancribed_images)


