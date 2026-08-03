"""Entry point: python -m tools.code_review review --file <path>"""
import sys
from .review import main

if __name__ == "__main__":
    sys.exit(main())
