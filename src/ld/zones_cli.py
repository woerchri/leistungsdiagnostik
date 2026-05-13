"""Thin entry point for `uv run python -m ld.zones_cli`."""
from __future__ import annotations

import sys
from ld.zones_override import main

if __name__ == "__main__":
    sys.exit(main())
