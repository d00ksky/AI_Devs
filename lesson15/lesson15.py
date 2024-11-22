import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase

load_dotenv()
KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPORT_URL = os.getenv("REPORT_URL")
SQL_API_URL = os.getenv("SQL_API_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

json = {
    "task": "database",
    "apikey": KLUCZ,
    "answer": ""
}

client = OpenAI(api_key=os.getenv(f"{OPENAI_API_KEY}"))
neo4j_driver = GraphDatabase.driver(f"{NEO4J_URI}", auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
#Polecenia SQL:
#show tables = zwraca listę tabel
#show create table NAZWA_TABELI = pokazuje, jak zbudowana jest konkretna tabela
#select * from users limit 1

def sql_query(query):
    response = requests.post(
        f"{SQL_API_URL}",
        json={
            "task": "connections",
            "apikey": KLUCZ,
            "query": query
        }
    )
    return response.json()

def neo4j_query(query):
    with neo4j_driver.session() as session:
        result = session.run(query)
        return result




neo4j_driver.close()