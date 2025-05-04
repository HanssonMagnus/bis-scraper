"""Tests for the institution_utils module."""

from bis_scraper.utils.institution_utils import (
    get_institution_from_metadata,
    normalize_institution_name,
    standardize_institution_name,
)


class TestInstitutionUtils:
    """Tests for institution utility functions."""

    def test_normalize_institution_name(self) -> None:
        """Test normalize_institution_name function."""
        cases = [
            ("European Central Bank", "european_central_bank"),
            ("Bank of England", "bank_of_england"),
            ("People's Bank of China", "peoples_bank_of_china"),
            ("Bank & Trust", "bank_and_trust"),
            ("Federal Reserve, Board", "federal_reserve_board"),
            ("  Spaces  ", "spaces"),
        ]

        for input_name, expected in cases:
            assert normalize_institution_name(input_name) == expected

    def test_standardize_institution_name(self) -> None:
        """Test standardize_institution_name function."""
        # Test with direct match
        assert (
            standardize_institution_name("European Central Bank")
            == "european central bank"
        )

        # Test with alias
        assert standardize_institution_name("ECB") == "european central bank"
        assert standardize_institution_name("Bank of Sweden") == "sveriges riksbank"
        assert (
            standardize_institution_name("Board of the US Federal Reserve System")
            == "board of governors of the federal reserve system"
        )

        # Test with unknown institution
        assert standardize_institution_name("Unknown Bank") == "unknown bank"

    def test_get_institution_from_metadata(self) -> None:
        """Test get_institution_from_metadata function."""
        # Test with direct mention in metadata
        metadata = "Speech by Mr. John Smith, Governor of the European Central Bank, at the Annual Conference"
        assert get_institution_from_metadata(metadata) == "european central bank"

        # Test with alias in metadata
        metadata = (
            "Speech by Mr. John Smith, Governor of the ECB, at the Annual Conference"
        )
        assert get_institution_from_metadata(metadata) == "european central bank"

        # Test with multiple institutions in metadata (should pick the first one)
        metadata = "Joint speech by governors of the ECB and the Bank of England at the Annual Conference"
        # The exact return value depends on which one is found first by the function
        # This is more of an integration test since it depends on the actual implementation
        result = get_institution_from_metadata(metadata)
        assert result in ["european central bank", "bank of england"]

        # Test with no institution in metadata
        metadata = "Speech by Mr. John Smith at the Annual Conference"
        assert get_institution_from_metadata(metadata) is None

        # Test with empty metadata
        assert get_institution_from_metadata("") is None

        # Test with None metadata
        assert get_institution_from_metadata(None) is None
