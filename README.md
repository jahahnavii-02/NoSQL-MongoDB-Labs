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

| Lab | Title | Folder |
| --- | --- | --- |
| Lab 01 | Introduction to NoSQL | lab_01/ |
| Lab 02 | MongoDB Setup & Basics | lab_02/ |
| Lab 03 | MongoDB CRUD Operations | lab_03/ |
| Lab 04 | MongoDB Query Operators | lab_04/ |
| Lab 05 | MongoDB Aggregation Pipeline | lab_05/ |
| Lab 06 | MongoDB Indexing & Performance | lab_06/ |
| Lab 07 | Cassandra Setup & Basics | lab_07/ |
| Lab 08 | Cassandra CQL & Tables | lab_08/ |
| Lab 09 | Cassandra Query-Oriented Modelling | lab_09/ |
| Lab 10 | Neo4j Setup & Basics | lab_10/ |
| Lab 11 | Cypher Queries | lab_11/ |
| Lab 12 | Graph Relationships & Threat Modelling | lab_12/ |
| Lab 13 | MongoDB + Python Integration | lab_13/ |
| Lab 14 | Cassandra + Python Integration | lab_14/ |
| Lab 15 | Neo4j + Python Integration | lab_15/ |
| Lab 16 | Multi-Database Integration | lab_16/ |
| Lab 17 | ThreatSentry Prototype | lab_17/ |
| Lab 18 | Final Integration & Reports | lab_18/ |
| Mini Project | ThreatSentry AI | mini-project/ThreatSentry/ |

---

## Prerequisites

| Requirement | Details |
| --- | --- |
| OS | Windows 10 / 11, Linux, or macOS |
| Docker | Docker Desktop / Docker Engine |
| Docker Compose | v2 or later |
| Git | To clone the repository |
| RAM | 8 GB minimum, 16 GB recommended |
| Disk Space | 10 GB free space |
| Browser | Chrome / Edge for dashboard |
| Python | 3.10+ (for local testing, optional) |

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

Source: [mini-project/ThreatSentry/](mini-project/ThreatSentry/)
Full report: [Mini Project - ThreatSentry AI Report](reports/Mini_Project_Report_ThreatSentry_AI.pdf)

---

## Security

No .env, API keys, JWT secrets, private keys, certs, or backups are committed. Secrets via environment variables only. See .gitignore.

---

## Docker Images

Current Image: jahnavii15/integrated-nosql-labs:2.3

Main labs image:
docker pull jahnavii15/integrated-nosql-labs:2.3
docker images jahnavii15/integrated-nosql-labs:2.3
docker compose up --build

ThreatSentry image:
docker pull jahnavii15/threatsentry

---

## Reports

- [Lab Experiments 01-18 Report](reports/Lab_Experiments_Report_Chapters_1-18.pdf)
- [Mini Project - ThreatSentry AI Report](reports/Mini_Project_Report_ThreatSentry_AI.pdf)

## Docker

[![Docker Image](https://img.shields.io/docker/pulls/jahnavii15/integrated-nosql-labs)](https://hub.docker.com/r/jahnavii15/integrated-nosql-labs)

- [View on Docker Hub](https://hub.docker.com/r/jahnavii15/integrated-nosql-labs)
