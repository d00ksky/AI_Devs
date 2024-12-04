import os
import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
REPORT_URL = os.getenv("REPORT_URL")
client = OpenAI(api_key=OPENAI_API_KEY)

"""
Pracownik centrali wyśle na Twoje API metodą POST dane w formacie JSON w formie jak poniżej:

{

"instruction":"tutaj instrukcja gdzie poleciał dron"

}
"""


""" # Template for report
{
"apikey":"TWOJ-KLUCZ",
"answer":"<https://azyl-12345.ag3nts.org/moje_api>",
"task":"webhook"
}

"""


def send_url_to_central(ngrok_url: str) -> dict:
    """Send our API URL to the central system"""
    load_dotenv(override=True)
    
    payload = {
        "apikey": KLUCZ,
        "answer": f"{ngrok_url}/instructions",
        "task": "webhook"
    }
    
    print(f"\n=== Sending to Central ===")
    print(f"URL: {REPORT_URL}")
    print(f"Payload: {payload}")
    
    response = requests.post(f"{REPORT_URL}", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Raw Response: {response.text}")
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Warning: Response was not valid JSON")
        return {"error": "Invalid JSON response", "raw_response": response.text}