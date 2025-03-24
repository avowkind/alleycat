"""Configuration settings for AlleyCat."""

from pathlib import Path
from typing import Any, Literal

from platformdirs import user_config_dir, user_data_dir
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from alleycat_core import logging


class Settings(BaseSettings):
    """AlleyCat configuration settings."""

    # LLM Provider settings
    provider: Literal["openai"] = "openai"
    openai_api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature", ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, description="Maximum number of tokens to generate")

    # File settings
    file_path: str | None = Field(default=None, description="Path to a file to upload")
    file_id: str | None = Field(default=None, description="ID of the uploaded file")

    # Chat settings
    history_file: Path | None = Field(default=None, description="Path to chat history file")
    max_history: int = Field(default=100, description="Maximum number of messages to keep in history")

    # Output settings
    output_format: Literal["text", "markdown", "json"] = Field(
        default="text", description="Output format for responses"
    )

    # Knowledge Base settings
    knowledge_bases: dict[str, str] = Field(
        default_factory=dict, description="Mapping of friendly names to vector store IDs"
    )
    kb_files: dict[str, dict[str, str]] = Field(
        default_factory=dict, description="Mapping of vector store IDs to files (file_id -> file_path)"
    )
    default_kb: str | None = Field(default=None, description="Default knowledge base to use")

    # Tool settings
    enable_web_search: bool = Field(default=False, description="Enable web search tool")
    vector_store_id: str = Field(default="", description="Vector store ID for file search tool")
    tools_requested: str = Field(default="", description="Comma-separated list of requested tools")

    # Persona settings
    personas_dir: Path | None = Field(default=None, description="Directory containing persona instruction files")

    # Config settings
    config_file: Path | None = Field(default=None, description="Path to config file")

    model_config = SettingsConfigDict(
        env_prefix="ALLEYCAT_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and load from file if available."""
        super().__init__(**kwargs)
        # Since we can't call the validator directly, initialize paths manually if needed
        if self.config_file is None:
            config_dir = Path(user_config_dir("alleycat"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / "config.yml"

        # Then load settings from file
        self.load_from_file()
        logging.debug(f"After initialization, knowledge_bases: {self.knowledge_bases}")
        logging.debug(f"After initialization, kb_files: {self.kb_files}")

    @model_validator(mode="after")
    def set_default_paths(self) -> "Settings":
        """Set default paths for configuration files."""
        # Use platformdirs to get standard OS-specific directories
        if self.config_file is None:
            config_dir = Path(user_config_dir("alleycat"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / "config.yml"

        if self.history_file is None:
            data_dir = Path(user_data_dir("alleycat"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = data_dir / "history.json"

        if self.personas_dir is None:
            config_dir = Path(user_config_dir("alleycat"))
            personas_dir = config_dir / "personas"
            personas_dir.mkdir(parents=True, exist_ok=True)
            self.personas_dir = personas_dir

        return self

    def load_from_file(self) -> None:
        """Load settings from config file if it exists."""
        if self.config_file is None or not self.config_file.exists():
            logging.debug(f"No config file found at {self.config_file}")
            return

        # Parse YAML file
        import yaml

        try:
            with open(str(self.config_file), encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logging.debug(f"Config file at {self.config_file} is empty or invalid")
                return

            logging.debug(f"Loaded raw data from {self.config_file}: {config_data}")

            # Only update fields that are explicitly set in the config file
            for key, value in config_data.items():
                if hasattr(self, key) and value is not None:
                    # Special handling for dictionary fields
                    if isinstance(value, dict) and hasattr(self, key) and isinstance(getattr(self, key), dict):
                        current_value = getattr(self, key)
                        current_value.clear()  # Clear existing
                        current_value.update(value)  # Update with new values
                    else:
                        setattr(self, key, value)

            logging.debug(f"After loading, knowledge_bases: {self.knowledge_bases}")
            logging.debug(f"After loading, kb_files: {self.kb_files}")
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            import traceback

            logging.debug(traceback.format_exc())

    def save_to_file(self) -> None:
        """Save current settings to config file."""
        if self.config_file is None:
            logging.debug("No config file path set")
            return

        # Ensure parent directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict, excluding None values and objects that can't be serialized
        config_data = {}
        for key, value in self.model_dump().items():
            # Skip None values and Path objects
            if value is None or isinstance(value, Path | bytes):
                continue
            config_data[key] = value

        try:
            # Write to YAML file
            import yaml

            with open(str(self.config_file), "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            logging.debug(f"Saved settings to {self.config_file}")
            logging.debug(f"Saved knowledge_bases: {self.knowledge_bases}")
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
