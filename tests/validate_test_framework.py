#!/usr/bin/env python3
"""
Validate that the test framework is properly set up.
This script checks the structure and configuration of the testing framework.
"""
import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists and print status."""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_directory_exists(dirpath, description):
    """Check if a directory exists and print status."""
    exists = os.path.isdir(dirpath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {dirpath}")
    return exists


def check_python_import(module_name):
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ Python module importable: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Cannot import {module_name}: {e}")
        return False


def main():
    print("=" * 60)
    print("AlphaPulse Test Framework Validation")
    print("=" * 60)

    # Track results
    all_passed = True

    print("\n📁 Checking directory structure...")

    # Check test directories
    test_dirs = [
        ("tests/", "Test root directory"),
        ("tests/unit/", "Unit tests directory"),
        ("tests/data/", "Data quality tests directory"),
        ("tests/integration/", "Integration tests directory"),
        ("tests/e2e/", "End-to-end tests directory"),
        ("tests/performance/", "Performance tests directory"),
        ("tests/fixtures/", "Test fixtures directory"),
    ]

    for dirpath, description in test_dirs:
        if not check_directory_exists(dirpath, description):
            all_passed = False

    print("\n📄 Checking configuration files...")

    # Check config files
    config_files = [
        ("pytest.ini", "pytest configuration"),
        (".coveragerc", "coverage configuration"),
        ("tests/conftest.py", "Shared test fixtures"),
    ]

    for filepath, description in config_files:
        if not check_file_exists(filepath, description):
            all_passed = False

    print("\n🧪 Checking test files...")

    # Check test files
    test_files = [
        ("tests/unit/test_sentiment_classifier.py", "Sentiment classifier tests"),
        ("tests/unit/test_rss_parser.py", "RSS parser tests"),
        ("tests/unit/test_data_transformers.py", "Data transformers tests"),
        ("tests/unit/test_api_schemas.py", "API schemas tests"),
        ("tests/data/test_rss_schema.py", "RSS schema quality tests"),
        ("tests/data/test_sentiment_output.py", "Sentiment output quality tests"),
        ("tests/data/test_data_freshness.py", "Data freshness tests"),
    ]

    for filepath, description in test_files:
        if not check_file_exists(filepath, description):
            all_passed = False

    print("\n📊 Checking test fixtures...")

    # Check fixture files
    fixture_files = [
        ("tests/fixtures/sample_rss_feed.xml", "Sample RSS feed fixture"),
    ]

    for filepath, description in fixture_files:
        if not check_file_exists(filepath, description):
            all_passed = False

    print("\n🐍 Checking Python imports (basic)...")

    # Check basic imports
    basic_imports = [
        "pytest",
        "pydantic",
        "pandas",
    ]

    for module in basic_imports:
        if not check_python_import(module):
            all_passed = False

    print("\n🔧 Checking Makefile commands...")

    # Check Makefile exists and has test commands
    makefile_path = "Makefile"
    if check_file_exists(makefile_path, "Makefile"):
        try:
            with open(makefile_path, "r") as f:
                makefile_content = f.read()

            test_commands = [
                "test-unit",
                "test-integration",
                "test-data",
                "test-all",
                "test-coverage",
                "test-fast",
                "test-performance",
            ]

            for cmd in test_commands:
                if cmd in makefile_content:
                    print(f"✅ Makefile contains: {cmd}")
                else:
                    print(f"❌ Makefile missing: {cmd}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Error reading Makefile: {e}")
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 Test framework validation PASSED!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r mage_pipeline/requirements.txt")
        print("2. Run unit tests: make test-unit")
        print("3. Run data quality tests: make test-data")
        print("4. Check coverage: make test-coverage")
        return 0
    else:
        print("⚠️  Test framework validation FAILED!")
        print("\nPlease fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
