from fastapi import APIRouter, UploadFile, File
import os, shutil, json
from kafka import KafkaProducer, KafkaConsumer
from pathlib import Path

router = APIRouter()
BACKEND_ROOT = Path(__file__).resolve().parents[2]   # .../backend
UPLOAD_DIR = BACKEND_ROOT / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

producer = None  # global placeholder

def get_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return producer

@router.post("/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    get_producer().send("doc-upload", {"filename": file.filename, "path": file_path})
    return {"status": "submitted", "filename": file.filename}
