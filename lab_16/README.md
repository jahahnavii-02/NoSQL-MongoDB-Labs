# Lab 16 – Hybrid NoSQL Implementation Using MongoDB, Cassandra and Neo4j

## 1. Aim

To design and implement a hybrid NoSQL system integrating MongoDB, Cassandra and Neo4j. The system combines document storage, distributed event storage and graph relationships to support transaction analysis, user profiling and possible fraud-ring detection.

## 2. Problem Statement

A single database model may not efficiently support every type of application query. This implementation combines three database technologies so that each handles the workload for which it is suited.

The system demonstrates:
- Document-based user and transaction storage.
- Time-oriented event storage.
- Relationship-based graph traversal.
- Hybrid queries combining information from multiple databases.
- Resilience using independent circuit breakers.
- Performance measurement across database query operations.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| MongoDB | User profiles and transaction documents |
| Apache Cassandra | Enrollment records and time-series user events |
| Neo4j | Student-course and user-transfer relationships |
| Python 3.11 | Hybrid service and database integration |
| FastAPI | REST API |
| Docker | Containerization |
| Pytest | Unit and integration testing |

## 4. System Architecture

The application uses a Python FastAPI service to communicate with three independent database systems.

### Database responsibilities

**MongoDB – Document database**
- Stores user profiles.
- Stores transaction documents.
- Supports lookup by user ID and transaction ID.

**Cassandra – Wide-column database**
- Stores student-course mappings.
- Stores course-student mappings.
- Stores user events partitioned by user ID and ordered by event time.

**Neo4j – Graph database**
- Represents students and courses using nodes and ENROLLED_IN relationships.
- Represents users and transfers using User nodes and TRANSFERRED_TO relationships.
- Supports relationship traversal for identifying connected users.

### Request flow

1. A client sends a request to the FastAPI application.
2. The service identifies the required database operations.
3. MongoDB, Cassandra and/or Neo4j are queried.
4. The results are combined into a single response.
5. The API returns the result in JSON format.

## 5. Database Schemas

### 5.1 Cassandra

Keyspace: `lab16`

Tables:

- `student_courses`: partitioned by student_id.
- `course_students`: partitioned by course_id.
- `user_events`: partitioned by user_id and clustered by event_time in descending order.

Example query:

```sql
SELECT *
FROM lab16.student_courses
WHERE student_id = 'S001';
```

Courses containing a particular student can be retrieved efficiently using the student partition.

Example query:

```sql
SELECT *
FROM lab16.course_students
WHERE course_id = 'C001';
```

This retrieves the students enrolled in a particular course.

Recent user events:

```sql
SELECT *
FROM lab16.user_events
WHERE user_id = 'U001'
LIMIT 20;
```

### 5.2 Neo4j

The university graph contains Student and Course nodes connected through ENROLLED_IN relationships.

Example query – courses taken by a student:

```cypher
MATCH (s:Student {id:'S001'})-[:ENROLLED_IN]->(c:Course)
RETURN s.name, c.name;
```

Example query – students enrolled in a course:

```cypher
MATCH (s:Student)-[:ENROLLED_IN]->(c:Course {id:'C001'})
RETURN s.name;
```

Example query – students sharing a course:

```cypher
MATCH (s1:Student)-[:ENROLLED_IN]->(c:Course)<-[:ENROLLED_IN]-(s2:Student)
WHERE s1.id < s2.id
RETURN s1.name, s2.name, c.name;
```

The fraud-detection graph separately uses User nodes and TRANSFERRED_TO relationships to identify connected users.

### 5.3 MongoDB

MongoDB uses the `lab16` database.

Collections used by the hybrid service:

- `users`
- `transactions`

Example user lookup:

```javascript
db.users.find(
  { user_id: "U001" },
  { _id: 0 }
)
```

Example transaction lookup:

```javascript
db.transactions.find(
  { transaction_id: "TXN001" },
  { _id: 0 }
)
```

## 6. Hybrid Service Implementation

The `HybridFraudService` class combines results from the three database systems.

### Main operations

**get_transaction(txn_id)**
- Retrieves a transaction from MongoDB.
- Retrieves recent events from Cassandra for the transaction's user.
- Combines the results into one response.

**get_user_profile(user_id)**
- Retrieves the user profile from MongoDB.
- Retrieves recent user events from Cassandra.
- Retrieves connected users from Neo4j.
- Returns the combined user profile.

**detect_fraud_rings(user_id, max_hops)**
- Traverses the Neo4j transfer graph.
- Retrieves recent user events from Cassandra.
- Identifies high-value events with amounts of at least 10,000.
- Reports a possible ring when there are at least three connected users or at least three high-value events.

The maximum graph traversal depth is restricted to 1–5 hops.

## 7. Circuit Breaker Mechanism

The implementation maintains independent circuit breakers for MongoDB, Cassandra and Neo4j.

The configured behaviour is:

- Failure threshold: 3 consecutive failures.
- Recovery timeout: 30 seconds.
- States: CLOSED, OPEN and HALF_OPEN.

Purpose:
- Prevent repeated calls to an unavailable database.
- Isolate failures between database services.
- Allow recovery attempts after the configured timeout.

## 8. REST API Endpoints

Base URL: `http://localhost:8016`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/transaction/{txn_id}` | Retrieve hybrid transaction information |
| GET | `/user/{user_id}` | Retrieve combined user profile |
| GET | `/fraud-rings/{user_id}?max_hops=3` | Analyse connected users and high-value events |

Example requests:

```text
GET http://localhost:8016/health
GET http://localhost:8016/transaction/TXN001
GET http://localhost:8016/user/U001
GET http://localhost:8016/fraud-rings/U001?max_hops=3
```

The API uses:
- HTTP 404 when a transaction is not found.
- HTTP 400 for an invalid hop count.
- HTTP 503 when a database operation is unavailable.

## 9. Testing and Validation

### Unit testing

File: `tests/test_unit.py`

Verified tests:
1. Circuit breaker opens after three failures.
2. Circuit breaker recovers after success.
3. Invalid graph traversal depth is rejected.
4. Missing transaction is handled.
5. Transaction results include Cassandra events.
6. Fraud detection uses graph and event data.

**Actual result: 6 tests passed.**

### Integration testing

File: `tests/test_integration.py`

The integration test verifies the actual database connections and sample records across MongoDB, Cassandra and Neo4j.

**Actual result: 1 test passed.**

### API testing

The following API requests were executed successfully:
- Health endpoint.
- Transaction endpoint.
- User profile endpoint.
- Fraud-ring endpoint.

## 10. Performance Benchmark

The benchmark was executed using 10 runs for each database query.

### Actual benchmark results

| Database operation | Mean (ms) | Minimum (ms) | Maximum (ms) |
|---|---:|---:|---:|
| MongoDB student lookup | 1.610 | 1.171 | 3.585 |
| Cassandra student courses | 9.387 | 5.310 | 21.875 |
| Neo4j student courses | 41.856 | 13.213 | 259.446 |

### Observations

- MongoDB recorded the lowest average query time in this benchmark.
- Cassandra provided the student-course lookup with a moderate average response time.
- Neo4j recorded a higher average and greater variation in this test.
- The results depend on the workload, database configuration, network and environment.

The benchmark demonstrates how different NoSQL databases behave under the tested operations.

## 11. Docker Deployment

The standalone Lab 16 service image:

```text
lab16-hybrid:1.0
```

The integrated project image was built using the existing version 2.3 image as its base.

Published Docker Hub image:

```text
jahnavii15/integrated-nosql-labs:2.0
```

Docker Hub command:

```powershell
docker pull jahnavii15/integrated-nosql-labs:2.0
```

The integrated version 2.0 retains Labs 1–15 and adds the Lab 16 files and dependencies.

The Lab 16 API uses port 8016. Its database connections are configured through environment variables. Credentials must be supplied securely and must not be committed to the repository.

## 12. Project Folder Structure

```text
lab16/
|
|-- Dockerfile
|-- requirements.txt
|
|-- schemas/
|   |-- lab16.cql
|   |-- lab16.cypher
|
|-- scripts/
|   |-- init_databases.py
|   |-- benchmark.py
|
|-- service/
|   |-- api.py
|   |-- db.py
|   |-- hybrid.py
|   |-- breaker.py
|   |-- __init__.py
|
|-- tests/
    |-- test_unit.py
    |-- test_integration.py
```

## 13. Result

The hybrid NoSQL application integrating MongoDB, Cassandra and Neo4j was implemented successfully.

The database initialization, unit tests, integration test, REST API operations and performance benchmark were completed successfully. The integrated Docker image containing Labs 1–16 was built, verified and published to Docker Hub as version 2.0.

## 14. Conclusion

This experiment demonstrates the advantages of combining different NoSQL database models in one application. MongoDB supports flexible document storage, Cassandra handles partitioned event data, and Neo4j provides relationship traversal. Their integration through FastAPI enables hybrid queries and a basic fraud-detection workflow.

