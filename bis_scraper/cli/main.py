"""Command-line interface for BIS Scraper.

Default paths:
- Data directory: ./data (from the current working directory)
- Log directory: ./logs (from the current working directory)
"""

import datetime
import logging
import pathlib
import sys
from typing import Optional, Tuple

import click

from bis_scraper import __version__
from bis_scraper.utils.constants import RAW_DATA_DIR


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--data-dir",
    "-d",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
    default=pathlib.Path("data"),
    help="Directory to store/read data files (default: ./data)",
)
@click.option(
    "--log-dir",
    "-l",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
    default=pathlib.Path("logs"),
    help="Directory to store log files (default: ./logs)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(
    ctx: click.Context,
    data_dir: pathlib.Path,
    log_dir: pathlib.Path,
    verbose: bool,
) -> None:
    """BIS Scraper - Download and process central bank speeches.

    This tool scrapes the Bank for International Settlements website
    for speeches from central banks globally and converts them to
    text format for further processing.

    Default paths:
    - Data directory: ./data (relative to current working directory)
    - Log directory: ./logs (relative to current working directory)

    Date Ranges:
    - By default, the scraper looks for speeches from 1 year ago to 30 days ago
    - For best results, specify dates known to have speeches with --start-date and --end-date
    - Recent dates (within the last week) may not have speeches published yet
    """
    # Create base directories
    data_dir.mkdir(exist_ok=True)
    log_dir.mkdir(exist_ok=True)

    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "bis_scraper.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Store configuration in context
    ctx.ensure_object(dict)
    ctx.obj["data_dir"] = data_dir
    ctx.obj["log_dir"] = log_dir
    ctx.obj["verbose"] = verbose


@main.command()
@click.option(
    "--start-date",
    "-s",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=lambda: (datetime.datetime.now() - datetime.timedelta(days=365)).strftime(
        "%Y-%m-%d"
    ),
    help="Start date for speeches (YYYY-MM-DD), defaults to 1 year ago",
)
@click.option(
    "--end-date",
    "-e",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=lambda: (datetime.datetime.now() - datetime.timedelta(days=30)).strftime(
        "%Y-%m-%d"
    ),
    help="End date for speeches (YYYY-MM-DD), defaults to 30 days ago",
)
@click.option(
    "--institutions",
    "-i",
    multiple=True,
    help="Specific institutions to scrape (can be used multiple times)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force download even if speeches already exist",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of speeches to download per day",
)
@click.pass_context
def scrape(
    ctx: click.Context,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    institutions: Tuple[str, ...],
    force: bool,
    limit: Optional[int],
) -> None:
    """Scrape speeches from the BIS website."""
    from bis_scraper.scrapers.controller import scrape_bis

    data_dir = ctx.obj["data_dir"]
    log_dir = ctx.obj["log_dir"]

    click.echo("Starting BIS web scraping...")
    click.echo(f"Data directory: {data_dir.absolute()}")
    click.echo(f"Date range: {start_date.date()} to {end_date.date()}")
    scrape_bis(
        data_dir=data_dir,
        log_dir=log_dir,
        start_date=start_date,
        end_date=end_date,
        institutions=institutions if institutions else None,
        force=force,
        limit=limit,
    )
    click.echo("Scraping completed!")


@main.command()
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date for conversion (format: YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date for conversion (format: YYYY-MM-DD)",
)
@click.option(
    "--institutions",
    "-i",
    multiple=True,
    help="Specific institutions to convert (can be used multiple times)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force conversion even if text files already exist",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of files to convert per institution",
)
@click.pass_context
def convert(
    ctx: click.Context,
    start_date: Optional[click.DateTime],
    end_date: Optional[click.DateTime],
    institutions: Tuple[str, ...],
    force: bool,
    limit: Optional[int],
) -> None:
    """Convert PDF speeches to text format."""
    # Import inside function to avoid CLI import-time side effects
    from bis_scraper.converters.controller import convert_pdfs_dates

    data_dir = ctx.obj["data_dir"]
    log_dir = ctx.obj["log_dir"]

    click.echo("Starting PDF to text conversion...")
    click.echo(f"Data directory: {data_dir.absolute()}")
    convert_pdfs_dates(
        data_dir=data_dir,
        log_dir=log_dir,
        start_date=start_date,
        end_date=end_date,
        institutions=institutions if institutions else None,
        force=force,
        limit=limit,
    )
    click.echo("Conversion completed!")


@main.command()
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date for processing (format: YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date for processing (format: YYYY-MM-DD)",
)
@click.option(
    "--institutions",
    "-i",
    multiple=True,
    help="Specific institutions to process (can be used multiple times)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force re-processing even if files already exist",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of speeches/files to process",
)
@click.pass_context
def run_all(
    ctx: click.Context,
    start_date: Optional[click.DateTime],
    end_date: Optional[click.DateTime],
    institutions: tuple[str, ...],
    force: bool,
    limit: Optional[int],
) -> None:
    """Run both scraping and conversion steps."""
    ctx.invoke(
        scrape,
        start_date=start_date,
        end_date=end_date,
        institutions=institutions,
        force=force,
        limit=limit,
    )
    # Call convert with the same date range
    ctx.invoke(
        convert,
        start_date=start_date,
        end_date=end_date,
        institutions=institutions,
        force=force,
        limit=limit,
    )


@main.command()
@click.pass_context
def clear_cache(ctx: click.Context) -> None:
    """Clear the date cache to force re-checking of all dates."""
    data_dir = ctx.obj["data_dir"]
    cache_file = data_dir / RAW_DATA_DIR / ".bis_scraper_date_cache.json"

    if cache_file.exists():
        try:
            # Read cache to show info
            import json

            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                num_dates = len(cache_data.get("dates", {}))

            # Confirm with user
            if click.confirm(f"Clear date cache containing {num_dates} checked dates?"):
                cache_file.unlink()
                click.echo(f"✅ Date cache cleared ({num_dates} dates removed)")
            else:
                click.echo("❌ Cache clearing cancelled")
        except Exception as e:
            click.echo(f"Error reading cache file: {e}", err=True)
            if click.confirm("Delete the cache file anyway?"):
                cache_file.unlink()
                click.echo("✅ Cache file deleted")
    else:
        click.echo("No date cache found. Nothing to clear.")


@main.command()
@click.pass_context
def show_cache_info(ctx: click.Context) -> None:
    """Show information about the date cache."""
    data_dir = ctx.obj["data_dir"]
    cache_file = data_dir / RAW_DATA_DIR / ".bis_scraper_date_cache.json"

    if not cache_file.exists():
        click.echo("No date cache found.")
        return

    try:
        import json

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        dates = cache_data.get("dates", {})
        updated = cache_data.get("updated", "Unknown")

        click.echo("Date cache information:")
        click.echo(f"  Location: {cache_file}")
        click.echo(f"  Last updated: {updated}")
        click.echo(f"  Total cached dates: {len(dates)}")

        # Show some statistics
        dates_with_speeches = sum(
            1 for d in dates.values() if d.get("had_speeches", False)
        )
        total_files = sum(d.get("files_found", 0) for d in dates.values())

        click.echo(f"  Dates with speeches: {dates_with_speeches}")
        click.echo(f"  Dates without speeches: {len(dates) - dates_with_speeches}")
        click.echo(f"  Total files found: {total_files}")

        # Show date range if available
        if dates:
            date_keys = [k.split("|")[0] for k in dates.keys()]  # Extract date part
            min_date = min(date_keys)
            max_date = max(date_keys)
            click.echo(f"  Date range: {min_date} to {max_date}")

    except Exception as e:
        click.echo(f"Error reading cache file: {e}", err=True)


if __name__ == "__main__":
    # Use Click's command line interface - no parameters needed here
    # Click will handle the argument parsing
    main()
