# API Documentation

This document provides details about the programmatic interface (API) of the BIS Scraper package. The API consists of:

1. **Python Functions and Classes**: These can be imported and used in your Python code
2. **Command-Line Interface (CLI)**: Available as the `bis-scraper` command in your terminal

The documentation below focuses primarily on the Python API - the functions and classes you can use when importing the package in your own Python scripts. For CLI usage, please refer to the README.

## Scraping Components

### `scrape_bis()`

Main function to scrape speeches from the BIS website.

```python
from bis_scraper.scrapers.controller import scrape_bis
from pathlib import Path
import datetime

result = scrape_bis(
    data_dir: Path,              # Base directory for data storage
    log_dir: Path,               # Directory for log files
    start_date: datetime.date,   # Start date for scraping (optional, default: 7 days ago)
    end_date: datetime.date,     # End date for scraping (optional, default: today)
    institutions: list[str],     # Specific institutions to scrape (optional, default: all)
    force: bool,                 # Whether to re-download existing files (default: False)
    limit: int                   # Maximum speeches to download (optional)
)
```

Returns a `ScrapingResult` object with the following attributes:
- `downloaded`: Number of speeches downloaded
- `skipped`: Number of speeches skipped (already existed)
- `failed`: Number of speeches that failed to download
- `errors`: Dictionary mapping file codes to error messages

### `BisScraper` Class

Low-level class for scraping speeches from the BIS website.

```python
from bis_scraper.scrapers.bis_scraper import BisScraper
from pathlib import Path

scraper = BisScraper(
    output_dir: Path,           # Directory to save downloaded files
    institutions: list[str],     # List of institutions to scrape (None = all)
    force_download: bool,        # Force re-download of existing files
    limit: int                   # Maximum number of speeches to download
)

# Scrape a specific date
scraper.scrape_date(date_obj)

# Get results
result = scraper.get_results()
```

## Conversion Components

### `convert_pdfs()`

Main function to convert PDF speeches to text.

```python
from bis_scraper.converters.controller import convert_pdfs
from pathlib import Path

result = convert_pdfs(
    data_dir: Path,             # Base directory for data storage
    log_dir: Path,              # Directory for log files
    institutions: list[str],    # Specific institutions to convert (optional, default: all)
    force: bool,                # Whether to re-convert existing files (default: False)
    limit: int                  # Maximum files to convert per institution (optional)
)
```

Returns a `ConversionResult` object with the following attributes:
- `successful`: Number of PDFs successfully converted
- `skipped`: Number of PDFs skipped (already converted)
- `failed`: Number of PDFs that failed to convert
- `errors`: Dictionary mapping file codes to error messages

### `PdfConverter` Class

Low-level class for converting PDFs to text.

```python
from bis_scraper.converters.pdf_converter import PdfConverter
from pathlib import Path

converter = PdfConverter(
    input_dir: Path,            # Directory containing PDF files
    output_dir: Path,           # Directory to save text files
    institutions: list[str],    # List of institutions to convert (None = all)
    force_convert: bool,        # Whether to re-convert existing files
    limit: int                  # Maximum number of files to convert per institution
)

# Convert files for a specific institution
converter.convert_institution("european_central_bank")

# Get results
result = converter.get_results()
```

## Utility Components

### Date Utils

```python
from bis_scraper.utils.date_utils import create_date_list, parse_date_code

# Create a list of date strings in format YYMMDD
date_list = create_date_list(start_date, end_date)

# Parse a date code from a BIS speech file
date_obj, letter_code = parse_date_code("220101a")
```

### Institution Utils

```python
from bis_scraper.utils.institution_utils import (
    normalize_institution_name,
    standardize_institution_name,
    get_institution_from_metadata,
    get_all_institutions
)

# Normalize institution name for filesystem use
norm_name = normalize_institution_name("European Central Bank")  # returns "european_central_bank"

# Standardize institution name using known aliases
std_name = standardize_institution_name("ECB")  # returns "european central bank"

# Extract institution name from speech metadata
inst = get_institution_from_metadata("Speech by Mr. Powell, Chairman of the Federal Reserve")

# Get all supported institutions as normalized names
insts = get_all_institutions()
```

### File Utils

```python
from bis_scraper.utils.file_utils import (
    create_directory,
    find_existing_files,
    format_filename,
    get_file_hash
)

# Create directory if it doesn't exist
create_directory(path)

# Find existing files with a specific extension in a directory
files = find_existing_files(directory, ".pdf")

# Format a filename for a BIS speech
filename = format_filename("r220101a", "European Central Bank")  # returns "220101a.pdf"

# Get SHA-256 hash of a file
file_hash = get_file_hash(file_path)
```

## Data Models

### ScrapingResult

```python
from bis_scraper.models import ScrapingResult

result = ScrapingResult()
result.downloaded = 10
result.skipped = 5
result.failed = 2
result.errors = {"220101a": "Error message"}
```

### ConversionResult

```python
from bis_scraper.models import ConversionResult

result = ConversionResult()
result.successful = 10
result.skipped = 5
result.failed = 2
result.errors = {"220101a": "Error message"}
```

## Command-Line Interface (CLI)

The package also provides a command-line interface that can be used in your terminal after installation:

```bash
# Get help
bis-scraper --help
```

### Main Commands

1. **scrape**: Download speeches from the BIS website
   ```bash
   bis-scraper scrape --start-date 2020-01-01 --end-date 2020-01-31
   ```

2. **convert**: Convert downloaded PDFs to text
   ```bash
   bis-scraper convert
   ```

3. **run-all**: Run both scraping and conversion in one command
   ```bash
   bis-scraper run-all --start-date 2020-01-01 --end-date 2020-01-31
   ```

### Common Options

- `--start-date TEXT`: Start date (YYYY-MM-DD format)
- `--end-date TEXT`: End date (YYYY-MM-DD format)
- `--institutions TEXT`: Filter by institution(s) (can be used multiple times)
- `--force`: Force re-download or re-conversion
- `--limit INTEGER`: Maximum number of speeches to process
- `--data-dir DIRECTORY`: Base directory for data storage
- `--log-dir DIRECTORY`: Directory for log files 