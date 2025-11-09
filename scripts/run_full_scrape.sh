#!/bin/bash
# Script to run a full BIS speech scraping and conversion process
# Usage: ./run_full_scrape.sh

# ======= Configuration =======
# Limit number
#LIMIT_NUM=5

# Data storage locations
DATA_DIR="../data/bis_full_data"
LOG_DIR="../data/bis_full_data/logs"

# Date range (format: YYYY-MM-DD)
#START_DATE="1997-01-01"   # BIS speeches start around 1997
START_DATE="2025-08-01"   # BIS speeches start around 1997
#START_DATE=$(date +%Y-%m-%d)  # Today's date
END_DATE=$(date +%Y-%m-%d)  # Today's date

# Filtering (leave empty "" for all institutions)
# Example: INSTITUTIONS=("European Central Bank" "Federal Reserve")
INSTITUTIONS=()

# Force download even if files exist
FORCE=false  # Set to "true" to force re-download

# ======= Setup =======
# Create directories if they don't exist
mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

# Log file for the whole process
LOGFILE="$LOG_DIR/full_scrape_$(date +%Y%m%d_%H%M%S).log"

# ======= Build the command =======
# Start with base command
CMD="bis-scraper"

# Complete the command with data and log directories
CMD="$CMD --data-dir \"$DATA_DIR\" --log-dir \"$LOG_DIR\" run-all --start-date $START_DATE --end-date $END_DATE"

# Add institutions if specified
for INST in "${INSTITUTIONS[@]}"; do
    CMD="$CMD --institutions \"$INST\""
done

# Add force flag if enabled
if [ "$FORCE" = true ]; then
    CMD="$CMD --force"
fi

# Add limit if specified - note: this sets a TOTAL limit across all dates, not per day
if [ ! -z "$LIMIT_NUM" ] && [ "$LIMIT_NUM" -gt 0 ]; then
    CMD="$CMD --limit $LIMIT_NUM"
fi

# ======= Execute =======
echo "========================================================"
echo "BIS Scraper - Full Run"
echo "========================================================"
echo "Start date: $START_DATE"
echo "End date: $END_DATE"
echo "Data directory: $DATA_DIR"
echo "Log directory: $LOG_DIR"
echo "Force download: $FORCE"
echo "Verbose: $VERBOSE"
if [ ${#INSTITUTIONS[@]} -gt 0 ]; then
    echo "Filtering by institutions: ${INSTITUTIONS[*]}"
else
    echo "Downloading speeches from all institutions"
fi
if [ ! -z "$LIMIT_NUM" ] && [ "$LIMIT_NUM" -gt 0 ]; then
    echo "Limit: $LIMIT_NUM speeches (TOTAL across all dates)"
    echo "NOTE: The process should stop after downloading $LIMIT_NUM speeches in total"
    echo "      If it doesn't, check the logs for 'Reached download limit' message"
else
    echo "No limit set - will download all available speeches"
fi
echo "Log file: $LOGFILE"
echo "========================================================"
echo "Starting scrape at $(date)"
echo "This may take several hours. Check the log file for progress."
echo "Command: $CMD"
echo "========================================================"

# Run the command and log output
echo "Starting BIS scraping process at $(date)" > "$LOGFILE"
echo "Command: $CMD" >> "$LOGFILE"
echo "=======================================================" >> "$LOGFILE"

# Actually execute the command
eval $CMD 2>&1 | tee -a "$LOGFILE"

# Report completion
echo "=======================================================" >> "$LOGFILE"
echo "Process completed at $(date)" >> "$LOGFILE"
echo "========================================================"
echo "Process completed at $(date)"
echo "Log file saved to: $LOGFILE"
echo "Data saved to: $DATA_DIR"

# Check if limit was applied
if [ ! -z "$LIMIT_NUM" ] && [ "$LIMIT_NUM" -gt 0 ]; then
    if grep -q "Reached download limit" "$LOGFILE"; then
        echo "✅ Download limit was applied successfully (found 'Reached download limit' in log)"
    else
        echo "⚠️  WARNING: Didn't find 'Reached download limit' message in log."
        echo "    This might mean the limit wasn't applied properly."
        echo "    Try checking the logs or the downloaded files manually."
    fi
fi
