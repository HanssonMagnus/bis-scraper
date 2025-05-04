"""Unit tests for BIS scraper."""

import datetime
import tempfile
import unittest
from pathlib import Path

import responses

from bis_scraper.scrapers.bis_scraper import BisScraper
from bis_scraper.utils.constants import HTML_EXTENSION, PDF_EXTENSION, SPEECHES_URL


class TestBisScraper(unittest.TestCase):
    """Test BIS scraper class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())

        # Sample speech date and code
        self.test_date = datetime.date(2020, 1, 1)
        self.speech_code = "r200101a"
        self.speech_code_without_r = "200101a"

        # Sample URLs
        self.metadata_url = f"{SPEECHES_URL}/{self.speech_code}{HTML_EXTENSION}"
        self.pdf_url = f"{SPEECHES_URL}/{self.speech_code}{PDF_EXTENSION}"

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @responses.activate
    def test_scrape_date(self) -> None:
        """Test scraping speeches for a specific date."""
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

        # Mock PDF response
        pdf_content = b"%PDF-1.4\nTest PDF content"
        responses.add(responses.GET, self.pdf_url, body=pdf_content, status=200)

        # Mock 404 for next letter to stop the loop
        responses.add(
            responses.GET, f"{SPEECHES_URL}/r200101b{HTML_EXTENSION}", status=404
        )

        # Initialize scraper
        scraper = BisScraper(
            output_dir=self.temp_dir,
            institutions=None,  # All institutions
            force_download=False,
        )

        # Scrape date
        scraper.scrape_date(self.test_date)

        # Check results
        result = scraper.get_results()
        self.assertEqual(result.downloaded, 1)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)

        # Check output files - should have one in european_central_bank directory
        ecb_dir = self.temp_dir / "european_central_bank"
        self.assertTrue(ecb_dir.exists())
        self.assertTrue((ecb_dir / f"{self.speech_code_without_r}.pdf").exists())

        # Check metadata file
        metadata_file = ecb_dir / "european_central_bank_meta.txt"
        self.assertTrue(metadata_file.exists())
        with open(metadata_file, "r") as f:
            metadata_content = f.read()
        self.assertIn(self.speech_code_without_r, metadata_content)
        self.assertIn("European Central Bank", metadata_content)

    @responses.activate
    def test_skip_existing_files(self) -> None:
        """Test skipping existing files."""
        # Create existing file structure
        ecb_dir = self.temp_dir / "european_central_bank"
        ecb_dir.mkdir(parents=True)
        existing_file = ecb_dir / f"{self.speech_code_without_r}.pdf"
        with open(existing_file, "wb") as f:
            f.write(b"Existing content")

        # We need to mock all possible letter responses
        for letter in "abcdefghijklmnopqrstuvwxyz":
            # Mock 404 responses for all letter codes
            responses.add(
                responses.GET,
                f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}",
                status=404,
            )

        # Initialize scraper with cache building enabled
        scraper = BisScraper(
            output_dir=self.temp_dir, institutions=None, force_download=False
        )

        # Scrape date - should skip due to existing file
        scraper.scrape_date(self.test_date)

        # Check results
        result = scraper.get_results()
        self.assertEqual(result.downloaded, 0)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.failed, 0)

        # Verify file wasn't modified (should still have original content)
        with open(existing_file, "rb") as f:
            content = f.read()
        self.assertEqual(content, b"Existing content")

    @responses.activate
    def test_force_download(self) -> None:
        """Test force downloading existing files."""
        # Create existing file structure
        ecb_dir = self.temp_dir / "european_central_bank"
        ecb_dir.mkdir(parents=True)
        existing_file = ecb_dir / f"{self.speech_code_without_r}.pdf"
        with open(existing_file, "wb") as f:
            f.write(b"Existing content")

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

        # Mock PDF response with new content
        new_pdf_content = b"%PDF-1.4\nNew content"
        responses.add(responses.GET, self.pdf_url, body=new_pdf_content, status=200)

        # Mock 404 for next letter to stop the loop
        responses.add(
            responses.GET, f"{SPEECHES_URL}/r200101b{HTML_EXTENSION}", status=404
        )

        # Initialize scraper with force_download=True
        scraper = BisScraper(
            output_dir=self.temp_dir, institutions=None, force_download=True
        )

        # Scrape date - should re-download
        scraper.scrape_date(self.test_date)

        # Check results
        result = scraper.get_results()
        self.assertEqual(result.downloaded, 1)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)

        # Verify file was modified with new content
        with open(existing_file, "rb") as f:
            content = f.read()
        self.assertEqual(content, new_pdf_content)

    @responses.activate
    def test_institution_filtering(self) -> None:
        """Test filtering by institution."""
        # Mock HTML response for ECB speech
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
        # Mock 404 for all other letters to stop the loop
        for letter in "bcdefghijklmnopqrstuvwxyz":
            responses.add(
                responses.GET,
                f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}",
                status=404,
            )

        # Test with Federal Reserve filter (will exclude ECB)
        # First reset all responses to ensure clean slate
        responses.reset()

        # Mock the same HTML response
        responses.add(responses.GET, self.metadata_url, body=html_content, status=200)

        # Mock 404 for all other letters
        for letter in "bcdefghijklmnopqrstuvwxyz":
            responses.add(
                responses.GET,
                f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}",
                status=404,
            )

        # Initialize scraper with Federal Reserve filter (will exclude ECB)
        scraper = BisScraper(
            output_dir=self.temp_dir,
            institutions=["Federal Reserve"],
            force_download=False,
        )

        # Scrape date - should skip due to institution filter
        scraper.scrape_date(self.test_date)

        # Check results
        result = scraper.get_results()
        self.assertEqual(result.downloaded, 0)
        self.assertEqual(result.skipped, 1)  # Skipped due to institution filter
        self.assertEqual(result.failed, 0)

        # Test with ECB filter (will include ECB)
        # First reset all responses to ensure clean slate
        responses.reset()

        # Mock HTML response again
        responses.add(responses.GET, self.metadata_url, body=html_content, status=200)

        # Mock PDF response
        pdf_content = b"%PDF-1.4\nTest PDF content"
        responses.add(responses.GET, self.pdf_url, body=pdf_content, status=200)

        # Mock 404 for next letter to stop the loop
        for letter in "bcdefghijklmnopqrstuvwxyz":
            responses.add(
                responses.GET,
                f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}",
                status=404,
            )

        # Initialize scraper with ECB filter (will include ECB)
        scraper = BisScraper(
            output_dir=self.temp_dir,
            institutions=["European Central Bank"],
            force_download=False,
        )

        # Scrape date - should download
        scraper.scrape_date(self.test_date)

        # Check results
        result = scraper.get_results()
        self.assertEqual(
            result.downloaded, 1
        )  # Downloaded due to matching institution filter
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)

    @responses.activate
    def test_error_handling(self) -> None:
        """Test error handling during scraping."""
        # Mock HTML response that will cause error
        responses.add(responses.GET, self.metadata_url, status=500)  # Server error

        # Mock 404 for all other letters to stop the loop
        for letter in "bcdefghijklmnopqrstuvwxyz":
            responses.add(
                responses.GET,
                f"{SPEECHES_URL}/r200101{letter}{HTML_EXTENSION}",
                status=404,
            )

        # Initialize scraper
        scraper = BisScraper(
            output_dir=self.temp_dir, institutions=None, force_download=False
        )

        # Scrape date - should handle error
        scraper.scrape_date(self.test_date)

        # Check results
        result = scraper.get_results()
        self.assertEqual(result.downloaded, 0)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 1)  # Failed due to server error


if __name__ == "__main__":
    unittest.main()
