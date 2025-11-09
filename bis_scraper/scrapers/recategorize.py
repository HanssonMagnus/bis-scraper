"""Function to re-categorize files from unknown folder."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple

from bis_scraper.utils.constants import RAW_DATA_DIR, TXT_DATA_DIR
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
    if not metadata_file.exists():
        logger.debug("No metadata.json found in unknown folder")
        return (0, 0)

    # Load metadata
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading metadata.json from unknown folder: {e}")
        return (0, 0)

    recategorized = 0
    remaining_metadata = {}

    # Process each entry in metadata
    for speech_code, metadata_entry in metadata_data.items():
        raw_text = metadata_entry.get("raw_text", "")
        if not raw_text:
            # Keep entry if no raw_text available
            remaining_metadata[speech_code] = metadata_entry
            continue

        # Try to extract institution from metadata
        institution = get_institution_from_metadata(raw_text)

        if institution:  # None means not found, any string means found
            # Found a valid institution - move the files
            pdf_filename = f"{speech_code}.pdf"
            txt_filename = f"{speech_code}.txt"
            pdf_path = unknown_dir / pdf_filename

            if pdf_path.exists():
                # Get target institution directories
                target_pdf_dir = get_institution_directory(output_dir, institution)
                target_pdf_path = target_pdf_dir / pdf_filename

                # Get text directories
                texts_dir = data_dir / TXT_DATA_DIR
                unknown_texts_dir = texts_dir / "unknown"
                target_txt_dir = get_institution_directory(texts_dir, institution)
                txt_path = unknown_texts_dir / txt_filename
                target_txt_path = target_txt_dir / txt_filename

                # Move PDF file
                try:
                    shutil.move(str(pdf_path), str(target_pdf_path))
                    logger.info(
                        f"Re-categorized {speech_code} PDF from unknown to {institution}"
                    )

                    # Move text file if it exists
                    if txt_path.exists():
                        # Ensure target text directory exists
                        target_txt_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(txt_path), str(target_txt_path))
                        logger.info(
                            f"Re-categorized {speech_code} text file from unknown to {institution}"
                        )

                    # Save metadata to target directory
                    date_str = metadata_entry.get("date")
                    date_obj = None
                    if date_str:
                        try:
                            date_obj = datetime.fromisoformat(date_str).date()
                        except ValueError:
                            pass

                    save_metadata_to_json(
                        target_pdf_dir, speech_code, raw_text, date_obj
                    )

                    recategorized += 1
                except Exception as e:
                    logger.error(
                        f"Error moving {speech_code} to {institution}: {e}",
                        exc_info=True,
                    )
                    # Keep entry if move failed
                    remaining_metadata[speech_code] = metadata_entry
            else:
                # PDF doesn't exist, but keep metadata entry
                remaining_metadata[speech_code] = metadata_entry
        else:
            # Still unknown, keep entry
            remaining_metadata[speech_code] = metadata_entry

    # Update metadata.json in unknown folder
    if remaining_metadata:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(remaining_metadata, f, indent=2, ensure_ascii=False)
    else:
        # No remaining files, remove metadata.json and unknown folders if empty
        metadata_file.unlink()
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

    remaining_count = len(remaining_metadata)
    if recategorized > 0:
        logger.info(
            f"Re-categorized {recategorized} file(s) from unknown folder. "
            f"{remaining_count} file(s) still unknown."
        )

    return (recategorized, remaining_count)
