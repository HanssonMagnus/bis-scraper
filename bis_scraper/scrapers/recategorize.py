"""Function to re-categorize files from unknown folder."""

import json
import logging
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

import requests
from bs4 import BeautifulSoup

from bis_scraper.utils.constants import (
    HTML_EXTENSION,
    RAW_DATA_DIR,
    SPEECHES_URL,
    TXT_DATA_DIR,
)
from bis_scraper.utils.file_utils import (
    get_institution_directory,
    save_metadata_to_json,
)
from bis_scraper.utils.institution_utils import get_institution_from_metadata

logger = logging.getLogger(__name__)


def recategorize_unknown_files(data_dir: Path) -> Tuple[int, int]:
    """Re-categorize files from unknown folder using updated institution mappings.

    This function checks the unknown folder and attempts to re-categorize files
    based on their metadata. This is useful when institution mappings are updated
    in constants.py after files have already been downloaded.

    The function processes files sequentially and updates metadata.json immediately
    after each successful move. This ensures that if the process fails, we don't
    lose track of what was already processed.

    The function processes:
    1. Files with entries in metadata.json
    2. PDF files without metadata.json entries (fetches metadata from BIS website)

    Args:
        data_dir: Base directory for data storage

    Returns:
        Tuple of (files_recategorized, files_remaining) counts
    """
    output_dir = data_dir / RAW_DATA_DIR
    unknown_dir = output_dir / "unknown"

    # If unknown folder doesn't exist, nothing to do
    if not unknown_dir.exists():
        return (0, 0)

    metadata_file = unknown_dir / "metadata.json"

    # Load metadata.json if it exists
    metadata_data = _load_metadata_file(metadata_file)

    # Get all PDF files in unknown folder
    pdf_files = list(unknown_dir.glob("*.pdf"))

    # If no PDFs and no metadata, nothing to do
    if not pdf_files and not metadata_data:
        return (0, 0)

    recategorized = 0
    processed_codes = set()

    # First, process entries from metadata.json sequentially
    # Process a copy of items to avoid modifying dict during iteration
    for speech_code, metadata_entry in list(metadata_data.items()):
        processed_codes.add(speech_code)
        raw_text = metadata_entry.get("raw_text", "")
        if not raw_text:
            # Keep entry if no raw_text available (don't remove from metadata)
            continue

        # Try to extract institution from metadata
        institution = get_institution_from_metadata(raw_text)

        if institution:  # None means not found, any string means found
            # Found a valid institution - move the files
            if _move_files_to_institution(
                unknown_dir,
                data_dir,
                speech_code,
                institution,
                raw_text,
                metadata_entry,
            ):
                # Successfully moved - remove entry from metadata.json immediately
                _remove_metadata_entry(metadata_file, speech_code)
                recategorized += 1
            # If move failed, keep entry in metadata.json (don't remove)
        # If institution not found, keep entry in metadata.json (don't remove)

    # Now process PDFs that don't have metadata.json entries
    for pdf_path in pdf_files:
        # Extract speech code from filename (e.g., "000718b.pdf" -> "000718b")
        speech_code = pdf_path.stem

        # Skip if already processed
        if speech_code in processed_codes:
            continue

        # Fetch metadata from BIS website
        logger.info(f"Fetching metadata for {speech_code} from BIS website")
        metadata_text, date_obj = _fetch_metadata_from_bis(speech_code)

        if not metadata_text:
            # Could not fetch metadata, keep file in unknown
            logger.warning(f"Could not fetch metadata for {speech_code}")
            continue

        # Try to extract institution from metadata
        institution = get_institution_from_metadata(metadata_text)

        if institution:
            # Found a valid institution - move the files
            metadata_entry = {
                "raw_text": metadata_text,
                "date": str(date_obj) if date_obj else None,
            }
            if _move_files_to_institution(
                unknown_dir,
                data_dir,
                speech_code,
                institution,
                metadata_text,
                metadata_entry,
            ):
                # Successfully moved - no metadata entry to remove (wasn't in metadata.json)
                recategorized += 1
            # If move failed, file stays in unknown folder
        else:
            # Still unknown - add to metadata.json for future processing
            _add_metadata_entry(metadata_file, speech_code, metadata_text, date_obj)

    # Final cleanup: check if metadata.json should be deleted
    remaining_pdfs = list(unknown_dir.glob("*.pdf"))
    remaining_metadata = _load_metadata_file(metadata_file)

    if not remaining_metadata and not remaining_pdfs:
        # No remaining files and no PDFs, safe to delete metadata.json
        if metadata_file.exists():
            metadata_file.unlink()
            logger.info("Removed metadata.json (no remaining files)")

        # Try to remove empty unknown folders
        try:
            unknown_dir.rmdir()  # Remove if empty
            logger.info("Removed empty unknown PDF folder")
        except OSError:
            # Folder not empty (might have other files)
            pass

        # Also try to remove unknown texts folder if empty
        texts_dir = data_dir / TXT_DATA_DIR
        unknown_texts_dir = texts_dir / "unknown"
        if unknown_texts_dir.exists():
            try:
                # Check if folder is empty (only check for .txt files, ignore other files)
                txt_files = list(unknown_texts_dir.glob("*.txt"))
                if not txt_files:
                    unknown_texts_dir.rmdir()
                    logger.info("Removed empty unknown texts folder")
            except OSError:
                # Folder not empty or other error
                pass

    # Calculate remaining count before logging
    remaining_pdfs_final = list(unknown_dir.glob("*.pdf"))
    pdf_codes_final = {p.stem for p in remaining_pdfs_final}
    pdf_codes_with_metadata_final = set(remaining_metadata.keys())
    # Count: PDFs without metadata + metadata entries without PDFs
    overlap_final = len(pdf_codes_final & pdf_codes_with_metadata_final)
    remaining_count = (
        len(remaining_pdfs_final) + len(remaining_metadata) - overlap_final
    )
    # Ensure count is never negative
    remaining_count = max(0, remaining_count)

    if recategorized > 0:
        logger.info(
            f"Re-categorized {recategorized} file(s) from unknown folder. "
            f"{remaining_count} file(s) still unknown."
        )

    return (recategorized, remaining_count)


def _load_metadata_file(metadata_file: Path) -> Dict[str, Any]:
    """Load metadata.json file, handling corruption.

    Args:
        metadata_file: Path to metadata.json file

    Returns:
        Dictionary of metadata entries, empty dict if file doesn't exist or is corrupted
    """
    if not metadata_file.exists():
        return {}

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Try to parse JSON, handling corrupted files
            try:
                return cast(Dict[str, Any], json.loads(content))
            except json.JSONDecodeError as e:
                # If JSON is corrupted, try to extract valid JSON portion
                logger.warning(
                    f"JSON parse error in metadata.json: {e}. Attempting to recover..."
                )
                # Try to find the end of valid JSON
                if e.pos and e.pos > 0:
                    try:
                        # Try parsing up to the error position
                        recovered_data = cast(
                            Dict[str, Any], json.loads(content[: e.pos])
                        )
                        logger.info(
                            f"Recovered {len(recovered_data)} entries from corrupted metadata.json"
                        )
                        return recovered_data
                    except json.JSONDecodeError:
                        logger.error(
                            "Could not recover metadata.json. File may be severely corrupted."
                        )
                        return {}
                else:
                    logger.error("Could not recover metadata.json")
                    return {}
    except IOError as e:
        logger.warning(f"Error reading metadata.json: {e}")
        return {}


def _remove_metadata_entry(metadata_file: Path, speech_code: str) -> None:
    """Remove a single entry from metadata.json atomically.

    Args:
        metadata_file: Path to metadata.json file
        speech_code: Speech code to remove
    """
    if not metadata_file.exists():
        return

    try:
        # Load current metadata
        metadata_data = _load_metadata_file(metadata_file)
        if speech_code not in metadata_data:
            return

        # Remove entry
        del metadata_data[speech_code]

        # Write back (atomic write)
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(
            f"Error removing metadata entry for {speech_code}: {e}", exc_info=True
        )


def _add_metadata_entry(
    metadata_file: Path, speech_code: str, metadata_text: str, date_obj: Optional[date]
) -> None:
    """Add a single entry to metadata.json atomically.

    Args:
        metadata_file: Path to metadata.json file
        speech_code: Speech code to add
        metadata_text: Raw metadata text
        date_obj: Optional date object
    """
    try:
        # Load current metadata
        metadata_data = _load_metadata_file(metadata_file)

        # Add entry
        metadata_data[speech_code] = {
            "raw_text": metadata_text,
            "date": str(date_obj) if date_obj else None,
        }

        # Write back (atomic write)
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(
            f"Error adding metadata entry for {speech_code}: {e}", exc_info=True
        )


def _fetch_metadata_from_bis(speech_code: str) -> Tuple[Optional[str], Optional[date]]:
    """Fetch metadata from BIS website for a speech code.

    Args:
        speech_code: Speech code without 'r' prefix (e.g., "000718b")

    Returns:
        Tuple of (metadata_text, date_obj) or (None, None) if fetch failed
    """
    try:
        # Add 'r' prefix if not present
        full_code = (
            f"r{speech_code}" if not speech_code.startswith("r") else speech_code
        )

        # Get metadata page URL
        metadata_url = f"{SPEECHES_URL}/{full_code}{HTML_EXTENSION}"

        # Get the metadata page
        metadata_response = requests.get(metadata_url, timeout=30)
        metadata_response.raise_for_status()

        # Parse metadata page
        metadata_soup = BeautifulSoup(metadata_response.text, "html.parser")

        # Extract metadata - specifically look for extratitle-div
        extratitle_div = metadata_soup.find(id="extratitle-div")
        if extratitle_div:
            metadata_text = extratitle_div.text.strip()
        else:
            # Fall back to full text if the specific div isn't found
            metadata_text = metadata_soup.get_text()

        # Try to extract date from speech code (YYMMDD format)
        date_obj = None
        if len(speech_code) >= 6:
            try:
                year = int(speech_code[:2])
                month = int(speech_code[2:4])
                day = int(speech_code[4:6])
                # Handle 2-digit year (assume 00-50 = 2000-2050, 51-99 = 1951-1999)
                if year <= 50:
                    year += 2000
                else:
                    year += 1900
                date_obj = datetime(year, month, day).date()
            except (ValueError, IndexError):
                pass

        return (metadata_text, date_obj)
    except Exception as e:
        logger.error(f"Error fetching metadata for {speech_code}: {e}", exc_info=True)
        return (None, None)


def _move_files_to_institution(
    unknown_dir: Path,
    data_dir: Path,
    speech_code: str,
    institution: str,
    metadata_text: str,
    metadata_entry: dict,
) -> bool:
    """Move PDF and text files from unknown folder to institution folder.

    Args:
        unknown_dir: Unknown directory path
        data_dir: Base data directory
        speech_code: Speech code without 'r' prefix
        institution: Institution name
        metadata_text: Raw metadata text
        metadata_entry: Metadata entry dictionary

    Returns:
        True if files were moved successfully, False otherwise
    """
    try:
        pdf_filename = f"{speech_code}.pdf"
        txt_filename = f"{speech_code}.txt"
        pdf_path = unknown_dir / pdf_filename

        if not pdf_path.exists():
            return False

        # Get target institution directories
        output_dir = data_dir / RAW_DATA_DIR
        target_pdf_dir = get_institution_directory(output_dir, institution)
        target_pdf_path = target_pdf_dir / pdf_filename

        # Get text directories
        texts_dir = data_dir / TXT_DATA_DIR
        unknown_texts_dir = texts_dir / "unknown"
        target_txt_dir = get_institution_directory(texts_dir, institution)
        txt_path = unknown_texts_dir / txt_filename
        target_txt_path = target_txt_dir / txt_filename

        # Move PDF file
        shutil.move(str(pdf_path), str(target_pdf_path))
        logger.info(f"Re-categorized {speech_code} PDF from unknown to {institution}")

        # Move text file if it exists
        if txt_path.exists():
            # Ensure target text directory exists
            target_txt_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(txt_path), str(target_txt_path))
            logger.info(
                f"Re-categorized {speech_code} text file from unknown to {institution}"
            )

        # Save metadata to target directory
        # Preserve existing structured metadata from metadata_entry if available
        json_path = target_pdf_dir / "metadata.json"

        # Check if metadata_entry has structured fields (more than raw_text and date)
        has_structured_metadata = len(metadata_entry) > 2 or any(
            key not in ("raw_text", "date") for key in metadata_entry.keys()
        )

        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except (IOError, json.JSONDecodeError):
                existing_data = {}

            # If we have structured metadata in metadata_entry, preserve it
            if has_structured_metadata:
                # Merge: preserve structured fields, update raw_text and date
                existing_data[speech_code] = {
                    **metadata_entry,  # Preserve all structured fields
                    "raw_text": metadata_text.strip(),  # Update raw_text
                }
                # Ensure date is in ISO format if provided
                date_str = metadata_entry.get("date")
                if date_str:
                    existing_data[speech_code]["date"] = date_str
                # Write back
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                return True

        # No structured metadata in metadata_entry, use normal save (will parse)
        date_str = metadata_entry.get("date")
        date_obj = None
        if date_str:
            try:
                # Handle both ISO format and string format
                if isinstance(date_str, str) and len(date_str) == 10:
                    date_obj = datetime.fromisoformat(date_str).date()
                elif isinstance(date_str, str):
                    # Try parsing as date string
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        save_metadata_to_json(target_pdf_dir, speech_code, metadata_text, date_obj)

        return True
    except Exception as e:
        logger.error(
            f"Error moving {speech_code} to {institution}: {e}",
            exc_info=True,
        )
        return False
