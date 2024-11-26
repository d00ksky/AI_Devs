import base64
import io
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
import re
import time

load_dotenv()

KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPORT_URL = os.getenv("REPORT_URL")
IMAGE_URL = os.getenv("IMAGE_URL")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def openai_call(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


json_data = {
    "task": "photos",
    "apikey": KLUCZ,
    "answer":"START"
}


first_response = requests.post(f"{REPORT_URL}", json=json_data)
print(first_response.json())

def get_image_url(data):
    response = openai_call(f"Based on the following data: {data}, please provide ONLY the complete image URLs, one per line, without any additional text.")
    print(response)
    return response

urls_list = []
urls = get_image_url(first_response.json())
for url in str(urls).split('\n'):
    if url.strip():
        urls_list.append(url.strip())
print(urls_list)

def download_image(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Successfully downloaded {filename}")
        else:
            print(f"Failed to download {filename}: Status code {response.status_code}")
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")
        
for url in urls_list:
    if url.split('/')[-1] not in os.listdir():
        download_image(url, url.split('/')[-1])
    else:
        print(f"Image {url.split('/')[-1]} already exists")
        
def base64_encode(filename):
    with open(filename, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def openai_vision_call(prompt, base64_image):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }   
                ]
            }]  
    )
    return response.choices[0].message.content


def improve_image(image_name, action):
    response = requests.post(f"{REPORT_URL}", json={
        "task": "photos",
        "apikey": KLUCZ,
        "answer": f"{action} {image_name}" 
    })
    print(response.json())
    return response.json()
    
    
def is_valid_image(filename):
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    return filename.lower().endswith(valid_extensions)
barbara_description = []
for image in os.listdir():
    if is_valid_image(image):
        base64_image = base64_encode(image)
        response = openai_vision_call(f"Describe person in the image. You need to describe best you can. If image is too dark say only BRIGHTEN, if too bright say only DARKEN, if damaged say only REPAIR.", base64_image)
        response = str(response)
        if "BRIGHTEN" in response or "DARKEN" in response or "REPAIR" in response:
            improved_image = improve_image(image, response)
            print(f"Image {image} improved")
            #print(improved_image)
            new_image = openai_call(f"Provide only image name or URL without any additional text: {improved_image}")
            print(new_image)
            new_image_str = str(new_image)
            if "http" in new_image_str:
                download_image(new_image_str, new_image_str.split('/')[-1])
                base64_image = base64_encode(new_image_str.split('/')[-1])
                new_description = openai_vision_call(f"Describe the image. You need to describe best you can. Focus on details and appearance and distinguishing features and tattoos. Answer only with description in Polish.", base64_image)
                print(new_description)
                barbara_description.append(new_description)
            else:
                download_image(f"{IMAGE_URL}{new_image_str}", new_image_str)
                base64_image = base64_encode(new_image_str)
                new_description = openai_vision_call(f"Describe the image. You need to describe best you can. Focus on details and appearance and distinguishing features and tattoos. Answer only with description in Polish.", base64_image)
                print(new_description)
                barbara_description.append(new_description)
        print(f"Response: {response}")
        
print(barbara_description)
final_description = openai_call(f"Based on provided snippets of descriptions of images in which Barbara is present, please provide one complete description of Barbara in Polish. Focus on details and appearance and distinguishing features and tattoos with details. Descriptions: {barbara_description}")
print(final_description)

final_answer = requests.post(f"{REPORT_URL}", json={
    "task": "photos",
    "apikey": KLUCZ,
    "answer": f"Barbara: {final_description}"
})
print(final_answer.json())
