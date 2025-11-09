# BIS Scraper Helper Scripts

This directory contains helper scripts for running and analyzing BIS Scraper operations.

## Available Scripts

### `run_full_scrape.sh`

Script to run a full BIS speech scraping and conversion process. This script downloads speeches from the BIS website and converts them to text.

**Usage:**
```bash
./run_full_scrape.sh
```

**Configuration:**
Edit the variables at the top of the script to customize:
- Data directory
- Date range
- Institution filtering
- Force download options
- Speech limits

### `analyze_results.sh`

Script to analyze the results of the BIS scraping process. Provides statistics on the downloaded PDFs and converted text files.

**Usage:**
```bash
./analyze_results.sh [path_to_data_dir]
```

If no data directory is specified, the script will use the default (`$HOME/bis_full_data`).

**Output:**
- Counts of PDF and text files
- Breakdown by institution
- Breakdown by year
- Conversion success rate
- Recent log entries

## Running a Full Scraping Process

1. **Configure the scraping job**:
   ```bash
   nano scripts/run_full_scrape.sh
   ```

2. **Run the scraping process**:
   ```bash
   cd scripts
   ./run_full_scrape.sh
   ```

   For long-running jobs, consider using screen or tmux:
   ```bash
   screen -S bis_scraper
   cd scripts
   ./run_full_scrape.sh
   # Detach with Ctrl+A followed by D
   # Reattach later with: screen -r bis_scraper
   ```

3. **Analyze the results**:
   ```bash
   cd scripts
   ./analyze_results.sh
   ```
