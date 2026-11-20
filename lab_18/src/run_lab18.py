import os
import json
import time
import uuid
import statistics
import random
import csv

from datetime import datetime, timedelta, timezone
from pathlib import Path

from pymongo import MongoClient, ReplaceOne
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from neo4j import GraphDatabase


# ============================================================
# CONFIGURATION
# ============================================================

N = int(os.getenv("LAB18_RECORDS", "100000"))
SEED = 18018

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"

BASE_TIME = datetime(2026, 11, 4, 23, 59, tzinfo=timezone.utc)

SOURCES = [
    "AlienVault", "AbuseCH", "URLhaus", "MalwareBazaar",
    "ThreatFox", "OpenPhish", "FeodoTracker", "EmergingThreats"
]

TYPES = [
    "malware", "phishing", "botnet",
    "ransomware", "suspicious_ip"
]

TARGETS = [f"asset-{i:04d}" for i in range(1, 101)]

QUERY_SOURCE = "AlienVault"
QUERY_TARGET = "asset-0001"
QUERY_DAY = "2026-11-04"

BENCHMARK_ROUNDS = 10
BENCHMARK_BATCH_SIZE = 100


# ============================================================
# DETERMINISTIC DATA GENERATION
# ============================================================

def make_threat(i):
    source = SOURCES[i % len(SOURCES)]
    kind = TYPES[(i * 7) % len(TYPES)]
    target = TARGETS[(i * 13) % len(TARGETS)]

    ts = BASE_TIME - timedelta(
        minutes=(i * 17) % (30 * 24 * 60)
    )

    return {
        "threat_id": str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"lab18-threat-{i}")
        ),
        "from_source": source,
        "threat_type": kind,
        "target": target,
        "timestamp": ts,
        "event_date": ts.date().isoformat(),
        "severity": ["low", "medium", "high", "critical"][i % 4],
        "confidence": round(0.50 + (i % 50) / 100, 2),
        "indicator": f"indicator-{i % 25000:05d}",
        "description": f"Synthetic {kind} intelligence event {i}",
        "is_false_positive": (i % 17 == 0),
        "dataset": "synthetic-lab18"
    }


def batches(items, size=1000):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def neo_record(record):
    return {
        "id": record["threat_id"],
        "source": record["from_source"],
        "kind": record["threat_type"],
        "target": record["target"],
        "severity": record["severity"],
        "confidence": record["confidence"],
        "indicator": record["indicator"],
        "event_date": record["event_date"],
        "timestamp": record["timestamp"].isoformat(),
        "false_positive": record["is_false_positive"],
        "dataset": record["dataset"]
    }


# ============================================================
# MONGODB SETUP
# ============================================================

def setup_mongo(uri):
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")
    db = client["lab18"]

    db.full_threats.create_index(
        [("from_source", 1), ("timestamp", -1)]
    )

    db.full_threats.create_index(
        [("target", 1), ("timestamp", -1)]
    )

    db.full_threats.create_index(
        [("event_date", 1), ("threat_type", 1)]
    )

    db.full_threats.create_index(
        "threat_id", unique=True
    )

    db.threat.create_index("updated_at")

    return client, db


def mongo_reset(db):
    db.full_threats.delete_many({})
    db.threat.delete_many({})
    db.lab18_insert_benchmark.delete_many({})


def mongo_load(db, records):
    for chunk in batches(records):
        operations = [
            ReplaceOne(
                {"threat_id": record["threat_id"]},
                record,
                upsert=True
            )
            for record in chunk
        ]

        if operations:
            db.full_threats.bulk_write(
                operations,
                ordered=False
            )

    for source in SOURCES:
        recent = list(
            db.full_threats.find(
                {"from_source": source},
                {"_id": 0}
            ).sort("timestamp", -1).limit(50)
        )

        db.threat.update_one(
            {"_id": source},
            {
                "$set": {
                    "from_source": source,
                    "recent_threats": recent,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
# ============================================================
# CASSANDRA SETUP
# ============================================================

def setup_cassandra():
    cluster = Cluster(
        [os.getenv("CASSANDRA_HOST", "lab16-cassandra")],
        port=int(os.getenv("CASSANDRA_PORT", "9042"))
    )

    session = cluster.connect()
    session.default_timeout = 60

    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS lab18
        WITH replication = {
            'class': 'SimpleStrategy',
            'replication_factor': 1
        }
    """)

    session.set_keyspace("lab18")

    statements = [
        """
        CREATE TABLE IF NOT EXISTS threats_by_source (
            from_source text,
            timestamp timestamp,
            threat_id text,
            threat_type text,
            target text,
            severity text,
            confidence double,
            indicator text,
            event_date text,
            is_false_positive boolean,
            PRIMARY KEY ((from_source), timestamp, threat_id)
        )
        WITH CLUSTERING ORDER BY (timestamp DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS threats_by_type (
            threat_type text,
            timestamp timestamp,
            threat_id text,
            from_source text,
            target text,
            severity text,
            confidence double,
            indicator text,
            event_date text,
            is_false_positive boolean,
            PRIMARY KEY ((threat_type), timestamp, threat_id)
        )
        WITH CLUSTERING ORDER BY (timestamp DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS threats_by_target (
            target text,
            timestamp timestamp,
            threat_id text,
            from_source text,
            threat_type text,
            severity text,
            event_date text,
            PRIMARY KEY ((target), timestamp, threat_id)
        )
        WITH CLUSTERING ORDER BY (timestamp DESC)
        """,
        """
        CREATE TABLE IF NOT EXISTS threats_by_day (
            event_date text,
            threat_type text,
            from_source text,
            threat_id text,
            target text,
            severity text,
            PRIMARY KEY (
                (event_date), threat_type, from_source, threat_id
            )
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS insert_benchmark (
            round_no int,
            threat_id text,
            from_source text,
            timestamp timestamp,
            threat_type text,
            target text,
            severity text,
            confidence double,
            indicator text,
            event_date text,
            is_false_positive boolean,
            PRIMARY KEY ((round_no), threat_id)
        )
        """
    ]

    for statement in statements:
        session.execute(statement)

    return cluster, session


# ============================================================
# CASSANDRA RESET
# ============================================================

def cassandra_reset(session):
    # Reset Lab 18 tables only.
    # Lab 16 and all other keyspaces remain untouched.

    tables = [
        "threats_by_source",
        "threats_by_type",
        "threats_by_target",
        "threats_by_day",
        "insert_benchmark"
    ]

    for table in tables:
        session.execute(
            f"TRUNCATE lab18.{table}"
        )
# ============================================================
# CASSANDRA DATA LOADING
# ============================================================

def cassandra_load(session, records):
    source_stmt = session.prepare("""
        INSERT INTO threats_by_source
        (
            from_source, timestamp, threat_id, threat_type,
            target, severity, confidence, indicator,
            event_date, is_false_positive
        )
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """)

    type_stmt = session.prepare("""
        INSERT INTO threats_by_type
        (
            threat_type, timestamp, threat_id, from_source,
            target, severity, confidence, indicator,
            event_date, is_false_positive
        )
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """)

    target_stmt = session.prepare("""
        INSERT INTO threats_by_target
        (
            target, timestamp, threat_id, from_source,
            threat_type, severity, event_date
        )
        VALUES (?,?,?,?,?,?,?)
    """)

    day_stmt = session.prepare("""
        INSERT INTO threats_by_day
        (
            event_date, threat_type, from_source,
            threat_id, target, severity
        )
        VALUES (?,?,?,?,?,?)
    """)

    for chunk in batches(records, 100):
        source_args = []
        type_args = []
        target_args = []
        day_args = []

        for record in chunk:
            source_args.append((
                record["from_source"],
                record["timestamp"],
                record["threat_id"],
                record["threat_type"],
                record["target"],
                record["severity"],
                record["confidence"],
                record["indicator"],
                record["event_date"],
                record["is_false_positive"]
            ))

            type_args.append((
                record["threat_type"],
                record["timestamp"],
                record["threat_id"],
                record["from_source"],
                record["target"],
                record["severity"],
                record["confidence"],
                record["indicator"],
                record["event_date"],
                record["is_false_positive"]
            ))

            target_args.append((
                record["target"],
                record["timestamp"],
                record["threat_id"],
                record["from_source"],
                record["threat_type"],
                record["severity"],
                record["event_date"]
            ))

            day_args.append((
                record["event_date"],
                record["threat_type"],
                record["from_source"],
                record["threat_id"],
                record["target"],
                record["severity"]
            ))

        for statement, arguments in (
            (source_stmt, source_args),
            (type_stmt, type_args),
            (target_stmt, target_args),
            (day_stmt, day_args)
        ):
            execute_concurrent_with_args(
                session,
                statement,
                arguments,
                concurrency=8,
                raise_on_first_error=True
            )
# ============================================================
# NEO4J SETUP
# ============================================================

def setup_neo4j():
    uri = os.getenv("NEO4J_URI", "bolt://lab16-neo4j:7687")
    password = os.getenv("LAB16_NEO4J_PASSWORD")

    if not password:
        raise RuntimeError(
            "LAB16_NEO4J_PASSWORD environment variable is missing."
        )

    driver = GraphDatabase.driver(
        uri,
        auth=("neo4j", password)
    )

    driver.verify_connectivity()

    with driver.session() as session:
        session.run("""
            CREATE CONSTRAINT lab18_source_name IF NOT EXISTS
            FOR (s:Lab18Source)
            REQUIRE s.name IS UNIQUE
        """)

        session.run("""
            CREATE CONSTRAINT lab18_threat_id IF NOT EXISTS
            FOR (t:Lab18Threat)
            REQUIRE t.id IS UNIQUE
        """)

    return driver


# ============================================================
# NEO4J RESET — LAB 18 ONLY
# ============================================================

def neo4j_reset(driver):
    with driver.session() as session:

        # Remove Lab 18 benchmark nodes and relationships.
        session.run("""
            MATCH (t:Lab18BenchmarkThreat)
            DETACH DELETE t
        """)

        # Remove Lab 18 threat nodes and their relationships.
        session.run("""
            MATCH (t:Lab18Threat)
            DETACH DELETE t
        """)

        # Remove Lab 18 source nodes and remaining relationships.
        session.run("""
            MATCH (s:Lab18Source)
            DETACH DELETE s
        """)
# ============================================================
# NEO4J DATA LOADING
# ============================================================

def neo4j_load(driver, records):
    with driver.session() as session:
        session.run("""
            UNWIND $sources AS name
            MERGE (s:Lab18Source {name: name})
            SET s.lab = 'lab18'
        """, sources=SOURCES)

        for chunk in batches(records, 1000):
            rows = [neo_record(record) for record in chunk]

            session.run("""
                UNWIND $rows AS row

                MATCH (s:Lab18Source {name: row.source})

                MERGE (t:Lab18Threat {id: row.id})

                SET
                    t.source = row.source,
                    t.kind = row.kind,
                    t.target = row.target,
                    t.severity = row.severity,
                    t.confidence = row.confidence,
                    t.indicator = row.indicator,
                    t.event_date = row.event_date,
                    t.timestamp = row.timestamp,
                    t.false_positive = row.false_positive,
                    t.dataset = row.dataset,
                    t.lab = 'lab18'

                MERGE (s)-[:REPORTED]->(t)
            """, rows=rows)


# ============================================================
# SUSPICIOUS SOURCE RELATIONSHIPS
# ============================================================

def build_suspicious_relationships(driver):
    with driver.session() as session:
        # Remove previous Lab18 suspicious relationships only.
        session.run("""
            MATCH (a:Lab18Source)-[r:SUSPICIOUS]-(b:Lab18Source)
            DELETE r
        """)

        result = session.run("""
            MATCH (s:Lab18Source)-[:REPORTED]->
                  (t:Lab18Threat)

            WITH s, collect(DISTINCT t.target) AS targets

            UNWIND targets AS target

            WITH target, collect(DISTINCT s) AS sources

            WHERE size(sources) >= 2

            UNWIND sources AS a
            UNWIND sources AS b

            WITH DISTINCT a, b, target
            WHERE a.name < b.name

            WITH a, b, collect(DISTINCT target) AS shared_targets

            WHERE size(shared_targets) >= 2

            MERGE (a)-[r:SUSPICIOUS]-(b)

            SET
                r.shared_targets = shared_targets,
                r.shared_target_count = size(shared_targets),
                r.lab = 'lab18'

            RETURN
                a.name AS source_a,
                b.name AS source_b,
                shared_targets,
                size(shared_targets) AS shared_target_count
            ORDER BY source_a, source_b
        """)

        return [record.data() for record in result]
# ============================================================
# QUERY TIMING
# ============================================================

def timed(function, runs=10):
    measurements = []
    last_result = None

    for _ in range(runs):
        start = time.perf_counter()
        last_result = function()
        elapsed_ms = (time.perf_counter() - start) * 1000
        measurements.append(elapsed_ms)

    return {
        "median_ms": round(statistics.median(measurements), 3),
        "runs": runs,
        "result_count": (
            len(last_result)
            if isinstance(last_result, (list, tuple))
            else None
        )
    }


# ============================================================
# MONGODB QUERIES
# ============================================================

def mongo_history(db):
    return list(
        db.full_threats.find(
            {"from_source": QUERY_SOURCE},
            {"_id": 0}
        )
        .sort("timestamp", -1)
        .limit(100)
    )


def mongo_target_spread(db):
    return list(
        db.full_threats.find(
            {"target": QUERY_TARGET},
            {"_id": 0}
        )
        .sort("timestamp", -1)
        .limit(500)
    )


def mongo_daily_volume(db):
    return list(
        db.full_threats.aggregate([
            {"$match": {"event_date": QUERY_DAY}},
            {
                "$group": {
                    "_id": "$threat_type",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ])
    )


# ============================================================
# CASSANDRA QUERIES
# ============================================================

def cassandra_history(session):
    rows = session.execute(
        """
        SELECT threat_id, threat_type, target, timestamp,
               severity, confidence
        FROM threats_by_source
        WHERE from_source = %s
        LIMIT 100
        """,
        (QUERY_SOURCE,)
    )

    return list(rows)


def cassandra_target_spread(session):
    rows = session.execute(
        """
        SELECT threat_id, threat_type, from_source,
               timestamp, severity
        FROM threats_by_target
        WHERE target = %s
        LIMIT 500
        """,
        (QUERY_TARGET,)
    )

    return list(rows)


def cassandra_daily_volume(session):
    # Read the selected day's partition and count by type in Python.
    # This avoids relying on unsupported arbitrary GROUP BY behavior.

    rows = session.execute(
        """
        SELECT threat_type
        FROM threats_by_day
        WHERE event_date = %s
        """,
        (QUERY_DAY,)
    )

    counts = {}

    for row in rows:
        counts[row.threat_type] = (
            counts.get(row.threat_type, 0) + 1
        )

    return [
        {"threat_type": kind, "count": counts[kind]}
        for kind in sorted(counts)
    ]


# ============================================================
# NEO4J QUERIES
# ============================================================

def neo4j_history(driver):
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Lab18Source {name: $source})
                  -[:REPORTED]->(t:Lab18Threat)

            RETURN
                t.id AS threat_id,
                t.kind AS threat_type,
                t.target AS target,
                t.timestamp AS timestamp,
                t.severity AS severity,
                t.confidence AS confidence

            ORDER BY t.timestamp DESC
            LIMIT 100
        """, source=QUERY_SOURCE)

        return [record.data() for record in result]


def neo4j_target_spread(driver):
    with driver.session() as session:
        result = session.run("""
            MATCH (t:Lab18Threat {target: $target})

            RETURN
                t.id AS threat_id,
                t.kind AS threat_type,
                t.source AS from_source,
                t.timestamp AS timestamp,
                t.severity AS severity

            ORDER BY t.timestamp DESC
            LIMIT 500
        """, target=QUERY_TARGET)

        return [record.data() for record in result]


def neo4j_daily_volume(driver):
    with driver.session() as session:
        result = session.run("""
            MATCH (t:Lab18Threat {event_date: $day})

            RETURN
                t.kind AS threat_type,
                count(t) AS count

            ORDER BY threat_type
        """, day=QUERY_DAY)

        return [record.data() for record in result]


# ============================================================
# COMPARATIVE QUERY BENCHMARKS
# ============================================================

def run_query_benchmarks(mongo_db, cassandra_session, neo4j_driver):
    workloads = {
        "threat_history_by_source": {
            "MongoDB": lambda: mongo_history(mongo_db),
            "Cassandra": lambda: cassandra_history(cassandra_session),
            "Neo4j": lambda: neo4j_history(neo4j_driver)
        },
        "target_spread": {
            "MongoDB": lambda: mongo_target_spread(mongo_db),
            "Cassandra": lambda: cassandra_target_spread(cassandra_session),
            "Neo4j": lambda: neo4j_target_spread(neo4j_driver)
        },
        "daily_volume_by_type": {
            "MongoDB": lambda: mongo_daily_volume(mongo_db),
            "Cassandra": lambda: cassandra_daily_volume(cassandra_session),
            "Neo4j": lambda: neo4j_daily_volume(neo4j_driver)
        }
    }

    results = {}

    for workload_name, databases in workloads.items():
        results[workload_name] = {}

        for database_name, function in databases.items():
            results[workload_name][database_name] = timed(
                function,
                runs=10
            )

    return results
# ============================================================
# ISOLATED INSERT BENCHMARK
# ============================================================

def run_insert_benchmark(mongo_db, cassandra_session, neo4j_driver):
    results = {}

    # Generate benchmark records separately from the main dataset.
    benchmark_records = [
        make_threat(N + i)
        for i in range(BENCHMARK_ROUNDS * BENCHMARK_BATCH_SIZE)
    ]

    # ---------------- MONGODB ----------------

    mongo_times = []

    for round_no in range(BENCHMARK_ROUNDS):
        chunk = benchmark_records[
            round_no * BENCHMARK_BATCH_SIZE:
            (round_no + 1) * BENCHMARK_BATCH_SIZE
        ]

        start = time.perf_counter()

        mongo_db.lab18_insert_benchmark.insert_many(
            chunk,
            ordered=False
        )

        mongo_times.append(
            time.perf_counter() - start
        )

    # ---------------- CASSANDRA ----------------

    cassandra_stmt = cassandra_session.prepare("""
        INSERT INTO insert_benchmark
        (
            round_no, threat_id, from_source, timestamp,
            threat_type, target, severity, confidence,
            indicator, event_date, is_false_positive
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """)

    cassandra_times = []

    for round_no in range(BENCHMARK_ROUNDS):
        chunk = benchmark_records[
            round_no * BENCHMARK_BATCH_SIZE:
            (round_no + 1) * BENCHMARK_BATCH_SIZE
        ]

        args = [
            (
                round_no,
                r["threat_id"],
                r["from_source"],
                r["timestamp"],
                r["threat_type"],
                r["target"],
                r["severity"],
                r["confidence"],
                r["indicator"],
                r["event_date"],
                r["is_false_positive"]
            )
            for r in chunk
        ]

        start = time.perf_counter()

        execute_concurrent_with_args(
            cassandra_session,
            cassandra_stmt,
            args,
            concurrency=8,
            raise_on_first_error=True
        )

        cassandra_times.append(
            time.perf_counter() - start
        )

    # ---------------- NEO4J ----------------

    neo4j_times = []

    with neo4j_driver.session() as session:
        for round_no in range(BENCHMARK_ROUNDS):
            chunk = benchmark_records[
                round_no * BENCHMARK_BATCH_SIZE:
                (round_no + 1) * BENCHMARK_BATCH_SIZE
            ]

            rows = [neo_record(r) for r in chunk]

            start = time.perf_counter()

            session.run("""
                UNWIND $rows AS row

                MATCH (s:Lab18Source {name: row.source})

                CREATE (t:Lab18BenchmarkThreat {
                    id: row.id,
                    source: row.source,
                    kind: row.kind,
                    target: row.target,
                    timestamp: row.timestamp,
                    dataset: 'synthetic-lab18-benchmark'
                })

                CREATE (s)-[:BENCHMARK_REPORTED]->(t)
            """, rows=rows).consume()

            neo4j_times.append(
                time.perf_counter() - start
            )

    def throughput(times):
        median_seconds = statistics.median(times)

        return round(
            BENCHMARK_BATCH_SIZE / median_seconds,
            2
        ) if median_seconds > 0 else 0

    results["MongoDB"] = {
        "median_records_per_second": throughput(mongo_times),
        "rounds": BENCHMARK_ROUNDS,
        "records_per_round": BENCHMARK_BATCH_SIZE
    }

    results["Cassandra"] = {
        "median_records_per_second": throughput(cassandra_times),
        "rounds": BENCHMARK_ROUNDS,
        "records_per_round": BENCHMARK_BATCH_SIZE
    }

    results["Neo4j"] = {
        "median_records_per_second": throughput(neo4j_times),
        "rounds": BENCHMARK_ROUNDS,
        "records_per_round": BENCHMARK_BATCH_SIZE
    }

    return results


# ============================================================
# GRAPH ANALYSIS
# ============================================================

def graph_analysis(driver, mongo_db):
    with driver.session() as session:
        source_result = session.run("""
            MATCH (s:Lab18Source)-[:REPORTED]->(t:Lab18Threat)

            RETURN
                s.name AS source,
                count(t) AS threat_count

            ORDER BY source
        """)

        source_activity = [
            record.data()
            for record in source_result
        ]

        edge_result = session.run("""
            MATCH (a:Lab18Source)-[r:SUSPICIOUS]-(b:Lab18Source)

            WHERE a.name < b.name

            RETURN
                a.name AS source_a,
                b.name AS source_b,
                r.shared_targets AS shared_targets,
                r.shared_target_count AS shared_target_count

            ORDER BY source_a, source_b
        """)

        edges = [
            record.data()
            for record in edge_result
        ]

        node_result = session.run("""
            MATCH (s:Lab18Source)
            RETURN s.name AS name
            ORDER BY name
        """)

        nodes = [
            record["name"]
            for record in node_result
        ]

    # Build an undirected adjacency list.
    adjacency = {
        node: set()
        for node in nodes
    }

    for edge in edges:
        a = edge["source_a"]
        b = edge["source_b"]

        adjacency[a].add(b)
        adjacency[b].add(a)

    # ---------------- CONNECTED COMPONENTS ----------------

    visited = set()
    components = []

    for start_node in sorted(nodes):
        if start_node in visited:
            continue

        stack = [start_node]
        visited.add(start_node)
        component = []

        while stack:
            current = stack.pop()
            component.append(current)

            for neighbour in sorted(adjacency[current]):
                if neighbour not in visited:
                    visited.add(neighbour)
                    stack.append(neighbour)

        components.append(sorted(component))

    # ---------------- LABEL PROPAGATION ----------------

    labels = {
        node: node
        for node in sorted(nodes)
    }

    iterations = 0
    max_iterations = 20

    for iteration in range(max_iterations):
        changed = False

        for node in sorted(nodes):
            neighbours = sorted(adjacency[node])

            if not neighbours:
                continue

            label_counts = {}

            for neighbour in neighbours:
                label = labels[neighbour]
                label_counts[label] = (
                    label_counts.get(label, 0) + 1
                )

            highest_count = max(label_counts.values())

            winning_labels = sorted([
                label
                for label, count in label_counts.items()
                if count == highest_count
            ])

            selected_label = winning_labels[0]

            if labels[node] != selected_label:
                labels[node] = selected_label
                changed = True

        iterations = iteration + 1

        if not changed:
            break

    communities = {}

    for node, label in sorted(labels.items()):
        communities.setdefault(label, []).append(node)

    # ---------------- MONGODB EVIDENCE ----------------

    evidence = []

    for edge in edges:
        source_a = edge["source_a"]
        source_b = edge["source_b"]

        targets = edge["shared_targets"]

        mongo_count = mongo_db.full_threats.count_documents({
            "from_source": {
                "$in": [source_a, source_b]
            },
            "target": {
                "$in": targets
            }
        })

        evidence.append({
            "source_a": source_a,
            "source_b": source_b,
            "shared_targets": targets,
            "shared_target_count": edge["shared_target_count"],
            "mongo_matching_record_count": mongo_count
        })

    return {
        "source_activity": source_activity,
        "suspicious_source_pairs": edges,
        "connected_components": components,
        "connected_component_count": len(components),
        "label_propagation": {
            "algorithm": "Deterministic Label Propagation",
            "iterations": iterations,
            "communities": communities
        },
        "mongo_evidence_cross_reference": evidence
    }


# ============================================================
# FALSE-POSITIVE SAMPLE
# ============================================================

def false_positive_sample(mongo_db, limit=20):
    return list(
        mongo_db.full_threats.find(
            {"is_false_positive": True},
            {
                "_id": 0,
                "threat_id": 1,
                "from_source": 1,
                "threat_type": 1,
                "target": 1,
                "severity": 1,
                "confidence": 1
            }
        ).limit(limit)
    )

# ============================================================
# VERIFICATION
# ============================================================

def verify_results(mongo_db, cassandra_session, neo4j_driver):
    mongo_full_count = mongo_db.full_threats.count_documents({})
    mongo_summary_count = mongo_db.threat.count_documents({})

    # Exact Cassandra counts.
    # These scans may take time on a 100,000-record dataset.
    cassandra_counts = {}

    for table in [
        "threats_by_source",
        "threats_by_type",
        "threats_by_target",
        "threats_by_day"
    ]:
        row = cassandra_session.execute(
            f"SELECT COUNT(*) AS total FROM lab18.{table}"
        ).one()

        cassandra_counts[table] = row.total

    with neo4j_driver.session() as session:
        threat_count = session.run("""
            MATCH (t:Lab18Threat)
            RETURN count(t) AS total
        """).single()["total"]

        source_count = session.run("""
            MATCH (s:Lab18Source)
            RETURN count(s) AS total
        """).single()["total"]

    return {
        "expected_dataset_records": N,

        "MongoDB": {
            "full_threats": mongo_full_count,
            "source_summary_documents": mongo_summary_count,
            "expected_full_threats": N,
            "verified": (
                mongo_full_count == N
                and mongo_summary_count == len(SOURCES)
            )
        },

        "Cassandra": {
            "table_counts": cassandra_counts,
            "expected_records_per_table": N,
            "verified": all(
                count == N
                for count in cassandra_counts.values()
            )
        },

        "Neo4j": {
            "threat_nodes": threat_count,
            "source_nodes": source_count,
            "expected_threat_nodes": N,
            "expected_source_nodes": len(SOURCES),
            "verified": (
                threat_count == N
                and source_count == len(SOURCES)
            )
        }
    }


# ============================================================
# CSV RESULT GENERATION
# ============================================================

def save_csv(results):
    RESULTS.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS / "benchmark_summary.csv"

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "Workload",
            "Database",
            "Median Latency (ms)",
            "Runs"
        ])

        for workload, databases in results.get(
            "query_benchmarks", {}
        ).items():

            for database, values in databases.items():
                writer.writerow([
                    workload,
                    database,
                    values.get("median_ms"),
                    values.get("runs")
                ])

        writer.writerow([])
        writer.writerow([
            "Insert Benchmark",
            "Database",
            "Median Records Per Second",
            "Rounds"
        ])

        for database, values in results.get(
            "insert_benchmarks", {}
        ).items():
            writer.writerow([
                "Insert Benchmark",
                database,
                values.get("median_records_per_second"),
                values.get("rounds")
            ])

    return str(output_path)


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    result_json = RESULTS / "benchmark_results.json"

    resume = os.getenv("LAB18_RESUME", "0") == "1"

    previous = {}

    if resume and result_json.exists():
        with result_json.open(
            "r",
            encoding="utf-8"
        ) as file:
            previous = json.load(file)

    mongo_client = None
    cassandra_cluster = None
    neo4j_driver = None

    try:
        # ---------------- CONNECTIONS ----------------

        mongo_uri = os.getenv("LAB16_MONGO_URI")

        if not mongo_uri:
            raise RuntimeError(
                "LAB16_MONGO_URI environment variable is missing."
            )

        mongo_client, mongo_db = setup_mongo(mongo_uri)

        cassandra_cluster, cassandra_session = setup_cassandra()

        neo4j_driver = setup_neo4j()

        # ---------------- DATASET ----------------

        records = [
            make_threat(i)
            for i in range(N)
        ]

        load_start = time.perf_counter()

        recover = os.getenv("LAB18_RECOVER", "0") == "1"

        if not resume:
            if recover:
                print("Recovery mode: preserving existing Lab18 threat data...")
            else:
                print("Resetting Lab18-only data...")
                mongo_reset(mongo_db)
                cassandra_reset(cassandra_session)
                neo4j_reset(neo4j_driver)

            print(f"Loading/reconciling {N} synthetic threat records...")

            mongo_load(mongo_db, records)
            cassandra_load(cassandra_session, records)
            neo4j_load(neo4j_driver, records)

            load_seconds = round(
                time.perf_counter() - load_start,
                3
            )
            # Clear isolated Lab 18 insert-benchmark data.
            mongo_db.lab18_insert_benchmark.delete_many({})

            cassandra_session.execute(
                "TRUNCATE lab18.insert_benchmark"
            )

            with neo4j_driver.session() as session:
                session.run("""
                    MATCH (t:Lab18BenchmarkThreat)
                    DETACH DELETE t
                """)

            insert_benchmarks = run_insert_benchmark(
                mongo_db,
                cassandra_session,
                neo4j_driver
            )

        else:
            print("Resume mode: skipping dataset loading.")

            load_seconds = previous.get("load_time_seconds")

            insert_benchmarks = previous.get(
                "insert_benchmarks",
                {}
            )

        # ---------------- GRAPH ----------------

        print("Building suspicious-source relationships...")

        suspicious_pairs = build_suspicious_relationships(
            neo4j_driver
        )

        print("Running graph analysis...")

        graph_results = graph_analysis(
            neo4j_driver,
            mongo_db
        )

        # ---------------- QUERY BENCHMARKS ----------------

        print("Running comparative query benchmarks...")

        query_benchmarks = run_query_benchmarks(
            mongo_db,
            cassandra_session,
            neo4j_driver
        )

        # ---------------- VERIFICATION ----------------

        print("Verifying database record counts...")

        verification = verify_results(
            mongo_db,
            cassandra_session,
            neo4j_driver
        )

        # ---------------- FALSE POSITIVES ----------------

        fp_sample = false_positive_sample(
            mongo_db,
            limit=20
        )

        # ---------------- FINAL RESULTS ----------------

        results = {
            "lab": "Lab 18 - Comparative NoSQL Threat Intelligence Capstone",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "dataset": {
                "records_requested": N,
                "records_generated": len(records),
                "source_count": len(SOURCES),
                "sources": SOURCES,
                "threat_types": TYPES,
                "target_count": len(TARGETS),
                "synthetic": True
            },

            "benchmark_methodology": {
                "query_runs": 10,
                "insert_rounds": BENCHMARK_ROUNDS,
                "insert_records_per_round": BENCHMARK_BATCH_SIZE,
                "query_source": QUERY_SOURCE,
                "query_target": QUERY_TARGET,
                "query_day": QUERY_DAY
            },

            "load_time_seconds": load_seconds,

            "query_benchmarks": query_benchmarks,

            "insert_benchmarks": insert_benchmarks,

            "graph_analysis": graph_results,

            "suspicious_relationships_created": len(
                suspicious_pairs
            ),

            "false_positive_sample": fp_sample,

            "verification": verification,

            "resume_mode": resume
        }

        with result_json.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                results,
                file,
                indent=4,
                default=str
            )

        csv_path = save_csv(results)

        print("\nLab 18 execution completed.")
        print(f"JSON results: {result_json}")
        print(f"CSV results: {csv_path}")

        print("\nVerification summary:")

        print(json.dumps(
            verification,
            indent=4
        ))

        if not (
            verification["MongoDB"]["verified"]
            and verification["Cassandra"]["verified"]
            and verification["Neo4j"]["verified"]
        ):
            raise RuntimeError(
                "Lab18 verification failed. Check the counts above."
            )

        print("\nALL DATABASE COUNT CHECKS PASSED.")

    finally:
        if mongo_client is not None:
            mongo_client.close()

        if cassandra_cluster is not None:
            cassandra_cluster.shutdown()

        if neo4j_driver is not None:
            neo4j_driver.close()


if __name__ == "__main__":
    main()

