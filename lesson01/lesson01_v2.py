import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
import os


load_dotenv()  

response  = requests.get("****************8/")
soup = BeautifulSoup(response.text, "html.parser")


def get_question(soup: BeautifulSoup) -> str:
    question_element = soup.find('p', {'id': 'human-question'})
    if question_element:
        question_text = question_element.text.strip()
        return question_text.replace('Question:', '').strip()
    return ""

print(get_question(soup))

def get_llm_answer(question: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Return just numeric value of the year from the following question: {question}"}]
    )
    return str(response.choices[0].message.content).strip()

print(get_llm_answer(get_question(soup)))

def submit_login(session: requests.Session, username: str, password: str, answer: str) -> requests.Response:
    data={"username": username, "password": password, "answer": answer}
    
    return session.post("****************8/", data=data)


def login_process():
    session = requests.Session()
    response = session.get("****************8/")
    soup = BeautifulSoup(response.text, "html.parser")
    
    question = get_question(soup)
    answer = get_llm_answer(question)
    login_response = submit_login(
        session, 
        username="**********", 
        password="************", 
        answer=answer
        )
    
    print(f"Response status: {login_response.status_code}")
    print(f"Response text: {login_response.text}")
    
    return login_response


print(login_process())
