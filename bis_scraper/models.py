"""Data models for the BIS Scraper package."""

from datetime import date
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class Institution(BaseModel):
    """Institution model for central banks."""
    
    name: str
    aliases: List[str] = Field(default_factory=list)


class SpeechMetadata(BaseModel):
    """Metadata for a speech."""
    
    date: date
    letter_code: str
    institution: str
    title: Optional[str] = None
    speaker: Optional[str] = None
    event: Optional[str] = None
    raw_text: str


class SpeechFile(BaseModel):
    """Model representing a speech file."""
    
    pdf_path: Path
    text_path: Optional[Path] = None
    metadata: Optional[SpeechMetadata] = None
    pdf_exists: bool = False
    text_exists: bool = False
    
    def check_file_exists(self) -> None:
        """Check if files exist and update status."""
        self.pdf_exists = self.pdf_path.exists()
        if self.text_path:
            self.text_exists = self.text_path.exists()


@dataclass
class ScrapingResult:
    """Results from a scraping operation."""
    
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConversionResult:
    """Results from a PDF conversion operation."""
    
    successful: int = 0
    skipped: int = 0
    failed: int = 0
    errors: Dict[str, str] = field(default_factory=dict) 