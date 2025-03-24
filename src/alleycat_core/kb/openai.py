"""OpenAI Knowledge Base provider implementation.

This module contains the implementation of the OpenAI KB provider.
It uses the OpenAI API to manage vector stores.

Author: Andrew Watkins <andrew@groat.nz>
"""

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from .. import logging
from .base import KBProvider


class OpenAIKBConfig(BaseModel):
    """Configuration for OpenAI KB provider."""

    api_key: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    file_purpose: Literal["assistants", "batch", "fine-tune", "vision", "user_data", "evals"] = "assistants"


class OpenAIKBProvider(KBProvider):
    """OpenAI implementation of KB provider."""

    def __init__(self, config: OpenAIKBConfig):
        """Initialize the OpenAI KB provider."""
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)

        logging.info("Initialized OpenAI KB provider")

    async def close(self) -> None:
        """Clean up resources and close any open connections."""
        try:
            if hasattr(self.client, "close"):
                await self.client.close()
        except Exception as e:
            logging.error(f"Error during provider cleanup: {e}")
            raise

    async def create_vector_store(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Create a new vector store.

        Args:
            name: Friendly name for the vector store
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing information about the created vector store

        """
        try:
            # Add the friendly name to the metadata
            metadata = self.config.metadata.copy()
            metadata["name"] = name

            # Create the vector store
            response = await self.client.vector_stores.create(name=name, metadata=metadata, **kwargs)

            return {"id": response.id, "name": name, "created_at": response.created_at, "metadata": response.metadata}
        except Exception as e:
            logging.error(f"Error creating vector store: {e}")
            raise

    async def list_vector_stores(self) -> list[dict[str, Any]]:
        """List all available vector stores."""
        try:
            response = await self.client.vector_stores.list()

            return [
                {"id": vs.id, "name": vs.name, "created_at": vs.created_at, "metadata": vs.metadata}
                for vs in response.data
            ]
        except Exception as e:
            logging.error(f"Error listing vector stores: {e}")
            raise

    async def get_vector_store(self, vector_store_id: str) -> dict[str, Any]:
        """Get information about a specific vector store."""
        try:
            response = await self.client.vector_stores.retrieve(vector_store_id)

            return {
                "id": response.id,
                "name": response.name,
                "created_at": response.created_at,
                "metadata": response.metadata,
            }
        except Exception as e:
            logging.error(f"Error getting vector store: {e}")
            raise

    async def delete_vector_store(self, vector_store_id: str) -> bool:
        """Delete a vector store."""
        try:
            await self.client.vector_stores.delete(vector_store_id)
            return True
        except Exception as e:
            logging.error(f"Error deleting vector store: {e}")
            return False

    async def _upload_file(self, file_path: Path) -> str:
        """Upload a file to OpenAI."""
        try:
            with open(file_path, "rb") as file:
                response = await self.client.files.create(file=file, purpose=self.config.file_purpose)
            return response.id
        except Exception as e:
            logging.error(f"Error uploading file {file_path}: {e}")
            raise

    async def add_files(self, vector_store_id: str, file_paths: Sequence[Path]) -> list[dict[str, Any]]:
        """Add files to a vector store."""
        try:
            logging.debug(f"Adding files to vector store {vector_store_id}")
            logging.debug(f"File paths: {file_paths}")
            result = []

            # First upload all files to get file IDs
            file_ids = await asyncio.gather(*[self._upload_file(path) for path in file_paths])
            logging.debug(f"Uploaded files, got file IDs: {file_ids}")

            # Process all files in a single batch instead of one by one
            logging.debug(f"Creating batch with {len(file_ids)} files")
            response = await self.client.vector_stores.file_batches.create(
                vector_store_id=vector_store_id,
                file_ids=file_ids,
            )

            # Wait for the batch to complete processing
            batch_id = response.id
            logging.debug(f"Created batch {batch_id}, waiting for processing")
            status = "processing"
            max_checks = 60  # Maximum number of status checks (60 seconds)
            checks = 0

            while status in ["processing", "pending", "in_progress"] and checks < max_checks:
                await asyncio.sleep(1)
                batch_status = await self.client.vector_stores.file_batches.retrieve(
                    vector_store_id=vector_store_id, batch_id=batch_id
                )
                status = batch_status.status
                logging.debug(f"Batch status: {status} (check {checks + 1}/{max_checks})")
                checks += 1

            if status == "completed":
                logging.debug(f"Successfully processed batch {batch_id}")
                # Create result entries for all files
                for file_id, file_path in zip(file_ids, file_paths, strict=False):
                    logging.debug(f"Added file {file_path} with ID {file_id}")
                    result.append({"file_id": file_id, "file_path": str(file_path), "batch_id": batch_id})
            else:
                logging.debug(f"Batch processing incomplete after {checks} checks, status: {status}")
                # Check each file individually to see if it was processed
                files_response = await self.client.vector_stores.files.list(vector_store_id=vector_store_id)
                processed_file_ids = [file.id for file in files_response.data]

                for file_id, file_path in zip(file_ids, file_paths, strict=False):
                    if file_id in processed_file_ids:
                        logging.debug(f"File {file_path} was successfully added")
                        result.append({"file_id": file_id, "file_path": str(file_path), "batch_id": batch_id})
                    else:
                        logging.debug(f"File {file_path} was not added")

            logging.debug(f"Returning result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error adding files to vector store: {e}")
            logging.debug(f"Exception: {e}")
            raise

    async def list_files(self, vector_store_id: str) -> list[dict[str, Any]]:
        """List files in a vector store."""
        try:
            response = await self.client.vector_stores.files.list(vector_store_id=vector_store_id)

            return [{"id": file.id, "created_at": file.created_at, "object": file.object} for file in response.data]
        except Exception as e:
            logging.error(f"Error listing files in vector store: {e}")
            raise

    async def delete_file(self, vector_store_id: str, file_id: str) -> bool:
        """Delete a file from a vector store."""
        try:
            await self.client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
            return True
        except Exception as e:
            logging.error(f"Error deleting file from vector store: {e}")
            return False


class OpenAIKBFactory:
    """Factory for creating OpenAI KB provider instances."""

    def create(self, **kwargs: Any) -> KBProvider:
        """Create an OpenAI KB provider instance.

        Args:
            **kwargs: Provider-specific configuration including api_key

        Returns:
            An instance of an OpenAI KB provider

        """
        config = OpenAIKBConfig(**kwargs)
        return OpenAIKBProvider(config)
