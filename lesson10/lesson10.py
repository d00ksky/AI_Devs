import base64
import subprocess
import tempfile
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
from bs4 import BeautifulSoup
import whisper
load_dotenv()

KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)



base_knowledge_raw = requests.get(f"*****************************************").text
pytania = requests.get(f"*****************************************").text

#print(base_knowledge_raw)
print(pytania)



def extract_text_content(url):
    print(url)
    response = requests.get(url)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    for script in soup(["script", "style"]):
        print("removing script")
        script.decompose()
        print("script removed")
    text = soup.get_text()
    print("text extracted")
    return text.strip()

def extract_images(url):
    print(url)
    response = requests.get(url)
    print("response received")
    soup = BeautifulSoup(response.content, 'html.parser')
    print("soup created")
    images = []
    
    for img in soup.find_all('img'):
        print("img found")
        img_url = urljoin(url, img.get('src'))
        print("img_url created")
        if img_url:
            img_data = requests.get(img_url).content
            images.append(img_data)
            print("img_data appended")
    return images


def extract_audio(url):
    print("extracting audio")
    audio_files = []
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    for audio in soup.find_all('audio'):
        print("audio found")
        audio_url = urljoin(url, audio.find('source').get('src'))
        print("audio_url created")
        filename = f"audio_{len(audio_files)}.mp3"
        print("filename created")
        with open(filename, 'wb') as f:
            f.write(requests.get(audio_url).content)
        audio_files.append(filename)
        print("audio_files appended")
    return audio_files

def transcribe_audio(filename):
    print("transcribing audio")
    try:
        model = whisper.load_model("base")
        result = model.transcribe(filename)
        print("audio transcribed")
        return result["text"]
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def process_url_content(url):
    print("processing url content")
    text_content = extract_text_content(url)
    print("text content extracted")
    images = extract_images(url)
    image_texts = []
    for img in images:
        base64_image = base64.b64encode(img).decode('utf-8')
        image_analysis = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Describe this image in detail and what is visible on it. What foods you see? What pizza is on the table?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }]
        )
        image_texts.append(image_analysis.choices[0].message.content)
        print(image_analysis.choices[0].message.content)
        print("image_analysis appended")
    audio_files = extract_audio(url)
    audio_texts = [transcribe_audio(audio) for audio in audio_files]
    
    all_content = {
        "text": text_content,
        "image_descriptions": image_texts,
        "audio_transcriptions": audio_texts
    }
    
    return all_content

knowledge = process_url_content("********************************************")

thread = client.beta.threads.create()
print("thread created")

assistant = client.beta.assistants.create(
    name="arxiv_assistant",
    instructions=f"You help with anwsering questions based on the provided knowledge: {knowledge}. If there is no direct anwser in provided knowledge use your own knowledge or try to find anwser by searching the web or combining information from multiple sources. Provide only short concise answer, no other text... Images descriptions are very important for finding answers.",
    model="gpt-4o"  
)
print("assistant created")

message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=f"Provide only answers to the following questions. For question: 04=Resztki jakiego dania zostały pozostawione przez Rafała? anwser is in image descriptions and it's not cake. Anwser in Polish. What fruit it was? Anwsers need to be short and concise and concrete. Anwsers can be in images that are described in the knowledge. For question about fruit and dish you will find anwsers in image descriptions. The dish in question could be pizza on a plate. All anwsers should be in the knowledge. Analyze the knowldge carefully and connect the dots: {knowledge}/ And here are the questions: {pytania}"
)
print("message created")

run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)
print("run created")

while run.status != "completed":
    print("waiting for run to complete")
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    print(f"Run status: {run.status}")
    
messages = client.beta.threads.messages.list(
    thread_id=thread.id
)
print("messages retrieved")
first_message = messages.data[0]
if first_message.content[0].type == "text":
    print(first_message.content[0].text.value)
    openai_answer = first_message.content[0].text.value
else:
    print("Message format not as expected:", first_message.content[0])
    


# After getting the response, add:
def format_answers_to_json(answers_text):
    # Split answers into lines and create dictionary
    answers_dict = {}
    for line in answers_text.split('\n'):
        if '=' in line:
            question_id, answer = line.split('=', 1)
            answers_dict[f"{question_id}"] = answer.strip()
    print(answers_dict)
    return answers_dict

# Replace the last part with:
if first_message.content[0].type == "text":
    raw_answers = first_message.content[0].text.value
    formatted_answers = format_answers_to_json(raw_answers)
    print("Formatted answers:", formatted_answers)
    
    # Send the formatted response with error handling
    finnish = requests.post(
        "**********************************", 
        json={
            "task": "arxiv", 
            "apikey": KLUCZ, 
            "answer": formatted_answers
        }
    )
    
    # Print response details for debugging
    print("Response status code:", finnish.status_code)
    print("Response text:", finnish.text)
    
    try:
        print("Response JSON:", finnish.json())
    except requests.exceptions.JSONDecodeError:
        print("Could not decode JSON response")