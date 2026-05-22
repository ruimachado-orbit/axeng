"""
Axeng CLI entry point for pip-installed environments.
Adds the package directory to sys.path so old-style imports
(from config import get, etc.) work without changes.
"""

import sys
from pathlib import Path

# Ensure the package directory is on sys.path
# This allows 'from config import get' to resolve to axeng/config.py
pkg_dir = str(Path(__file__).parent.resolve())
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from cli import main as cli_main


def main():
    cli_main()


if __name__ == "__main__":
    main()