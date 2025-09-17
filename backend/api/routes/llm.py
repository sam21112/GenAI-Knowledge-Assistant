# backend/api/routes/llm.py  (or backend/models/llm.py if you prefer)
import os
from openai import OpenAI

# Read key from env var
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_llm(prompt: str) -> str:
    # Pick any available chat model in your account.
    # "gpt-4o-mini" is a good, inexpensive default; use "gpt-4o" if you have access.
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content
