from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to my API madafaka!"}

@app.post("/instructions")
async def instructions(request: Request):
    try:
        data = await request.json()
        print("Received data:", data)
        return {"message": "Report received", "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid JSON data: {str(e)}"}
        )
