import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from lesson19 import send_url_to_central
from dotenv import load_dotenv

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Force reload environment variables
    load_dotenv(override=True)
    ngrok_url = os.getenv("NGROK_URL")
    if ngrok_url:
        print(f"Using NGROK URL: {ngrok_url}")
        send_url_to_central(ngrok_url)

@app.get("/")
async def root():
    return {"message": "Welcome to my API madafaka!"}

@app.post("/instructions")
async def instructions(request: Request):
    try:
        data = await request.json()
        instruction = data.get("instruction")
        
        print("\n=== Received Instruction ===")
        print(f"Raw data: {data}")
        print(f"Instruction: {instruction}")
        print("============================\n")
        
        return {
            "received_instruction": instruction,
            "raw_data": data
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid JSON data: {str(e)}"}
        )




