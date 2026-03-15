"""
ChromaDB implementation of the VectorStore interface.

Uses ChromaDB's PersistentClient for local, file-based vector storage
with built-in embedding support (default: all-MiniLM-L6-v2).
"""

import logging
from typing import Any

import chromadb

from app.config.settings import VectorDBConfig
from app.vectordb.base import VectorStore

logger = logging.getLogger(__name__)


class ChromaStore(VectorStore):
    """
    Vector store backed by ChromaDB.

    Persists data to a local directory and uses ChromaDB's default
    embedding function for automatic text embedding.
    """

    def __init__(self, config: VectorDBConfig) -> None:
        """
        Initialize the ChromaDB client and collection.

        Args:
            config: Vector database configuration.
        """
        self._client = chromadb.PersistentClient(path=config.persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB initialized — collection='%s', persist_dir='%s'",
            config.collection_name,
            config.persist_directory,
        )

    def add(
        self,
        document_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        """Store a document with its embedding."""
        self._collection.upsert(
            ids=[document_id],
            documents=[text],
            metadatas=[metadata],
        )
        logger.debug("Upserted document id='%s'", document_id)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Search for similar documents by query text."""
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        documents: list[dict[str, Any]] = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                documents.append(
                    {
                        "id": doc_id,
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                )
        return documents

    def delete(self, document_id: str) -> None:
        """Delete a document by its ID."""
        self._collection.delete(ids=[document_id])
        logger.debug("Deleted document id='%s'", document_id)

    def list_all(self) -> list[dict[str, Any]]:
        """List all stored documents."""
        results = self._collection.get()

        documents: list[dict[str, Any]] = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                documents.append(
                    {
                        "id": doc_id,
                        "text": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    }
                )
        return documents
