"""Controller module for PDF to text conversion operations."""

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

from bis_scraper.converters.pdf_converter import PdfConverter
from bis_scraper.models import ConversionResult
from bis_scraper.utils.constants import RAW_DATA_DIR, TXT_DATA_DIR
from bis_scraper.utils.file_utils import list_directories
from bis_scraper.utils.institution_utils import normalize_institution_name

logger = logging.getLogger(__name__)


def convert_pdfs(
    data_dir: Path,
    log_dir: Path,
    institutions: Optional[Tuple[str, ...]] = None,
    force: bool = False,
    limit: Optional[int] = None,
) -> ConversionResult:
    """Convert PDF speeches to text format.

    Args:
        data_dir: Base directory for data storage
        log_dir: Directory for log files
        institutions: Specific institutions to convert (default: all)
        force: Whether to force re-convert existing files
        limit: Maximum number of files to convert per institution

    Returns:
        ConversionResult with statistics
    """
    start_time = time.time()

    # Set up input and output directories
    input_dir = data_dir / RAW_DATA_DIR
    output_dir = data_dir / TXT_DATA_DIR

    # Check if input directory exists
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        result = ConversionResult()
        result.errors["global"] = f"Input directory {input_dir} does not exist"
        return result

    # Get list of institutions to process
    available_institutions = list_directories(input_dir)
    logger.info(f"Found {len(available_institutions)} institutions in {input_dir}")

    # Initialize converter with normalized institution names if provided
    normalized_institutions = (
        [normalize_institution_name(i) for i in institutions] if institutions else None
    )

    converter = PdfConverter(
        input_dir=input_dir,
        output_dir=output_dir,
        institutions=normalized_institutions,
        force_convert=force,
        limit=limit,
    )

    # Process each institution
    for institution in available_institutions:
        try:
            converter.convert_institution(institution)
        except Exception as e:
            logger.error(
                f"Error processing institution {institution}: {str(e)}", exc_info=True
            )

    # Get results
    result = converter.get_results()

    # Log summary
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    logger.info(
        f"Conversion completed in {int(hours):02}:{int(minutes):02}:{seconds:05.2f}"
    )
    logger.info(
        f"Results: {result.successful} converted, {result.skipped} skipped, "
        f"{result.failed} failed"
    )

    return result
