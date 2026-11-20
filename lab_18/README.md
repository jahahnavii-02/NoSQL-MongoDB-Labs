# Lab 18 ? Comparative NoSQL Threat Intelligence Capstone

## 1. Objective

Implement a comparative threat-intelligence workload using three NoSQL database models:

- MongoDB ? document-oriented threat storage and flexible source summaries.
- Apache Cassandra ? denormalised wide-column storage for source, target, type and date-based access.
- Neo4j ? graph representation of threat sources and reported threats, with source correlations based on shared targets.

The experiment compares query latency and insert throughput and demonstrates graph connectivity, community detection and cross-database evidence lookup.

## 2. Dataset

- Dataset size: 100,000 deterministic synthetic threat records.
- Sources: eight source names.
- Data type: generated synthetic records; these are not live downloaded threat-feed events.
- Records include threat identifiers, source, threat type, target, severity, confidence, indicator, timestamp, event date and false-positive status.

The same generated workload is used to populate the three database systems.

## 3. Database design

### MongoDB

Database: `lab18`

Collections:

- `full_threats` ? individual threat documents.
- `threat` ? one summary document per source, containing the latest 50 threats and an update timestamp.
- `lab18_insert_benchmark` ? dedicated insert-throughput benchmark records.

Indexes include:

- Compound index on `(from_source, timestamp descending)`.
- Compound index on `(target, timestamp descending)`.
- Compound index on `(event_date, threat_type)`.
- Unique index on `threat_id`.
- Index on `updated_at` in the source-summary collection.

### Apache Cassandra

Keyspace: `lab18`

Denormalised query tables:

- `threats_by_source`
- `threats_by_type`
- `threats_by_target`
- `threats_by_day`
- `insert_benchmark` ? dedicated insert benchmark table.

Each query table is designed around its corresponding partition-key access pattern.

### Neo4j

Lab 18 node labels:

- `Lab18Source`
- `Lab18Threat`
- `Lab18BenchmarkThreat` ? dedicated insert benchmark nodes.

Relationships:

- `REPORTED` ? connects a source to a threat it reported.
- `SUSPICIOUS` ? connects source pairs that share at least two distinct targets.

The suspicious-source correlation is based on shared targets, not shared indicators. The graph analysis also calculates connected components and applies deterministic Label Propagation community detection.

## 4. Benchmark methodology

Three query categories are measured on each database:

1. Threat history by source.
2. Threat spread by target.
3. Daily threat volume by date and threat type.

Each query is executed 10 times. The reported query latency is the median of the 10 measured runs.

A separate insert-throughput benchmark uses 10 rounds of 100 records per database. The reported throughput is calculated from the median round duration.

The benchmark uses the same query parameters across the three systems:

- Source: `AlienVault`
- Target: `asset-0001`
- Date: `2026-11-04`

Results are environment-dependent. They describe this execution environment and should not be treated as universal database performance rankings.

## 5. Measured query results

Median query latency from the completed 16 November 2026 execution:

| Query | MongoDB (ms) | Cassandra (ms) | Neo4j (ms) |
|---|---:|---:|---:|
| Threat history by source | 5.245 | 25.036 | 57.870 |
| Target spread | 14.038 | 35.480 | 203.123 |
| Daily volume by type | 24.864 | 115.667 | 211.844 |

MongoDB had the lowest median latency in all three measured query categories in this execution.

Each median is based on 10 runs. The result counts were 100 for threat history, 500 for target spread and 5 for daily volume.

## 6. Measured insert throughput

Median throughput from 10 rounds of 100 records:

| Database | Records per second |
|---|---:|
| MongoDB | 9,136.51 |
| Cassandra | 1,012.28 |
| Neo4j | 1,096.34 |

MongoDB had the highest measured insert throughput in this execution.

These values are measurements from this test environment, not guaranteed performance figures for other hardware or configurations.

## 7. Graph analysis

The completed graph analysis:

- Counts reported threats per source.
- Identifies source pairs sharing at least two distinct targets.
- Builds connected components from `SUSPICIOUS` relationships.
- Applies deterministic Label Propagation community detection.
- Cross-references shared-target evidence against MongoDB threat documents.
- Produces a 20-record sample marked as false positives for review.

The execution identified four suspicious source relationships:

- AbuseCH ? OpenPhish
- AlienVault ? ThreatFox
- EmergingThreats ? MalwareBazaar
- FeodoTracker ? URLhaus

Each pair had 25 shared targets in the generated dataset. The graph analysis reported four connected components and completed deterministic label propagation in two iterations.

Because the dataset is synthetic and deterministic, these detected communities demonstrate the graph-analysis workflow. They do not establish real-world coordination or malicious relationships between threat-feed providers. Shared-target overlap is an investigative signal, not proof.

## 8. Result files

Generated result files:

- `results/benchmark_results.json` ? detailed benchmark results, medians, insert throughput, graph analysis, false-positive sample and verification counts.
- `results/benchmark_summary.csv` ? query benchmark summary.

The JSON and CSV files should be kept together as evidence of the same execution.

## 9. Execution notes

The runner is located at:

`src/run_lab18.py`

It connects to the database services using environment variables. Required connection settings are supplied at runtime and must not be committed to source control or included in public documentation.

The runner supports normal execution, recovery and resume behaviour. Recovery mode preserves existing Lab 18 threat data while reconciling the generated records. Resume mode uses `LAB18_RESUME=1` to skip the main database loading stage and rerun the analysis and query benchmarks, assuming the required Lab 18 data already exists in all three databases.

The result directory is resolved relative to the Lab 18 project folder.

## 10. Verification and limitations

The completed execution verified:

| Database | Verified data | Actual count |
|---|---|---:|
| MongoDB | `full_threats` documents | 100,000 |
| MongoDB | Source summary documents | 8 |
| Cassandra | `threats_by_source` rows | 100,000 |
| Cassandra | `threats_by_type` rows | 100,000 |
| Cassandra | `threats_by_target` rows | 100,000 |
| Cassandra | `threats_by_day` rows | 100,000 |
| Neo4j | `Lab18Threat` nodes | 100,000 |
| Neo4j | `Lab18Source` nodes | 8 |

All database count checks passed.

The recorded main dataset load time was 2,310.347 seconds (approximately 38 minutes and 30 seconds). This is the recorded execution time and is environment-dependent.

Insert-throughput tests use dedicated benchmark storage rather than being counted as part of the original 100,000-record dataset.

No 1-million, 10-million or 100-million record performance tests are claimed by this result set. Any discussion of those scales must be clearly identified as a projection unless separate experiments are conducted.

## 11. Conclusion

Lab 18 demonstrates the use of document, wide-column and graph databases for a common 100,000-record synthetic threat-intelligence workload.

In this execution, MongoDB recorded the lowest median latency across all three query categories and the highest measured insert throughput. Cassandra and Neo4j demonstrated their respective wide-column and graph-based data models, query patterns and analysis capabilities.

The graph workflow identified four source pairs with shared-target overlap, generated four connected components and performed deterministic label propagation. These results demonstrate the analysis process, not real-world attribution.

The results illustrate how database data models and query access patterns affect observed performance. Conclusions are limited to the dataset, queries and execution environment used in this experiment.
