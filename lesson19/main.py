import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from utils import send_url_to_central, analyze_instructions
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
        
        if not instruction:
            return JSONResponse(
                status_code=400,
                content={"error": "No instruction provided"}
        )
        
        print("\n=== Received Instruction ===")
        print(f"Raw data: {data}")
        print(f"Instruction: {instruction}")
        print("============================\n")
        
        result = analyze_instructions(instruction)
        
        return {
            "answer": result
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid JSON data: {str(e)}"}
        )




