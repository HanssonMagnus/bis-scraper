# Test Coverage

This document outlines the testing approach and coverage for the BIS Scraper package.

## Testing Structure

The project uses pytest as the testing framework and tests are organized into two main categories:

### Unit Tests

Located in `tests/unit/`, these tests focus on testing individual components in isolation:

- **test_date_utils.py**: Tests for date utility functions
- **test_institution_utils.py**: Tests for institution name parsing and normalization
- **test_file_utils.py**: Tests for file operations and path handling
- **test_bis_scraper.py**: Tests for the BIS scraper component
- **test_pdf_converter.py**: Tests for the PDF converter component

### Integration Tests

Located in `tests/integration/`, these tests verify that components work correctly together:

- **test_workflow.py**: Tests the full workflow from scraping to conversion

## Mocking Strategy

To avoid making actual network requests during testing, the tests use the `responses` library to mock HTTP responses. This allows tests to run quickly and reliably without depending on external services.

## Test Fixtures

Common test setup and teardown is handled using pytest fixtures defined in `tests/conftest.py`. These fixtures provide:

- Temporary directories for file operations
- Sample data for consistent testing
- Mock HTTP responses

## Running Tests

Tests can be run using several methods:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test files
pytest tests/unit/test_bis_scraper.py

# Run specific test functions
pytest tests/unit/test_bis_scraper.py::TestBisScraper::test_download_speech
```

## Test Coverage

The test suite aims to cover:

- All public functions and methods
- Error handling and edge cases
- Different parameter combinations
- Workflow integration scenarios

## Requirements for Contributors

When adding new features or modifying existing code, please ensure:

1. **New tests are added** for any new functionality
2. **Existing tests are updated** when modifying behavior
3. **Edge cases are considered** in test design
4. **Tests use mocks appropriately** to avoid external dependencies
5. **Integration impacts are tested** when changing core components

The project uses GitHub Actions to automatically run tests on pull requests, ensuring that all contributions maintain the expected quality standards. 