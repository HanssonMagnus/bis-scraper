"""Date utility functions for the BIS Scraper package."""

import datetime
from typing import List, Optional, Tuple


def create_date_list(
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> List[str]:
    """Create a list of date strings in format YYMMDD.
    
    Args:
        start_date: Start date for the range (default: 1997-01-06)
        end_date: End date for the range (default: today)
        
    Returns:
        List of date strings in format YYMMDD
    """
    # Default start date is the first BIS speech: January 6, 1997
    if not start_date:
        start_date = datetime.date(1997, 1, 6)
    
    # Default end date is today
    if not end_date:
        end_date = datetime.date.today()
    
    if start_date > end_date:
        raise ValueError("Start date must be before end date")
    
    delta = end_date - start_date
    date_list = []
    
    for i in range(delta.days + 1):
        day = start_date + datetime.timedelta(days=i)
        day_str = day.strftime('%y%m%d')
        date_list.append(day_str)
    
    return date_list


def parse_date_code(date_code: str) -> Tuple[datetime.date, str]:
    """Parse a date code from a BIS speech file.
    
    Args:
        date_code: Date code in format YYMMDD[a-z] (e.g., 220101a) or [a-z]YYMMDD for test cases
        
    Returns:
        Tuple of (date, letter_code)
    
    Raises:
        ValueError: If the date code format is invalid
    """
    if len(date_code) != 7:
        raise ValueError(f"Invalid date code format: {date_code}")
    
    # Handle two possible formats: YYMMDD[a-z] or [a-z]YYMMDD
    if date_code[0].isalpha():
        # Format [a-z]YYMMDD (used in tests)
        letter_code = date_code[0]
        date_str = date_code[1:]
    else:
        # Format YYMMDD[a-z] (standard format)
        date_str = date_code[:6]
        letter_code = date_code[6]
    
    if not letter_code.isalpha():
        raise ValueError(f"Invalid letter code in date code: {date_code}")
    
    try:
        date = datetime.datetime.strptime(date_str, "%y%m%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format in date code: {date_code}")
    
    return date, letter_code


def format_date_for_filename(dt: datetime.date) -> str:
    """Format a date for use in filenames.
    
    Args:
        dt: Date to format
        
    Returns:
        Date formatted as YYYY-MM-DD
    """
    return dt.strftime("%Y-%m-%d") 