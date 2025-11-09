"""BIS Scraper - Download and process central bank speeches from the BIS website."""

from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import re

try:
    __version__ = version("bis_scraper")
except PackageNotFoundError:
    # Package is not installed, read from pyproject.toml (source of truth)
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            __version__ = match.group(1)
        else:
            __version__ = "0.1.0"
    else:
        __version__ = "0.1.0"
