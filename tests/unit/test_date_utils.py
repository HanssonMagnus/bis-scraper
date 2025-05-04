"""Unit tests for date utilities."""

import datetime
import unittest

from bis_scraper.utils.date_utils import (
    create_date_list,
    format_date_for_filename,
    parse_date_code,
)


class TestDateUtils(unittest.TestCase):
    """Test date utility functions."""

    def test_create_date_list_default(self) -> None:
        """Test create_date_list with default parameters."""
        # Test that we get dates that include today
        date_list = create_date_list()
        today_str = datetime.date.today().strftime("%y%m%d")
        self.assertIn(today_str, date_list)

        # Test that we get the first date
        first_date = "970106"  # Jan 6, 1997
        self.assertIn(first_date, date_list)

    def test_create_date_list_range(self) -> None:
        """Test create_date_list with specific date range."""
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date(2020, 1, 10)
        date_list = create_date_list(start_date, end_date)

        # Check length - should be 10 days
        self.assertEqual(len(date_list), 10)

        # Check specific dates
        self.assertIn("200101", date_list)
        self.assertIn("200110", date_list)

        # Check order
        self.assertEqual(date_list[0], "200101")
        self.assertEqual(date_list[-1], "200110")

    def test_create_date_list_invalid_range(self) -> None:
        """Test create_date_list with invalid date range."""
        # End date before start date
        start_date = datetime.date(2020, 1, 10)
        end_date = datetime.date(2020, 1, 1)

        with self.assertRaises(ValueError):
            create_date_list(start_date, end_date)

    def test_parse_date_code_valid(self) -> None:
        """Test parse_date_code with valid input."""
        # Test a normal case
        date, letter = parse_date_code("a200101")
        self.assertEqual(date, datetime.date(2020, 1, 1))
        self.assertEqual(letter, "a")

        # Test different letter
        date, letter = parse_date_code("z201231")
        self.assertEqual(date, datetime.date(2020, 12, 31))
        self.assertEqual(letter, "z")

    def test_parse_date_code_invalid(self) -> None:
        """Test parse_date_code with invalid input."""
        # Invalid length
        with self.assertRaises(ValueError):
            parse_date_code("a20010")

        # Invalid letter
        with self.assertRaises(ValueError):
            parse_date_code("1200101")

        # Invalid date
        with self.assertRaises(ValueError):
            parse_date_code("a209901")  # No 99th month

    def test_format_date_for_filename(self) -> None:
        """Test format_date_for_filename."""
        # Test normal case
        date = datetime.date(2020, 1, 1)
        formatted = format_date_for_filename(date)
        self.assertEqual(formatted, "2020-01-01")

        # Test single digit month and day
        date = datetime.date(2020, 1, 1)
        formatted = format_date_for_filename(date)
        self.assertEqual(formatted, "2020-01-01")

        # Test different date
        date = datetime.date(2020, 12, 31)
        formatted = format_date_for_filename(date)
        self.assertEqual(formatted, "2020-12-31")


if __name__ == "__main__":
    unittest.main()
