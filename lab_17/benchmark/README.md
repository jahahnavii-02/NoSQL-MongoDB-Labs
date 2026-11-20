# Lab 17.2 - HNSW vs IVF Benchmark

This experiment compares FAISS HNSW and IVF approximate nearest-neighbour
indexes using 5,000 normalized 384-dimensional vectors.

## Metrics
- Index build time
- Mean query latency
- P95 query latency
- Recall@20 against exact brute-force search

## Run

From the integrated project root:

```powershell
docker build -t lab17-benchmark:1.0 -f lab17/benchmark/Dockerfile lab17/benchmark
docker run --rm -v "${PWD}/lab17:/app" lab17-benchmark:1.0
```

Results are written to `lab17/results/`.
