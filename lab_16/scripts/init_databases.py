import os
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase


def main():
    mongo_uri = os.environ["LAB16_MONGO_URI"]
    neo_password = os.environ["LAB16_NEO4J_PASSWORD"]

    # MongoDB: isolated Lab 16 database
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    mongo = mongo_client["lab16"]

    students = [
        {"student_id": "S001", "name": "Alice", "course_ids": ["C001", "C002"]},
        {"student_id": "S002", "name": "Bob", "course_ids": ["C001"]},
        {"student_id": "S003", "name": "Carol", "course_ids": ["C002"]},
    ]
    courses = [
        {"course_id": "C001", "name": "Machine Learning", "student_ids": ["S001", "S002"]},
        {"course_id": "C002", "name": "Database Systems", "student_ids": ["S001", "S003"]},
    ]

    mongo.students.delete_many({})
    mongo.courses.delete_many({})
    mongo.users.delete_many({})
    mongo.transactions.delete_many({})

    mongo.students.insert_many(students)
    mongo.courses.insert_many(courses)

    mongo.users.insert_many([
        {"user_id": "U001", "name": "User One", "risk_level": "medium"},
        {"user_id": "U002", "name": "User Two", "risk_level": "low"},
        {"user_id": "U003", "name": "User Three", "risk_level": "high"},
        {"user_id": "U004", "name": "User Four", "risk_level": "medium"},
    ])

    mongo.transactions.insert_many([
        {"transaction_id": "TXN001", "user_id": "U001", "amount": 15000, "status": "flagged"},
        {"transaction_id": "TXN002", "user_id": "U002", "amount": 1200, "status": "completed"},
        {"transaction_id": "TXN003", "user_id": "U003", "amount": 22000, "status": "flagged"},
    ])

    # Cassandra: create keyspace, then connect to it
    cluster = Cluster(
        [os.getenv("CASSANDRA_HOST", "lab16-cassandra")],
        port=int(os.getenv("CASSANDRA_PORT", "9042"))
    )
    session = cluster.connect()
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS lab16
        WITH replication = {'class':'SimpleStrategy','replication_factor':1}
    """)
    session.set_keyspace("lab16")

    session.execute("""
        CREATE TABLE IF NOT EXISTS student_courses (
            student_id text, course_id text, student_name text,
            course_name text, PRIMARY KEY (student_id, course_id)
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS course_students (
            course_id text, student_id text, student_name text,
            course_name text, PRIMARY KEY (course_id, student_id)
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS user_events (
            user_id text, event_time timestamp, event_type text,
            transaction_id text, amount double, counterparty_id text,
            PRIMARY KEY (user_id, event_time)
        ) WITH CLUSTERING ORDER BY (event_time DESC)
    """)

    for student in students:
        for course_id in student["course_ids"]:
            course = next(c for c in courses if c["course_id"] == course_id)
            session.execute(
                "INSERT INTO student_courses (student_id,course_id,student_name,course_name) VALUES (%s,%s,%s,%s)",
                (student["student_id"], course_id, student["name"], course["name"])
            )
            session.execute(
                "INSERT INTO course_students (course_id,student_id,student_name,course_name) VALUES (%s,%s,%s,%s)",
                (course_id, student["student_id"], student["name"], course["name"])
            )

    now = datetime.now(timezone.utc)
    event_rows = [
        ("U001", "TRANSFER", "TXN001", 15000.0, "U002"),
        ("U001", "TRANSFER", "TXN004", 18000.0, "U003"),
        ("U002", "TRANSFER", "TXN002", 1200.0, "U003"),
        ("U003", "TRANSFER", "TXN003", 22000.0, "U004"),
        ("U004", "TRANSFER", "TXN005", 12500.0, "U001"),
    ]
    for index, row in enumerate(event_rows):
        user_id, event_type, txn_id, amount, counterparty = row
        session.execute(
            "INSERT INTO user_events (user_id,event_time,event_type,transaction_id,amount,counterparty_id) VALUES (%s,%s,%s,%s,%s,%s)",
            (user_id, now - timedelta(minutes=index), event_type, txn_id, amount, counterparty)
        )

    # Neo4j: university graph and transfer network
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://lab16-neo4j:7687"),
        auth=("neo4j", neo_password)
    )
    with driver.session() as graph:
        graph.run("MATCH (n) DETACH DELETE n")
        graph.run("""
            CREATE
            (a:Student {id:'S001', name:'Alice'}),
            (b:Student {id:'S002', name:'Bob'}),
            (c:Student {id:'S003', name:'Carol'}),
            (ml:Course {id:'C001', name:'Machine Learning'}),
            (db:Course {id:'C002', name:'Database Systems'}),
            (a)-[:ENROLLED_IN]->(ml),
            (a)-[:ENROLLED_IN]->(db),
            (b)-[:ENROLLED_IN]->(ml),
            (c)-[:ENROLLED_IN]->(db)
        """)
        graph.run("""
            CREATE
            (u1:User {id:'U001'}),
            (u2:User {id:'U002'}),
            (u3:User {id:'U003'}),
            (u4:User {id:'U004'}),
            (u1)-[:TRANSFERRED_TO]->(u2),
            (u1)-[:TRANSFERRED_TO]->(u3),
            (u2)-[:TRANSFERRED_TO]->(u3),
            (u3)-[:TRANSFERRED_TO]->(u4),
            (u4)-[:TRANSFERRED_TO]->(u1)
        """)

    driver.close()
    session.shutdown()
    cluster.shutdown()
    mongo_client.close()

    print("Lab 16 sample data initialized successfully.")
    print("MongoDB: university, users and transactions")
    print("Cassandra: enrollment tables and user events")
    print("Neo4j: enrollment graph and transfer network")


if __name__ == "__main__":
    main()
