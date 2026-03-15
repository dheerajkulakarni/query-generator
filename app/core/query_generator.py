"""
Query generator — orchestrates schema retrieval and LLM-based query generation.

Retrieves the most relevant schemas from the vector store, constructs a
detailed prompt, and calls the LLM to produce a database query.
"""

import logging
from typing import Any, Optional

from app.core.schema_manager import SchemaManager
from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert database query generator. Your role is to generate precise, \
correct, and optimized database queries based on the user's request and the \
provided database schema(s).

Rules:
1. Generate ONLY the query — no explanations, no markdown fences, no commentary.
2. Use the exact table and column names from the provided schema.
3. Match the SQL dialect or query language to the database type specified in the schema.
4. For MongoDB, generate a valid MongoDB query/aggregation pipeline as JSON.
5. If the request is ambiguous, make reasonable assumptions and generate the most \
   likely intended query.
6. Always write safe, read-only queries unless the user explicitly asks for mutations.
7. Use proper aliasing and formatting for readability.\
"""

USER_PROMPT_TEMPLATE = """\
Given the following database schema(s):

{schemas}

User's request: {question}

Generate the appropriate database query.\
"""


class QueryGenerator:
    """
    Orchestrates the query generation pipeline:
    1. Retrieves relevant schemas from the vector store.
    2. Constructs a prompt with the schemas and the user's question.
    3. Calls the LLM to generate the query.
    """

    def __init__(
        self, schema_manager: SchemaManager, llm_provider: LLMProvider
    ) -> None:
        """
        Args:
            schema_manager: Manager for schema CRUD and search.
            llm_provider: A concrete LLMProvider implementation.
        """
        self._schema_manager = schema_manager
        self._llm = llm_provider

    def generate(
        self,
        question: str,
        app_name_filter: Optional[str] = None,
        db_name_filter: Optional[str] = None,
        db_type_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Generate a database query from a natural-language question.

        Args:
            question: The user's natural-language question.
            app_name_filter: Optional filter to restrict to a specific application.
            db_name_filter: Optional filter to restrict to a specific database.
            db_type_filter: Optional filter to restrict by database type.
            top_k: Number of schemas to retrieve for context.

        Returns:
            A dict containing:
                - 'query': The generated database query.
                - 'schemas_used': List of schemas used as context.
        """
        # Step 1: Retrieve relevant schemas (fetch more to allow filtering)
        search_query = question
        if app_name_filter:
            search_query = f"{app_name_filter} {search_query}"
        if db_name_filter:
            search_query = f"{db_name_filter} {search_query}"

        retrieved = self._schema_manager.search_schemas(
            query=search_query, top_k=top_k
        )

        # Filter by app_name if specified
        if app_name_filter:
            filtered = [
                doc
                for doc in retrieved
                if doc.get("metadata", {}).get("app_name", "").lower()
                == app_name_filter.lower()
            ]
            if filtered:
                retrieved = filtered

        # Filter by db_name if specified (only tables in the same DB can be joined)
        if db_name_filter:
            filtered = [
                doc
                for doc in retrieved
                if doc.get("metadata", {}).get("db_name", "").lower()
                == db_name_filter.lower()
            ]
            if filtered:
                retrieved = filtered

        # Optionally filter by db_type in metadata
        if db_type_filter and db_type_filter != "All":
            filtered = [
                doc
                for doc in retrieved
                if doc.get("metadata", {}).get("db_type", "").lower()
                == db_type_filter.lower()
            ]
            if filtered:
                retrieved = filtered

        if not retrieved:
            return {
                "query": "-- No matching schemas found. Please add relevant schemas first.",
                "schemas_used": [],
            }

        # Step 2: Build the prompt
        schemas_text = self._format_schemas(retrieved)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            schemas=schemas_text, question=question
        )

        logger.info(
            "Generating query — question='%s', schemas_used=%d",
            question[:80],
            len(retrieved),
        )

        # Step 3: Call the LLM
        generated_query = self._llm.generate(
            prompt=user_prompt, system_prompt=SYSTEM_PROMPT
        )

        # Clean up the response (strip markdown fences if the LLM adds them)
        generated_query = self._clean_query(generated_query)

        return {
            "query": generated_query,
            "schemas_used": [
                {
                    "app_name": doc.get("metadata", {}).get("app_name", "unknown"),
                    "table": doc.get("metadata", {}).get("table_name", "unknown"),
                    "db_type": doc.get("metadata", {}).get("db_type", "unknown"),
                    "db_name": doc.get("metadata", {}).get("db_name", "unknown"),
                }
                for doc in retrieved
            ],
        }

    @staticmethod
    def _format_schemas(schemas: list[dict[str, Any]]) -> str:
        """Format retrieved schemas into a readable string for the prompt."""
        parts: list[str] = []
        for i, doc in enumerate(schemas, 1):
            meta = doc.get("metadata", {})
            parts.append(
                f"--- Schema {i} ---\n"
                f"Application: {meta.get('app_name', 'Unknown')}\n"
                f"Database Type: {meta.get('db_type', 'Unknown')}\n"
                f"Database Name: {meta.get('db_name', 'Unknown')}\n"
                f"Table: {meta.get('table_name', 'Unknown')}\n"
                f"{doc.get('text', '')}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def _clean_query(raw: str) -> str:
        """Remove markdown code fences if present."""
        cleaned = raw.strip()
        # Remove ```sql ... ``` or ``` ... ```
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Drop first line (```sql or ```) and last line (```)
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            cleaned = "\n".join(lines).strip()
        return cleaned
