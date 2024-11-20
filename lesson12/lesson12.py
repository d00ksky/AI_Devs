import time
import requests
import zipfile
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
KLUCZ = os.getenv("KLUCZ")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
REPORT_URL = os.getenv("REPORT_URL")

    
vector_stores = client.beta.vector_stores.list()

if VECTOR_STORE_ID not in [store.id for store in vector_stores]:
    vector_store = client.beta.vector_stores.create(name="AI_devs_Kuba")
    VECTOR_STORE_ID = vector_store.id
    print("Created new vector store:", VECTOR_STORE_ID)
else:
    vector_store_id = VECTOR_STORE_ID
    print("Using existing vector store:", vector_store_id)

openai_assistant_id = OPENAI_ASSISTANT_ID
vector_store_id = VECTOR_STORE_ID
print(f"openai_assistant_id: {openai_assistant_id}")
print(f"vector_store_id: {vector_store_id}")



if OPENAI_ASSISTANT_ID not in [assistant.id for assistant in client.beta.assistants.list()]:
    openai_assistant = client.beta.assistants.create(
        name="AI_devs_Kuba", 
        instructions="""You are a helpful assistant that searches through reports for information about weapon prototype theft. 
        When asked about the date of the theft, return ONLY the date in YYYY-MM-DD format from the report that mentions it.
        Look for keywords like 'kradzież', 'prototyp', 'broń' in the reports.""", 
        model="gpt-4-turbo-preview",
        tool_resources={"file_search": {"vector_store_ids": [str(VECTOR_STORE_ID)]}}
        )
    openai_assistant_id = openai_assistant.id
    print(openai_assistant_id)
else:
    client.beta.assistants.update(
        assistant_id=OPENAI_ASSISTANT_ID,
        instructions="""You are a helpful assistant that searches through reports for information about weapon prototype theft. 
        When asked about the date of the theft, return ONLY the date in YYYY-MM-DD format from the report that mentions it.
        Look for keywords like 'kradzież', 'prototyp', 'broń' in the reports.""",
        tool_resources={"file_search": {"vector_store_ids": [str(VECTOR_STORE_ID)]}},
        model="gpt-4-turbo-preview"
    )
    print("Assistant updated")


def add_date_to_file(file_name):
    date = file_name.split(".")[0]
    file_path = f"pliki_z_fabryki/weapons_tests/do-not-share/{file_name}"
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    new_content = f"Data raportu: {date}\nRaport:\n{content}"
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(new_content)
        
        


def add_document_to_vector_store(document):
    # Upload file
    with open(document, "rb") as file:
        uploaded_file = client.files.create(file=file, purpose="assistants")
    
    # Add to vector store
    client.beta.vector_stores.files.create(
        vector_store_id=str(vector_store_id),
        file_id=uploaded_file.id
    )
    
    # Wait for processing
    while True:
        status = client.beta.vector_stores.files.retrieve(
            vector_store_id=str(vector_store_id),
            file_id=uploaded_file.id
        )
        if status.status == 'completed':
            break
        time.sleep(1)
    
    return uploaded_file.id
    

def query_assistant(query):
    thread = client.beta.threads.create()
    thread_id = thread.id
    
    # Create message
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=query
    )
    
    # Create run with file search tool and vector store
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=str(openai_assistant_id),
    )
    
    # Wait for completion
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        time.sleep(1)
    
    # Get response
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    if messages.data:
        first_message = messages.data[0]
        if first_message.content:
            for content in first_message.content:
                if content.type == 'text':
                    return content.text.value
    
    return "No response found"

    
    

if not os.path.exists("pliki_z_fabryki.zip"):
    response_zip = requests.get("*************************************************")

    with open("pliki_z_fabryki.zip", "wb") as file:
        file.write(response_zip.content)
else:
    print("Pliki już istnieją") 

def unzip_files():
    with zipfile.ZipFile("pliki_z_fabryki.zip", "r") as zip_ref:
        zip_ref.extractall("pliki_z_fabryki")

def unzip_weapons_files():
    zip_password = "1670"
    with zipfile.ZipFile("pliki_z_fabryki/weapons_tests.zip", "r") as zip_ref:
        zip_ref.extractall("pliki_z_fabryki/weapons_tests", pwd=zip_password.encode())
    
unzip_files()
unzip_weapons_files()


for file in os.listdir("pliki_z_fabryki/weapons_tests/do-not-share"):
    print(file)
    add_date_to_file(file)
    add_document_to_vector_store(f"pliki_z_fabryki/weapons_tests/do-not-share/{file}")
    print(f"Added file: {file} to vector store")
    time.sleep(1)
    

finnish = query_assistant("Znajdź w raportach wzmiankę o kradzieży prototypu broni i zwróć TYLKO datę raportu w formacie YYYY-MM-DD.")
print(finnish)

json = json = {
            "task": "wektory", 
            "apikey": KLUCZ, 
            "answer": finnish
        }
sent_finnish = requests.post(f"{REPORT_URL}", json=json)
print(sent_finnish.json())


def test_vector_store_access():
    # List all files in vector store
    files = client.beta.vector_stores.files.list(
        vector_store_id=str(vector_store_id)
    )
    print(f"\nFiles in vector store: {len(files.data)} files found")
    for file in files.data:
        print(f"- {file.id}: {file.status}")
    
    # Make a test query
    test_response = query_assistant(
        "Please list all files you can access and their dates. Return only the filenames and dates."
    )
    print("\nTest query response:")
    print(test_response)

# Add this after your file processing loop
test_vector_store_access()