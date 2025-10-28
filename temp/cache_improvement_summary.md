# Date Cache Performance Improvement

## Problem
The BIS scraper was slow on repeated runs because:
- It checked every possible date by iterating through letters a-z
- Even for dates with no speeches, it made at least one HTTP request
- For a full scrape from 1997 to today (~9,855 days), this meant thousands of unnecessary HTTP requests

## Solution
Implemented a date-level cache that:
1. **Tracks fully checked dates** - Once a date is completely processed, it's marked in the cache
2. **Stores metadata** - Records whether speeches were found and how many
3. **Supports filtered searches** - Separate cache entries for institution-filtered scrapes
4. **Persists between runs** - Cache is saved to `.bis_scraper_date_cache.json`

## Implementation Details

### Code Changes
1. **`bis_scraper/scrapers/bis_scraper.py`**:
   - Added date cache loading/saving functionality
   - Skip entire dates if found in cache
   - Track dates after processing (whether speeches found or not)
   - Institution-aware cache keys for filtered searches

2. **`bis_scraper/cli/main.py`**:
   - Added `show-cache-info` command to view cache statistics
   - Added `clear-cache` command to reset the cache when needed

3. **Tests**:
   - Created comprehensive unit tests in `tests/unit/test_date_cache.py`
   - All existing tests continue to pass

### Cache File Format
```json
{
  "version": 1,
  "dates": {
    "2023-01-01": {
      "checked_at": "2023-01-02T10:00:00",
      "had_speeches": true,
      "files_found": 3
    },
    "2023-01-02": {
      "checked_at": "2023-01-02T10:05:00",
      "had_speeches": false,
      "files_found": 0
    }
  },
  "updated": "2023-01-02T10:05:00"
}
```

## Performance Impact
- **First run**: Still needs to check all dates (no change)
- **Subsequent runs**: Skip dates entirely - no HTTP requests, no file checks
- **Expected speedup**: 100x-1000x for dates already in cache
- **Real-world impact**: Full scrape re-runs go from hours to minutes

## Usage
```bash
# Normal scraping - cache is used automatically
bis-scraper scrape --start-date 2020-01-01 --end-date 2020-12-31

# View cache information
bis-scraper show-cache-info

# Clear cache if needed (e.g., to force re-check)
bis-scraper clear-cache

# Force download bypasses cache
bis-scraper scrape --force --start-date 2020-01-01 --end-date 2020-12-31
```

## Backward Compatibility
- Fully backward compatible - existing scripts work without changes
- Cache is created automatically on first run
- Old installations can be upgraded without issues 