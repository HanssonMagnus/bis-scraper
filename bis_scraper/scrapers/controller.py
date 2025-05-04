"""Controller module for BIS scraper operations."""

import datetime
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

from bis_scraper.models import ScrapingResult
from bis_scraper.scrapers.bis_scraper import BisScraper
from bis_scraper.utils.constants import RAW_DATA_DIR
from bis_scraper.utils.file_utils import create_directory
from bis_scraper.utils.date_utils import create_date_list
from bis_scraper.utils.institution_utils import normalize_institution_name

logger = logging.getLogger(__name__)


def scrape_bis(
    data_dir: Path,
    log_dir: Path,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    institutions: Optional[Tuple[str, ...]] = None,
    force: bool = False,
    limit: Optional[int] = None,
) -> ScrapingResult:
    """Scrape speech data from the BIS website.
    
    Args:
        data_dir: Base directory for data storage
        log_dir: Directory for log files
        start_date: Start date for scraping
        end_date: End date for scraping
        institutions: Specific institutions to scrape (default: all)
        force: Whether to force re-scraping existing files
        limit: Maximum number of speeches to download per day
        
    Returns:
        ScrapingResult with statistics
    """
    start_time = time.time()
    
    # Convert datetime objects to date objects
    start_date_obj = start_date.date() if start_date else datetime.date.today() - datetime.timedelta(days=7)
    end_date_obj = end_date.date() if end_date else datetime.date.today()
    
    # Check if we're scraping recent dates and provide warning
    today = datetime.date.today()
    if (end_date_obj >= today - datetime.timedelta(days=3)):
        warning_msg = (
            f"WARNING: Scraping very recent dates (within 3 days of today: {today}). "
            f"The BIS website may not have speeches published yet for these dates. "
            f"Consider using --start-date and --end-date options to specify dates "
            f"further in the past if no speeches are found."
        )
        logger.warning(warning_msg)
        print(warning_msg)  # Print to stdout for CLI feedback
    
    # Create output directory
    output_dir = data_dir / RAW_DATA_DIR
    create_directory(output_dir)
    
    # Normalize institution names if provided
    normalized_institutions = [normalize_institution_name(i) for i in institutions] if institutions else None
    
    # Initialize scraper
    scraper = BisScraper(
        output_dir=output_dir,
        institutions=normalized_institutions,
        force_download=force,
        limit=limit,  # Pass the limit to BisScraper for fine-grained control
    )
    
    # Scrape data for each date in the range
    date_range = [
        start_date_obj + datetime.timedelta(days=x)
        for x in range((end_date_obj - start_date_obj).days + 1)
    ]
    
    total_dates = len(date_range)
    logger.info(f"Scraping speeches from {start_date_obj.isoformat()} to {end_date_obj.isoformat()} ({total_dates} days)")
    print(f"Scraping speeches from {start_date_obj.isoformat()} to {end_date_obj.isoformat()} ({total_dates} days)")
    
    # Track progress
    progress_interval = max(1, total_dates // 10)  # Report progress at 10% intervals
    
    for i, date_obj in enumerate(date_range, 1):
        try:
            # Show progress at intervals
            if i % progress_interval == 0 or i == total_dates:
                progress_pct = (i / total_dates) * 100
                logger.info(f"Progress: {i}/{total_dates} days ({progress_pct:.1f}%)")
                print(f"Progress: {i}/{total_dates} days ({progress_pct:.1f}%)")
                
            logger.info(f"Scraping data for {date_obj.isoformat()}")
            should_continue = scraper.scrape_date(date_obj)
            
            # Check if we need to stop (either from BisScraper's internal limit check or here)
            if not should_continue or (limit is not None and scraper.result.downloaded >= limit):
                # If BisScraper didn't already log this (from internal check), log it here
                if should_continue and limit is not None and scraper.result.downloaded >= limit:
                    logger.info(f"Reached download limit of {limit} speeches. Stopping.")
                    print(f"Reached download limit of {limit} speeches at date level. Stopping.")
                break
                
        except Exception as e:
            logger.error(f"Error scraping data for {date_obj.isoformat()}: {str(e)}", exc_info=True)
    
    # Get results
    result = scraper.get_results()
    
    # Log summary
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Calculate rate
    rate = (result.downloaded + result.skipped) / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(
        f"Scraping completed in {int(hours):02}:{int(minutes):02}:{seconds:05.2f}"
    )
    logger.info(
        f"Results: {result.downloaded} downloaded, {result.skipped} skipped, "
        f"{result.failed} failed (processing rate: {rate:.1f} speeches/second)"
    )
    
    # Print summary to stdout
    print(f"Scraping completed in {int(hours):02}:{int(minutes):02}:{seconds:05.2f}")
    print(f"Results: {result.downloaded} downloaded, {result.skipped} skipped, "
          f"{result.failed} failed (processing rate: {rate:.1f} speeches/second)")
    
    return result 