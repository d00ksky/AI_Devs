from transformers import AutoTokenizer, AutoModelForCausalLM
import requests
from dotenv import load_dotenv
import os
load_dotenv()
import ollama
import json

KLUCZ = os.getenv("KLUCZ")



def censor_text(text):
    prompt = f"""<<SYS>>
You are a text censoring tool. Replace ALL personal information with 'CENZURA', including:
- Full names
- City names
- Street names with numbers
- Age
Output only the censored text without any explanation.
<</SYS>>

[INST]
Input: Dane osoby podejrzanej: Paweł Zieliński. Zamieszkały w Warszawie na ulicy Pięknej 5. Ma 28 lat.
Output: Dane osoby podejrzanej: CENZURA. Zamieszkały w CENZURA na ulicy CENZURA. Ma CENZURA lat.

Input: {text}
Output:
[/INST]
"""
    response = ollama.chat(model='mistral', messages=[
        {
            'role': 'user',
            'content': prompt
        }
    ])
    return response['message']['content']

response = requests.get(f"****************************************")
print(response.text)
text = response.text
print("Original text:", text)

censored_text = censor_text(text)
print("\nCensored text:", censored_text)

payload = {    "task": "CENZURA",    "apikey": KLUCZ,    "answer": censored_text}
payload = json.dumps(payload)

finnish_him = requests.post("**********************************", data=payload)
print(finnish_him.text)
