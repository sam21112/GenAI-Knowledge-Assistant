 
 # backend/services/vector_search.py
import os, json
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from openai import OpenAI
from utils.file_loader import chunk_text

# ---- Paths ----
BACKEND_ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = BACKEND_ROOT / "data" / "index"
EMBS_PATH = INDEX_DIR / "embs.npy"
TEXTS_PATH = INDEX_DIR / "texts.jsonl"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# ---- OpenAI client (env var) ----
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- In-memory state ----
_TEXTS: List[str] = []
_EMBS: Optional[np.ndarray] = None
_LOADED = False

# ---- IO helpers ----
def _save_index() -> None:
    # embeddings
    if _EMBS is not None:
        tmp = EMBS_PATH.with_suffix(".npy.tmp")
        with open(tmp, "wb") as f:
            np.save(f, _EMBS)
        tmp.replace(EMBS_PATH)
    # texts
    tmp_txt = TEXTS_PATH.with_suffix(".jsonl.tmp")
    with open(tmp_txt, "w", encoding="utf-8") as f:
        for t in _TEXTS:
            f.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
    tmp_txt.replace(TEXTS_PATH)

def _load_index() -> None:
    global _TEXTS, _EMBS, _LOADED
    _TEXTS = []
    if TEXTS_PATH.exists():
        with open(TEXTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    _TEXTS.append(json.loads(line)["text"])
                except Exception:
                    continue
    _EMBS = None
    if EMBS_PATH.exists():
        with open(EMBS_PATH, "rb") as f:
            _EMBS = np.load(f)
    _LOADED = True

def _ensure_loaded() -> None:
    global _LOADED
    if not _LOADED:
        _load_index()

# ---- Embeddings ----
def _embed(texts: List[str]) -> List[np.ndarray]:
    if not texts:
        return []
    resp = _client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [np.asarray(d.embedding, dtype="float32") for d in resp.data]

def _append_emb(vec: np.ndarray) -> None:
    global _EMBS
    vec = vec.reshape(1, -1)
    _EMBS = vec if _EMBS is None else np.vstack([_EMBS, vec])

# ---- Public API ----
def add_to_index(full_text: str, chunk_size: int = 800, overlap: int = 200) -> int:
    """
    Called by the Kafka worker after parsing a PDF.
    Persists updates so the API process can see them.
    """
    text = (full_text or "").strip()
    if not text:
        return 0
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap) or []
    if not chunks:
        return 0
    embs = _embed(chunks)
    for ch, emb in zip(chunks, embs):
        _TEXTS.append(ch)
        _append_emb(emb)
    _save_index()
    return len(chunks)

def retrieve_similar(query: str, k: int = 3) -> List[Tuple[str, float]]:
    """
    Called by the API at query time. Loads from disk if needed.
    """
    _ensure_loaded()
    
    if _EMBS is None or not _TEXTS:
        return []
    q = _embed([query])[0]
    A = _EMBS / (np.linalg.norm(_EMBS, axis=1, keepdims=True) + 1e-8)
    qn = q / (np.linalg.norm(q) + 1e-8)
    sims = A @ qn
    idx = sims.argsort()[-k:][::-1]
    return [(_TEXTS[i], float(sims[i])) for i in idx]

def reload_index() -> dict:
    _load_index()
    return {"texts": len(_TEXTS), "embs": 0 if _EMBS is None else int(_EMBS.shape[0])}
