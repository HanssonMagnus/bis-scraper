"""BIS website scraper for central bank speeches."""

import datetime
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup

from bis_scraper.models import ScrapingResult
from bis_scraper.utils.constants import (
    BASE_URL,
    HTML_EXTENSION, 
    INSTITUTIONS, 
    PDF_EXTENSION,
    SPEECHES_URL
)
from bis_scraper.utils.file_utils import (
    create_directory,
    format_filename,
    get_institution_directory,
    find_existing_files,
    save_metadata_to_json,
)
from bis_scraper.utils.institution_utils import get_institution_from_metadata, normalize_institution_name

logger = logging.getLogger(__name__)


class BisScraper:
    """Scraper for the BIS central bank speeches website."""
    
    def __init__(
        self,
        output_dir: Path,
        institutions: Optional[List[str]] = None,
        force_download: bool = False,
        limit: Optional[int] = None,
    ):
        """Initialize the BIS scraper.
        
        Args:
            output_dir: Directory to save downloaded files
            institutions: List of institutions to scrape (None = all)
            force_download: Force re-download of existing files
            limit: Maximum number of speeches to download
        """
        self.output_dir = output_dir
        self.institutions = institutions
        self.force_download = force_download
        self.limit = limit  # Used directly in this class to limit downloads
        self.result = ScrapingResult()
        
        # Ensure output directory exists
        create_directory(self.output_dir)
        
        # Build cache of existing files (filename without the 'r' prefix)
        self.existing_files = set()
        if not force_download:
            self._build_existing_files_cache()
            logger.info(f"Found {len(self.existing_files)} existing speech files in cache")
    
    def _build_existing_files_cache(self) -> None:
        """Build cache of existing files to avoid filesystem checks."""
        # Find all institution directories
        for inst_dir in self.output_dir.iterdir():
            if inst_dir.is_dir():
                # Find all PDF files in this institution directory
                for file_path in inst_dir.glob("*.pdf"):
                    # Extract the code part without the 'r' prefix
                    code = file_path.stem
                    self.existing_files.add(code)
    
    def scrape_date(self, date_obj: datetime.date) -> bool:
        """Scrape speeches for a specific date.
        
        Args:
            date_obj: Date to scrape
            
        Returns:
            bool: True if processing should continue, False if limit reached
        """
        # Format date for URL: YYMMDD (without century)
        date_str = date_obj.strftime("%y%m%d")
        
        # Try all possible letters for this date
        for letter_code in 'abcdefghijklmnopqrstuvwxyz':
            # Create the code without the 'r' prefix for cache checking
            code_without_r = f"{date_str}{letter_code}"
            speech_code = f"r{code_without_r}"
            
            # Quick check for cached file before making network request
            if not self.force_download and code_without_r in self.existing_files:
                # Skip the network request entirely if we already have this file
                logger.debug(f"Skipping {speech_code} (found in cache)")
                self.result.skipped += 1
                continue
                
            url = f"{SPEECHES_URL}/{speech_code}{HTML_EXTENSION}"
            
            try:
                # Request the page
                response = requests.get(url, timeout=30)
                if response.status_code == 404:
                    # If first letter returns 404, likely no speeches for this date
                    if letter_code == 'a':
                        message = f"No speeches found for {date_obj.isoformat()} (404 Not Found at {url})"
                        logger.info(message)
                        print(message)  # Print to stdout for CLI feedback
                    # Stop trying more letters if we hit a 404
                    break
                
                response.raise_for_status()
                
                # We found a valid speech, process it
                logger.info(f"Found speech {speech_code} for {date_obj.isoformat()}")
                
                # Process the speech
                pdf_url = f"{SPEECHES_URL}/{speech_code}{PDF_EXTENSION}"
                should_continue = self._process_speech_from_code(speech_code, pdf_url, date_obj)
                if not should_continue:
                    return False
                
            except Exception as e:
                if response.status_code != 404:  # Don't log 404s as errors
                    logger.error(f"Error scraping {date_obj.isoformat()} - {speech_code}: {str(e)}", exc_info=True)
                    self.result.failed += 1
        
        return True
    
    def _process_speech_from_code(self, speech_code: str, pdf_url: str, date_obj: datetime.date) -> bool:
        """Process a speech using its code.
        
        Args:
            speech_code: Speech code (e.g., r200108a)
            pdf_url: URL to the PDF file
            date_obj: Date of the speech
            
        Returns:
            bool: True if processing should continue, False if limit reached
        """
        try:
            # Get metadata page URL
            metadata_url = f"{SPEECHES_URL}/{speech_code}{HTML_EXTENSION}"
            
            # Get the metadata page
            metadata_response = requests.get(metadata_url, timeout=30)
            metadata_response.raise_for_status()
            
            # Parse metadata page
            metadata_soup = BeautifulSoup(metadata_response.text, "html.parser")
            
            # Extract metadata - specifically look for extratitle-div like in the original code
            extratitle_div = metadata_soup.find(id='extratitle-div')
            if extratitle_div:
                metadata_text = extratitle_div.text.strip()
            else:
                # Fall back to full text if the specific div isn't found
                metadata_text = metadata_soup.get_text()
            
            # Extract institution from metadata
            institution = get_institution_from_metadata(metadata_text)
            
            if not institution:
                # If no institution found, log warning but still download
                logger.warning(f"Could not identify institution for {speech_code}")
                institution = "unknown"
            
            # Filter if institutions specified
            if self.institutions is not None and institution.lower() not in [i.lower() for i in self.institutions]:
                logger.debug(f"Skipping {speech_code} (institution {institution} not in filter)")
                self.result.skipped += 1
                return True
            
            # Create institution directory
            inst_dir = get_institution_directory(self.output_dir, institution)
            create_directory(inst_dir)
            
            # Code without 'r' prefix for metadata entry
            code_without_r = speech_code[1:] if speech_code.startswith('r') else speech_code
            
            # Save metadata in text format (for backward compatibility)
            normalized_inst = normalize_institution_name(institution)
            metadata_filename = f"{normalized_inst}_meta.txt"
            metadata_path = inst_dir / metadata_filename
            
            # Append metadata entry to the text file
            with open(metadata_path, "a", encoding="utf-8") as metadata_file:
                metadata_file.write(f"{code_without_r}: {metadata_text}\n")
            
            # Save metadata in JSON format
            save_metadata_to_json(inst_dir, code_without_r, metadata_text, date_obj)
            
            # Format output filename
            output_filename = format_filename(speech_code, institution)
            output_path = inst_dir / output_filename
            
            # Skip if file exists and not forcing download (second check in case the file was created in a different institution directory)
            if output_path.exists() and not self.force_download:
                # Print a message for the CLI that the speech already exists
                skip_message = f"Skipping {speech_code} (already exists at {output_path})"
                logger.debug(skip_message)
                self.result.skipped += 1
                return True
            
            # Download the PDF
            logger.debug(f"Downloading {pdf_url} to {output_path}")
            
            pdf_response = requests.get(pdf_url, timeout=30)
            pdf_response.raise_for_status()
            
            # Save PDF
            with open(output_path, "wb") as pdf_file:
                pdf_file.write(pdf_response.content)
            
            # Add to in-memory cache
            self.existing_files.add(code_without_r)
            
            # Print download message for CLI feedback
            download_message = f"Downloaded {speech_code} to {output_path}"
            logger.info(download_message)
            print(download_message)  # Print to stdout for CLI feedback
            self.result.downloaded += 1
            
            # Check if we've hit the limit - NEW CODE
            if self.limit is not None and self.result.downloaded >= self.limit:
                logger.info(f"Reached download limit of {self.limit} speeches. Stopping.")
                print(f"Reached download limit of {self.limit} speeches at speech level. Stopping.")
                return False
            
            # Sleep briefly to avoid overloading the server - only when actually downloading
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing speech {speech_code}: {str(e)}", exc_info=True)
            self.result.failed += 1
            return True
    
    def get_results(self) -> ScrapingResult:
        """Get the scraping results.
        
        Returns:
            ScrapingResult object with statistics
        """
        return self.result 