from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import os, shutil, base64, mimetypes
from openai import OpenAI
from services.vector_search import add_to_index  # optional: index caption into RAG

router = APIRouter()

BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.get("/vision-status")
def vision_status():
    # Always ready when using OpenAI Vision
    return {"ready": True, "engine": "openai-vision", "error": None}

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # Save upload
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Read & base64-encode
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    mime = (mimetypes.guess_type(str(file_path))[0] or "image/jpeg")
    data_url = f"data:{mime};base64,{b64}"

    content = [
        {"type": "text", "text": "Describe this image in one concise sentence."},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": content}],
        temperature=0.2,
    )
    caption = resp.choices[0].message.content.strip()

    # (optional) index the caption so images are searchable in your RAG
    try:
        add_to_index(f"IMAGE:{file.filename}\nCAPTION:{caption}")
    except Exception:
        pass

    return {"filename": file.filename, "caption": caption, "vision_ready": True}
