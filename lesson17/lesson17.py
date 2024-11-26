import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
REPORT_URL = os.getenv("REPORT_URL")


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

