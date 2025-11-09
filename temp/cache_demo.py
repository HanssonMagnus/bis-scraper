#!/usr/bin/env python3
"""Demo script to show the date cache performance improvement."""

import datetime
import time
from pathlib import Path

from bis_scraper.scrapers.bis_scraper import BisScraper


def main() -> None:
    """Run a demo showing cache performance."""
    # Create a temporary directory for the demo
    demo_dir = Path("temp/demo_output")
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Initialize scraper
    scraper = BisScraper(demo_dir)

    # Test dates (using dates from 2020 as they likely have speeches)
    test_dates = [
        datetime.date(2020, 1, 1),
        datetime.date(2020, 1, 2),
        datetime.date(2020, 1, 3),
    ]

    print("=== BIS Scraper Date Cache Demo ===\n")

    # First run - no cache
    print("🔍 First run (no cache):")
    start_time = time.time()

    for date in test_dates:
        print(f"  Checking {date}...", end=" ", flush=True)
        date_start = time.time()
        scraper.scrape_date(date)
        date_time = time.time() - date_start
        print(f"took {date_time:.2f}s")

    first_run_time = time.time() - start_time
    print(f"\n  Total time: {first_run_time:.2f}s")
    print(f"  Results: {scraper.result.downloaded} downloaded, {scraper.result.skipped} skipped")

    # Save the cache
    scraper._save_date_cache()

    # Second run - with cache
    print("\n🚀 Second run (with cache):")
    scraper2 = BisScraper(demo_dir)  # New instance will load the cache
    start_time = time.time()

    for date in test_dates:
        print(f"  Checking {date}...", end=" ", flush=True)
        date_start = time.time()
        scraper2.scrape_date(date)
        date_time = time.time() - date_start
        print(f"took {date_time:.3f}s")

    second_run_time = time.time() - start_time
    print(f"\n  Total time: {second_run_time:.3f}s")
    print(f"  Results: {scraper2.result.downloaded} downloaded, {scraper2.result.skipped} skipped")

    # Show improvement
    improvement = (first_run_time - second_run_time) / first_run_time * 100
    speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')

    print(f"\n✨ Performance improvement:")
    print(f"  Time saved: {first_run_time - second_run_time:.2f}s ({improvement:.1f}%)")
    print(f"  Speedup: {speedup:.0f}x faster")

    # Show cache info
    cache_file = demo_dir / ".bis_scraper_date_cache.json"
    if cache_file.exists():
        print(f"\n📁 Cache file: {cache_file}")
        print(f"  Size: {cache_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
