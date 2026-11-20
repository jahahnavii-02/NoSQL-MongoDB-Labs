import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    APP_NAME = os.getenv("APP_NAME", "ThreatSentry AI")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27133/")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "threatsentry")

    CASSANDRA_HOSTS = _csv_env("CASSANDRA_HOSTS", "127.0.0.1")
    CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
    CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "threatsentry")

    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", os.getenv("LAB16_NEO4J_PASSWORD", ""))

    OLLAMA_BASE_URL = os.getenv(
        "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
    ).rstrip("/")
    OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")
    OLLAMA_EMBED_MODEL = os.getenv(
        "OLLAMA_EMBED_MODEL", "mxbai-embed-large"
    )

    # Where the monitored Ubuntu system lives: "wsl" (Windows host + WSL2) or "local" (Linux/Docker)
    SCANNER_MODE = os.getenv("SCANNER_MODE", "wsl").lower()
    WSL_DISTRIBUTION = os.getenv("WSL_DISTRIBUTION", "Ubuntu")
    # Fixes are only logged unless this is explicitly set to "false"
    MITIGATION_DRY_RUN = os.getenv("MITIGATION_DRY_RUN", "true").lower() != "false"
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "350"))


settings = Settings()

