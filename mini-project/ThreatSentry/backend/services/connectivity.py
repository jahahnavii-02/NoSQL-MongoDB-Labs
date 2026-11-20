import requests
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase

from backend.core.config import settings


def check_mongodb():
    client = None
    try:
        client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
        )
        client.admin.command("ping")
        return {"status": "connected"}
    except Exception:
        return {"status": "unavailable"}
    finally:
        if client is not None:
            client.close()


def check_cassandra():
    cluster = None
    session = None
    try:
        cluster = Cluster(
            contact_points=settings.CASSANDRA_HOSTS,
            port=settings.CASSANDRA_PORT,
            connect_timeout=5,
        )
        session = cluster.connect()
        session.execute("SELECT release_version FROM system.local")
        return {"status": "connected"}
    except Exception:
        return {"status": "unavailable"}
    finally:
        if session is not None:
            session.shutdown()
        if cluster is not None:
            cluster.shutdown()


def check_neo4j():
    if not settings.NEO4J_PASSWORD:
        return {"status": "not_configured"}

    driver = None
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=5,
        )
        driver.verify_connectivity()
        return {"status": "connected"}
    except Exception:
        return {"status": "unavailable"}
    finally:
        if driver is not None:
            driver.close()


def check_ollama():
    try:
        response = requests.get(
            f"{settings.OLLAMA_BASE_URL}/api/tags",
            timeout=5,
        )
        response.raise_for_status()
        models = response.json().get("models", [])
        names = [model.get("name", "") for model in models]

        return {
            "status": "connected",
            "chat_model_available": any(
                name == settings.OLLAMA_CHAT_MODEL
                or name.startswith(settings.OLLAMA_CHAT_MODEL + ":")
                for name in names
            ),
            "embedding_model_available": any(
                name == settings.OLLAMA_EMBED_MODEL
                or name.startswith(settings.OLLAMA_EMBED_MODEL + ":")
                for name in names
            ),
        }
    except Exception:
        return {"status": "unavailable"}


def check_all_services():
    return {
        "mongodb": check_mongodb(),
        "cassandra": check_cassandra(),
        "neo4j": check_neo4j(),
        "ollama": check_ollama(),
    }
