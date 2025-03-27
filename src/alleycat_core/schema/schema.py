"""Schema class for handling JSON schema validation and processing."""

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


class SchemaValidationError(Exception):
    """Exception raised for schema validation errors."""

    pass


class Schema(BaseModel):
    """Schema for structured output."""

    type: Literal["json_schema"] = "json_schema"
    name: str
    json_schema_data: dict[str, Any] = Field(..., description="JSON schema definition", alias="schema")
    strict: bool = True

    @classmethod
    def from_file(cls, file_path: str | Path) -> "Schema":
        """Load schema from a JSON file.

        Args:
            file_path: Path to the JSON schema file

        Returns:
            Schema: Loaded schema object

        Raises:
            SchemaValidationError: If schema file is invalid or cannot be loaded

        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise SchemaValidationError(f"Schema file not found: {file_path}")

            with open(file_path, encoding="utf-8") as f:
                schema = json.load(f)

            # Create schema object with name from filename and raw schema
            return cls(
                name=file_path.stem.replace(".", "_"),
                schema=schema,
            )

        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"Invalid JSON in schema file: {e}") from e
        except ValidationError as e:
            raise SchemaValidationError(f"Invalid schema structure: {e}") from e
        except Exception as e:
            raise SchemaValidationError(f"Error loading schema: {e}") from e

    def to_request_format(self) -> dict[str, Any]:
        """Convert schema to format expected by OpenAI API.

        Returns:
            Dict[str, Any]: Schema in OpenAI API format

        """
        return {"type": self.type, "schema": self.json_schema_data, "name": self.name, "strict": self.strict}

    def validate_response(self, response: dict[str, Any]) -> None:
        """Validate response against schema.

        Args:
            response: Response data to validate

        Raises:
            SchemaValidationError: If response does not match schema

        """
        # TODO: Implement response validation against schema
        # This will require a JSON Schema validator like jsonschema
        pass

    def validate_data(self, data: Any) -> bool:
        """Validate data against the schema."""
        # TODO: Implement validation
        return True
