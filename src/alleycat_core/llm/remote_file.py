"""RemoteFile interface and implementations.

This module contains the abstract interface for remote files and concrete implementations
for different file types (uploaded files vs text-based files).

Author: Andrew Watkins <andrew@groat.nz>
"""

from abc import ABC, abstractmethod
from pathlib import Path

from openai import AsyncOpenAI
from openai.types.responses.easy_input_message_param import EasyInputMessageParam

from .. import logging


class RemoteFile(ABC):
    """Abstract interface for remote files."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the remote file, uploading if necessary."""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up the remote file, deleting if necessary."""
        pass

    @abstractmethod
    def get_file_prompt(self, input_text: str) -> EasyInputMessageParam:
        """Get a file prompt that can be included in the input list.

        Args:
            input_text: The user's input text

        Returns:
            An EasyInputMessageParam that can be added to the input list

        """
        pass


class UploadedFile(RemoteFile):
    """A file that has been uploaded to the OpenAI API."""

    def __init__(self, file_path: str, client: AsyncOpenAI):
        """Initialize the uploaded file.

        Args:
            file_path: Path to the file to upload
            client: The OpenAI client

        """
        self.file_path = file_path
        self.client = client
        self.file_id: str | None = None

    async def initialize(self) -> bool:
        """Upload the file to OpenAI.

        Returns:
            True if the file was uploaded successfully, False otherwise

        """
        path = Path(self.file_path)
        if not path.exists():
            logging.error(f"File not found: {self.file_path}")
            return False

        try:
            with open(path, "rb") as file:
                response = await self.client.files.create(
                    file=file,
                    purpose="user_data",
                )

            self.file_id = response.id
            logging.info(f"Uploaded file [cyan]{path.name}[/cyan] with ID [cyan]{self.file_id}[/cyan]")
            return True
        except Exception as e:
            error_msg = str(e)
            # Check for common error cases and provide more helpful messages
            if "context_length_exceeded" in error_msg or "maximum limit" in error_msg:
                logging.error("File too large: The file exceeds the maximum token limit for the chosen model.")
                logging.error("Try using a smaller file or splitting the content into multiple smaller files.")
            elif "invalid_request_error" in error_msg and "file type" in error_msg:
                logging.error(f"Invalid file format: {error_msg}")
            else:
                logging.error(f"Error uploading file: {error_msg}")
            return False

    async def cleanup(self) -> bool:
        """Delete the file from OpenAI.

        Returns:
            True if the file was deleted successfully, False otherwise

        """
        if not self.file_id:
            logging.warning("No file ID provided for deletion")
            return False

        try:
            await self.client.files.delete(self.file_id)
            logging.info(f"Deleted file with ID [cyan]{self.file_id}[/cyan]")
            self.file_id = None
            return True
        except Exception as e:
            logging.error(f"Error deleting file: {str(e)}")
            return False

    def get_file_prompt(self, input_text: str) -> EasyInputMessageParam:
        """Get a file prompt that includes the file_id.

        Adds the file id and input text to the input list.

        Args:
            input_text: The user's input text

        Returns:
            An EasyInputMessageParam that includes the file_id

        """
        if not self.file_id:
            logging.warning("No file ID available for file prompt")
            return {"role": "user", "content": input_text}

        return {
            "role": "user",
            "content": [
                {"type": "input_file", "file_id": self.file_id},
                {"type": "input_text", "text": input_text},
            ],
            "type": "message",
        }


class TextFile(RemoteFile):
    """A text file that will be included directly in the prompt."""

    MAX_SIZE_BYTES = 1024 * 1024  # 1MB

    def __init__(self, file_path: str):
        """Initialize the text file.

        Args:
            file_path: Path to the text file

        """
        self.file_path = file_path
        self.content: str | None = None

    async def initialize(self) -> bool:
        """Read the file content.

        Returns:
            True if the file was read successfully, False otherwise

        """
        path = Path(self.file_path)
        if not path.exists():
            logging.error(f"File not found: {self.file_path}")
            return False

        # Check file size
        size = path.stat().st_size
        if size > self.MAX_SIZE_BYTES:
            logging.error(
                f"File too large: {self.file_path} ({size} bytes). Maximum size is {self.MAX_SIZE_BYTES} bytes (1MB)."
            )
            return False

        try:
            with open(path, encoding="utf-8") as file:
                self.content = file.read()
            logging.info(f"Read text file: [cyan]{path.name}[/cyan] ({size} bytes)")
            return True
        except Exception as e:
            logging.error(f"Error reading file: {str(e)}")
            return False

    async def cleanup(self) -> bool:
        """Clean up the text file (no action needed).

        Returns:
            Always returns True

        """
        self.content = None
        return True

    def get_file_prompt(self, input_text: str) -> EasyInputMessageParam:
        """Get a file prompt that includes the file content.

        Args:
            input_text: The user's input text

        Returns:
            An EasyInputMessageParam that includes the file content

        """
        if not self.content:
            logging.warning("No content available for file prompt")
            return {"role": "user", "content": input_text}

        # Create a message with the file content as text and the user's input
        file_name = Path(self.file_path).name
        return {
            "role": "user",
            "content": [
                {"type": "input_text", "text": f"File: {file_name}\n\n{self.content}"},
                {"type": "input_text", "text": input_text},
            ],
            "type": "message",
        }


def create_remote_file(file_path: str, client: AsyncOpenAI) -> RemoteFile:
    """Create the appropriate RemoteFile implementation based on file type.

    Args:
        file_path: Path to the file
        client: The OpenAI client

    Returns:
        An appropriate RemoteFile implementation

    """
    path = Path(file_path)

    # Text files that should be included directly in the prompt
    text_extensions = [".txt", ".log", ".md", ".csv"]

    # Files that should be uploaded to OpenAI
    uploadable_extensions = [".pdf", ".json", ".jsonl"]

    if path.suffix.lower() in text_extensions:
        return TextFile(file_path)
    elif path.suffix.lower() in uploadable_extensions:
        return UploadedFile(file_path, client)
    else:
        logging.warning(f"Unsupported file format: {path.suffix}. Treating as uploadable file, but it may fail.")
        return UploadedFile(file_path, client)
