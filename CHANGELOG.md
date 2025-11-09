# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-09

### Added
- Initial release
- Command-line interface (CLI) for scraping and converting speeches
- Python API for programmatic use
- Date-based caching system to avoid redundant HTTP requests
- Support for filtering by institutions
- PDF to text conversion using textract
- Structured metadata extraction and JSON storage
- Comprehensive test suite with unit and integration tests
- Full documentation including README and API documentation
- Support for date range filtering
- Progress reporting during long-running operations

### Features
- Download speeches from BIS website by date range
- Filter by specific central bank institutions
- Convert PDFs to text format
- Clean organization structure (by institution)
- Efficient caching to skip already-processed dates
- Configurable output directories
- Error handling and logging

[0.1.0]: https://github.com/HanssonMagnus/bis-scraper/releases/tag/v0.1.0
