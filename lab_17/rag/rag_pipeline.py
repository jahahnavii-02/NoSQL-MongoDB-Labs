import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

load_dotenv(PROJECT_DIR / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE = os.getenv("MONGODB_DATABASE", "lab17")
COLLECTION = os.getenv("MONGODB_COLLECTION", "threat_chunks")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")

CHUNK_SIZE = 100
OVERLAP = 20
TOP_K = 3
MEMORY_LIMIT = 5

DOCUMENT_FILE = BASE_DIR / "documents" / "threat_intel.json"


# --------------------------------------------------
# OLLAMA EMBEDDINGS
# --------------------------------------------------

def generate_embedding(text):
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": EMBED_MODEL,
            "input": text
        },
        timeout=120
    )

    response.raise_for_status()
    data = response.json()

    if "embeddings" not in data or not data["embeddings"]:
        raise RuntimeError("Ollama returned no embedding.")

    return data["embeddings"][0]


# --------------------------------------------------
# DOCUMENT CHUNKING
# --------------------------------------------------

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()

    if not words:
        return []

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk = words[start:start + chunk_size]

        if chunk:
            chunks.append(" ".join(chunk))

        if start + chunk_size >= len(words):
            break

    return chunks


# --------------------------------------------------
# LOAD AND PROCESS DOCUMENTS
# --------------------------------------------------

def load_documents():
    if not DOCUMENT_FILE.exists():
        raise FileNotFoundError(DOCUMENT_FILE)

    with open(DOCUMENT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def prepare_chunks():
    documents = load_documents()
    processed = []

    for document in documents:
        chunks = chunk_text(document["content"])

        for number, chunk in enumerate(chunks):
            processed.append({
                "title": document["title"],
                "source": document["source"],
                "chunk_number": number,
                "text": chunk,
                "embedding": generate_embedding(chunk),
                "created_at": datetime.now(timezone.utc)
            })

    return processed


# --------------------------------------------------
# MONGODB CONNECTION AND STORAGE
# --------------------------------------------------

def connect_database():
    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI is not configured in .env")

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    database = client[DATABASE]

    return client, database


def store_chunks(collection, chunks):
    if not chunks:
        raise ValueError("No document chunks to store.")

    collection.delete_many({})

    collection.insert_many(chunks)

    print(f"Stored {len(chunks)} document chunks.")


# --------------------------------------------------
# VECTOR SEARCH
# --------------------------------------------------

def retrieve_context(collection, question):
    query_vector = generate_embedding(question)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 30,
                "limit": TOP_K
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "source": 1,
                "text": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    return list(collection.aggregate(pipeline))


# --------------------------------------------------
# CONVERSATION MEMORY
# --------------------------------------------------

def get_recent_memory(memory_collection, session_id):
    history = list(
        memory_collection.find(
            {"session_id": session_id},
            {"_id": 0, "question": 1, "answer": 1}
        ).sort("created_at", -1).limit(MEMORY_LIMIT)
    )

    history.reverse()
    return history


def save_memory(memory_collection, session_id, question, answer):
    memory_collection.insert_one({
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "created_at": datetime.now(timezone.utc)
    })


# --------------------------------------------------
# GENERATE ANSWER USING LOCAL OLLAMA
# --------------------------------------------------

def generate_answer(question, retrieved, history):
    context = "\n\n".join(
        f"Source: {item['source']}\n"
        f"Topic: {item['title']}\n"
        f"Information: {item['text']}"
        for item in retrieved
    )

    conversation = "\n".join(
        f"User: {item['question']}\n"
        f"Assistant: {item['answer']}"
        for item in history
    )

    prompt = f"""
You are a threat-intelligence assistant.

Answer the user's question using the retrieved information.
Do not invent facts. If the context is insufficient, clearly say so.

Previous conversation:
{conversation}

Retrieved threat-intelligence context:
{context}

Current question:
{question}

Provide a clear and concise answer.
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()["response"].strip()


# --------------------------------------------------
# COMPLETE RAG PIPELINE
# --------------------------------------------------

def initialize_pipeline():
    print("Connecting to MongoDB Atlas...")

    client, database = connect_database()

    chunks_collection = database[COLLECTION]
    memory_collection = database["conversation_memory"]

    print("Generating document embeddings...")
    chunks = prepare_chunks()

    print("Storing document chunks...")
    store_chunks(chunks_collection, chunks)

    print("RAG pipeline initialized successfully.")

    return client, chunks_collection, memory_collection


def ask_question(collection, memory_collection, question, session_id):
    history = get_recent_memory(memory_collection, session_id)

    retrieved = retrieve_context(collection, question)

    if not retrieved:
        context = []
        answer = (
            "I could not find relevant information in the "
            "available threat-intelligence documents."
        )
    else:
        answer = generate_answer(question, retrieved, history)

    save_memory(memory_collection, session_id, question, answer)

    return {
        "question": question,
        "answer": answer,
        "retrieved_sources": [
            {
                "title": item["title"],
                "source": item["source"],
                "score": item["score"]
            }
            for item in retrieved
        ]
    }


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

if __name__ == "__main__":
    client = None

    try:
        client, chunks_collection, memory_collection = (
            initialize_pipeline()
        )

        session_id = "lab17-demo"

        print("\nThreat Intelligence RAG is ready.")
        print("Type 'exit' to stop.\n")

        while True:
            question = input("You: ").strip()

            if question.lower() == "exit":
                break

            if not question:
                continue

            result = ask_question(
                chunks_collection,
                memory_collection,
                question,
                session_id
            )

            print("\nAssistant:", result["answer"])

            print("\nRetrieved sources:")
            for source in result["retrieved_sources"]:
                print(
                    f"- {source['title']} "
                    f"(score: {source['score']:.4f})"
                )

            print()

    except (PyMongoError, requests.RequestException, RuntimeError,
            FileNotFoundError, ValueError) as error:
        print(f"Pipeline error: {type(error).__name__}")
        print("Check the local service or database connection.")

    finally:
        if client:
            client.close()