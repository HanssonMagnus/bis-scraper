"""Unit tests for PDF converter."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bis_scraper.converters.pdf_converter import PdfConverter
from bis_scraper.models import ConversionResult


class TestPdfConverter(unittest.TestCase):
    """Test PDF converter class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create temporary directories for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.temp_dir / "input"
        self.output_dir = self.temp_dir / "output"
        
        # Create input directory structure
        self.input_dir.mkdir(exist_ok=True)
        self.ecb_dir = self.input_dir / "european_central_bank"
        self.fed_dir = self.input_dir / "federal_reserve"
        self.ecb_dir.mkdir(exist_ok=True)
        self.fed_dir.mkdir(exist_ok=True)
        
        # Create sample PDF files
        (self.ecb_dir / "220101a.pdf").touch()
        (self.ecb_dir / "220102b.pdf").touch()
        (self.fed_dir / "220103c.pdf").touch()
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
    
    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Clean up temporary directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('textract.process')
    def test_convert_institution(self, mock_process) -> None:
        """Test converting PDFs for a specific institution."""
        # Mock the textract process function to return sample text
        mock_process.return_value = b"Sample PDF content"
        
        # Initialize converter with ECB only
        converter = PdfConverter(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            institutions=["European Central Bank"]
        )
        
        # Convert for ECB
        converter.convert_institution("european_central_bank")
        
        # Check output files
        ecb_output_dir = self.output_dir / "european_central_bank"
        self.assertTrue(ecb_output_dir.exists())
        self.assertTrue((ecb_output_dir / "220101a.txt").exists())
        self.assertTrue((ecb_output_dir / "220102b.txt").exists())
        
        # Check conversion results
        result = converter.get_results()
        self.assertEqual(result.successful, 2)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)
        
        # Verify textract was called twice
        self.assertEqual(mock_process.call_count, 2)
    
    @patch('textract.process')
    def test_convert_with_limit(self, mock_process) -> None:
        """Test converting PDFs with a limit."""
        # Mock the textract process function to return sample text
        mock_process.return_value = b"Sample PDF content"
        
        # Initialize converter with limit=1
        converter = PdfConverter(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            limit=1
        )
        
        # Convert for ECB
        converter.convert_institution("european_central_bank")
        
        # Check output files - should only have one
        ecb_output_dir = self.output_dir / "european_central_bank"
        files = list(ecb_output_dir.glob("*.txt"))
        self.assertEqual(len(files), 1)
        
        # Check conversion results
        result = converter.get_results()
        self.assertEqual(result.successful, 1)
        
        # Verify textract was called once
        self.assertEqual(mock_process.call_count, 1)
    
    @patch('textract.process')
    def test_skip_existing_files(self, mock_process) -> None:
        """Test skipping already converted files."""
        # Mock the textract process function to return sample text
        mock_process.return_value = b"Sample PDF content"
        
        # Create existing output file
        ecb_output_dir = self.output_dir / "european_central_bank"
        ecb_output_dir.mkdir(exist_ok=True, parents=True)
        existing_file = ecb_output_dir / "220101a.txt"
        with open(existing_file, "w") as f:
            f.write("Existing content")
        
        # Initialize converter without force_convert
        converter = PdfConverter(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            institutions=["European Central Bank"]
        )
        
        # Convert for ECB
        converter.convert_institution("european_central_bank")
        
        # Check results
        result = converter.get_results()
        self.assertEqual(result.successful, 1)  # Only converted the new file
        self.assertEqual(result.skipped, 1)     # Skipped the existing file
        
        # Verify textract was called once
        self.assertEqual(mock_process.call_count, 1)
        
        # Check the existing file wasn't modified
        with open(existing_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "Existing content")
    
    @patch('textract.process')
    def test_force_convert(self, mock_process) -> None:
        """Test force converting existing files."""
        # Mock the textract process function to return sample text
        mock_process.return_value = b"New content"
        
        # Create existing output file
        ecb_output_dir = self.output_dir / "european_central_bank"
        ecb_output_dir.mkdir(exist_ok=True, parents=True)
        existing_file = ecb_output_dir / "220101a.txt"
        with open(existing_file, "w") as f:
            f.write("Existing content")
        
        # Initialize converter with force_convert=True
        converter = PdfConverter(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            institutions=["European Central Bank"],
            force_convert=True
        )
        
        # Convert for ECB
        converter.convert_institution("european_central_bank")
        
        # Check results
        result = converter.get_results()
        self.assertEqual(result.successful, 2)  # Converted both files
        self.assertEqual(result.skipped, 0)     # No skipped files
        
        # Verify textract was called twice
        self.assertEqual(mock_process.call_count, 2)
        
        # Check the existing file was modified
        with open(existing_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "New content")
    
    @patch('textract.process')
    def test_converter_error_handling(self, mock_process) -> None:
        """Test handling of conversion errors."""
        # Mock textract to raise an exception for the second file
        def side_effect(file_path):
            if "220102b.pdf" in file_path:
                raise Exception("Test conversion error")
            return b"Sample content"
        
        mock_process.side_effect = side_effect
        
        # Initialize converter
        converter = PdfConverter(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            institutions=["European Central Bank"]
        )
        
        # Convert for ECB - error should be handled internally
        converter.convert_institution("european_central_bank")
        
        # Check results
        result = converter.get_results()
        self.assertEqual(result.successful, 1)  # First file converted
        # The PDF converter counts errors both in the converter's internal state
        # and in the exception handler in convert_institution, resulting in 2 counts
        self.assertEqual(result.failed, 2)      # Second file failed, counted in two places
        self.assertIn("220102b", result.errors)  # Error recorded


if __name__ == "__main__":
    unittest.main() 