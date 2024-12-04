import json
import os
from typing import Dict, Any
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()



KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
REPORT_URL = os.getenv("REPORT_URL")

client = OpenAI(api_key=OPENAI_API_KEY)


def send_url_to_central(ngrok_url: str) -> Dict[str, Any]:
    """
    Send the URL to the central server.
    """
    load_dotenv(override=True)

    if not REPORT_URL:
        print("Error: REPORT_URL not found in environment variables")
        return {"error": "REPORT_URL not configured"}

    payload = {
        "apikey": KLUCZ,
        "answer": f"{ngrok_url}/instructions",
        "task": "webhook"
    }

    print("""\n=== Sending to Central ===\n""")
    print(f"URL: {REPORT_URL}")
    print(f"Payload: {payload}")

    try:
        response = requests.post(
            str(REPORT_URL),  # Cast to str to satisfy type checker
            json=payload,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}")

        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Warning: Response was not valid JSON")
        return {"error": "Invalid JSON response", "raw_response": response.text}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}


prompt = """Jesteś asystentem nawigacyjnym. Otrzymasz instrukcje poruszania się po siatce/planszy.
Twoim zadaniem jest:
1. Przeanalizować otrzymane instrukcje krok po krok
2. Określić końcową pozycję
3. Zwrócić DOKŁADNIE dwa słowa w języku polskim opisujące miejsce, w którym się znalazłeś

Zasady:
- Odpowiadaj TYLKO dwoma słowami opisującymi końcową lokalizację
- Nie dodawaj żadnych wyjaśnień ani dodatkowych informacji
- Słowa muszą być w języku polskim
- Używaj wyłącznie rzeczowników lub przymiotników

Mapa (siatka 4x4, numerowana od 0 do 3, gdzie [0,0] to lewy górny róg):
[0,0]: Znacznik lokalizacji (pin)
[0,1]: Trawa
[0,2]: Pojedyncze drzewo
[0,3]: Dom z dachem
[1,0]: Trawa
[1,1]: Wiatrak
[1,2]: Pusta przestrzeń
[1,3]: Pusta przestrzeń
[2,0]: Trawa
[2,1]: Pusta przestrzeń
[2,2]: Skały/góry
[2,3]: Dwa drzewa
[3,0]: Wysokie góry
[3,1]: Pusta przestrzeń
[3,2]: Samochód (widok z góry)
[3,3]: Wzgórze

Poruszasz się po tej siatce, gdzie:
- Północ oznacza ruch w górę
- Południe oznacza ruch w dół
- Wschód oznacza ruch w prawo
- Zachód oznacza ruch w lewo"""

def analyze_instructions(instructions: str) -> str:
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": instructions}]
    )
    print(response.choices[0].message.content)
    result = response.choices[0].message.content
    return str(result)

print(analyze_instructions("Idź 3 kroki na północ, następnie 2 na wschód"))
