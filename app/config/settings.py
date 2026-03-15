"""
Configuration management for the Query Generator application.

Loads settings from config.yaml and allows overrides via environment variables.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(default="gemini", description="Provider name (gemini, openai, ollama)")
    model: str = Field(default="gemini-2.0-flash", description="Model identifier")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    base_url: Optional[str] = Field(
        default=None, description="Custom API base URL (auto-resolved from provider if not set)"
    )
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Sampling temperature"
    )


class VectorDBConfig(BaseModel):
    """Vector database configuration."""

    provider: str = Field(default="chroma", description="Vector DB provider name")
    persist_directory: str = Field(
        default="./chroma_data", description="Directory to persist vector data"
    )
    collection_name: str = Field(
        default="schemas", description="Name of the collection/index"
    )


class AppConfig(BaseModel):
    """Application server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=7860, description="Server port")
    share: bool = Field(default=False, description="Create a public Gradio link")


class Settings(BaseModel):
    """Root configuration model."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    vectordb: VectorDBConfig = Field(default_factory=VectorDBConfig)
    app: AppConfig = Field(default_factory=AppConfig)


def load_config(config_path: str = "config.yaml") -> Settings:
    """
    Load configuration from a YAML file and overlay with environment variables.

    Priority (highest to lowest):
    1. Environment variables
    2. config.yaml values
    3. Pydantic defaults

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        A validated Settings instance.
    """
    config_data = {}

    # Load .env file into environment variables
    load_dotenv()

    # Load from YAML if file exists
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}

    # Build settings from YAML
    settings = Settings(**config_data)

    # Override with environment variables
    # LLM settings
    if api_key := os.getenv("LLM_API_KEY"):
        settings.llm.api_key = api_key
    if base_url := os.getenv("LLM_BASE_URL"):
        settings.llm.base_url = base_url
    if model := os.getenv("LLM_MODEL"):
        settings.llm.model = model
    if temperature := os.getenv("LLM_TEMPERATURE"):
        settings.llm.temperature = float(temperature)

    # Vector DB settings
    if persist_dir := os.getenv("VECTORDB_PERSIST_DIR"):
        settings.vectordb.persist_directory = persist_dir
    if collection := os.getenv("VECTORDB_COLLECTION"):
        settings.vectordb.collection_name = collection

    return settings
