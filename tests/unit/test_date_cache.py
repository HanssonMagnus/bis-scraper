"""Tests for date caching functionality in BisScraper."""

import datetime
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from bis_scraper.scrapers.bis_scraper import BisScraper


class TestDateCache:
    """Test the date caching functionality."""

    def test_date_cache_initialization(self, tmp_path: Path) -> None:
        """Test that date cache is properly initialized."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir)

        assert scraper.date_cache_file == output_dir / ".bis_scraper_date_cache.json"
        assert scraper.checked_dates == {}

    def test_date_cache_load_existing(self, tmp_path: Path) -> None:
        """Test loading an existing date cache."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a cache file
        cache_data = {
            "version": 1,
            "dates": {
                "2023-01-01": {
                    "checked_at": "2023-01-02T10:00:00",
                    "had_speeches": True,
                    "files_found": 2,
                }
            },
            "updated": "2023-01-02T10:00:00",
        }

        cache_file = output_dir / ".bis_scraper_date_cache.json"
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        scraper = BisScraper(output_dir)

        assert "2023-01-01" in scraper.checked_dates
        assert scraper.checked_dates["2023-01-01"]["had_speeches"] is True
        assert scraper.checked_dates["2023-01-01"]["files_found"] == 2

    def test_date_cache_save(self, tmp_path: Path) -> None:
        """Test saving the date cache."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir)

        # Add some dates to the cache
        scraper.checked_dates["2023-01-01"] = {
            "checked_at": "2023-01-02T10:00:00",
            "had_speeches": False,
            "files_found": 0,
        }

        scraper._save_date_cache()

        # Verify the file was created
        assert scraper.date_cache_file.exists()

        # Verify the content
        with open(scraper.date_cache_file, "r") as f:
            saved_data = json.load(f)

        assert saved_data["version"] == 1
        assert "2023-01-01" in saved_data["dates"]
        assert saved_data["dates"]["2023-01-01"]["had_speeches"] is False

    def test_get_date_cache_key_no_institutions(self, tmp_path: Path) -> None:
        """Test cache key generation without institution filtering."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir)
        date_obj = datetime.date(2023, 1, 1)

        key = scraper._get_date_cache_key(date_obj)
        assert key == "2023-01-01"

    def test_get_date_cache_key_with_institutions(self, tmp_path: Path) -> None:
        """Test cache key generation with institution filtering."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir, institutions=["Bank of England", "ECB"])
        date_obj = datetime.date(2023, 1, 1)

        key = scraper._get_date_cache_key(date_obj)
        assert key == "2023-01-01|Bank of England,ECB"

    @patch("requests.get")
    def test_scrape_date_uses_cache(self, mock_get: MagicMock, tmp_path: Path) -> None:
        """Test that scrape_date skips dates found in cache."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir)

        # Add a date to the cache
        date_obj = datetime.date(2023, 1, 1)
        cache_key = scraper._get_date_cache_key(date_obj)
        scraper.checked_dates[cache_key] = {
            "checked_at": "2023-01-02T10:00:00",
            "had_speeches": True,
            "files_found": 3,
        }

        # Scrape the date
        result = scraper.scrape_date(date_obj)

        # Should not make any HTTP requests
        mock_get.assert_not_called()

        # Should update skipped count
        assert scraper.result.skipped == 3
        assert result is True

    @patch("requests.get")
    def test_scrape_date_updates_cache(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """Test that scrape_date updates the cache after checking."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir)

        # Mock a 404 response (no speeches for this date)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        date_obj = datetime.date(2023, 1, 1)
        scraper.scrape_date(date_obj)

        # Check that the date was added to the cache
        cache_key = scraper._get_date_cache_key(date_obj)
        assert cache_key in scraper.checked_dates
        assert scraper.checked_dates[cache_key]["had_speeches"] is False
        assert scraper.checked_dates[cache_key]["files_found"] == 0

    def test_force_download_ignores_cache(self, tmp_path: Path) -> None:
        """Test that force_download ignores the date cache."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        scraper = BisScraper(output_dir, force_download=True)

        # Add a date to the cache
        date_obj = datetime.date(2023, 1, 1)
        cache_key = scraper._get_date_cache_key(date_obj)
        scraper.checked_dates[cache_key] = {
            "checked_at": "2023-01-02T10:00:00",
            "had_speeches": True,
            "files_found": 3,
        }

        # With force_download=True, the cache should not be loaded
        scraper2 = BisScraper(output_dir, force_download=True)
        assert scraper2.checked_dates == {}
