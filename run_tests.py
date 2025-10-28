#!/usr/bin/env python3
"""Script to run all tests for the BIS Scraper package."""

import argparse
import sys
import unittest
from pathlib import Path


def run_tests(test_type: str = "all", verbose: bool = False) -> int:
    """Run the specified tests.
    
    Args:
        test_type: Type of tests to run ("unit", "integration", or "all")
        verbose: Whether to run tests in verbose mode
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Set verbosity level
    verbosity = 2 if verbose else 1
    
    # Find the test directory
    test_dir = Path(__file__).parent / "tests"
    
    # Create test loader
    loader = unittest.TestLoader()
    
    if test_type == "unit" or test_type == "all":
        print("Running unit tests...")
        unit_dir = test_dir / "unit"
        
        # Run each unit test file separately to avoid Responses state issues
        unit_test_files = list(unit_dir.glob("test_*.py"))
        for test_file in unit_test_files:
            print(f"\nRunning {test_file.name}...")
            file_tests = loader.discover(start_dir=str(unit_dir), pattern=test_file.name)
            unit_runner = unittest.TextTestRunner(verbosity=verbosity)
            unit_result = unit_runner.run(file_tests)
            if not unit_result.wasSuccessful():
                return 1
    
    if test_type == "integration" or test_type == "all":
        print("\nRunning integration tests...")
        # For integration tests, we'll manually load them
        # This is more direct than using discover, which can have path issues
        sys.path.insert(0, str(Path(__file__).parent))
        
        try:
            from tests.integration.test_workflow import TestCompleteWorkflow
            
            # Create test suite and run it
            suite = unittest.TestLoader().loadTestsFromTestCase(TestCompleteWorkflow)
            integration_runner = unittest.TextTestRunner(verbosity=verbosity)
            integration_result = integration_runner.run(suite)
            if not integration_result.wasSuccessful():
                return 1
        except ImportError as e:
            print(f"Error importing integration tests: {e}")
            return 1
    
    if test_type == "all":
        print("\nRunning CLI tests...")
        # Manually import CLI tests to avoid discover path import issues
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        try:
            from tests.test_cli import TestCli

            cli_suite = unittest.TestLoader().loadTestsFromTestCase(TestCli)
            cli_runner = unittest.TextTestRunner(verbosity=verbosity)
            cli_result = cli_runner.run(cli_suite)
            if not cli_result.wasSuccessful():
                return 1
        except ImportError as e:
            print(f"Error importing CLI tests: {e}")
            return 1
    
    print("\nAll tests passed!")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BIS Scraper tests")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="Type of tests to run (unit, integration, or all)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Run tests in verbose mode"
    )
    
    args = parser.parse_args()
    sys.exit(run_tests(args.type, args.verbose)) 