# backend/services/rag.py
import os
from typing import List, Tuple
from openai import OpenAI
from services.vector_search import retrieve_similar

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _build_prompt(question: str, contexts: List[str]) -> str:
 
    joined = "\n\n---\n\n".join(contexts)
    return (
        "You are a helpful assistant. Answer the QUESTION using  the CONTEXT.\n"
        "If the answer isn't in the context, still answer.\n\n"
        f"CONTEXT:\n{joined}\n\nQUESTION:\n{question}"
    )

def answer_with_rag(question: str, k: int = 4) -> dict:
    # Retrieve top-k chunks
    hits: List[Tuple[str, float]] = retrieve_similar(question, k=k)  # [(text, score)]
    print("hits",hits)
    contexts = [t for (t, _s) in hits]

    # Build prompt and ask LLM
    print("context",contexts)
    prompt = _build_prompt(question, contexts)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # or another chat model you have access to
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    answer = resp.choices[0].message.content

    # Return answer + “citations”
    return {
        "answer": answer,
        "sources": [
            {"text": t[:280] + ("…" if len(t) > 280 else ""), "score": float(s)}
            for (t, s) in hits
        ],
    }
