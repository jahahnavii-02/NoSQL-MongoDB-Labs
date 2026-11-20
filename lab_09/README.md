# MongoDB Lab 09 — Write Concern and Network Partition

## Experiments

### Lab 9.1 — Measure Write Concern Latency
Measures insertion latency for write concerns and compares journal settings.

Script: `lab9_1/lab9.1_write_concern.py`

Results: `lab9_1/lab9_1_results.csv`

### Lab 9.2 — Simulate a Network Partition
Tests writes with `w:1` and `w:majority`, observes replica-set health, and records recovery behavior.

Script: `lab9_2/lab9.2_partition_test.py`

Results are written to `lab9_2/lab9_2_results.csv` when the script runs.

## Build

```powershell
docker build -t YOUR_DOCKERHUB_USERNAME/mongodb-lab09:1.0 .
```

## Demonstration

The MongoDB replica set must be running separately.

Run Lab 9.1:

```powershell
docker run --rm YOUR_DOCKERHUB_USERNAME/mongodb-lab09:1.0 lab9_1/lab9.1_write_concern.py
```

Run Lab 9.2:

```powershell
docker run --rm YOUR_DOCKERHUB_USERNAME/mongodb-lab09:1.0 lab9_2/lab9.2_partition_test.py
```

Configure the MongoDB URI for the environment in which the container runs. For Docker Desktop on Windows, `host.docker.internal` can reach services published on the host.

## Notes

- The network partition is created separately using Docker network commands.
- Record actual experiment outputs; do not treat example outcomes as measured results.
- MongoDB does not support the literal write concern `w: "all"`. This project uses `w: 3` to request acknowledgment from all three data-bearing members in the four-member replica set that includes an arbiter.