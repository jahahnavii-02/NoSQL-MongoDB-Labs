# NoSQL-MongoDB-Labs

**Student:** Jahnavi S | **USN:** 24BTRCL235
**Course:** NoSQL Database Laboratory, JAIN University
**GitHub:** https://github.com/jahahnavii-02/NoSQL-MongoDB-Labs
**Docker:** https://hub.docker.com/r/jahnavii15/integrated-nosql-labs

---

## Technologies & Architecture

- MongoDB - Document store, CRUD, aggregations
- Cassandra - Wide-column, query-oriented tables
- Neo4j - Graph, threats / sources / targets relationships
- Python, FastAPI, REST API, Frontend dashboard
- Ingestion + Linux Agent -> API -> MongoDB | Cassandra | Neo4j
- Docker, Docker Compose

---

## Project Structure

NoSQL-MongoDB-Labs/
README.md
docker-compose.yml
lab_01 to lab_18 / README.md + code/ + output/
mini-project/ThreatSentry/
reports/
docs/

Each lab_XX folder contains README.md + code/ + output/

---

## Lab Mapping

lab_01 - Basic NoSQL operations
lab_02 - Database and document operations
lab_03 - MongoDB fundamentals
lab_04 - Database operations and queries
lab_05 - Data modelling and CRUD
lab_06 - Advanced database activities
lab_07 - MongoDB laboratory exercises
lab_08 - Replication and replica sets
lab_09 - Database implementation and integration
lab_10 - Transactions and inventory management
lab_11 - Sharding and distributed data
lab_12 - Security, RBAC and TLS
lab_13 - Advanced NoSQL implementation
lab_14 - Advanced database concepts
lab_15 - Multi-tenant API and tenant migration
lab_16 - Hybrid NoSQL implementation
lab_17 - Integrated NoSQL application
lab_18 - Comparative NoSQL Threat Intelligence

---

## Prerequisites

- Python 3.11+ - Lab scripts
- MongoDB 7.0+ - Primary database
- Docker Latest - Container-based labs
- mongosh 2.0+ - Shell scripts
- Cassandra Latest - Polyglot labs (16, 18)
- Neo4j Latest - Graph labs (16, 18)

---

## Running the Labs

Single lab:
Open the lab folder and follow its README. Example: lab_05/

Replica Set labs (08, 09):
These require a running 3-node replica set. Use the Docker setup in lab_08/

Docker:
docker pull jahnavii15/integrated-nosql-labs:2.3
docker compose up --build

---

## Mini Project - ThreatSentry

ThreatSentry is the capstone mini-project of this course - a polyglot threat-intelligence platform.

Ingestion + Linux Agent -> FastAPI -> MongoDB | Cassandra | Neo4j -> Dashboard

- MongoDB - Threat history and documents
- Cassandra - Wide-column analytics
- Neo4j - Threat to Source to Target graph
- FastAPI + Dashboard - API and visualisation

Source: mini-project/ThreatSentry/
Full report: reports/Mini_Project_Report_ThreatSentry_AI.pdf

---

## Security

No .env, API keys, JWT secrets, private keys, certs, or backups are committed. Secrets via environment variables only. See .gitignore.

---

## Docker Images

Current Image: jahnavii15/integrated-nosql-labs:2.3
Tag 1.9 is deprecated. Use Docker 2.3 only.

Main labs image:
docker pull jahnavii15/integrated-nosql-labs:2.3
docker images jahnavii15/integrated-nosql-labs:2.3
docker compose up --build

ThreatSentry image:
docker pull jahnavii15/threatsentry

---

## Reports

Lab Experiments 01-18:
reports/Lab_Experiments_Report_Chapters_1-18.pdf

Mini Project - ThreatSentry AI:
reports/Mini_Project_Report_ThreatSentry_AI.pdf
