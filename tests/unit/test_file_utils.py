"""Unit tests for file utilities."""

import tempfile
import unittest
from pathlib import Path

from bis_scraper.utils.file_utils import (
    create_directory,
    find_existing_files,
    format_filename,
    get_file_hash,
    get_institution_directory,
    list_directories,
    normalize_institution_name,
)


class TestFileUtils(unittest.TestCase):
    """Test file utility functions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_create_directory(self) -> None:
        """Test create_directory function."""
        test_dir = self.temp_dir / "test_dir"

        # Test creating a directory
        create_directory(test_dir)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())

        # Test creating a nested directory
        nested_dir = self.temp_dir / "parent" / "child"
        create_directory(nested_dir)
        self.assertTrue(nested_dir.exists())
        self.assertTrue(nested_dir.is_dir())

        # Test creating an existing directory (should not raise)
        create_directory(test_dir)  # This should not raise an exception

    def test_get_file_hash(self) -> None:
        """Test get_file_hash function."""
        # Create a test file with known content
        test_file = self.temp_dir / "test_file.txt"
        with open(test_file, "wb") as f:
            f.write(b"test content")

        # Known SHA-256 hash for "test content"
        expected_hash = (
            "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        )

        # Test hash calculation
        actual_hash = get_file_hash(test_file)
        self.assertEqual(actual_hash, expected_hash)

    def test_list_directories(self) -> None:
        """Test list_directories function."""
        # Create test directories
        dir1 = self.temp_dir / "dir1"
        dir2 = self.temp_dir / "dir2"
        create_directory(dir1)
        create_directory(dir2)

        # Create a file (should not be listed)
        with open(self.temp_dir / "test_file.txt", "w") as f:
            f.write("test")

        # Test listing directories
        dirs = list_directories(self.temp_dir)
        self.assertEqual(len(dirs), 2)
        self.assertIn("dir1", dirs)
        self.assertIn("dir2", dirs)

        # Test with non-existent directory
        non_existent = self.temp_dir / "non_existent"
        dirs = list_directories(non_existent)
        self.assertEqual(dirs, [])

    def test_find_existing_files(self) -> None:
        """Test find_existing_files function."""
        # Create test files
        file1 = self.temp_dir / "220101a.pdf"
        file2 = self.temp_dir / "220102b.pdf"
        file3 = self.temp_dir / "220103c.txt"  # Different extension

        with open(file1, "w") as f:
            f.write("test1")
        with open(file2, "w") as f:
            f.write("test2")
        with open(file3, "w") as f:
            f.write("test3")

        # Test finding PDF files
        pdf_files = find_existing_files(self.temp_dir, ".pdf")
        self.assertEqual(len(pdf_files), 2)
        self.assertIn("220101a", pdf_files)
        self.assertIn("220102b", pdf_files)

        # Test finding TXT files
        txt_files = find_existing_files(self.temp_dir, ".txt")
        self.assertEqual(len(txt_files), 1)
        self.assertIn("220103c", txt_files)

        # Test with non-existent directory
        non_existent = self.temp_dir / "non_existent"
        files = find_existing_files(non_existent, ".pdf")
        self.assertEqual(files, set())

    def test_normalize_institution_name(self) -> None:
        """Test normalize_institution_name function."""
        # Test basic normalization
        self.assertEqual(
            normalize_institution_name("European Central Bank"), "european_central_bank"
        )

        # Test with special characters
        self.assertEqual(
            normalize_institution_name("Bank's & Money"), "banks_and_money"
        )

        # Test with commas
        self.assertEqual(
            normalize_institution_name("Finance, Economics"), "finance_economics"
        )

    def test_get_institution_directory(self) -> None:
        """Test get_institution_directory function."""
        # Test creating institution directory
        institution = "European Central Bank"
        expected_dir = self.temp_dir / "european_central_bank"

        actual_dir = get_institution_directory(self.temp_dir, institution)
        self.assertEqual(actual_dir, expected_dir)
        self.assertTrue(actual_dir.exists())
        self.assertTrue(actual_dir.is_dir())

    def test_format_filename(self) -> None:
        """Test format_filename function."""
        # Test with 'r' prefix
        self.assertEqual(
            format_filename("r220101a", "European Central Bank"), "220101a.pdf"
        )

        # Test without 'r' prefix
        self.assertEqual(
            format_filename("220102b", "European Central Bank"), "220102b.pdf"
        )


if __name__ == "__main__":
    unittest.main()
