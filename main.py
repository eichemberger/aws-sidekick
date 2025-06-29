#!/usr/bin/env python3
"""
AWS Sidekick - Main Entry Point
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from api import main

if __name__ == "__main__":
    sys.exit(main())
