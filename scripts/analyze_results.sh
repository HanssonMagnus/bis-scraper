#!/bin/bash
# Script to analyze the results of the BIS scraping process
# Usage: ./analyze_results.sh [path_to_data_dir]

# ======= Configuration =======
# Default data directory
DEFAULT_DATA_DIR="$HOME/bis_full_data"
DATA_DIR=${1:-$DEFAULT_DATA_DIR}

# Directories
PDF_DIR="$DATA_DIR/pdfs"
TXT_DIR="$DATA_DIR/texts"
LOG_DIR="$DATA_DIR/logs"

# ======= Helper Functions =======
check_directory() {
    if [ ! -d "$1" ]; then
        echo "ERROR: Directory $1 does not exist."
        return 1
    fi
    return 0
}

# ======= Main Analysis =======
echo "========================================================"
echo "BIS Scraper Results Analysis"
echo "========================================================"
echo "Data directory: $DATA_DIR"
echo "========================================================"

# Check if directories exist
if ! check_directory "$DATA_DIR"; then
    echo "The data directory does not exist. Did the scraping process run successfully?"
    exit 1
fi

# Check for log files
if check_directory "$LOG_DIR"; then
    echo "Log files found in $LOG_DIR"
    log_count=$(find "$LOG_DIR" -type f -name "*.log" | wc -l)
    echo "Number of log files: $log_count"
    
    # Find the most recent log file
    most_recent=$(find "$LOG_DIR" -type f -name "*.log" -printf "%T@ %p\n" | sort -n | tail -1 | cut -f2 -d' ')
    if [ ! -z "$most_recent" ]; then
        echo "Most recent log file: $most_recent"
        echo "Last few lines of log file:"
        echo "---"
        tail -10 "$most_recent"
        echo "---"
    fi
else
    echo "No log directory found."
fi

# Analyze PDF data
if check_directory "$PDF_DIR"; then
    echo -e "\n======= PDF files analysis ======="
    
    # Total PDFs
    total_pdfs=$(find "$PDF_DIR" -type f -name "*.pdf" | wc -l)
    echo "Total PDF files: $total_pdfs"
    
    # Count by institution
    echo -e "\nPDF files by institution:"
    echo "---"
    for inst_dir in "$PDF_DIR"/*; do
        if [ -d "$inst_dir" ]; then
            inst_name=$(basename "$inst_dir")
            inst_count=$(find "$inst_dir" -type f -name "*.pdf" | wc -l)
            echo "$inst_name: $inst_count"
        fi
    done
    echo "---"
    
    # Count by year (based on filename pattern YYMMDD[a-z].pdf)
    echo -e "\nPDF files by year:"
    echo "---"
    for year in {97..99} {00..23}; do
        year_count=$(find "$PDF_DIR" -type f -name "${year}????.pdf" | wc -l)
        if [ $year_count -gt 0 ]; then
            if [ $year -lt 50 ]; then
                display_year="20$year"
            else
                display_year="19$year"
            fi
            echo "$display_year: $year_count"
        fi
    done
    echo "---"
else
    echo "No PDF directory found."
fi

# Analyze TXT data
if check_directory "$TXT_DIR"; then
    echo -e "\n======= Text files analysis ======="
    
    # Total TXTs
    total_txts=$(find "$TXT_DIR" -type f -name "*.txt" | wc -l)
    echo "Total TXT files: $total_txts"
    
    # Count by institution
    echo -e "\nTXT files by institution:"
    echo "---"
    for inst_dir in "$TXT_DIR"/*; do
        if [ -d "$inst_dir" ]; then
            inst_name=$(basename "$inst_dir")
            inst_count=$(find "$inst_dir" -type f -name "*.txt" | wc -l)
            echo "$inst_name: $inst_count"
        fi
    done
    echo "---"
    
    # Conversion success rate
    if [ $total_pdfs -gt 0 ]; then
        success_rate=$(echo "scale=2; $total_txts * 100 / $total_pdfs" | bc)
        echo -e "\nConversion success rate: $success_rate%"
    fi
else
    echo "No TXT directory found."
fi

echo -e "\n========================================================"
echo "Analysis complete"
echo "========================================================" 