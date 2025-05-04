"""Institution utility functions for the BIS Scraper package."""

import logging
import re
from typing import Dict, List, Optional

from bis_scraper.utils.constants import INSTITUTIONS, INSTITUTION_ALIASES

logger = logging.getLogger(__name__)


def normalize_institution_name(institution: str) -> str:
    """Normalize institution name to a standard format.
    
    Args:
        institution: Institution name to normalize
        
    Returns:
        Normalized institution name with spaces converted to underscores and lowercase
    """
    # Convert to lowercase for case-insensitive matching
    normalized = institution.lower()
    
    # Strip whitespace from the ends
    normalized = normalized.strip()
    
    # Replace spaces with underscores
    normalized = normalized.replace(' ', '_')
    
    # Replace special characters
    normalized = normalized.replace("'", '')
    normalized = normalized.replace(",", '')
    normalized = normalized.replace("&", 'and')
    
    return normalized


def standardize_institution_name(institution: str) -> str:
    """Standardize institution name using aliases.
    
    Args:
        institution: The institution name to standardize
        
    Returns:
        Standardized institution name
    """
    institution_lower = institution.lower()
    
    # Check if this is an alias
    for standard_name, aliases in INSTITUTION_ALIASES.items():
        if institution_lower in [alias.lower() for alias in aliases]:
            return standard_name
    
    # If not an alias, return the original (but lowercase)
    return institution_lower


def get_institution_from_metadata(metadata: str) -> Optional[str]:
    """Extract institution name from speech metadata.
    
    Args:
        metadata: Metadata string from BIS website
        
    Returns:
        Normalized institution name or None if not found
    """
    if not metadata:
        return None
    
    # Convert to lowercase for case-insensitive matching
    metadata_lower = metadata.lower()
    
    # First try direct matching of institution names
    for institution in INSTITUTIONS:
        if institution.lower() in metadata_lower:
            return standardize_institution_name(institution)
    
    # Then try matching aliases
    for standard_name, aliases in INSTITUTION_ALIASES.items():
        for alias in aliases:
            if alias.lower() in metadata_lower:
                return standard_name
    
    logger.warning(f"No institution found in metadata: {metadata}")
    return None


def get_all_institutions() -> List[str]:
    """Get list of all supported institutions.
    
    Returns:
        List of institution names (normalized)
    """
    return [normalize_institution_name(inst) for inst in INSTITUTIONS]


def get_institution_aliases() -> Dict[str, List[str]]:
    """Get mapping of standard institution names to their aliases.
    
    Returns:
        Dictionary of standardized institution names to aliases
    """
    return INSTITUTION_ALIASES 