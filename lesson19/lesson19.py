import os
import requests
import json
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

