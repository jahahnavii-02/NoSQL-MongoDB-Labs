from datetime import datetime, timezone
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase


def test_lab16_database_workflow():
    import os

    mongo_client = MongoClient(os.environ["LAB16_MONGO_URI"])
    mongo = mongo_client["lab16"]

    cluster = Cluster([os.getenv("CASSANDRA_HOST", "lab16-cassandra")])
    cassandra = cluster.connect("lab16")

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://lab16-neo4j:7687"),
        auth=("neo4j", os.environ["LAB16_NEO4J_PASSWORD"])
    )

    assert mongo.students.find_one({"student_id": "S001"}) is not None

    rows = list(cassandra.execute(
        "SELECT * FROM student_courses WHERE student_id=%s",
        ("S001",)
    ))
    assert len(rows) >= 1

    with driver.session() as session:
        result = session.run(
            "MATCH (s:Student {id:$id})-[:ENROLLED_IN]->(c:Course) RETURN count(c) AS total",
            id="S001"
        ).single()
        assert result["total"] >= 1

    driver.close()
    cassandra.shutdown()
    cluster.shutdown()
    mongo_client.close()
