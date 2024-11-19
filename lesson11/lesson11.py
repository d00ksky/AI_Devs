import io
import zipfile
import requests
from dotenv import load_dotenv
from openai import OpenAI
import os
import base64


load_dotenv()
KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.path.exists("pliki_z_fabryki.zip"):
    response_zip = requests.get("******************************************")

    with open("pliki_z_fabryki.zip", "wb") as file:
        file.write(response_zip.content)
else:
    print("Pliki już istnieją") 

def unzip_files():
    with zipfile.ZipFile("pliki_z_fabryki.zip", "r") as zip_ref:
        zip_ref.extractall("pliki_z_fabryki")

unzip_files()

extracted_knowledge = {}

def extract_summary_from_txt(file):
    if file.endswith(".txt"):
        print(f"Przetwarzanie pliku: {file}")
        with open(f"pliki_z_fabryki/{file}", "r") as f:
            content = f.read()
        prompt = f"Podaj podsumowanie pliku {file}: {content}"
        summary = openai_call(prompt)
        extracted_knowledge[file] = summary
        print(f"Podsumowanie pliku {file}: {summary}")
        return summary
    


def extract_summary_from_png(file):
    if file.endswith(".png"):
        print(f"Przetwarzanie pliku: {file}")
        
        # Read image and encode to base64
        with open(f"pliki_z_fabryki/{file}", "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Opisz co widzisz na obrazie {file}"},
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
        
        summary = response.choices[0].message.content
        extracted_knowledge[file] = summary
        print(f"Podsumowanie obrazu {file}: {summary}")
        return summary

extracted_audio = {}

def extract_mp3(file):
    if file.endswith(".mp3"):
        print(f"Przetwarzanie pliku: {file}")
        with open(f"pliki_z_fabryki/{file}", "rb") as f:
            summary = whisper_call(f)
            extracted_audio[file] = summary
            print(f"Przetworzone audio {file}: {summary}")
            return summary



def extract_summary_from_mp3(file):
    transcript = extract_mp3(file)
    prompt = f"Podaj podsumowanie audio {file}: {transcript}"
    summary = openai_call(prompt)
    extracted_knowledge[file] = summary
    print(f"Podsumowanie audio {file}: {summary}")
    return summary


def whisper_call(file):
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=file,
    )
    return response.text

def openai_call(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": f"Wykonując zadanie możesz korzystać z podsumowań plików wiedzy: {extracted_knowledge} aby mieć więcej informacji o zawartości plików."}, {"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

files_with_tags = {}

def tag_files():
    text_files = sorted([f for f in os.listdir("pliki_z_fabryki") if f.endswith(".txt")])
    
    for file in text_files:
        with open(f"pliki_z_fabryki/{file}", "r") as f:
            content = f.read()
            prompt = f"""Przeanalizuj tekst i zwróć WSZYSTKIE pasujące tagi oddzielone przecinkami.
            
            Zasady tagowania:
            1. Dla Aleksandra Ragowskiego: 'zatrzymanie', 'nauczyciel', 'ruch', 'oporu', oraz inne tagi związane z jego działalnością. Koniecznie tag 'nauczyciel'
            2. Dla Barbary Zawadzkiej: 'programistka', 'frontend', 'JavaScript', 'ruch', 'oporu', 'odciski', 'palcow', oraz inne tagi związane z jej działalnością. W szczególności ważne są tagi dotyczące znalezienia odcisków palców jeżeli zostały znalezione.
            3. Dla zwierząt: 'zwierzyna', konkretny_gatunek (np. 'mysz'), oraz inne tagi związane z zwierzętami
            4. Dla zatrzymań: 'zatrzymanie', 'aresztowanie', oraz inne tagi związane z tymi zdarzeniami
            5. Dla aktywności ruchu oporu: 'ruch', 'oporu', 'sabotaz', 'infiltracja', oraz inne tagi związane z tymi zdarzeniami
            6. Dla sprzętu: 'naprawa', 'awaria', 'aktualizacja', oraz inne tagi związane z tymi zdarzeniami
            7. Dla pozostałych osób: 'osoba', oraz inne tagi związane z ich działalnością
            8. Także dla innych tagów, które uważasz za istotne bazując na całej dostępnej wiedzy z innych plików.
            9. Dodawaj tagi także dla innych zdarzeń, które uważasz za istotne w danym tekście bazując na całej dostępnej wiedzy.
            10. Czy widzisz coś o odciskach palców Barbary Zawadzkiej? Jeśli tak, to dodaj tag 'odciski', 'palcow' i inne tagi związane z tym zdarzeniem.
            11. Taguj także wszystkie istotne zdarzenia, które nie są wymienione w zasadach.
            12. W tagach powinno być umieszczone każde słowo które może być istotne w lepszym wyszukiwaniu w przyszłości informacji i wydarzeń
            13. Tagi powinny być w formie mianownika (np. 'zatrzymanie' a nie 'zatrzymany')
            14. Czy widzisz coś o programowaniu? Jeśli tak, to dodaj tag 'programowanie' i inne tagi związane z tym zdarzeniem oraz językiem programowania (np. 'JavaScript').
            
            Zwróć wszystkie pasujące tagi, nie pomijaj żadnej istotnej informacji. Dodaj także inne tagi, które uważasz za istotne bazując na całej dostępnej wiedzy.
            
            Tekst: {content}"""
            
            tags = openai_call(prompt)
            files_with_tags[file] = tags
    
    # Print for debugging
    print("Tagged files:", len(files_with_tags))
    for i, tags in enumerate(files_with_tags):
        print(f"File {i+1}: {tags}")
    
    return files_with_tags

def extract_summary_from_facts(file):
    if file.startswith("f") and file.endswith(".txt"):
        print(f"Przetwarzanie pliku facts: {file}")
        with open(f"pliki_z_fabryki/facts/{file}", "r", encoding='utf-8') as f:
            content = f.read()
        prompt = f"Podaj podsumowanie pliku {file}: {content}"
        summary = openai_call(prompt)
        extracted_knowledge[file] = summary
        print(f"Podsumowanie pliku facts {file}: {summary}")
        return summary

for file in os.listdir("pliki_z_fabryki"):
    if file.endswith(".txt"):
        extract_summary_from_txt(file)
    elif file.endswith(".png"):
        extract_summary_from_png(file)
    elif file.endswith(".mp3"):
        extract_summary_from_mp3(file)

facts_files = os.listdir("pliki_z_fabryki/facts")
for file in facts_files:
    extract_summary_from_facts(file)

tag_files()

print(files_with_tags)

json = {
            "task": "dokumenty", 
            "apikey": KLUCZ, 
            "answer": files_with_tags
        }

finnish = requests.post("****************************", json=json)

print(finnish.json())




