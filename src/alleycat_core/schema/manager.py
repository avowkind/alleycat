"""Schema manager for handling schema caching and management."""

from pathlib import Path

from .schema import Schema


class SchemaManager:
    """Manager class for handling schema caching and management."""

    def __init__(self) -> None:
        """Initialize schema manager."""
        self._schema_cache: dict[str, Schema] = {}

    def get_schema(self, schema_path: str | Path) -> Schema:
        """Get schema from cache or load from file.

        Args:
            schema_path: Path to schema file

        Returns:
            Schema: Loaded schema object

        Raises:
            SchemaValidationError: If schema is invalid or cannot be loaded

        """
        schema_path = str(schema_path)
        if schema_path not in self._schema_cache:
            self._schema_cache[schema_path] = Schema.from_file(schema_path)
        return self._schema_cache[schema_path]

    def clear_cache(self) -> None:
        """Clear schema cache."""
        self._schema_cache.clear()

    def validate_schema_file(self, schema_path: str | Path) -> None:
        """Validate schema file without caching.

        Args:
            schema_path: Path to schema file

        Raises:
            SchemaValidationError: If schema is invalid

        """
        Schema.from_file(schema_path)
