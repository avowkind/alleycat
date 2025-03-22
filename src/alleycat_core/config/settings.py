"""Configuration settings for AlleyCat."""

from pathlib import Path
from typing import Literal

from platformdirs import user_cache_dir, user_config_dir, user_data_dir
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @model_validator(mode="after")
    def set_default_paths(self) -> "Settings":
        """Set default paths for files and directories using XDG standards."""
        app_name = "alleycat"

        # Get standard directories
        config_dir = Path(user_config_dir(app_name))
        data_dir = Path(user_data_dir(app_name))
        cache_dir = Path(user_cache_dir(app_name))

        # Ensure directories exist
        config_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Set default paths if not explicitly set
        if self.config_file is None:
            self.config_file = config_dir / "config.yml"

        if self.history_file is None:
            self.history_file = data_dir / "history.json"

        if self.personas_dir is None:
            self.personas_dir = data_dir / "personas"

        return self

    def load_from_file(self) -> None:
        """Load settings from config file if it exists."""
        if self.config_file is None or not self.config_file.exists():
            return

        # Parse YAML file
        import yaml

        with open(str(self.config_file), encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            return

        # Only update fields that are explicitly set in the config file
        for key, value in config_data.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

    def save_to_file(self) -> None:
        """Save current settings to config file."""
        if self.config_file is None:
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

        # Write to YAML file
        import yaml

        with open(str(self.config_file), "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)
