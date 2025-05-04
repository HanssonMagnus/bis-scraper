"""Test fixtures and configuration for the BIS Scraper package."""

import os
import shutil
from pathlib import Path
from typing import Generator

import pytest
import responses

from bis_scraper.utils.constants import RAW_DATA_DIR, TXT_DATA_DIR


@pytest.fixture
def mock_responses() -> Generator[responses.RequestsMock, None, None]:
    """Fixture for mocking HTTP responses."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Fixture for creating a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (data_dir / RAW_DATA_DIR).mkdir(exist_ok=True)
    (data_dir / TXT_DATA_DIR).mkdir(exist_ok=True)
    
    yield data_dir
    
    # Clean up after test
    if data_dir.exists():
        shutil.rmtree(data_dir)


@pytest.fixture
def test_log_dir(tmp_path: Path) -> Path:
    """Fixture for creating a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    
    yield log_dir
    
    # Clean up after test
    if log_dir.exists():
        shutil.rmtree(log_dir)


@pytest.fixture
def sample_speech_html() -> str:
    """Fixture for a sample speech HTML page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Speech</title>
    </head>
    <body>
        <div id="extratitle-div">
            Speech by Mr. John Smith, Governor of the European Central Bank, at the Annual Conference
        </div>
        <div class="content">
            <p>Sample speech content...</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_speech_pdf() -> bytes:
    """Fixture for a sample speech PDF content."""
    # This is a minimal valid PDF
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>endobj 4 0 obj<</Length 10>>stream\nSample text\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n0000000194 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n252\n%%EOF"


@pytest.fixture
def sample_date_page_html() -> str:
    """Fixture for a sample date listing page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Speeches</title>
    </head>
    <body>
        <div class="content">
            <ul>
                <li><a href="/review/r200101a.pdf">Speech PDF</a></li>
                <li><a href="/review/r200101b.pdf">Another Speech PDF</a></li>
                <li><a href="/other/document.pdf">Non-speech PDF</a></li>
            </ul>
        </div>
    </body>
    </html>
    """ 