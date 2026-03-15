"""
Tests for the SchemaManager class.

Uses a real in-memory ChromaDB instance (no mocking) to verify
add, search, list, and delete operations.
"""

import pytest

from app.config.settings import VectorDBConfig
from app.core.schema_manager import SchemaManager
from app.vectordb.chroma_store import ChromaStore


@pytest.fixture()
def schema_manager(tmp_path):
    """Create a SchemaManager backed by a temporary ChromaDB instance."""
    config = VectorDBConfig(
        provider="chroma",
        persist_directory=str(tmp_path / "chroma_test"),
        collection_name="test_schemas",
    )
    store = ChromaStore(config=config)
    return SchemaManager(vector_store=store)


class TestSchemaManager:
    """Test suite for SchemaManager."""

    def test_add_and_list(self, schema_manager: SchemaManager):
        """Adding a schema should make it appear in list_schemas."""
        doc_id = schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="myapp_db",
            table_name="users",
            schema_text="CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL);",
        )

        assert doc_id  # non-empty ID
        schemas = schema_manager.list_schemas()
        assert len(schemas) == 1
        assert schemas[0]["metadata"]["db_type"] == "PostgreSQL"
        assert schemas[0]["metadata"]["table_name"] == "users"

    def test_add_multiple_schemas(self, schema_manager: SchemaManager):
        """Multiple schemas should all be stored and listed."""
        schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="myapp_db",
            table_name="users",
            schema_text="CREATE TABLE users (id SERIAL, name TEXT);",
        )
        schema_manager.add_schema(
            app_name="myapp",
            db_type="MySQL",
            db_name="shop_db",
            table_name="orders",
            schema_text="CREATE TABLE orders (id INT AUTO_INCREMENT, total DECIMAL);",
        )

        schemas = schema_manager.list_schemas()
        assert len(schemas) == 2

    def test_search_finds_relevant_schema(self, schema_manager: SchemaManager):
        """Searching should return schemas relevant to the query."""
        schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="myapp_db",
            table_name="users",
            schema_text="CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT, email TEXT);",
        )
        schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="myapp_db",
            table_name="orders",
            schema_text="CREATE TABLE orders (id SERIAL, user_id INT, total DECIMAL);",
        )

        results = schema_manager.search_schemas("find all users", top_k=1)
        assert len(results) >= 1
        assert results[0]["metadata"]["table_name"] == "users"

    def test_delete_schema(self, schema_manager: SchemaManager):
        """Deleting a schema should remove it from the store."""
        doc_id = schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="temp_db",
            table_name="temp_table",
            schema_text="CREATE TABLE temp_table (id INT);",
        )

        schema_manager.delete_schema(doc_id)
        schemas = schema_manager.list_schemas()
        assert len(schemas) == 0

    def test_upsert_same_table(self, schema_manager: SchemaManager):
        """Adding the same table twice should update (upsert), not duplicate."""
        schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="myapp_db",
            table_name="users",
            schema_text="CREATE TABLE users (id INT);",
        )
        schema_manager.add_schema(
            app_name="myapp",
            db_type="PostgreSQL",
            db_name="myapp_db",
            table_name="users",
            schema_text="CREATE TABLE users (id INT, name TEXT, email TEXT);",
        )

        schemas = schema_manager.list_schemas()
        assert len(schemas) == 1
        assert "email" in schemas[0]["text"]

    def test_deterministic_id(self, schema_manager: SchemaManager):
        """Same app_name + db_type + db_name + table_name should produce the same ID."""
        id1 = SchemaManager._generate_id("myapp", "PostgreSQL", "myapp_db", "users")
        id2 = SchemaManager._generate_id("myapp", "PostgreSQL", "myapp_db", "users")
        id3 = SchemaManager._generate_id("myapp", "MySQL", "myapp_db", "users")
        id4 = SchemaManager._generate_id("myapp", "PostgreSQL", "other_db", "users")
        id5 = SchemaManager._generate_id("other_app", "PostgreSQL", "myapp_db", "users")

        assert id1 == id2
        assert id1 != id3
        assert id1 != id4
        assert id1 != id5
