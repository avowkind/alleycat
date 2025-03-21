"""Tests for the remote_file module."""

import unittest
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from openai import AsyncOpenAI

from alleycat_core.llm.remote_file import TextFile, UploadedFile, create_remote_file


class TestRemoteFile(unittest.TestCase):
    """Tests for RemoteFile implementations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_file_dir = Path(__file__).parent / "test_files"
        self.test_file_dir.mkdir(exist_ok=True)

        # Create a test text file
        self.text_file_path = self.test_file_dir / "test.txt"
        with open(self.text_file_path, "w") as f:
            f.write("This is a test file.")

        # Mock OpenAI client
        self.mock_client = MagicMock(spec=AsyncOpenAI)
        self.mock_client.files = MagicMock()
        self.mock_client.files.create = AsyncMock()
        self.mock_client.files.delete = AsyncMock()

        # Setup response for file upload
        self.mock_client.files.create.return_value = MagicMock(id="test_file_id")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Clean up test files
        if self.text_file_path.exists():
            self.text_file_path.unlink()

        # Clean up test directory if empty
        if self.test_file_dir.exists() and not list(self.test_file_dir.iterdir()):
            self.test_file_dir.rmdir()

    @patch("alleycat_core.llm.remote_file.logging")
    async def test_text_file_initialization(self, mock_logging: Any) -> None:
        """Test initializing a text file."""
        # Create a TextFile instance
        text_file = TextFile(str(self.text_file_path))

        # Initialize the file
        result = await text_file.initialize()

        # Verify initialization was successful
        self.assertTrue(result)
        self.assertEqual(text_file.content, "This is a test file.")

        # Verify logging
        mock_logging.info.assert_called_once()

    @patch("alleycat_core.llm.remote_file.logging")
    async def test_text_file_prompt(self, mock_logging: Any) -> None:
        """Test getting a prompt from a text file."""
        # Create and initialize a TextFile instance
        text_file = TextFile(str(self.text_file_path))
        await text_file.initialize()

        # Get a file prompt
        prompt = text_file.get_file_prompt("Analyze this file")

        # Verify the prompt structure
        self.assertEqual(prompt["role"], "user")
        self.assertTrue(isinstance(prompt["content"], list))
        self.assertEqual(len(prompt["content"]), 2)

        # Cast content to any to avoid TypedDict typing issues in the test
        content: list[dict[str, Any]] = prompt["content"]  # type: ignore

        self.assertEqual(content[0]["type"], "input_text")
        self.assertTrue("test.txt" in content[0]["text"])
        self.assertTrue("This is a test file." in content[0]["text"])
        self.assertEqual(content[1]["type"], "input_text")
        self.assertEqual(content[1]["text"], "Analyze this file")

    @patch("alleycat_core.llm.remote_file.logging")
    async def test_uploaded_file_initialization(self, mock_logging: Any) -> None:
        """Test initializing an uploaded file."""
        # Create an UploadedFile instance
        uploaded_file = UploadedFile(str(self.text_file_path), self.mock_client)

        # Initialize the file (mock upload)
        result = await uploaded_file.initialize()

        # Verify initialization was successful
        self.assertTrue(result)
        self.assertEqual(uploaded_file.file_id, "test_file_id")

        # Verify client method was called
        self.mock_client.files.create.assert_called_once()

    @patch("alleycat_core.llm.remote_file.logging")
    async def test_uploaded_file_cleanup(self, mock_logging: Any) -> None:
        """Test cleaning up an uploaded file."""
        # Create and initialize an UploadedFile instance
        uploaded_file = UploadedFile(str(self.text_file_path), self.mock_client)
        await uploaded_file.initialize()

        # Clean up the file
        result = await uploaded_file.cleanup()

        # Verify cleanup was successful
        self.assertTrue(result)
        self.assertIsNone(uploaded_file.file_id)

        # Verify client method was called
        self.mock_client.files.delete.assert_called_once_with("test_file_id")

    @patch("alleycat_core.llm.remote_file.logging")
    async def test_uploaded_file_prompt(self, mock_logging: Any) -> None:
        """Test getting a prompt from an uploaded file."""
        # Create and initialize an UploadedFile instance
        uploaded_file = UploadedFile(str(self.text_file_path), self.mock_client)
        await uploaded_file.initialize()

        # Get a file prompt
        prompt = uploaded_file.get_file_prompt("Analyze this file")

        # Verify the prompt structure
        self.assertEqual(prompt["role"], "user")

        # Cast content to any to avoid TypedDict typing issues in the test
        content: list[dict[str, Any]] = prompt["content"]  # type: ignore

        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]["type"], "input_file")
        self.assertEqual(content[0]["file_id"], "test_file_id")
        self.assertEqual(content[1]["type"], "input_text")
        self.assertEqual(content[1]["text"], "Analyze this file")

    def test_create_remote_file_text(self) -> None:
        """Test creating a RemoteFile for a text file."""
        # Test with a .txt file
        remote_file = create_remote_file(str(self.text_file_path), self.mock_client)
        self.assertIsInstance(remote_file, TextFile)

        # Test with other text extensions
        for ext in [".md", ".log", ".csv"]:
            path = self.test_file_dir / f"test{ext}"
            with open(path, "w") as f:
                f.write("Test content")

            try:
                remote_file = create_remote_file(str(path), self.mock_client)
                self.assertIsInstance(remote_file, TextFile)
            finally:
                # Clean up test file
                if path.exists():
                    path.unlink()

    def test_create_remote_file_uploaded(self) -> None:
        """Test creating a RemoteFile for an uploadable file."""
        # Test with known uploadable extensions
        for ext in [".pdf", ".json", ".jsonl"]:
            path = self.test_file_dir / f"test{ext}"
            with open(path, "w") as f:
                f.write("Test content")

            try:
                remote_file = create_remote_file(str(path), self.mock_client)
                self.assertIsInstance(remote_file, UploadedFile)
            finally:
                # Clean up test file
                if path.exists():
                    path.unlink()


if __name__ == "__main__":
    unittest.main()
