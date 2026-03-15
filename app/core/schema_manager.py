"""
Schema manager — handles storing, retrieving, and deleting database schemas.

Acts as the bridge between the application logic and the vector store,
enriching schema documents with metadata (database type, table name)
for structured retrieval.
"""

import hashlib
import logging
from typing import Any

from app.vectordb.base import VectorStore

logger = logging.getLogger(__name__)

# Supported database types
SUPPORTED_DB_TYPES = [
    "PostgreSQL",
    "MySQL",
    "SQLite",
    "MongoDB",
    "SQL Server",
    "Oracle",
    "MariaDB",
    "Other",
]


class SchemaManager:
    """
    Manages database schema storage and retrieval via a vector store.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        """
        Args:
            vector_store: A concrete VectorStore implementation.
        """
        self._store = vector_store

    @staticmethod
    def _generate_id(app_name: str, db_type: str, db_name: str, table_name: str) -> str:
        """Generate a deterministic document ID from app_name, db_type, db_name, and table_name."""
        raw = f"{app_name.lower()}:{db_type.lower()}:{db_name.lower()}:{table_name.lower()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def add_schema(
        self,
        app_name: str,
        db_type: str,
        db_name: str,
        table_name: str,
        schema_text: str,
    ) -> str:
        """
        Store a database schema in the vector store.

        Args:
            app_name: Application/project name (e.g., 'my_ecommerce_app').
            db_type: The database type (e.g., 'PostgreSQL', 'MongoDB').
            db_name: The database name (e.g., 'ecommerce_db').
            table_name: Name of the table / collection.
            schema_text: Raw schema definition (SQL DDL, JSON schema, etc.).

        Returns:
            The generated document ID.
        """
        doc_id = self._generate_id(app_name, db_type, db_name, table_name)

        # Enrich the text with context for better embeddings
        enriched_text = (
            f"Application: {app_name}\n"
            f"Database Type: {db_type}\n"
            f"Database Name: {db_name}\n"
            f"Table: {table_name}\n"
            f"Schema:\n{schema_text}"
        )

        metadata = {
            "app_name": app_name,
            "db_type": db_type,
            "db_name": db_name,
            "table_name": table_name,
        }

        self._store.add(document_id=doc_id, text=enriched_text, metadata=metadata)
        logger.info(
            "Schema stored — app='%s', db_type='%s', db_name='%s', table='%s', id='%s'",
            app_name,
            db_type,
            db_name,
            table_name,
            doc_id,
        )
        return doc_id

    def search_schemas(
        self, query: str, top_k: int = 3
    ) -> list[dict[str, Any]]:
        """
        Search for schemas relevant to a natural-language query.

        Args:
            query: The user's natural-language description.
            top_k: Maximum number of results.

        Returns:
            A list of matching schema documents with metadata.
        """
        return self._store.search(query=query, top_k=top_k)

    def list_schemas(self) -> list[dict[str, Any]]:
        """List all stored schemas."""
        return self._store.list_all()

    def delete_schema(self, schema_id: str) -> None:
        """
        Delete a schema by its ID.

        Args:
            schema_id: The document ID to delete.
        """
        self._store.delete(document_id=schema_id)
        logger.info("Schema deleted — id='%s'", schema_id)
