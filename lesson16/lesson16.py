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

'''
Oto polecenia, które rozpoznaje automat:

REPAIR NAZWA_PLIKU

DARKEN NAZWA_PLIKU

BRIGHTEN NAZWA_PLIKU
'''

json_data = {
    "task": "photos",
    "apikey": KLUCZ,
    "answer":"START"
}

first_response = requests.post(f"{REPORT_URL}", json=json_data)
print(first_response.json())

def get_image_list(data):
    response = openai_call(f"Based on the following data: {data}, please provide ONLY the image filenames, one per line, without any additional text or descriptions.")
    image_list = [name.strip() for name in response.split('\n') if name.strip()]
    return image_list

def get_image_url(data):
    response = openai_call(f"Based on the following data: {data}, please provide ONLY the complete image URLs, one per line, without any additional text.")
    urls = [url.strip() for url in response.split('\n') if url.strip()]
    return urls

image_list = get_image_list(first_response.json())
print(image_list)

image_url = get_image_url(first_response.json())
print(image_url)

map_image_url = dict(zip(image_list, image_url))
print(map_image_url)

for image_name, image_url in map_image_url.items():
    print(image_name, image_url)
    download_image(image_url, image_name)

def describe_image(image_data, is_file=True):
    try:
        # Handle binary image data properly
        if is_file:
            # Read image as binary
            image_bytes = image_data
            if isinstance(image_data, str):
                with open(image_data, 'rb') as f:
                    image_bytes = f.read()
        else:
            image_bytes = image_data
            
        # Convert to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe Barbara in the image. If image is too dark say only BRIGHTEN, if too bright say only DARKEN, if damaged say only REPAIR."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in describe_image: {e}")
        return "REPAIR"  # Default to REPAIR on errors

def describe_image_mini(image_data):
    base64_image = base64.b64encode(image_data).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
            messages=[{"role": "user", "content": [
            {"type": "text", "text": "Describe Barbara, person in image. Focus on her appearance."},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]}]
    )
    return response.choices[0].message.content

BARBARA_DESCRIPTION = {}
def process_image(image_name, max_attempts=3, attempt=0):
    try:
        if attempt >= max_attempts:
            print(f"Max attempts ({max_attempts}) reached for {image_name}")
            return "REPAIR"
        
        # Get current image description
        with open(image_name, 'rb') as f:
            current_content = f.read()
        description = describe_image(current_content)
        print(f"Image description: {description}")
        
        if "REPAIR" in description:
            print(f"Attempt {attempt + 1}: Repairing image...")
            response = requests.post(f"{IMAGE_URL}", json={
                "task": "photos",
                "apikey": KLUCZ,
                "answer": f"REPAIR {image_name}"
            })
            
            if response.ok:
                # Get the improved image URL/instructions from response
                improved_info = response.json()
                # Download the improved image
                improved_response = requests.get(improved_info['url'])
                if improved_response.ok:
                    with open(f"improved_{image_name}", "wb") as f:
                        f.write(improved_response.content)
                    return process_image(f"improved_{image_name}", max_attempts, attempt + 1)
                
        elif "BRIGHTEN" in description:
            print(f"Attempt {attempt + 1}: Brightening image...")
            response = requests.post(f"{IMAGE_URL}", json={
                "task": "photos",
                "apikey": KLUCZ,
                "answer": f"BRIGHTEN {image_name}"
            })
            
            if response.ok:
                improved_info = response.json()
                improved_response = requests.get(improved_info['url'])
                if improved_response.ok:
                    with open(f"improved_{image_name}", "wb") as f:
                        f.write(improved_response.content)
                    return process_image(f"improved_{image_name}", max_attempts, attempt + 1)
                    
        elif "DARKEN" in description:
            print(f"Attempt {attempt + 1}: Darkening image...")
            response = requests.post(f"{IMAGE_URL}", json={
                "task": "photos",
                "apikey": KLUCZ,
                "answer": f"DARKEN {image_name}"
            })
            
            if response.ok:
                improved_info = response.json()
                improved_response = requests.get(improved_info['url'])
                if improved_response.ok:
                    with open(f"improved_{image_name}", "wb") as f:
                        f.write(improved_response.content)
                    return process_image(f"improved_{image_name}", max_attempts, attempt + 1)
        
        else:
            BARBARA_DESCRIPTION[image_name] = description
            return description
            
    except Exception as e:
        print(f"Error in process_image: {e}")
        return "REPAIR"

for image_name in image_list:
    final_description = process_image(image_name)
    if final_description:
        print(f"Final description for {image_name}: {final_description}")
    else:
        print(f"Failed to get proper description for {image_name}")

print(BARBARA_DESCRIPTION)
