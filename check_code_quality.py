#!/usr/bin/env python3
"""Script to run code quality checks for the BIS Scraper package."""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], name: str) -> bool:
    """Run a shell command and report its success.
    
    Args:
        command: Command to run as a list of arguments
        name: Name of the tool being run
    
    Returns:
        True if the command succeeded, False otherwise
    """
    print(f"\nRunning {name}...")
    try:
        subprocess.run(command, check=True)
        print(f"✅ {name} passed")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {name} failed")
        return False


def main() -> int:
    """Run code quality checks.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues automatically")
    args = parser.parse_args()
    
    pkg_dir = Path("bis_scraper")
    test_dir = Path("tests")
    
    # Check if directories exist
    if not pkg_dir.exists() or not test_dir.exists():
        print(f"Error: Could not find required directories: {pkg_dir} and {test_dir}")
        return 1
    
    # Define commands to run
    commands = []
    
    # Black (code formatting)
    black_cmd = ["black"]
    if not args.fix:
        black_cmd.append("--check")
    black_cmd.extend([str(pkg_dir), str(test_dir)])
    commands.append((black_cmd, "Black (code formatting)"))
    
    # isort (import sorting)
    isort_cmd = ["isort"]
    if not args.fix:
        isort_cmd.append("--check")
    isort_cmd.extend([str(pkg_dir), str(test_dir)])
    commands.append((isort_cmd, "isort (import sorting)"))
    
    # mypy (type checking)
    mypy_cmd = ["mypy", str(pkg_dir)]
    commands.append((mypy_cmd, "mypy (type checking)"))
    
    # ruff (linting)
    ruff_cmd = ["ruff"]
    if args.fix:
        ruff_cmd.append("--fix")
    ruff_cmd.extend([str(pkg_dir), str(test_dir)])
    commands.append((ruff_cmd, "ruff (linting)"))
    
    # Run all commands
    results = []
    for cmd, name in commands:
        cmd_result = run_command(cmd, name)
        results.append(cmd_result)
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for i, (cmd, name) in enumerate(commands):
        status = "PASS" if results[i] else "FAIL"
        print(f"{status}: {name}")
        if not results[i]:
            all_passed = False
    
    if all_passed:
        print("\n✅ All checks passed!")
        return 0
    else:
        print("\n❌ Some checks failed.")
        if not args.fix:
            print("Run with --fix to attempt to automatically fix issues")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 