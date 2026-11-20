import os
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase
from .breaker import CircuitBreaker


class DatabaseHub:
    def __init__(self):
        mongo_uri = os.environ["LAB16_MONGO_URI"]
        neo4j_password = os.environ["LAB16_NEO4J_PASSWORD"]

        self.mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=10
        )
        self.mongo = self.mongo_client["lab16"]

        self.cassandra_cluster = Cluster(
            [os.getenv("CASSANDRA_HOST", "lab16-cassandra")],
            port=int(os.getenv("CASSANDRA_PORT", "9042")),
            executor_threads=4
        )
        self.cassandra_session = self.cassandra_cluster.connect("lab16")

        self.neo4j_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://lab16-neo4j:7687"),
            auth=("neo4j", neo4j_password),
            max_connection_pool_size=10
        )

        self.breakers = {
            "mongo": CircuitBreaker(),
            "cassandra": CircuitBreaker(),
            "neo4j": CircuitBreaker()
        }

    def run(self, backend, function, *args, **kwargs):
        return self.breakers[backend].call(function, *args, **kwargs)

    def close(self):
        self.mongo_client.close()
        self.cassandra_session.shutdown()
        self.cassandra_cluster.shutdown()
        self.neo4j_driver.close()
