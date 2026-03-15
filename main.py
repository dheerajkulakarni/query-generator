"""
Query Generator — Main entry point.

Wires up configuration, vector store, LLM provider, and launches the Gradio UI.
"""

import logging

from app.config.settings import load_config
from app.core.query_generator import QueryGenerator
from app.core.schema_manager import SchemaManager
from app.llm.llm_provider import OpenAICompatibleProvider
from app.ui.gradio_app import create_app
from app.vectordb.chroma_store import ChromaStore

# ─── Logging setup ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize all components and launch the application."""
    # 1. Load configuration
    config = load_config()
    logger.info("Configuration loaded successfully")

    # 2. Initialize vector store
    vector_store = ChromaStore(config=config.vectordb)

    # 3. Initialize LLM provider
    llm_provider = OpenAICompatibleProvider(config=config.llm)

    # 4. Wire up core services
    schema_manager = SchemaManager(vector_store=vector_store)
    query_generator = QueryGenerator(
        schema_manager=schema_manager,
        llm_provider=llm_provider,
    )

    # 5. Build and launch the Gradio app
    app = create_app(
        schema_manager=schema_manager,
        query_generator=query_generator,
    )

    logger.info(
        "Launching Query Generator on %s:%d", config.app.host, config.app.port
    )
    app.launch(
        server_name=config.app.host,
        server_port=config.app.port,
        share=config.app.share,
    )


if __name__ == "__main__":
    main()
