"""File utility functions for the BIS Scraper package."""

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

logger = logging.getLogger(__name__)


def create_directory(directory: Path) -> None:
    """Create a directory if it doesn't exist.
    
    Args:
        directory: Directory path to create
    """
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {directory}")


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 hash as hex string
    """
    hash_obj = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def list_directories(base_dir: Path) -> List[str]:
    """List all directories in a base directory.
    
    Args:
        base_dir: Base directory to list
        
    Returns:
        List of directory names (not full paths)
    """
    if not base_dir.exists():
        return []
    
    return [d.name for d in base_dir.iterdir() if d.is_dir()]


def find_existing_files(directory: Path, extension: str) -> Set[str]:
    """Find all existing files with a specific extension.
    
    Args:
        directory: Directory to search in
        extension: File extension to look for (e.g., '.pdf')
        
    Returns:
        Set of file codes (without extension)
    """
    result: Set[str] = set()
    if not directory.exists():
        return result
    
    for file_path in directory.glob(f"*{extension}"):
        # Extract the code part from filename (e.g., "220101a" from "220101a.pdf")
        filename = file_path.stem
        result.add(filename)
    
    return result


def normalize_institution_name(name: str) -> str:
    """Normalize an institution name for use in filenames and directories.
    
    Args:
        name: Institution name
        
    Returns:
        Normalized name with spaces converted to underscores and lowercase
    """
    # Convert to lowercase for consistency
    normalized = name.lower()
    
    # Replace spaces with underscores
    normalized = normalized.replace(' ', '_')
    
    # Replace special characters
    normalized = normalized.replace("'", '')
    normalized = normalized.replace(",", '')
    normalized = normalized.replace("&", 'and')
    
    return normalized


def get_institution_directory(base_dir: Path, institution: str) -> Path:
    """Get or create directory for an institution.
    
    Args:
        base_dir: Base directory
        institution: Institution name
        
    Returns:
        Path to institution directory
    """
    # Normalize institution name for directory
    normalized_name = normalize_institution_name(institution)
    directory = base_dir / normalized_name
    create_directory(directory)
    return directory


def format_filename(speech_code: str, institution: str) -> str:
    """Format filename for a speech PDF.
    
    Args:
        speech_code: Speech code (e.g., "r220101a")
        institution: Institution name
        
    Returns:
        Formatted filename with just the date and letter code (e.g., "220101a.pdf")
    """
    # Remove 'r' prefix if present
    clean_code = speech_code
    if speech_code.startswith('r'):
        clean_code = speech_code[1:]
    
    return f"{clean_code}.pdf"


def save_metadata_to_json(institution_dir: Path, speech_code: str, metadata_text: str, date_obj: Optional[Any] = None) -> None:
    """Save speech metadata to a JSON file.
    
    Args:
        institution_dir: Directory for the institution
        speech_code: Speech code (without 'r' prefix, e.g., "220101a")
        metadata_text: Raw metadata text from the speech page
        date_obj: Date object of the speech
    """
    json_path = institution_dir / "metadata.json"
    
    # Initialize data structure or load existing
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {json_path}, creating new file")
            data = {}
    else:
        data = {}
    
    # Extract structured information from metadata text
    structured_metadata = parse_metadata_text(metadata_text)
    
    # Create metadata entry
    metadata = {
        "raw_text": metadata_text.strip(),
        **structured_metadata
    }
    
    # Add date if provided
    if date_obj:
        metadata["date"] = date_obj.isoformat()
    
    # Add or update entry
    data[speech_code] = metadata
    
    # Write updated JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_metadata_text(metadata_text: str) -> Dict[str, str]:
    """Parse metadata text to extract structured information.
    
    Args:
        metadata_text: Raw metadata text
        
    Returns:
        Dictionary with structured metadata fields
    """
    result = {}
    
    # First check if there's a speech title in quotes at the beginning
    title_match = re.match(r'^\s*\"([^\"]+)\"', metadata_text)
    
    # Extract speech type from the beginning of the text
    speech_type_match = re.match(r'^\s*([A-Za-z]+(?:\s+[a-z]+)?)\s+(?:by|remarks)', metadata_text)
    if speech_type_match:
        result["speech_type"] = speech_type_match.group(1).strip()
    
    # Extract full speaker information
    full_speaker_info = re.search(r"(?:by|remarks by)\s+([^,]+),\s+(.+?)(?:,\s+at|,\s+on|at|on|,\s+\d)", metadata_text)
    
    if full_speaker_info:
        # Just the name (Ms Name or Mr Name)
        result["speaker"] = full_speaker_info.group(1).strip()
        # The role without trailing comma
        if full_speaker_info.group(2):
            role = full_speaker_info.group(2).strip()
            # Remove trailing comma if present
            if role.endswith(','):
                role = role[:-1].strip()
            result["role"] = role
    else:
        # Fallback for cases where the pattern doesn't match
        basic_speaker_match = re.search(r"(?:by|remarks by)\s+([^,]+)", metadata_text)
        if basic_speaker_match:
            result["speaker"] = basic_speaker_match.group(1).strip()
    
    # Other patterns
    patterns = {
        "event": r"(?:at|on)\s+the\s+(.+?)(?:,|\.|$)",  # After "at"/"on" before comma/period/end
        "speech_date": r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})",  # Date format like "3 May 2024"
    }
    
    # Extract title if found
    if title_match:
        result["title"] = title_match.group(1).strip()
    else:
        # Fallback title extraction
        alt_title_match = re.search(r"(?:\"|\")([^\"]+)(?:\"|\")", metadata_text)
        if alt_title_match:
            result["title"] = alt_title_match.group(1).strip()
    
    # Extract other fields using regex patterns
    for field, pattern in patterns.items():
        match = re.search(pattern, metadata_text)
        if match:
            result[field] = match.group(1).strip()
    
    # Location extraction - try multiple patterns
    # First look for common US location pattern: City, State before date
    us_location_match = re.search(r',\s+([^,]+,\s+[A-Za-z]+)(?:,\s+\d)', metadata_text)
    if us_location_match:
        result["location"] = us_location_match.group(1).strip()
    
    # If that didn't work, check for specific known locations
    elif not result.get("location"):
        specific_locations = ["Washington DC", "New York City", "Frankfurt", "London", "Tokyo", "Paris", "Berlin", "Basel", "Zurich"]
        for loc in specific_locations:
            # Make sure we match whole words
            if re.search(rf'\b{re.escape(loc)}\b', metadata_text, re.IGNORECASE):
                result["location"] = loc
                break
    
    # If still no location, try the fallback method
    if not result.get("location") and "speech_date" in result:
        # Look for text between the last comma and the date
        date_index = metadata_text.find(result["speech_date"])
        if date_index > 0:
            text_before_date = metadata_text[:date_index].strip()
            last_comma = text_before_date.rfind(',')
            second_last_comma = text_before_date[:last_comma].rfind(',') if last_comma > 0 else -1
            
            if last_comma >= 0 and second_last_comma >= 0:
                # Extract the text between the second-last and last comma
                location = text_before_date[second_last_comma+1:last_comma].strip()
                # Don't capture "organized by" text
                if "organised by" not in location.lower() and "organized by" not in location.lower():
                    result["location"] = location
    
    # Clean up event field - sometimes it includes 'the' or has location info
    if "event" in result:
        result["event"] = result["event"].strip()
        # Remove "the" prefix if it exists
        if result["event"].startswith("the "):
            result["event"] = result["event"][4:]
    
    # Add organizer information if available
    organizer_match = re.search(r'organised by\s+([^,]+)', metadata_text, re.IGNORECASE)
    if organizer_match:
        result["organizer"] = organizer_match.group(1).strip()
    
    return result 