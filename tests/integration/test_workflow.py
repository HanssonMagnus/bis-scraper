"""Integration tests for the complete workflow."""

import datetime
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import responses

from bis_scraper.converters.controller import convert_pdfs
from bis_scraper.scrapers.controller import scrape_bis
from bis_scraper.utils.constants import HTML_EXTENSION, PDF_EXTENSION, SPEECHES_URL


class TestCompleteWorkflow(unittest.TestCase):
    """Test the complete scraping and conversion workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = Path(tempfile.mkdtemp())
        # Use the actual directory names from constants
        from bis_scraper.utils.constants import RAW_DATA_DIR, TXT_DATA_DIR

        self.raw_dir = self.temp_dir / RAW_DATA_DIR
        self.txt_dir = self.temp_dir / TXT_DATA_DIR
        self.log_dir = self.temp_dir / "logs"
        self.raw_dir.mkdir()
        self.txt_dir.mkdir()
        self.log_dir.mkdir()

        # Sample speech data
        self.test_date = datetime.datetime(2020, 1, 1)
        self.speech_code = "r200101a"
        self.speech_code_without_r = "200101a"
        self.institution = "European Central Bank"

        # Sample URLs
        self.metadata_url = f"{SPEECHES_URL}/{self.speech_code}{HTML_EXTENSION}"
        self.pdf_url = f"{SPEECHES_URL}/{self.speech_code}{PDF_EXTENSION}"

        # Make sure responses mock is clean at start of each test
        responses.reset()

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @responses.activate
    @patch("textract.process")
    def test_scrape_and_convert(self, mock_process) -> None:
        """Test the complete workflow from scraping to conversion."""
        # Mock HTML response
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Speech</title></head>
        <body>
            <div id="extratitle-div">
                Speech by Mr. John Smith, Governor of the European Central Bank, at the Conference
            </div>
        </body>
        </html>
        """
        responses.add(responses.GET, self.metadata_url, body=html_content, status=200)

        # Mock PDF response with minimally valid PDF
        pdf_content = b"%PDF-1.4\nTest PDF content"
        responses.add(responses.GET, self.pdf_url, body=pdf_content, status=200)

        # Mock 404 for all other letters to stop the loop
        # Use a consistent approach with what we're doing in test_bis_scraper.py
        for letter in "bcdefghijklmnopqrstuvwxyz":
            url = f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}"
            responses.add(responses.GET, url, status=404)

        # Prepare dates for scraping
        start_date = self.test_date
        end_date = self.test_date

        # 1. Scrape speeches
        scrape_result = scrape_bis(
            data_dir=self.temp_dir,
            log_dir=self.temp_dir / "logs",
            start_date=start_date,
            end_date=end_date,
            institutions=None,  # Use no institution filter to match all institutions
            force=False,
        )

        # Verify scraping results
        self.assertEqual(scrape_result.downloaded, 1)
        self.assertEqual(scrape_result.skipped, 0)
        self.assertEqual(scrape_result.failed, 0)

        # Check if PDF was saved
        ecb_dir = self.raw_dir / "european_central_bank"
        pdf_file = ecb_dir / f"{self.speech_code_without_r}.pdf"
        self.assertTrue(pdf_file.exists())

        # Mock textract to return converted text
        mock_process.return_value = b"Converted text from the speech PDF"

        # 2. Convert PDFs
        convert_result = convert_pdfs(
            data_dir=self.temp_dir,
            log_dir=self.temp_dir / "logs",
            institutions=[self.institution],
            force=False,
        )

        # Verify conversion results
        self.assertEqual(convert_result.successful, 1)
        self.assertEqual(convert_result.skipped, 0)
        self.assertEqual(convert_result.failed, 0)

        # Check if text file was created
        ecb_txt_dir = self.txt_dir / "european_central_bank"
        txt_file = ecb_txt_dir / f"{self.speech_code_without_r}.txt"
        self.assertTrue(txt_file.exists())

        # Verify text content
        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "Converted text from the speech PDF")

    @responses.activate
    @patch("textract.process")
    def test_incremental_workflow(self, mock_process) -> None:
        """Test incremental workflow with existing files."""
        # Create existing PDF file
        ecb_dir = self.raw_dir / "european_central_bank"
        ecb_dir.mkdir(parents=True)
        pdf_file = ecb_dir / f"{self.speech_code_without_r}.pdf"
        with open(pdf_file, "wb") as f:
            f.write(b"Existing PDF content")

        # Create metadata file
        with open(ecb_dir / "european_central_bank_meta.txt", "w") as f:
            f.write(f"{self.speech_code_without_r}: Existing metadata")

        # Mock HTML and PDF responses (shouldn't be used due to caching)
        responses.add(
            responses.GET, self.metadata_url, status=200, body="Should not be accessed"
        )

        # Mock 404 for other letters to avoid potential issues
        for letter in "bcdefghijklmnopqrstuvwxyz":
            url = f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}"
            responses.add(responses.GET, url, status=404)

        # Run scraping - it should skip the existing file
        scrape_result = scrape_bis(
            data_dir=self.temp_dir,
            log_dir=self.temp_dir / "logs",
            start_date=self.test_date,
            end_date=self.test_date,
            institutions=[self.institution],
            force=False,
        )

        # Verify it was skipped
        self.assertEqual(scrape_result.downloaded, 0)
        self.assertEqual(scrape_result.skipped, 1)

        # Create existing text file
        ecb_txt_dir = self.txt_dir / "european_central_bank"
        ecb_txt_dir.mkdir(parents=True)
        txt_file = ecb_txt_dir / f"{self.speech_code_without_r}.txt"
        with open(txt_file, "w") as f:
            f.write("Existing converted text")

        # Convert PDFs - should skip existing
        convert_result = convert_pdfs(
            data_dir=self.temp_dir,
            log_dir=self.temp_dir / "logs",
            institutions=[self.institution],
            force=False,
        )

        # Verify it was skipped
        self.assertEqual(convert_result.successful, 0)
        self.assertEqual(convert_result.skipped, 1)

        # Verify text wasn't modified
        with open(txt_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "Existing converted text")

        # Now run with force flags
        mock_process.return_value = b"New converted content"

        # Mock HTML response for force download
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Speech</title></head>
        <body>
            <div id="extratitle-div">
                Speech by Mr. John Smith, Governor of the European Central Bank, at the Conference
            </div>
        </body>
        </html>
        """
        responses.replace(
            responses.GET, self.metadata_url, body=html_content, status=200
        )

        # Mock PDF response with new content
        new_pdf_content = b"%PDF-1.4\nNew PDF content"
        responses.add(responses.GET, self.pdf_url, body=new_pdf_content, status=200)

        # Run scraping with force
        scrape_result = scrape_bis(
            data_dir=self.temp_dir,
            log_dir=self.temp_dir / "logs",
            start_date=self.test_date,
            end_date=self.test_date,
            institutions=None,  # Use no institution filter to match all institutions
            force=True,
        )

        # Verify it was downloaded
        self.assertEqual(scrape_result.downloaded, 1)

        # Verify PDF was updated
        with open(pdf_file, "rb") as f:
            content = f.read()
        self.assertEqual(content, new_pdf_content)

        # Run conversion with force
        convert_result = convert_pdfs(
            data_dir=self.temp_dir,
            log_dir=self.temp_dir / "logs",
            institutions=[self.institution],
            force=True,
        )

        # Verify it was converted
        self.assertEqual(convert_result.successful, 1)

        # Verify text was updated
        with open(txt_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "New converted content")


if __name__ == "__main__":
    unittest.main()
