"""Entry point: `python -m videogen.clip_pool fetch --config ...`"""
import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
