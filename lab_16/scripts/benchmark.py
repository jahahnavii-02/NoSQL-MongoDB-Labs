import os
import time
import statistics
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase


def measure(label, operation, runs=10):
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - start) * 1000)

    print(
        f"{label}: mean={statistics.mean(samples):.3f} ms, "
        f"min={min(samples):.3f} ms, max={max(samples):.3f} ms "
        f"(runs={runs})"
    )


def main():
    mongo = MongoClient(os.environ["LAB16_MONGO_URI"])["lab16"]

    cluster = Cluster([os.getenv("CASSANDRA_HOST", "lab16-cassandra")])
    cassandra = cluster.connect("lab16")

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://lab16-neo4j:7687"),
        auth=("neo4j", os.environ["LAB16_NEO4J_PASSWORD"])
    )

    # Warm up connections before measuring.
    mongo.command("ping")
    cassandra.execute("SELECT * FROM student_courses LIMIT 1")
    with driver.session() as session:
        session.run("RETURN 1").consume()

    print("Lab 16 database query benchmark")
    measure(
        "MongoDB student lookup",
        lambda: mongo.students.find_one({"student_id": "S001"})
    )
    measure(
        "Cassandra student courses",
        lambda: list(cassandra.execute(
            "SELECT * FROM student_courses WHERE student_id=%s",
            ("S001",)
        ))
    )

    def neo_query():
        with driver.session() as session:
            session.run(
                "MATCH (s:Student {id:$id})-[:ENROLLED_IN]->(c:Course) RETURN c",
                id="S001"
            ).consume()

    measure("Neo4j student courses", neo_query)

    driver.close()
    cassandra.shutdown()
    cluster.shutdown()
    mongo.client.close()


if __name__ == "__main__":
    main()
