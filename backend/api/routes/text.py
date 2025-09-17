from fastapi import APIRouter, Form
from .llm import query_llm
 
from services.rag import answer_with_rag

router = APIRouter()

@router.post("/text-query")  # no trailing slash
async def handle_text_query(prompt: str = Form(...)):
    result = answer_with_rag(prompt, k=4)  # {"answer": "...", "sources":[...]}
    return result
@router.post("/text-query-raw")
async def handle_text_query(prompt: str = Form(...)):
    result = query_llm(prompt)
    return {"response": result}
