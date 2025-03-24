"""Base classes and types for Knowledge Base providers.

This module defines the core interfaces and types for interacting with different
vector store providers. It includes base classes for vector stores management.

Author: Andrew Watkins <andrew@groat.nz>
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol


class KBProvider(ABC):
    """Abstract base class for Knowledge Base providers."""

    @abstractmethod
    async def create_vector_store(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Create a new vector store.

        Args:
            name: Friendly name for the vector store
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing information about the created vector store

        """
        pass

    @abstractmethod
    async def list_vector_stores(self) -> list[dict[str, Any]]:
        """List all available vector stores.

        Returns:
            List of dictionaries containing vector store information

        """
        pass

    @abstractmethod
    async def get_vector_store(self, vector_store_id: str) -> dict[str, Any]:
        """Get information about a specific vector store.

        Args:
            vector_store_id: ID of the vector store

        Returns:
            Dictionary containing vector store information

        """
        pass

    @abstractmethod
    async def delete_vector_store(self, vector_store_id: str) -> bool:
        """Delete a vector store.

        Args:
            vector_store_id: ID of the vector store to delete

        Returns:
            True if deletion was successful, False otherwise

        """
        pass

    @abstractmethod
    async def add_files(self, vector_store_id: str, file_paths: Sequence[Path]) -> list[dict[str, Any]]:
        """Add files to a vector store.

        Args:
            vector_store_id: ID of the vector store
            file_paths: Paths to the files to add

        Returns:
            List of dictionaries containing information about the added files

        """
        pass

    @abstractmethod
    async def list_files(self, vector_store_id: str) -> list[dict[str, Any]]:
        """List files in a vector store.

        Args:
            vector_store_id: ID of the vector store

        Returns:
            List of dictionaries containing file information

        """
        pass

    @abstractmethod
    async def delete_file(self, vector_store_id: str, file_id: str) -> bool:
        """Delete a file from a vector store.

        Args:
            vector_store_id: ID of the vector store
            file_id: ID of the file to delete

        Returns:
            True if deletion was successful, False otherwise

        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close any open connections.

        This method should be called when the provider is no longer needed.
        It should clean up any resources, close connections, and handle any necessary cleanup.
        """
        pass


class KBFactory(Protocol):
    """Protocol for KB provider factories."""

    def create(self, **kwargs: Any) -> KBProvider:
        """Create a KB provider instance.

        Args:
            **kwargs: Provider-specific configuration

        Returns:
            An instance of a KB provider

        """
        pass
