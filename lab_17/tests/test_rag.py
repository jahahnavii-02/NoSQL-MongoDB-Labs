import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rag"))

from rag_pipeline import chunk_text, load_documents


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_chunk_text_short_document():
    text = " ".join(["threat"] * 49)
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert len(chunks[0].split()) == 49


def test_chunk_text_long_document():
    text = " ".join(["security"] * 250)
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert all(len(chunk.split()) <= 100 for chunk in chunks)


def test_chunk_overlap():
    words = [f"word{i}" for i in range(150)]
    chunks = chunk_text(" ".join(words))

    first = chunks[0].split()
    second = chunks[1].split()

    assert first[-20:] == second[:20]


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("sample text", chunk_size=10, overlap=10)


def test_load_documents():
    documents = load_documents()

    assert len(documents) == 5
    assert all("title" in doc for doc in documents)
    assert all("source" in doc for doc in documents)
    assert all("content" in doc for doc in documents)