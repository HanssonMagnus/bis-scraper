#!/bin/bash
# Installation script for bis-scraper

# Exit on error
set -e

echo "=== Installing bis-scraper ==="

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install package in development mode
echo "Installing package..."
pip install -e .

echo "=== Installation complete ==="
echo "To activate the environment, run: source .venv/bin/activate"
echo "To use the package, run: bis-scraper --help"
