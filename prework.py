import requests


response = requests.get("***************************")
print(response.text)

data = response.text.strip().split("\n")
print(data)

API_KEY = "*********************************88"
TASK = "POLIGON"

payload = {
    "task": TASK,
    "apikey": API_KEY,
    "answer": data
}

result = requests.post("https://******************", json=payload)
print(result.json())


