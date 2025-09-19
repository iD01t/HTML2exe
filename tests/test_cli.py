"""Tests for CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from html2exe.cli import create_parser, main


class TestCLIParser:
    """Test command-line argument parsing."""

    def test_parser_creation(self):
        """Test parser is created successfully."""
        parser = create_parser()
        assert parser.prog == "html2exe"

    def test_required_arguments(self):
        """Test required arguments are enforced."""
        parser = create_parser()

        # Missing required arguments should raise SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_valid_arguments(self):
        """Test parsing valid arguments."""
        parser = create_parser()
        args = parser.parse_args([
            "--input", "test.html",
            "--output", "test.exe"
        ])

        assert args.input == Path("test.html")
        assert args.output == Path("test.exe")
        assert args.width == 1024  # default
        assert args.height == 768  # default
        assert not args.check
        assert not args.verbose

    def test_optional_arguments(self):
        """Test optional arguments."""
        parser = create_parser()
        args = parser.parse_args([
            "--input", "test.html",
            "--output", "test.exe",
            "--title", "My App",
            "--width", "800",
            "--height", "600",
            "--check",
            "--verbose"
        ])

        assert args.title == "My App"
        assert args.width == 800
        assert args.height == 600
        assert args.check
        assert args.verbose


class TestCLIMain:
    """Test main CLI function."""

    def test_nonexistent_input(self):
        """Test error handling for nonexistent input."""
        result = main([
            "--input", "nonexistent.html",
            "--output", "test.exe"
        ])
        assert result == 1

    def test_invalid_html_file(self):
        """Test error handling for non-HTML file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            txt_path = Path(f.name)

        try:
            result = main([
                "--input", str(txt_path),
                "--output", "test.exe"
            ])
            assert result == 1
        finally:
            txt_path.unlink()

    @patch("html2exe.cli.convert_html_to_exe")
    def test_successful_conversion(self, mock_convert):
        """Test successful conversion."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            html_path = Path(f.name)
            f.write(b"<html><body>Test</body></html>")

        try:
            result = main([
                "--input", str(html_path),
                "--output", "test.exe",
                "--check"
            ])
            assert result == 0
            mock_convert.assert_called_once()
        finally:
            html_path.unlink()

    def test_missing_index_html_in_directory(self):
        """Test error handling for directory without index.html."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = main([
                "--input", temp_dir,
                "--output", "test.exe"
            ])
            assert result == 1
