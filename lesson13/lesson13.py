import requests
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KLUCZ = os.getenv("KLUCZ")
REPORT_URL = os.getenv("REPORT_URL")
SQL_API_URL = os.getenv("SQL_API_URL")


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#Polecenia SQL:
#show tables = zwraca listę tabel
#show create table NAZWA_TABELI = pokazuje, jak zbudowana jest konkretna tabela
#select * from users limit 1

def sql_query(query):
    response = requests.post(
        f"{SQL_API_URL}",
        json={
            "task": "database",
            "apikey": KLUCZ,
            "query": query
        }
    )
    return response.json()


database_info = {}

database_info["tables"] = sql_query("show tables")
database_info["users"] = sql_query("show create table users")
database_info["datacenters"] = sql_query("show create table datacenters")

#print(database_info)

def create_sql_with_llm(database_info):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that helps with SQL queries. Return only the query without any additional text or characters or comments.Query must be ready to execute straight from answer."},
            {"role": "user", "content": f"Create a SQL query and return only the query without any additional text or characters or comments based on the following database info: {database_info} to answer the question: które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)"}
        ]
    )
    sql = str(response.choices[0].message.content).strip("```sql\n").strip("```")
    return sql


#print(create_sql_with_llm(database_info))

print(sql_query(create_sql_with_llm(database_info)))
answer = sql_query(create_sql_with_llm(database_info))

dc_ids = [item['dc_id'] for item in answer['reply']]


json = {
    "task": "database",
    "apikey": KLUCZ,
    "answer": dc_ids
}

finnish = requests.post(f"{REPORT_URL}", json=json)
print(finnish.json())

