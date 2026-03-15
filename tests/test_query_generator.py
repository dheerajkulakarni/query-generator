"""
Tests for the QueryGenerator class.

Uses a mock LLM provider to test prompt construction and query cleaning
without making real API calls.
"""

import pytest

from app.config.settings import VectorDBConfig
from app.core.query_generator import QueryGenerator
from app.core.schema_manager import SchemaManager
from app.llm.base import LLMProvider
from app.vectordb.chroma_store import ChromaStore


class MockLLMProvider(LLMProvider):
    """Mock LLM that returns the prompt it received, for assertion."""

    def __init__(self):
        self.last_prompt = ""
        self.last_system_prompt = ""
        self.response = "SELECT COUNT(*) FROM users;"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return self.response


@pytest.fixture()
def mock_llm():
    return MockLLMProvider()


@pytest.fixture()
def query_generator(tmp_path, mock_llm):
    """Create a QueryGenerator with a real ChromaDB and mock LLM."""
    config = VectorDBConfig(
        provider="chroma",
        persist_directory=str(tmp_path / "chroma_test"),
        collection_name="test_schemas",
    )
    store = ChromaStore(config=config)
    schema_manager = SchemaManager(vector_store=store)

    # Pre-populate with test schemas
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
        schema_text="CREATE TABLE orders (id SERIAL, user_id INT, total DECIMAL, created_at TIMESTAMP);",
    )

    return QueryGenerator(schema_manager=schema_manager, llm_provider=mock_llm)


class TestQueryGenerator:
    """Test suite for QueryGenerator."""

    def test_generate_returns_query(self, query_generator: QueryGenerator):
        """Generate should return a query string."""
        result = query_generator.generate("Get total number of users")
        assert "query" in result
        assert result["query"]  # non-empty

    def test_generate_returns_schemas_used(self, query_generator: QueryGenerator):
        """Generate should report which schemas were used as context."""
        result = query_generator.generate("Get total number of users")
        assert "schemas_used" in result
        assert len(result["schemas_used"]) > 0

    def test_prompt_includes_schema(self, query_generator: QueryGenerator, mock_llm):
        """The prompt sent to the LLM should include the retrieved schema."""
        query_generator.generate("Count all users")
        assert "users" in mock_llm.last_prompt

    def test_system_prompt_is_set(self, query_generator: QueryGenerator, mock_llm):
        """A system prompt should be passed to the LLM."""
        query_generator.generate("Count all users")
        assert mock_llm.last_system_prompt  # non-empty

    def test_clean_query_strips_markdown(self):
        """Markdown code fences should be stripped from LLM output."""
        raw = "```sql\nSELECT * FROM users;\n```"
        cleaned = QueryGenerator._clean_query(raw)
        assert cleaned == "SELECT * FROM users;"

    def test_clean_query_no_fences(self):
        """Plain queries should pass through unchanged."""
        raw = "SELECT * FROM users;"
        cleaned = QueryGenerator._clean_query(raw)
        assert cleaned == "SELECT * FROM users;"

    def test_no_schemas_found(self, tmp_path):
        """When no schemas exist, a helpful message should be returned."""
        config = VectorDBConfig(
            provider="chroma",
            persist_directory=str(tmp_path / "empty_chroma"),
            collection_name="empty_schemas",
        )
        store = ChromaStore(config=config)
        sm = SchemaManager(vector_store=store)
        llm = MockLLMProvider()
        qg = QueryGenerator(schema_manager=sm, llm_provider=llm)

        result = qg.generate("Get all users")
        assert "No matching schemas" in result["query"]
