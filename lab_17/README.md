Lab 17 — AI-Native MongoDB: Vector Search and RAG Foundations

Lab 17.1 — Simple RAG Pipeline

Objective: Build a threat-intelligence Retrieval-Augmented Generation (RAG) pipeline using MongoDB Atlas Vector Search and local Ollama models.

Workflow:

1. Prepare 3–5 threat-intelligence documents.
2. Split documents into approximately 100-word overlapping chunks.
3. Generate embeddings using Ollama.
4. Store chunks and embeddings in MongoDB Atlas.
5. Retrieve the top 3 relevant chunks using vector search.
6. Generate answers using a local Ollama language model.
7. Store conversation history and include the last 5 exchanges in subsequent prompts.

Status: Vector Search index created. End-to-end pipeline pending Atlas TLS connection resolution.

Lab 17.2 — HNSW versus IVF Benchmark

Objective: Compare HNSW and IVF approximate nearest-neighbour indexing using FAISS.

Configuration:

- Documents: 5,000
- Dimensions: 384
- Queries: 100
- Top-K: 20
- Ground truth: FAISS IndexFlatIP
- Metrics: Build time, mean latency, p95 latency and Recall@20

Methodology:

1. Generate reproducible synthetic normalized vectors.
2. Calculate exact nearest neighbours.
3. Build HNSW and IVF indexes with different parameters.
4. Measure query latency and recall.
5. Generate a latency-recall comparison graph.

Execution:

docker build -t lab17-benchmark:1.0 -f lab17/benchmark/Dockerfile lab17/benchmark

docker run --rm -v "${PWD}/lab17:/app" lab17-benchmark:1.0 python benchmark/run_benchmark.py

Actual output files:

- "results/benchmark_results.csv"
- "results/benchmark_results.json"
- "results/latency_recall_curve.png"

Note: The benchmark uses synthetic vectors rather than Wikipedia-derived embeddings. Results reflect the tested configuration and environment.

Setup

1. Install dependencies from "requirements.txt".
2. Copy ".env.example" to ".env".
3. Configure the Atlas connection URI privately in ".env".
4. Keep Ollama running with the required models installed.
5. Never commit or share ".env" or database credentials.

Project Structure

lab17/
├── benchmark/
│   ├── Dockerfile
│   ├── README.md
│   ├── requirements.txt
│   └── run_benchmark.py
├── data/
├── results/
│   ├── benchmark_results.csv
│   ├── benchmark_results.json
│   └── latency_recall_curve.png
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

Final Execution and Verification Results

Lab 17.1 – RAG Pipeline

- MongoDB Atlas connection and authentication verified successfully.
- Vector Search index "vector_index" reached Ready status.
- Five threat-intelligence document chunks generated and stored successfully.
- Embeddings generated using the local "mxbai-embed-large" model (1024 dimensions).
- Top 3 relevant documents retrieved through Atlas Vector Search.
- Answers generated using the local "llama3.2:3b" model.
- Conversation memory tested successfully using consecutive questions in the same session.

Lab 17.2 – HNSW vs IVF

- 5,000 normalized 384-dimensional vectors and 100 query vectors generated.
- Exact FAISS search used as the ground-truth reference.
- Four HNSW configurations and nine IVF configurations benchmarked.
- Build time, mean query latency, p95 latency and Recall@20 recorded.
- Actual results saved in "results/benchmark_results.csv" and "results/benchmark_results.json".
- Latency-recall visualization saved as "results/latency_recall_curve.png".
- Synthetic random vectors were used for this benchmark, not Wikipedia sentence embeddings.

Testing

- Unit tests executed using pytest.
- Result: 6 passed, 0 failed.
- One pytest/AnyIO deprecation warning was reported; it did not affect test execution.

Conclusion

Both Lab 17.1 and Lab 17.2 implementations were executed. The RAG pipeline successfully connected to MongoDB Atlas, retrieved relevant threat-intelligence documents, generated responses and demonstrated conversation memory. The vector-index benchmark produced actual HNSW and IVF performance measurements for comparison.