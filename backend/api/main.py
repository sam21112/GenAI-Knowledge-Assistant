# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from pathlib import Path

# api/main.py (top of file)
from dotenv import load_dotenv
BACKEND_DIR = Path(__file__).resolve().parents[1]   # .../backend
load_dotenv(BACKEND_DIR / ".env")
import os

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not loaded from backend/.env")
    
from api.routes import text, image, document
app = FastAPI(redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,     # ok if you DON'T use cookies; still fine to leave on
    allow_methods=["*"],        # POST/GET/OPTIONS/DELETE/PUT/PATCH
    allow_headers=["*"],        # Content-Type, Authorization, etc.
)

 
app.include_router(image.router)
app.include_router(document.router)
app.include_router(text.router)

@app.get("/")
def root():
    return {"status": "GenAI backend running"}
