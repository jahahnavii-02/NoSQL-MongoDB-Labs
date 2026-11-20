import csv
import json
import os
import time
from pathlib import Path

import faiss
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
N = 5000
DIM = 384
N_QUERIES = 100
TOP_K = 20
RESULTS = Path("/app/results")
DATA = Path("/app/data")

RESULTS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

rng = np.random.default_rng(SEED)

# Reproducible synthetic document embeddings.
vectors = rng.standard_normal((N, DIM)).astype("float32")
queries = rng.standard_normal((N_QUERIES, DIM)).astype("float32")

faiss.normalize_L2(vectors)
faiss.normalize_L2(queries)

# Exact brute-force ground truth.
exact = faiss.IndexFlatIP(DIM)
exact.add(vectors)
_, ground_truth = exact.search(queries, TOP_K)

np.save(DATA / "documents_5000.npy", vectors)
np.save(DATA / "queries_100.npy", queries)

results = []

def evaluate(index, name, build_seconds, parameters):
    latencies = []
    recalls = []

    for i in range(N_QUERIES):
        start = time.perf_counter()
        _, ids = index.search(queries[i:i+1], TOP_K)
        elapsed = (time.perf_counter() - start) * 1000

        latencies.append(elapsed)
        found = set(ids[0].tolist())
        expected = set(ground_truth[i].tolist())
        recalls.append(len(found & expected) / TOP_K)

    row = {
        "index": name,
        "parameters": parameters,
        "build_time_seconds": round(build_seconds, 6),
        "mean_latency_ms": round(float(np.mean(latencies)), 6),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 6),
        "mean_recall_at_20": round(float(np.mean(recalls)), 6),
        "queries": N_QUERIES,
        "documents": N,
        "dimensions": DIM
    }

    results.append(row)
    print(json.dumps(row, indent=2))

# HNSW configurations.
for M, efc in [(16, 100), (16, 200), (32, 100), (32, 200)]:
    start = time.perf_counter()

    index = faiss.IndexHNSWFlat(DIM, M, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = efc
    index.add(vectors)

    build_time = time.perf_counter() - start
    index.hnsw.efSearch = 64

    evaluate(
        index,
        "HNSW",
        build_time,
        {"M": M, "efConstruction": efc, "efSearch": 64}
    )

# IVF configurations.
for nlist in [50, 100, 200]:
    start = time.perf_counter()

    quantizer = faiss.IndexFlatIP(DIM)
    index = faiss.IndexIVFFlat(
        quantizer, DIM, nlist, faiss.METRIC_INNER_PRODUCT
    )
    index.train(vectors)
    index.add(vectors)

    build_time = time.perf_counter() - start

    for nprobe in sorted(set([max(1, nlist // 20), max(1, nlist // 5), nlist])):
        index.nprobe = nprobe

        evaluate(
            index,
            "IVF",
            build_time,
            {"nlist": nlist, "nprobe": nprobe}
        )

# Save CSV and JSON results.
csv_path = RESULTS / "benchmark_results.csv"

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

with (RESULTS / "benchmark_results.json").open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# Latency-recall trade-off graph.
plt.figure(figsize=(10, 6))

for row in results:
    plt.scatter(
        row["mean_latency_ms"],
        row["mean_recall_at_20"],
        label=f'{row["index"]} {row["parameters"]}'
    )

plt.xlabel("Mean query latency (ms)")
plt.ylabel("Recall@20")
plt.title("HNSW vs IVF: Latency–Recall Trade-off")
plt.grid(True)
plt.legend(fontsize=7)
plt.tight_layout()
plt.savefig(RESULTS / "latency_recall_curve.png", dpi=180)
plt.close()

print("\nBENCHMARK COMPLETED")
print("Documents:", N)
print("Dimensions:", DIM)
print("Queries:", N_QUERIES)
print("Configurations:", len(results))
print("CSV:", csv_path)
print("JSON:", RESULTS / "benchmark_results.json")
print("Graph:", RESULTS / "latency_recall_curve.png")
