from fastapi import FastAPI

app = FastAPI()

@app.get("/instructions")
async def instructions_get():
    return {"description": "trawa"}