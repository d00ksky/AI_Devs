import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
URL_WYSZUKIWARKA_OSOB = os.getenv("URL_WYSZUKIWARKA_OSOB")
URL_WYSZUKIWARKA_MIEJSC = os.getenv("URL_WYSZUKIWARKA_MIEJSC")
REPORT_URL = os.getenv("REPORT_URL")
NOTE_BARBARA = os.getenv("NOTE_BARBARA")

client = OpenAI(api_key=OPENAI_API_KEY)

""" 
Json template for search query

{
 "apikey":"TWÓJ KLUCZ",
 "query": "IMIE lub MIASTO"
}
"""

note = requests.get(f"{NOTE_BARBARA}").text

#print(note)

query_json = {
    "apikey": KLUCZ,
    "query": "KRAKOW"
}

example_query = requests.post(f"{URL_WYSZUKIWARKA_OSOB}", json=query_json)
example_query_city = requests.post(f"{URL_WYSZUKIWARKA_MIEJSC}", json=query_json)

#print(example_query.json())
#print(example_query_city.json())

collected_data = {}

def collect_data_about_names(names):
    for name in names:
        print(f"Collecting data about {name}")
        query_json = {
            "apikey": KLUCZ,
            "query": name
        }
        response = requests.post(f"{URL_WYSZUKIWARKA_OSOB}", json=query_json)
        print(f"Data about {name} collected")
        print(response.json())
        collected_data[name] = response.json()
    return collected_data

def collect_data_about_cities(cities):
    for city in cities:
        print(f"Collecting data about {city}")
        query_json = {
            "apikey": KLUCZ,
            "query": city
        }
        response = requests.post(f"{URL_WYSZUKIWARKA_MIEJSC}", json=query_json)
        print(f"Data about {city} collected")
        print(response.json())
        collected_data[city] = response.json()
    return collected_data

def extract_from_note(note):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful assistant that extracts data from a note. Extract only names mentioned in the note and provide them in a list without -. Do not include any other information or words. Return only first name. Don't use polish signs - Rafał should be Rafal for example."}, {"role": "user", "content": note}]
    )
    return response.choices[0].message.content

def extract_from_data_cities(data):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful assistant that extracts data from a note. Extract only cities mentioned in the note and provide them in a list without -. Do not include any other information or words. Return only name of city. Don't use polish signs - Kraków should be Krakow for example."}, {"role": "user", "content": str(data)}]
    )
    return response.choices[0].message.content

names = extract_from_note(note)
names = str(names).split("\n")
names = [name.strip() for name in names if name.strip()]
#print(names)

collect_data_about_names(names)

#print(collected_data)
collected_data_str = str(collected_data)
#print(collected_data_str)


cities = extract_from_data_cities(collected_data_str)
#print(cities)
cities = str(cities).split("\n")
#print(cities)

def final_prompt(collected_data):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are detective that is looking for Bardara Zawadzka. You have note and a list of names and cities. In this list there are names with cities where they were last seen and cities with which people were seen. You need to find out where Bardara Zawadzka is now. Return only one city name without any other words or information. Return name without polish signs like - Kraków should be Krakow for example."}, {"role": "user", "content": f"Note: {note}\nNames: {collected_data}"}]        
    )
    return response.choices[0].message.content

answer = final_prompt(collected_data)
answer = str(answer).strip()
#print(answer)


json = {
    "task": "loop",
    "apikey": KLUCZ,
    "answer": answer
}

final_report = requests.post(f"{REPORT_URL}", json=json)

#print(final_report.json())

while "FLG" not in final_report.json():
    # Extract cities from current data
    cities = extract_from_data_cities(str(collected_data))
    cities = str(cities).split("\n")
    cities = list(set(cities))  # Remove duplicates
    
    # Get data about cities and update collected_data
    city_data = collect_data_about_cities(cities)
    collected_data.update(city_data)
    
    # Extract new names from city data
    new_names = extract_from_note(str(city_data))
    new_names = str(new_names).split("\n")
    new_names = [name.strip() for name in new_names if name.strip()]
    new_names = list(set(new_names))  # Remove duplicates
    
    # Get data about new names and update collected_data
    name_data = collect_data_about_names(new_names)
    collected_data.update(name_data)
    
    # Try to find Barbara's location
    answer = final_prompt(collected_data)
    answer = str(answer).strip()
    
    json = {
        "task": "loop",
        "apikey": KLUCZ,
        "answer": answer
    }
    final_report = requests.post(f"{REPORT_URL}", json=json)
    print(final_report.json())

