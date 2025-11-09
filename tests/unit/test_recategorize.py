"""Unit tests for recategorize functionality."""

import json
import tempfile
import unittest
from pathlib import Path

from bis_scraper.scrapers.recategorize import recategorize_unknown_files
from bis_scraper.utils.constants import RAW_DATA_DIR, TXT_DATA_DIR


class TestRecategorize(unittest.TestCase):
    """Test recategorize_unknown_files function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / RAW_DATA_DIR
        self.texts_dir = self.temp_dir / TXT_DATA_DIR
        self.unknown_dir = self.output_dir / "unknown"
        self.unknown_texts_dir = self.texts_dir / "unknown"
        self.unknown_dir.mkdir(parents=True)
        self.unknown_texts_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_no_unknown_folder(self) -> None:
        """Test when unknown folder doesn't exist."""
        # Remove unknown folder
        self.unknown_dir.rmdir()
        self.output_dir.rmdir()

        recategorized, remaining = recategorize_unknown_files(self.temp_dir)
        self.assertEqual(recategorized, 0)
        self.assertEqual(remaining, 0)

    def test_no_metadata_file(self) -> None:
        """Test when metadata.json doesn't exist."""
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)
        self.assertEqual(recategorized, 0)
        self.assertEqual(remaining, 0)

    def test_recategorize_successful(self) -> None:
        """Test successful re-categorization of files."""
        # Create metadata.json with ECB speech
        metadata_data = {
            "200101a": {
                "raw_text": "Speech by Mr. John Smith, Governor of the European Central Bank, at the Conference",
                "speech_type": "Speech",
                "speaker": "Mr. John Smith",
                "role": "Governor of the European Central Bank",
                "date": "2020-01-01",
            }
        }
        metadata_file = self.unknown_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # Create PDF file
        pdf_file = self.unknown_dir / "200101a.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nTest PDF content")

        # Create corresponding text file
        txt_file = self.unknown_texts_dir / "200101a.txt"
        txt_file.write_text("Test text content", encoding="utf-8")

        # Run recategorize
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)

        # Check results
        self.assertEqual(recategorized, 1)
        self.assertEqual(remaining, 0)

        # Check PDF file was moved
        ecb_pdf_dir = self.output_dir / "european_central_bank"
        self.assertTrue(ecb_pdf_dir.exists())
        self.assertTrue((ecb_pdf_dir / "200101a.pdf").exists())
        self.assertFalse(pdf_file.exists())

        # Check text file was moved
        ecb_txt_dir = self.texts_dir / "european_central_bank"
        self.assertTrue(ecb_txt_dir.exists())
        self.assertTrue((ecb_txt_dir / "200101a.txt").exists())
        self.assertFalse(txt_file.exists())

        # Check metadata was moved
        self.assertTrue((ecb_pdf_dir / "metadata.json").exists())
        with open(ecb_pdf_dir / "metadata.json", "r", encoding="utf-8") as f:
            moved_metadata = json.load(f)
        self.assertIn("200101a", moved_metadata)

        # Check unknown folders were removed (empty)
        self.assertFalse(self.unknown_dir.exists())
        self.assertFalse(self.unknown_texts_dir.exists())

    def test_recategorize_partial(self) -> None:
        """Test partial re-categorization when some files can't be categorized."""
        # Create metadata with one recognizable and one unrecognizable
        metadata_data = {
            "200101a": {
                "raw_text": "Speech by Mr. John Smith, Governor of the European Central Bank",
                "date": "2020-01-01",
            },
            "200101b": {
                "raw_text": "Some unrecognizable text without institution",
                "date": "2020-01-01",
            },
        }
        metadata_file = self.unknown_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # Create PDF files
        (self.unknown_dir / "200101a.pdf").write_bytes(b"%PDF-1.4\nTest PDF")
        (self.unknown_dir / "200101b.pdf").write_bytes(b"%PDF-1.4\nTest PDF")

        # Create text files
        (self.unknown_texts_dir / "200101a.txt").write_text(
            "Test text", encoding="utf-8"
        )
        (self.unknown_texts_dir / "200101b.txt").write_text(
            "Test text", encoding="utf-8"
        )

        # Run recategorize
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)

        # Check results
        self.assertEqual(recategorized, 1)
        self.assertEqual(remaining, 1)

        # Check ECB files were moved
        ecb_pdf_dir = self.output_dir / "european_central_bank"
        ecb_txt_dir = self.texts_dir / "european_central_bank"
        self.assertTrue((ecb_pdf_dir / "200101a.pdf").exists())
        self.assertTrue((ecb_txt_dir / "200101a.txt").exists())

        # Check unknown files remain
        self.assertTrue((self.unknown_dir / "200101b.pdf").exists())
        self.assertTrue((self.unknown_texts_dir / "200101b.txt").exists())
        self.assertTrue(metadata_file.exists())

        # Check remaining metadata
        with open(metadata_file, "r", encoding="utf-8") as f:
            remaining_metadata = json.load(f)
        self.assertIn("200101b", remaining_metadata)
        self.assertNotIn("200101a", remaining_metadata)

    def test_missing_pdf_file(self) -> None:
        """Test when PDF file doesn't exist."""
        # Create metadata but no PDF
        metadata_data = {
            "200101a": {
                "raw_text": "Speech by Mr. John Smith, Governor of the European Central Bank",
                "date": "2020-01-01",
            }
        }
        metadata_file = self.unknown_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # Create text file (but no PDF)
        (self.unknown_texts_dir / "200101a.txt").write_text(
            "Test text", encoding="utf-8"
        )

        # Run recategorize
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)

        # Should not recategorize (no PDF)
        self.assertEqual(recategorized, 0)
        self.assertEqual(remaining, 1)

        # Metadata and text file should remain
        self.assertTrue(metadata_file.exists())
        self.assertTrue((self.unknown_texts_dir / "200101a.txt").exists())

    def test_pdf_without_text_file(self) -> None:
        """Test when PDF exists but text file doesn't."""
        # Create metadata with ECB speech
        metadata_data = {
            "200101a": {
                "raw_text": "Speech by Mr. John Smith, Governor of the European Central Bank",
                "date": "2020-01-01",
            }
        }
        metadata_file = self.unknown_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # Create PDF file but no text file
        pdf_file = self.unknown_dir / "200101a.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nTest PDF content")

        # Run recategorize
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)

        # Should recategorize (PDF exists, text file optional)
        self.assertEqual(recategorized, 1)
        self.assertEqual(remaining, 0)

        # Check PDF was moved
        ecb_pdf_dir = self.output_dir / "european_central_bank"
        self.assertTrue((ecb_pdf_dir / "200101a.pdf").exists())

        # Text file should not exist in target (wasn't created)
        ecb_txt_dir = self.texts_dir / "european_central_bank"
        if ecb_txt_dir.exists():
            self.assertFalse((ecb_txt_dir / "200101a.txt").exists())

    def test_no_raw_text(self) -> None:
        """Test when metadata has no raw_text."""
        # Create metadata without raw_text
        metadata_data = {
            "200101a": {
                "speech_type": "Speech",
                "date": "2020-01-01",
            }
        }
        metadata_file = self.unknown_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # Create PDF file
        (self.unknown_dir / "200101a.pdf").write_bytes(b"%PDF-1.4\nTest PDF")

        # Run recategorize
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)

        # Should not recategorize (no raw_text to extract institution from)
        self.assertEqual(recategorized, 0)
        self.assertEqual(remaining, 1)

    def test_invalid_json(self) -> None:
        """Test handling of invalid JSON."""
        # Create invalid JSON file
        metadata_file = self.unknown_dir / "metadata.json"
        metadata_file.write_text("{ invalid json }", encoding="utf-8")

        # Run recategorize (should not crash)
        recategorized, remaining = recategorize_unknown_files(self.temp_dir)

        # Should return 0, 0 (graceful failure)
        self.assertEqual(recategorized, 0)
        self.assertEqual(remaining, 0)


if __name__ == "__main__":
    unittest.main()
