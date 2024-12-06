import asyncio
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from utils import send_url_to_central, analyze_instructions
from dotenv import load_dotenv
from logger import logger

load_dotenv()

ngrok_url = os.getenv("NGROK_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug(f"NGROK_URL: {ngrok_url}")
    if not ngrok_url:
        raise RuntimeError("NGROK_URL not configured")
    
    # Start registration in background task
    async def register():
        try:
            # Type assertion to handle Optional[str]
            if isinstance(ngrok_url, str):
                result = await send_url_to_central(ngrok_url)
                logger.info("=== REGISTRATION RESPONSE ===")
                logger.info(f"Full registration result: {json.dumps(result, indent=2)}")
                
                if "error" in result:
                    logger.error(f"Error registering URL: {result['error']}")
                else:
                    # Log every field from the response
                    for key, value in result.items():
                        logger.info(f"{key}: {value}")
            else:
                logger.error("NGROK_URL is not a string")
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
    
    # Start registration without awaiting
    asyncio.create_task(register())
    
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
    try:
        # Log everything about the request
        logger.info(f"Headers: {dict(request.headers)}")
        body = await request.body()
        logger.info(f"Raw body: {body.decode()}")
        
        data = await request.json()
        logger.info(f" FULL RESPONSE DATA: {json.dumps(data, indent=2)}")
        
        instruction = data.get("instruction")
        if not instruction:
            logger.warning("No instruction provided")
            return {"description": "error", "error": "No instruction provided"}
            
        logger.debug("Processing instruction: %s", instruction)
        analyzed_result = analyze_instructions(instruction)
        
        response = {"description": analyzed_result}
        logger.debug(f"Sending response: {response}")
        return response
        
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return {"description": "error", "error": str(e)}







