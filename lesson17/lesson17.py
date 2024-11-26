import time
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
import shutil
import json
load_dotenv()

KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
REPORT_URL = os.getenv("REPORT_URL")
LAB_DATA_URL = os.getenv("LAB_DATA_URL")
FINETUNED_MODEL_ID = os.getenv("FINETUNED_MODEL_ID")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



'''commenting out following code as it is only used for downloading and unpacking the lab data and then uploading it to openai and fine tuning model



zip_file = requests.get(f"{LAB_DATA_URL}")
print(f"Zip file: {zip_file}")
with open("lab_data.zip", "wb") as file:
    print(f"Writing zip file to disk")
    file.write(zip_file.content)

shutil.unpack_archive("lab_data.zip", "lab_data")
print(f"Unpacked archive")

def label_data(input_file_path, completion, output_file_path):
    print(f"Labeling data from {input_file_path}")
    with open(input_file_path, "r", encoding="utf-8") as input_file, \
         open(output_file_path, "a", encoding="utf-8") as output_file:
        print(f"Writing to {output_file_path}")
        for line in input_file:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that classifies sequences of numbers."},
                {"role": "user", "content": line.strip()},
                {"role": "assistant", "content": completion}
            ]
            json_obj = {"messages": messages}
            output_file.write(json.dumps(json_obj) + '\n')
        print(f"Finished labeling data from {input_file_path}")

if not os.path.exists("labeled_data.jsonl"):
    print("Labeling data")
    label_data("lab_data/correct.txt", "correct", "labeled_data.jsonl")
    label_data("lab_data/incorrect.txt", "incorrect", "labeled_data.jsonl")
    print("Finished labeling data")
else:
    print("Labeled data already exists")


# upload labeled data to openai

response = client.files.create(
    file=open("labeled_data.jsonl", "rb"), 
    purpose="fine-tune"
)

print(f"Response from file upload: {response}")
training_file_id = response.id
print(f"Training file ID: {training_file_id}")


fine_tuning_job = client.fine_tuning.jobs.create(
    training_file=training_file_id,
    model="gpt-4o-mini-2024-07-18",
    suffix="ai_devs-17"
)

print(f"Fine tuning job created: {fine_tuning_job}")

while fine_tuning_job.status != "succeeded":
    print(f"Fine tuning job status: {fine_tuning_job.status}")
    time.sleep(10)
    fine_tuning_job = client.fine_tuning.jobs.retrieve(fine_tuning_job.id)

print(f"Fine tuning job completed: {fine_tuning_job}")


# end of commented out code

'''

verification_data = open("lab_data/verify.txt", "r").read().splitlines()
print(verification_data)

def openai_call(prompt):
    response = client.chat.completions.create(
        model=f"{FINETUNED_MODEL_ID}",
        messages=[
            {"role": "system", "content": "You are expert in number sequences. You are given a sequence of numbers and you need to determine which sequences are correct. Provide two digit identifiers of correct sequences separated by commas."},
            {"role": "user", "content": f"Here is the data, please provide correct identifiers: {prompt}"}
        ],
    )
    return response.choices[0].message.content

correct_identifiers = []
for line in verification_data:
    result = openai_call(line)
    print(result)
    if result == "correct":
        correct_identifiers.append(line.split("=")[0])
    

print(correct_identifiers)
answer = []
for identifier in correct_identifiers:
    answer.append(f"{identifier.strip()}")

print(answer)

json_data = {
    "task": "research",
    "apikey": KLUCZ,
    "answer": answer
}


final_answer = requests.post(f"{REPORT_URL}", json=json_data)
print(final_answer.json())