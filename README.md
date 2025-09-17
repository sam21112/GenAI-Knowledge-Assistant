GenAI Knowledge Assistant

<img width="1358" height="609" alt="Screenshot 2025-09-17 at 7 47 46 PM" src="https://github.com/user-attachments/assets/fcde5486-dd7e-44bc-99d5-a322bf0d85ff" />
<img width="1436" height="628" alt="Screenshot 2025-09-17 at 7 47 06 PM" src="https://github.com/user-attachments/assets/017057c1-f4b3-494b-a121-e1ec38404ebd" />

A production-style, multimodal RAG system: streaming ingestion (Kafka), embedding + retrieval, grounded chat with citations, image captioning, and a clean API + React frontend. Built to be swapped across model providers and vector stores, and deployable on Docker/Kubernetes.

✨ What it does

RAG over your private knowledge (PDFs/Docs/Images): uploads → chunk & embed → store → ask grounded questions with citations.

Multimodal: image uploads are captioned (OpenAI Vision by default; optional local Transformers) and indexed into the same knowledge base.

Streaming ingestion (optional): Kafka decouples uploads from heavy processing to keep the API snappy.

APIs you own: clean REST for /upload-doc, /upload-image, /text-query, and /search.

Front-end: React app to test chat, uploads, and status.

 
🏗 Architecture (high level)
flowchart LR
    FE[React Frontend] -->|/text-query /upload-doc /upload-image| API[FastAPI Backend]
    API -->|enqueue| K[Kafka (optional)]
    API -->|direct index (simple mode)| IDX[(On-disk Index)]
    K --> W[Worker(s)]
    W -->|parse/embed| IDX
    API -->|retrieve top-k| IDX
    API -->|LLM with context| LLM[(Chat Model)]
    API --> FE


Backend: FastAPI + modular routes (api/routes)

RAG: simple on-disk vector store (backend/data/index) using OpenAI Embeddings; swap to Chroma/Qdrant/Pinecone as needed

Workers: kafka_worker.py (docs) and optional image_worker.py

Vision: default = OpenAI Vision (no heavy local deps), optional = HF vit-gpt2-image-captioning

Frontend: React client to exercise all endpoints

📂 Repository layout
GenAI Knowledge Assistant/
├── backend/
│   ├── api/
│   │   ├── main.py             # loads .env, mounts routes, CORS
│   │   └── routes/
│   │       ├── text.py         # POST /text-query, GET /search
│   │       ├── document.py     # POST /upload-doc (Kafka producer)
│   │       ├── image.py        # POST /upload-image (Vision)
│   │       └── llm.py          # lazy OpenAI client + query_llm()
│   ├── services/
│   │   ├── rag.py              # builds context + calls LLM
│   │   └── vector_search.py    # chunk/embeddings/index (disk)
│   ├── utils/
│   │   └── file_loader.py      # PDF parsing, chunking
│   ├── kafka_worker.py         # consumes doc-upload -> index
│   ├── image_worker.py         # (optional) consumes image-upload -> caption + index
│   ├── requirements.txt
│   ├── data/                   # generated: embeddings/texts
│   └── uploads/                # uploaded files
└── frontend/
    ├── package.json
    └── src/App.js

⚙️ Tech choices (with Core-style rigor)

LLM provider abstraction: OpenAI by default; lazy client, model via env (OPENAI_CHAT_MODEL) so you can flip to other providers.

RAG:

Chunking: overlap + size tunable, stored alongside embeddings to permit re-ranking later.

Vector math: cosine similarity with normalization; designed to swap to ANN/vector DB easily.

Ingestion: Kafka topic per modality (doc-upload, image-upload) for durability and scale-out workers.

Observability: logs at each stage; easy to add OpenTelemetry tracing.

Deployment: Dockerfile + K8s manifests (samples below); stateless API pods, durable index via PVC or managed vector DB.

Security: .env never committed; CORS locked to localhost:3000 in dev; clear privacy notes.

🚀 Quickstart (5 minutes)
1) Backend
cd backend
python -m venv .venv && source .venv/bin/activate    # or conda
pip install -r requirements.txt
cp .env.example .env
# edit .env -> set OPENAI_API_KEY=sk-...
uvicorn api.main:app --reload
# → http://127.0.0.1:8000


Env (.env)

OPENAI_API_KEY=sk-REPLACE_ME
OPENAI_CHAT_MODEL=gpt-4o-mini
# Optional: OPENAI_VISION_MODEL=gpt-4o-mini

2) Frontend
cd ../frontend
npm install
npm start
# → http://localhost:3000

3) Try it

Ask: type a question in the frontend (it calls POST /text-query).

Upload a PDF: it hits POST /upload-doc, then worker indexes it (Kafka optional—see “Lite mode” below).

Upload an image: POST /upload-image captions via OpenAI Vision and indexes the caption.

Lite mode (no Kafka): the API can index directly. If you prefer that, wire document.py to call add_to_index() inline (commented snippet included in code).

🔌 API Endpoints

GET / → health

POST /text-query (Form: prompt) → { answer, sources[] }

GET /search?q=...&k=4 → top chunks with scores (debug)

POST /upload-doc (multipart file) → enqueues to Kafka (or indexes inline)

POST /upload-image (multipart file) → captions + indexes; {filename, caption}

GET /vision-status → { ready, engine, error }

POST /reload-index → force reload on API (debug)

cURL examples

curl -X POST http://127.0.0.1:8000/text-query \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "prompt=Summarize my resume's backend experience."

curl -F "file=@/abs/path/file.pdf" http://127.0.0.1:8000/upload-doc
curl -F "file=@/abs/path/image.jpg" http://127.0.0.1:8000/upload-image

curl "http://127.0.0.1:8000/search?q=vector db choice&k=3"

🧠 RAG details

Embedding model: text-embedding-3-small (good cost/quality tradeoff).

Index persistence: backend/data/index/texts.jsonl + embs.npy. The API auto-reloads when files change, so worker and API stay in sync across processes.

Citation strategy: return top-k chunks and show a preview; easy to wire to source file/byte offsets.

Swap to a real vector DB: implement the same interface in services/vector_search.py (adders + retriever). Suggested: Chroma for dev; Qdrant or Pinecone for prod.

🖼 Multimodal (images)

Default: OpenAI Vision (gpt-4o-mini), no heavy local deps; great dev UX.

Optional: local Transformers (nlpconnect/vit-gpt2-image-captioning) with lazy background load, but heavier on laptops.

Indexing: store IMAGE:<filename>\nCAPTION:<caption> so images become searchable in text queries.

☁️ Optional: Kafka ingestion
# Start Kafka locally (example with Homebrew)
brew services start zookeeper
brew services start kafka
kafka-topics --create --topic doc-upload --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
kafka-topics --create --topic image-upload --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Run worker
cd backend
python kafka_worker.py
# (optional) python image_worker.py


Why Kafka? It decouples uploads from heavy parsing/embedding, provides back-pressure, and lets you scale horizontally with multiple workers.

📦 Docker (local)

Backend Dockerfile (already included)

FROM python:3.10-slim
WORKDIR /app
COPY backend/ /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


Run

docker build -t genai-backend ./backend
docker run --rm -p 8000:8000 --env-file backend/.env -v "$(pwd)/backend/data:/app/data" genai-backend


For local dev, we keep the simple on-disk index mounted to persist across container restarts. For prod, use a managed vector DB.

☸️ Kubernetes (sketch)

API: stateless Deployment + Service

Index: PVC (if using on-disk) or managed vector DB

Workers: separate Deployment(s) consuming Kafka

Secrets: mount OPENAI_API_KEY via Secret + envFrom

Observability: OpenTelemetry Collector sidecar or DaemonSet

apiVersion: apps/v1
kind: Deployment
metadata: { name: genai-api }
spec:
  replicas: 2
  selector: { matchLabels: { app: genai-api } }
  template:
    metadata: { labels: { app: genai-api } }
    spec:
      containers:
      - name: api
        image: ghcr.io/you/genai-backend:main
        ports: [{ containerPort: 8000 }]
        env:
        - name: OPENAI_API_KEY
          valueFrom: { secretKeyRef: { name: openai, key: key } }
        volumeMounts:
        - name: index
          mountPath: /app/data
      volumes:
      - name: index
        persistentVolumeClaim: { claimName: genai-index-pvc }
---
apiVersion: v1
kind: Service
metadata: { name: genai-api }
spec:
  selector: { app: genai-api }
  ports: [{ port: 80, targetPort: 8000 }]

🔒 Security & privacy

Secrets via .env (never committed). For CI/K8s, use Secret managers.

CORS restricted in dev; configure allowed origins for prod.

If privacy requires, switch Vision/Embeddings to local or private providers; the module boundaries make this straightforward.

📈 Observability & evals (hooks)

Log retrieval scores & latency; add OpenTelemetry (opentelemetry-instrumentation-fastapi) for traces.

Add regression evals (faithfulness, answerability) against a small golden set to catch prompt/index changes.

Token/cost logging (if using OpenAI) to track spend.

🧪 Testing

Unit: chunking & retrieval math (deterministic).

Integration: upload → worker → index → query returns non-empty hits.

Load: Locust/k6 to exercise /text-query with retrieval only (mock LLM) to benchmark infra.

🧭 Roadmap

🔁 Hybrid search (BM25 + vector, with reranking)

🧩 Structured tool use (e.g., SQL/db connectors with guarded function calling)

🔐 Multi-tenant ACLs & row-level security on metadata

🧠 Re-ranking (bge-reranker/minilm) to improve grounding

🗂 Chunk-source offsets & page thumbnails in citations

🧪 Evals + CI gating

🧰 Troubleshooting

CORS 307/blocked: ensure allow_origins includes your frontend origin (http://localhost:3000).

OPENAI_API_KEY missing: verify backend/.env; ensure load_dotenv() runs before importing routes.

No search hits: check that backend/data/index/embs.npy and texts.jsonl exist and are non-empty; restart worker and re-upload.

Vision slow: use OpenAI Vision (default); local Transformers require large downloads and Torch init.
