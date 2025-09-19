"""Command-line interface for HTML2exe."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .builder import convert_html_to_exe
from .logging_utils import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="html2exe",
        description="Convert HTML projects to Windows executables",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Input HTML file or directory containing index.html",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Output EXE file path",
    )
    parser.add_argument(
        "--title",
        "-t",
        help="Window title (defaults to input filename)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="Window width in pixels (default: 1024)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=768,
        help="Window height in pixels (default: 768)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate inputs and show what would be built without building",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="HTML2exe 1.0.0",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    setup_logging(verbose=args.verbose)

    try:
        # Validate inputs
        if not args.input.exists():
            print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
            return 1

        if args.input.is_file() and args.input.suffix.lower() != ".html":
            print(f"Error: Input file must be HTML: {args.input}", file=sys.stderr)
            return 1

        if args.input.is_dir() and not (args.input / "index.html").exists():
            print(f"Error: Directory must contain index.html: {args.input}", file=sys.stderr)
            return 1

        # Convert
        convert_html_to_exe(args.input, args.output, args.title, args.width, args.height, args.check)
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
