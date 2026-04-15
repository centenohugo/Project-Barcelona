#!/usr/bin/env python3
"""
Setup script for the semantic chunking project.
Checks dependencies and helps configure API keys.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "anthropic",
        "sentence_transformers",
        "sklearn",
        "numpy",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing.append(package)

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("\nInstalling dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed!")


def check_api_key():
    """Check if ANTHROPIC_API_KEY is configured"""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        print(f"✓ ANTHROPIC_API_KEY is configured ({api_key[:10]}...)")
        return True

    print("\n⚠ ANTHROPIC_API_KEY not found")
    print("\nTo set it up:")

    if sys.platform == "win32":
        print("  PowerShell: $env:ANTHROPIC_API_KEY = 'your-key-here'")
        print("  CMD: set ANTHROPIC_API_KEY=your-key-here")
    else:
        print("  Linux/Mac: export ANTHROPIC_API_KEY='your-key-here'")

    print("\nOr create a .env file with: ANTHROPIC_API_KEY=your-key-here")
    return False


def check_data_structure():
    """Check if the data structure exists"""
    repo_root = Path(__file__).parent
    data_path = repo_root / "Data"

    if data_path.exists():
        student_dirs = list(data_path.glob("Student-*"))
        if student_dirs:
            print(f"✓ Data structure found ({len(student_dirs)} students)")
            return True

    print("⚠ Data structure not found")
    print(f"  Expected: {data_path}")
    return False


def main():
    print("=" * 60)
    print("SETUP: Semantic Chunking Script")
    print("=" * 60)

    print("\n[1] Checking Python version...")
    check_python_version()

    print("\n[2] Checking dependencies...")
    check_dependencies()

    print("\n[3] Checking API configuration...")
    api_configured = check_api_key()

    print("\n[4] Checking data structure...")
    data_exists = check_data_structure()

    print("\n" + "=" * 60)
    if api_configured and data_exists:
        print("✓ All checks passed! You can now run: python chunk_transcripts.py")
    else:
        print("⚠ Please complete the missing configuration before running the script")
    print("=" * 60)


if __name__ == "__main__":
    main()
