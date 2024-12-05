import asyncio
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from utils import send_url_to_central, analyze_instructions
from dotenv import load_dotenv
import logging
logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
# Add a simple stream handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

load_dotenv()

ngrok_url = os.getenv("NGROK_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug(f"NGROK_URL: {ngrok_url}")
    if not ngrok_url:
        raise RuntimeError("NGROK_URL not configured")
    
    result = await send_url_to_central(ngrok_url)
    logger.debug(f"Send URL result: {result}")
    if "error" in result:
        logger.error(f"Error registering URL: {result['error']}")
    
    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    logger.debug("Received request to root")
    return {"message": "Welcome to my API madafaka!"}

@app.get("/instructions")
async def instructions_get():
    logger.debug("Received request to instructions, sending test response")
    return {"description": "zielona trawa"} 

@app.post("/instructions")
async def instructions(request: Request):
    logger.debug("Received request to instructions")
    logger.debug("Headers: %s", dict(request.headers))
    
    try:
        body = await request.body()
        logger.debug("Raw body: %s", body.decode())
            
        data = await request.json()
        logger.debug("Parsed JSON: %s", data)
            
        instruction = data.get("instruction")
        if not instruction:
            print(data)
            logger.debug("No instruction provided - sending test response")
            return {"description": "zielona trawa"}
                
        logger.debug("Processing instruction: %s", instruction)
        analyzed_result = analyze_instructions(instruction)
        logger.debug("Analyzed result: %s", analyzed_result)
            
    
        logger.debug("Sending response: %s", {"description": analyzed_result})
        return {"description": analyzed_result}
        
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return {"description": "error", "error": str(e)}







