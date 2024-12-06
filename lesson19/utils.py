import json
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from logger import logger
import aiohttp
import asyncio


load_dotenv()

KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
REPORT_URL = os.getenv("REPORT_URL")

client = OpenAI(api_key=OPENAI_API_KEY)

async def send_url_to_central(ngrok_url: str) -> Dict[str, Any]:
    logger.debug("\n=== REGISTERING URL ===")
    if not REPORT_URL or not KLUCZ:
        logger.debug("Missing REPORT_URL or KLUCZ!")
        return {"error": "Missing configuration"}
    
    base_url = ngrok_url.rstrip('/')
    url = f"{base_url}/instructions"
    
    payload = {
        "apikey": KLUCZ,
        "answer": url,
        "task": "webhook"
    }
    
    logger.debug(f"Sending registration with payload: {payload}")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Try multiple times with increasing timeouts
    timeouts = [30, 45, 60]  # seconds
    
    for timeout in timeouts:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    REPORT_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    logger.info(f"Response status: {response.status}")
                    text = await response.text()
                    logger.info(f"Response body: {text}")
                    
                    if response.status == 200:
                        return await response.json()
                    
                    logger.error(f"Registration failed with status {response.status}")
                    logger.error(f"Response: {text}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout after {timeout}s, retrying...")
            continue
        except Exception as e:
            logger.error(f"Error registering URL: {str(e)}")
            continue
    
    return {"error": "All registration attempts failed"}

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
[0,1]: trawa
[0,2]: Pojedyncze drzewo
[0,3]: Dom
[1,0]: trawa
[1,1]: Wiatrak
[1,2]: trawa
[1,3]: trawa
[2,0]: trawa
[2,1]: trawa
[2,2]: Skały
[2,3]: Dwa drzewa
[3,0]: Wysokie góry
[3,1]: Wysokie góry
[3,2]: Samochód
[3,3]: Jaskinia

Poruszasz się po tej siatce, gdzie:
- Północ oznacza ruch w górę
- Południe oznacza ruch w dół
- Wschód oznacza ruch w prawo
- Zachód oznacza ruch w lewo

Na początku masz znacznik lokalizacji (pin) w pozycji [0,0]"""

def analyze_instructions(instructions: str) -> str:
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": instructions}]
    )
    result = response.choices[0].message.content
    logger.debug(f"Analyzed result: {result}")
    return str(result)


