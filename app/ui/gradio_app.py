"""
Gradio-based web UI for the Query Generator application.

Provides two main tabs:
1. Add Schema — store database schemas in the vector store.
2. Generate Query — ask natural-language questions and get database queries.
"""

import logging

import gradio as gr

from app.core.query_generator import QueryGenerator
from app.core.schema_manager import SUPPORTED_DB_TYPES, SchemaManager

logger = logging.getLogger(__name__)


def create_app(
    schema_manager: SchemaManager,
    query_generator: QueryGenerator,
) -> gr.Blocks:
    """
    Build and return the Gradio Blocks application.

    Args:
        schema_manager: Manages schema storage and retrieval.
        query_generator: Orchestrates query generation.

    Returns:
        A configured gr.Blocks instance ready to launch.
    """

    def _add_schema(
        app_name: str, db_type: str, db_name: str, table_name: str, schema_text: str
    ) -> tuple[str, str]:
        """Handle adding a new schema."""
        # Validation
        if not table_name.strip():
            return "❌ **Error:** Table name is required.", _get_schemas_display()
        if not schema_text.strip():
            return "❌ **Error:** Schema definition is required.", _get_schemas_display()

        try:
            doc_id = schema_manager.add_schema(
                app_name=app_name.strip() or "default",
                db_type=db_type,
                db_name=db_name.strip() or "default",
                table_name=table_name.strip(),
                schema_text=schema_text.strip(),
            )
            return (
                f"✅ **Schema stored successfully!**\n\n"
                f"- **Application:** {app_name.strip() or 'default'}\n"
                f"- **Database Type:** {db_type}\n"
                f"- **Database Name:** {db_name.strip() or 'default'}\n"
                f"- **Table:** {table_name.strip()}\n"
                f"- **ID:** `{doc_id}`",
                _get_schemas_display(),
            )
        except Exception as e:
            logger.exception("Failed to add schema")
            return f"❌ **Error:** {e}", _get_schemas_display()

    def _delete_schema(schema_id: str) -> tuple[str, str]:
        """Handle deleting a schema."""
        if not schema_id.strip():
            return "❌ **Error:** Schema ID is required.", _get_schemas_display()

        try:
            schema_manager.delete_schema(schema_id.strip())
            return (
                f"✅ **Schema `{schema_id.strip()}` deleted.**",
                _get_schemas_display(),
            )
        except Exception as e:
            logger.exception("Failed to delete schema")
            return f"❌ **Error:** {e}", _get_schemas_display()

    def _get_schemas_display() -> str:
        """Build a markdown display of all stored schemas."""
        schemas = schema_manager.list_schemas()
        if not schemas:
            return "_No schemas stored yet. Add one using the form above._"

        lines: list[str] = ["| ID | App | DB Type | DB Name | Table |", "|---|---|---|---|---|"]
        for doc in schemas:
            meta = doc.get("metadata", {})
            lines.append(
                f"| `{doc['id']}` "
                f"| {meta.get('app_name', 'default')} "
                f"| {meta.get('db_type', '—')} "
                f"| {meta.get('db_name', 'default')} "
                f"| {meta.get('table_name', '—')} |"
            )
        return "\n".join(lines)

    def _view_schema(schema_id: str) -> tuple[str, str]:
        """Retrieve and display a schema's full definition."""
        if not schema_id.strip():
            return "", "❌ **Error:** Please enter a Schema ID."

        schemas = schema_manager.list_schemas()
        for doc in schemas:
            if doc["id"] == schema_id.strip():
                meta = doc.get("metadata", {})
                info = (
                    f"**Application:** {meta.get('app_name', 'default')}  \n"
                    f"**Database Type:** {meta.get('db_type', '—')}  \n"
                    f"**Database Name:** {meta.get('db_name', 'default')}  \n"
                    f"**Table:** {meta.get('table_name', '—')}  \n"
                    f"**ID:** `{doc['id']}`"
                )
                # Extract raw schema text (strip the enriched prefix)
                text = doc.get("text", "")
                # The stored text starts with "Database: ...\nTable: ...\nSchema:\n"
                if "Schema:\n" in text:
                    text = text.split("Schema:\n", 1)[1]
                return text, info

        return "", f"❌ **Error:** No schema found with ID `{schema_id.strip()}`."

    def _generate_query(
        question: str, app_name: str, db_name: str, db_type_filter: str
    ) -> tuple[str, str]:
        """Handle query generation."""
        if not question.strip():
            return "❌ Please enter a question.", ""

        try:
            result = query_generator.generate(
                question=question.strip(),
                app_name_filter=app_name.strip() if app_name.strip() else None,
                db_name_filter=db_name.strip() if db_name.strip() else None,
                db_type_filter=db_type_filter if db_type_filter != "All" else None,
            )

            # Build the schemas-used info
            schemas_info = ""
            if result["schemas_used"]:
                schemas_info = "**Schemas used as context:**\n\n"
                for s in result["schemas_used"]:
                    schemas_info += (
                        f"- `{s['app_name']}/{s['db_name']}.{s['table']}` "
                        f"({s['db_type']})\n"
                    )

            return result["query"], schemas_info

        except Exception as e:
            logger.exception("Query generation failed")
            return f"-- Error: {e}", ""

    # ─────────────────────────────────────────────
    # Build the UI
    # ─────────────────────────────────────────────
    with gr.Blocks(
        title="Query Generator",
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="blue",
        ),
    ) as app:
        gr.Markdown(
            "# 🗃️ Query Generator\n"
            "Store your database schemas and generate queries from natural language."
        )

        with gr.Tabs():
            # ── Tab 1: Add Schema ──────────────────
            with gr.TabItem("📋 Add Schema"):
                with gr.Row():
                    with gr.Column(scale=1):
                        app_name_input = gr.Textbox(
                            label="Application Name",
                            value="default",
                            placeholder="e.g., my_ecommerce_app",
                        )
                        db_type_input = gr.Dropdown(
                            choices=SUPPORTED_DB_TYPES,
                            value="PostgreSQL",
                            label="Database Type",
                        )
                        db_name_input = gr.Textbox(
                            label="Database Name",
                            value="default",
                            placeholder="e.g., ecommerce_db",
                        )
                        table_name_input = gr.Textbox(
                            label="Table Name",
                            placeholder="e.g., users, orders, products",
                        )
                    with gr.Column(scale=2):
                        schema_input = gr.Textbox(
                            label="Schema Definition",
                            placeholder=(
                                "Paste your CREATE TABLE statement, "
                                "JSON schema, or any schema definition here..."
                            ),
                            lines=12,
                        )

                with gr.Row():
                    add_btn = gr.Button("➕ Add Schema", variant="primary")

                add_status = gr.Markdown()

                gr.Markdown("### Stored Schemas")
                schemas_display = gr.Markdown(value=_get_schemas_display)

                with gr.Row():
                    with gr.Column(scale=3):
                        schema_id_input = gr.Textbox(
                            label="Schema ID",
                            placeholder="Paste a schema ID to view or delete",
                        )
                    with gr.Column(scale=1):
                        view_btn = gr.Button("👁️ View", variant="secondary")
                        delete_btn = gr.Button("🗑️ Delete", variant="stop")

                # View schema output
                with gr.Accordion("Schema Details", open=False) as schema_details:
                    view_info = gr.Markdown()
                    view_output = gr.Code(
                        label="Schema Definition",
                        language="sql",
                        interactive=False,
                    )

                delete_status = gr.Markdown()

                # Wire up events
                add_btn.click(
                    fn=_add_schema,
                    inputs=[app_name_input, db_type_input, db_name_input, table_name_input, schema_input],
                    outputs=[add_status, schemas_display],
                )
                view_btn.click(
                    fn=_view_schema,
                    inputs=[schema_id_input],
                    outputs=[view_output, view_info],
                )
                delete_btn.click(
                    fn=_delete_schema,
                    inputs=[schema_id_input],
                    outputs=[delete_status, schemas_display],
                )

            # ── Tab 2: Generate Query ──────────────
            with gr.TabItem("⚡ Generate Query"):
                with gr.Row():
                    question_input = gr.Textbox(
                        label="What query do you need?",
                        placeholder=(
                            "e.g., Get the total number of users who signed up "
                            "in the last 30 days"
                        ),
                        lines=3,
                        scale=2,
                    )
                with gr.Row():
                    app_name_filter = gr.Textbox(
                        label="Application Name",
                        value="default",
                        placeholder="Filter by application",
                        scale=1,
                    )
                    db_name_filter = gr.Textbox(
                        label="Database Name",
                        value="default",
                        placeholder="Filter by database",
                        scale=1,
                    )
                    db_filter = gr.Dropdown(
                        choices=["All"] + SUPPORTED_DB_TYPES,
                        value="All",
                        label="Database Type",
                        scale=1,
                    )

                generate_btn = gr.Button(
                    "🚀 Generate Query", variant="primary", size="lg"
                )

                query_output = gr.Code(
                    label="Generated Query",
                    language="sql",
                    interactive=False,
                )
                schemas_used_output = gr.Markdown(label="Context")

                # Wire up events
                generate_btn.click(
                    fn=_generate_query,
                    inputs=[question_input, app_name_filter, db_name_filter, db_filter],
                    outputs=[query_output, schemas_used_output],
                )

    return app
