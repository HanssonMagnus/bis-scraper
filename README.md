# BIS Scraper

[![Tests](https://github.com/HanssonMagnus/bis-scraper/actions/workflows/tests.yml/badge.svg)](https://github.com/HanssonMagnus/bis-scraper/actions/workflows/tests.yml)
[![Python Versions](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11-blue)](https://github.com/HanssonMagnus/bis-scraper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)
[![Type Checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue)](https://github.com/python/mypy)

A Python package for downloading and processing central bank speeches from the Bank for International Settlements (BIS) website.

## Overview

BIS Scraper allows you to download speeches from various central banks worldwide that are collected on the BIS website. It organizes these speeches by institution, downloads the PDFs, and can convert them to text format for further analysis.

## Features

- Download speeches from the BIS website by date range
- Filter by specific institutions
- Convert PDFs to text format
- Clean organization structure for the downloaded files
- Efficient caching to avoid re-downloading existing files
- Command-line interface for easy usage

## Documentation

- [API Documentation](docs/api.md): Detailed information about the package's APIs
- [Test Coverage](docs/test_coverage.md): Testing approach and requirements
- [Project Plan](temp/project_plan.md): Current development status and roadmap

## Installation

### From PyPI (recommended)

```bash
pip install bis-scraper
```

### From Source

```bash
git clone https://github.com/HanssonMagnus/bis-scraper.git
cd bis-scraper
./install.sh  # This creates a virtual environment and installs the package
source .venv/bin/activate
```

### Dependencies

The package requires Python 3.9+ and the following main dependencies:
- requests
- beautifulsoup4
- textract
- click
- pydantic

## Usage

BIS Scraper provides two ways to use its functionality:

1. **Command-Line Interface (CLI)**: A terminal-based tool called `bis-scraper` for easy use
2. **Python API**: Functions and classes that can be imported into your Python scripts

Both methods provide the same core functionality but are suited for different use cases:
- Use the CLI for quick downloads or one-off tasks
- Use the Python API for integration with your own code or for more complex workflows

### Command-Line Interface

#### Download Speeches

Download speeches for a specific date range:

```bash
bis-scraper scrape --start-date 2020-01-01 --end-date 2020-01-31
```

Filter by institution:

```bash
bis-scraper scrape --start-date 2020-01-01 --end-date 2020-01-31 --institutions "European Central Bank" --institutions "Federal Reserve System"
```

Force re-download of existing files:

```bash
bis-scraper scrape --start-date 2020-01-01 --end-date 2020-01-31 --force
```

#### Convert to Text

Convert all downloaded PDFs to text:

```bash
bis-scraper convert
```

Convert only specific institutions:

```bash
bis-scraper convert --institutions "European Central Bank"
```

Convert only a specific date range (inclusive):

```bash
bis-scraper convert --start-date 2020-01-01 --end-date 2020-01-31
```

#### Run Both Steps

Run both scraping and conversion in one command:

```bash
bis-scraper run-all --start-date 2020-01-01 --end-date 2020-01-31
```

Note: The run-all command forwards the same date range to conversion, so only PDFs in that range are converted.

#### Cache Management

The scraper uses an intelligent date-based cache to avoid re-checking dates that have already been processed:

```bash
# Show information about the cache
bis-scraper show-cache-info

# Clear the cache to force re-checking all dates
bis-scraper clear-cache
```

The date cache significantly improves performance for repeated runs by:
- Skipping dates that have already been fully checked
- Avoiding unnecessary HTTP requests for dates with no speeches
- Maintaining separate cache entries for filtered institution searches

#### Helper Scripts

For large-scale scraping operations, we provide helper scripts in the `scripts` directory:

```bash
# Run a full scraping and conversion process
scripts/run_full_scrape.sh

# Analyze the results
scripts/analyze_results.sh
```

See [Scripts README](scripts/README.md) for more details.

### Python API

#### Basic Usage

```python
from pathlib import Path
import datetime
from bis_scraper.scrapers.controller import scrape_bis
from bis_scraper.converters.controller import convert_pdfs_dates

# Download speeches
result = scrape_bis(
    data_dir=Path("data"),
    log_dir=Path("logs"),
    start_date=datetime.datetime(2020, 1, 1),
    end_date=datetime.datetime(2020, 1, 31),
    institutions=["European Central Bank"],
    force=False,
    limit=None
)

# Convert to text (filtering to the same date range)
convert_result = convert_pdfs_dates(
    data_dir=Path("data"),
    log_dir=Path("logs"),
    start_date=datetime.datetime(2020, 1, 1),
    end_date=datetime.datetime(2020, 1, 31),
    institutions=["European Central Bank"],
    force=False,
    limit=None
)

# Print results
print(f"Downloaded: {result.downloaded}, Skipped: {result.skipped}, Failed: {result.failed}")
print(f"Converted: {convert_result.successful}, Skipped: {convert_result.skipped}, Failed: {convert_result.failed}")
```

#### Advanced Usage

```python
import datetime
import logging
from pathlib import Path
from bis_scraper.scrapers.controller import scrape_bis
from bis_scraper.converters.controller import convert_pdfs
from bis_scraper.utils.constants import INSTITUTIONS
from bis_scraper.utils.institution_utils import get_all_institutions

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bis_scraper.log"),
        logging.StreamHandler()
    ]
)

# Custom data directories
data_dir = Path("custom_data_dir")
log_dir = Path("logs")

# Get all available institutions
all_institutions = get_all_institutions()
print(f"Available institutions: {len(all_institutions)}")

# Select specific institutions
selected_institutions = [
    "European Central Bank",
    "Board of Governors of the Federal Reserve System",
    "Bank of England"
]

# Date ranges - past 3 months
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=90)

# Download with limit of 10 speeches per institution
scrape_result = scrape_bis(
    data_dir=data_dir,
    log_dir=log_dir,
    start_date=start_date,
    end_date=end_date,
    institutions=selected_institutions,
    force=False,
    limit=10
)

# Convert all downloaded speeches
convert_result = convert_pdfs(
    data_dir=data_dir,
    log_dir=log_dir,
    institutions=selected_institutions,
    force=False
)

# Process the results
print(f"Downloaded {scrape_result.downloaded} speeches")
print(f"Skipped {scrape_result.skipped} speeches")
if scrape_result.failed > 0:
    print(f"Failed to download {scrape_result.failed} speeches")

print(f"Converted {convert_result.successful} PDFs to text")
print(f"Skipped {convert_result.skipped} already converted PDFs")
if convert_result.failed > 0:
    print(f"Failed to convert {convert_result.failed} PDFs")
    for code, error in convert_result.errors.items():
        print(f"  - {code}: {error}")
```

## Data Organization

By default, the data is organized as follows:

```
data/
├── pdfs/                  # Raw PDF files
│   ├── european_central_bank/
│   │   ├── 200101a.pdf    # Speech from 2020-01-01, first speech of the day
│   │   ├── 200103b.pdf    # Speech from 2020-01-03, second speech of the day
│   │   └── metadata.json  # Structured metadata in JSON format
│   └── federal_reserve_system/
│       └── ...
└── texts/                 # Converted text files
    ├── european_central_bank/
    │   ├── 200101a.txt
    │   └── ...
    └── federal_reserve_system/
        └── ...
```

### Metadata JSON Format

Each institution directory contains a `metadata.json` file with structured information about the speeches:

```json
{
  "200101a": {
    "raw_text": "Original metadata text from the BIS website",
    "speech_type": "Speech",
    "speaker": "Ms Jane Smith",
    "role": "Governor of the Central Bank",
    "event": "Annual Banking Conference",
    "speech_date": "1 January 2020",
    "location": "Frankfurt, Germany",
    "organizer": "European Banking Association",
    "date": "2020-01-01"
  },
  "200103b": {
    ...
  }
}
```

The structured format makes it easier to extract specific information about each speech for analysis.

## Extending with Custom Text Processing

You can extend the functionality to perform custom text processing on the downloaded speeches. Here's an example:

```python
import glob
import os
from pathlib import Path
import re
import pandas as pd
from collections import Counter

def analyze_speeches(data_dir, institution, keywords):
    """Analyze text files for keyword frequency."""
    # Path to text files for the institution
    institution_dir = Path(data_dir) / "texts" / institution.lower().replace(" ", "_")
    results = []

    # Process each text file
    for txt_file in glob.glob(f"{institution_dir}/*.txt"):
        file_code = os.path.basename(txt_file).split('.')[0]

        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read().lower()

            # Count keywords
            word_counts = {}
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                word_counts[keyword] = len(re.findall(pattern, text))

            # Get total word count
            total_words = len(re.findall(r'\b\w+\b', text))

            # Add to results
            results.append({
                'file_code': file_code,
                'total_words': total_words,
                **word_counts
            })

    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    return df

# Example usage
keywords = ['inflation', 'recession', 'policy', 'interest', 'rate']
results_df = analyze_speeches('data', 'European Central Bank', keywords)

# Display summary
print(f"Analyzed {len(results_df)} speeches")
print("\nAverage word counts:")
for keyword in keywords:
    print(f"- {keyword}: {results_df[keyword].mean():.2f}")

# Most mentioned keywords by speech
print("\nSpeeches with most 'inflation' mentions:")
print(results_df.sort_values('inflation', ascending=False)[['file_code', 'inflation']].head())
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/HanssonMagnus/bis-scraper.git
cd bis-scraper

# Run the install script (creates virtual environment and installs package)
./install.sh

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

The project uses pytest for testing. Tests are organized into unit tests and integration tests.

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests with coverage report
pytest --cov=bis_scraper
```

### Code Quality

This project uses several tools to ensure code quality:

- `black` for code formatting
- `isort` for import sorting
- `mypy` for type checking
- `ruff` for linting

You can run all these checks using the provided script:

```bash
# Check code quality
./check_code_quality.py

# Fix issues automatically where possible
./check_code_quality.py --fix
```

Or run each tool individually:

```bash
# Format code
black bis_scraper tests
isort bis_scraper tests

# Check types
mypy bis_scraper

# Run linter
ruff bis_scraper tests
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) hooks to automatically run the full CI pipeline locally before each commit. This ensures that all code quality checks pass before pushing to the repository.

#### Installation

First, install pre-commit (if not already installed). If you've installed the dev dependencies, pre-commit is already included:

```bash
# If you've installed dev dependencies, pre-commit is already available
pip install -e ".[dev]"

# Or install pre-commit separately
pip install pre-commit
```

Then install the git hooks:

```bash
pre-commit install
```

This will set up the hooks to run automatically on every commit.

#### Running Manually

You can run all pre-commit hooks manually on all files:

```bash
pre-commit run --all-files
```

To run a specific hook:

```bash
pre-commit run <hook-id> --all-files
```

For example:
```bash
pre-commit run pytest --all-files
pre-commit run mypy --all-files
pre-commit run black --all-files
```

#### What the Hooks Do

The pre-commit hooks run the same checks as the CI pipeline:

1. **pytest** - Runs all tests
2. **mypy** - Type checking on `bis_scraper` package
3. **black** - Code formatting check
4. **isort** - Import sorting check
5. **ruff** - Linting

If any hook fails, the commit will be blocked. Fix the issues and try committing again.

#### Skipping Hooks (Not Recommended)

If you need to skip hooks for a specific commit (not recommended), you can use:

```bash
git commit --no-verify
```

However, the CI pipeline will still run these checks, so it's better to fix issues locally.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Before submitting your PR, please make sure:
- All tests pass
- Code is formatted with Black
- Imports are sorted with isort
- Type hints are correct (mypy)
- Linting passes with ruff

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bank for International Settlements for providing access to central bank speeches
- All the central banks for making their speeches publicly available
