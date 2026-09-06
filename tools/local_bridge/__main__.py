"""Entry point for `python -m tools.local_bridge`."""

import sys

from tools.local_bridge.cli import main

if __name__ == "__main__":
    sys.exit(main())
