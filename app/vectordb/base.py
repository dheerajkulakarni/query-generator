"""
Abstract base class for vector store implementations.

To add a new vector database provider:
1. Create a new file in this package (e.g., `pinecone_store.py`).
2. Implement the `VectorStore` interface.
3. Update the factory in `__init__.py` or wire it up in `main.py`.
"""

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """
    Abstract interface for vector database operations.

    All vector store implementations must inherit from this class
    and implement all abstract methods.
    """

    @abstractmethod
    def add(
        self,
        document_id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        """
        Store a document with its embedding in the vector database.

        Args:
            document_id: Unique identifier for the document.
            text: The text content to embed and store.
            metadata: Additional metadata to store alongside the document.
        """
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """
        Search for the most similar documents to the query.

        Args:
            query: The natural-language search query.
            top_k: Number of top results to return.

        Returns:
            A list of dicts, each containing 'id', 'text', 'metadata',
            and 'score' (similarity score).
        """
        ...

    @abstractmethod
    def delete(self, document_id: str) -> None:
        """
        Delete a document from the vector store.

        Args:
            document_id: Unique identifier of the document to delete.
        """
        ...

    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]:
        """
        List all stored documents.

        Returns:
            A list of dicts, each containing 'id', 'text', and 'metadata'.
        """
        ...
