"""PDF to text converter implementation."""

import logging
from pathlib import Path
from typing import List, Optional

import textract  # type: ignore

from bis_scraper.models import ConversionResult
from bis_scraper.utils.date_utils import parse_date_code
from bis_scraper.utils.file_utils import create_directory
from bis_scraper.utils.institution_utils import normalize_institution_name

logger = logging.getLogger(__name__)


class PdfConverter:
    """PDF to text converter class."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        institutions: Optional[List[str]] = None,
        force_convert: bool = False,
        limit: Optional[int] = None,
    ):
        """Initialize the PDF converter.

        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save text files
            institutions: List of institutions to convert (None = all)
            force_convert: Whether to re-convert files that already exist
            limit: Maximum number of files to convert per institution
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        # Normalize institution names if provided
        self.institutions = (
            [normalize_institution_name(i) for i in institutions]
            if institutions
            else None
        )
        self.force_convert = force_convert
        self.limit = limit
        self.result = ConversionResult()

        # Create output directory
        create_directory(self.output_dir)

    def convert_institution(self, institution: str) -> None:
        """Convert all PDFs for a specific institution.

        Args:
            institution: Institution name (directory name)
        """
        # Normalize the institution name for consistent comparison and path handling
        normalized_institution = normalize_institution_name(institution)

        # Skip if not in the list of required institutions
        if (
            self.institutions is not None
            and normalized_institution not in self.institutions
        ):
            logger.debug(f"Skipping institution {institution} (not in required list)")
            return

        # Check if institution directory exists in input
        inst_input_dir = self.input_dir / normalized_institution
        if not inst_input_dir.exists() or not inst_input_dir.is_dir():
            logger.warning(f"Input directory not found for {normalized_institution}")
            return

        # Create output directory for institution
        inst_output_dir = self.output_dir / normalized_institution
        create_directory(inst_output_dir)

        # Process all PDFs in the institution directory - using new filename format
        pdf_files = list(inst_input_dir.glob("*.pdf"))

        # Apply limit if specified
        if self.limit is not None and self.limit > 0:
            logger.info(
                f"Limiting conversion to {self.limit} files for {normalized_institution}"
            )
            pdf_files = pdf_files[: self.limit]

        for pdf_file in pdf_files:
            # Process each file, catching exceptions to allow processing to continue
            try:
                self._convert_pdf(pdf_file, inst_output_dir, normalized_institution)
            except Exception as e:
                # Log error and continue with the next file
                file_code = pdf_file.stem
                logger.error(f"Error converting {file_code}: {str(e)}", exc_info=True)
                self.result.failed += 1
                self.result.errors[file_code] = str(e)

    def _convert_pdf(self, pdf_path: Path, output_dir: Path, institution: str) -> None:
        """Convert a single PDF file to text.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save text file
            institution: Institution name
        """
        # Extract file code (e.g., "220101a") from filename (now just the stem without extension)
        file_code = pdf_path.stem

        try:
            # Parse date from file code
            date_obj, letter_code = parse_date_code(file_code)

            # Create output filename matching the input filename but with .txt extension
            txt_filename = f"{file_code}.txt"
            txt_path = output_dir / txt_filename

            # Skip if the text file already exists and we're not forcing conversion
            if txt_path.exists() and not self.force_convert:
                # Print a message for CLI feedback
                skip_message = (
                    f"Skipping {file_code} (already converted to {txt_filename})"
                )
                logger.debug(skip_message)
                print(skip_message)  # Print to stdout for CLI feedback
                self.result.skipped += 1
                return

            # Extract text from PDF
            logger.debug(f"Converting {pdf_path}")
            text = textract.process(str(pdf_path))
            text_str = text.decode("utf-8")

            # Save text to file
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text_str)

            # Print conversion message for CLI feedback
            conversion_message = f"Converted {file_code} to {txt_filename}"
            logger.info(conversion_message)
            print(conversion_message)  # Print to stdout for CLI feedback
            self.result.successful += 1

        except Exception as e:
            error_message = f"Error converting {file_code}: {str(e)}"
            logger.error(error_message, exc_info=True)
            print(f"Error: {error_message}")  # Print to stdout for CLI feedback
            self.result.failed += 1
            self.result.errors[file_code] = str(e)
            # Re-raise the exception to be caught by the calling function
            raise

    def get_results(self) -> ConversionResult:
        """Get the conversion results.

        Returns:
            ConversionResult object with statistics
        """
        return self.result
