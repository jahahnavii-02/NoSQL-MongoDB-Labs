# NoSQL-MongoDB-Labs

**Student:** Jahnavi S | **USN:** 24BTRCL235
**Course:** NoSQL Database Laboratory, JAIN University
**GitHub:** https://github.com/jahahnavii-02/NoSQL-MongoDB-Labs
**Docker:** https://hub.docker.com/r/jahnavii15/integrated-nosql-labs
**Current Image:** `jahnavii15/integrated-nosql-labs:2.3`

> Labs 1-18 + ThreatSentry mini-project + reports.
> Docker 2.3 only. Tag 1.9 is deprecated.

## Technologies & Architecture

- **MongoDB** - Document store, CRUD, aggregations
- **Cassandra** - Wide-column, query-oriented tables
- **Neo4j** - Graph, threats / sources / targets relationships
- **Python, FastAPI, REST API, Frontend dashboard**
- **Ingestion + Linux Agent -> API -> MongoDB | Cassandra | Neo4j**
- **Docker, Docker Compose**

## Structure
lab_01 to lab_18 /  README.md + code/ + output/
mini-project/ThreatSentry/
reports/
docs/


| Lab | Title |
|---|---|
| lab_01 | Basic NoSQL operations |
| lab_02 | Database and document operations |
| lab_03 | MongoDB fundamentals |
| lab_04 | Database operations and queries |
| lab_05 | Data modelling and CRUD |
| lab_06 | Advanced database activities |
| lab_07 | MongoDB laboratory exercises |
| lab_08 | Replication and replica sets |
| lab_09 | Database implementation and integration |
| lab_10 | Transactions and inventory management |
| lab_11 | Sharding and distributed data |
| lab_12 | Security, RBAC and TLS |
| lab_13 | Advanced NoSQL implementation |
| lab_14 | Advanced database concepts |
| lab_15 | Multi-tenant API and tenant migration |
| lab_16 | Hybrid NoSQL implementation |
| lab_17 | Integrated NoSQL application |
| lab_18 | Comparative NoSQL Threat Intelligence |

## Setup

- Docker Desktop, Git, Python 3.11+

```bash
docker pull jahnavii15/integrated-nosql-labs:2.3
docker images jahnavii15/integrated-nosql-labs:2.3
docker compose up --build
ThreatSentry: docker pull jahnavii15/threatsentry
Testing / Benchmarks
Measured: Lab 18 tables below = actual run in lab env, 100k synthetic records. Not universal.Design: Architecture / modelling = design, not performance.Synthetic: Lab 18 data is synthetic, not real threat data.QueryMongoDBCassandraNeo4jThreat history by source5.245 ms25.036 ms57.870 msTarget spread14.038 ms35.480 ms203.123 msDaily volume by type24.864 ms115.667 ms211.844 msInsertRecords/secMongoDB9136.51Cassandra1012.28Neo4j1096.34Details in lab_18/.
Security
No .env, API keys, JWT secrets, private keys, certs, or backups committed. Secrets via env vars only. See .gitignore.
Acknowledgement
Lab instructions from instructor's official course material. Peer reference: https://github.com/SOLANKYYY/No_Sql_Mongodb_work
TODO: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB
