"""Tests for the command line interface."""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from bis_scraper.cli.main import main


class TestCli(unittest.TestCase):
    """Test the command line interface."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_help(self) -> None:
        """Test the main help command."""
        result = self.runner.invoke(main, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "BIS Scraper - Download and process central bank speeches", result.output
        )

    @patch("bis_scraper.scrapers.controller.scrape_bis")
    def test_scrape_command(self, mock_scrape_bis) -> None:
        """Test the scrape command."""
        # Set up the mock to return a simple result
        from bis_scraper.models import ScrapingResult

        mock_scrape_bis.return_value = ScrapingResult(downloaded=5, skipped=2, failed=1)

        # Test with verbose and institution
        result = self.runner.invoke(
            main, ["--verbose", "scrape", "--institutions", "European Central Bank"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Starting BIS web scraping", result.output)
        self.assertIn("Scraping completed", result.output)

    @patch("bis_scraper.converters.controller.convert_pdfs_dates")
    def test_convert_command(self, mock_convert) -> None:
        """Test the convert command."""
        # Set up the mock to return a simple result
        from bis_scraper.models import ConversionResult

        mock_convert.return_value = ConversionResult(
            successful=5, skipped=2, failed=1
        )

        # Test with verbose and institution
        result = self.runner.invoke(
            main,
            [
                "--verbose",
                "convert",
                "--institutions",
                "European Central Bank",
                "--start-date",
                "2022-01-01",
                "--end-date",
                "2022-01-02",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Starting PDF to text conversion", result.output)
        self.assertIn("Conversion completed", result.output)


if __name__ == "__main__":
    unittest.main()
